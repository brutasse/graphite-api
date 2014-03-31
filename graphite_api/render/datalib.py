"""Copyright 2008 Orbitz WorldWide

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License."""
from structlog import get_logger

from ..utils import epoch

logger = get_logger()


class TimeSeries(list):
    def __init__(self, name, start, end, step, values, consolidate='average'):
        list.__init__(self, values)
        self.name = name
        self.start = start
        self.end = end
        self.step = step
        self.consolidationFunc = consolidate
        self.valuesPerPoint = 1
        self.options = {}

    def __iter__(self):
        if self.valuesPerPoint > 1:
            return self.__consolidatingGenerator(list.__iter__(self))
        else:
            return list.__iter__(self)

    def consolidate(self, valuesPerPoint):
        self.valuesPerPoint = int(valuesPerPoint)

    def __consolidatingGenerator(self, gen):
        buf = []
        for x in gen:
            buf.append(x)
            if len(buf) == self.valuesPerPoint:
                while None in buf:
                    buf.remove(None)
                if buf:
                    yield self.__consolidate(buf)
                    buf = []
                else:
                    yield None
        while None in buf:
            buf.remove(None)
        if buf:
            yield self.__consolidate(buf)
        else:
            yield None
        raise StopIteration

    def __consolidate(self, values):
        usable = [v for v in values if v is not None]
        if not usable:
            return None
        if self.consolidationFunc == 'sum':
            return sum(usable)
        if self.consolidationFunc == 'average':
            return float(sum(usable)) / len(usable)
        if self.consolidationFunc == 'max':
            return max(usable)
        if self.consolidationFunc == 'min':
            return min(usable)
        raise Exception("Invalid consolidation function!")

    def __repr__(self):
        return 'TimeSeries(name=%s, start=%s, end=%s, step=%s)' % (
            self.name, self.start, self.end, self.step)


# Data retrieval API
def fetchData(requestContext, pathExpr):
    from ..app import app

    seriesList = []
    startTime = int(epoch(requestContext['startTime']))
    endTime = int(epoch(requestContext['endTime']))

    def _fetchData(pathExpr, startTime, endTime, requestContext, seriesList):
        matching_nodes = app.store.find(pathExpr, startTime, endTime)
        fetches = [
            (node, node.fetch(startTime, endTime)) for node in matching_nodes
            if node.is_leaf]

        for node, results in fetches:
            if not results:
                logger.info("no results", node=node, start=startTime,
                            end=endTime)
                continue

            try:
                timeInfo, values = results
            except ValueError as e:
                raise Exception("could not parse timeInfo/values from metric "
                                "'%s': %s" % (node.path, e))
            start, end, step = timeInfo

            series = TimeSeries(node.path, start, end, step, values)
            # hack to pass expressions through to render functions
            series.pathExpression = pathExpr
            seriesList.append(series)

        # Prune empty series with duplicate metric paths to avoid showing
        # empty graph elements for old whisper data
        names = set([s.name for s in seriesList])
        for name in names:
            series_with_duplicate_names = [
                s for s in seriesList if s.name == name]
            empty_duplicates = [
                s for s in series_with_duplicate_names
                if not nonempty(series)]

            if (
                series_with_duplicate_names == empty_duplicates and
                len(empty_duplicates) > 0
            ):  # if they're all empty
                empty_duplicates.pop()  # make sure we leave one in seriesList

            for series in empty_duplicates:
                seriesList.remove(series)

        return seriesList

    return _fetchData(pathExpr, startTime, endTime, requestContext, seriesList)


def nonempty(series):
    for value in series:
        if value is not None:
            return True
    return False
