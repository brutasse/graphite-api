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
from collections import defaultdict

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
        self.pathExpression = name

    def __eq__(self, other):
        if isinstance(other, TimeSeries):
            color_eq = True
            if hasattr(self, 'color'):
                if hasattr(other, 'color'):
                    color_eq = (self.color == other.color)
                else:
                    color_eq = False
            elif hasattr(other, 'color'):
                color_eq = False

            return ((self.name, self.start, self.step, self.consolidationFunc,
                     self.valuesPerPoint, self.options) ==
                    (other.name, other.start, other.step,
                     other.consolidationFunc, other.valuesPerPoint,
                     other.options)) and list.__eq__(self, other) and color_eq
        return False

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
        return

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
        raise Exception(
            "Invalid consolidation function: '%s'" % self.consolidationFunc)

    def __repr__(self):
        return 'TimeSeries(name=%s, start=%s, end=%s, step=%s)' % (
            self.name, self.start, self.end, self.step)


class DataStore(object):
    """
    Simple object to store results of multi fetches.
    Also aids in looking up data by pathExpressions.
    """
    def __init__(self):
        self.paths = defaultdict(set)
        self.data = defaultdict(list)

    def get_paths(self, path_expr):
        """
        Returns all paths found for path_expr
        """
        return sorted(self.paths[path_expr])

    def add_data(self, path, time_info, data, exprs):
        """
        Stores data before it can be put into a time series
        """
        # Dont add if empty
        if not nonempty(data):
            for d in self.data[path]:
                if nonempty(d['values']):
                    return

        # Add data to path
        for expr in exprs:
            self.paths[expr].add(path)
        self.data[path].append({
            'time_info': time_info,
            'values': data
        })

    def get_series_list(self, path_expr):
        series_list = []
        for path in self.get_paths(path_expr):
            for data in self.data.get(path):
                start, end, step = data['time_info']
                series = TimeSeries(path, start, end, step, data['values'])
                series.pathExpression = path_expr
                series_list.append(series)
        return series_list


def fetchData(requestContext, pathExprs):
    from ..app import app
    startTime = int(epoch(requestContext['startTime']))
    endTime = int(epoch(requestContext['endTime']))
    if 'now' in requestContext:
        now = int(epoch(requestContext['now']))
    else:
        now = None

    # Convert to list if given single path
    if not isinstance(pathExprs, list):
        pathExprs = [pathExprs]

    data_store = DataStore()
    multi_nodes = defaultdict(list)
    single_nodes = []

    path_to_exprs = defaultdict(list)

    # Group nodes that support multiple fetches
    for pathExpr in pathExprs:
        for node in app.store.find(pathExpr, startTime, endTime):
            if not node.is_leaf:
                continue
            if node.path not in path_to_exprs:
                if hasattr(node, '__fetch_multi__'):
                    multi_nodes[node.__fetch_multi__].append(node)
                else:
                    single_nodes.append(node)
            path_to_exprs[node.path].append(pathExpr)

    # Multi fetches
    for finder in app.store.finders:
        if not hasattr(finder, '__fetch_multi__'):
            continue
        nodes = multi_nodes[finder.__fetch_multi__]
        if not nodes:
            continue
        try:
            time_info, series = finder.fetch_multi(nodes, startTime, endTime,
                                                   now, requestContext)
        except TypeError:
            time_info, series = finder.fetch_multi(nodes, startTime, endTime)
        for path, values in series.items():
            data_store.add_data(path, time_info, values,
                                path_to_exprs[path])

    # Single fetches
    fetches = [
        (node.path, node.fetch(startTime, endTime, now, requestContext))
        for node in single_nodes
    ]
    for path, results in fetches:
        if not results:
            logger.info("no results", path=path, start=startTime,
                        end=endTime)
            continue

        try:
            time_info, values = results
        except ValueError as e:
            raise Exception("could not parse timeInfo/values from metric "
                            "'%s': %s" % (path, e))
        data_store.add_data(path, time_info, values, path_to_exprs[path])

    return data_store


def nonempty(series):
    for value in series:
        if value is not None:
            return True
    return False
