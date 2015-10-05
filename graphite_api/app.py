import os
import csv
import json
import itertools
import math
import pytz
import shutil
import six
import tempfile
import time

from collections import defaultdict
from datetime import datetime
from io import StringIO, BytesIO

from flask import Flask
from structlog import get_logger
from werkzeug.http import http_date

from .config import configure
from .encoders import JSONEncoder
from .render.attime import parseATTime
from .render.datalib import fetchData, TimeSeries
from .render.glyph import GraphTypes
from .render.grammar import grammar
from .utils import RequestParams, hash_request

logger = get_logger()


def jsonify(data, status=200, headers=None):
    if headers is None:
        headers = {}

    jsonp = RequestParams.get('jsonp', False)

    body = json.dumps(data, cls=JSONEncoder)
    if jsonp:
        headers['Content-Type'] = 'text/javascript'
        body = '{0}({1})'.format(jsonp, body)
    else:
        headers['Content-Type'] = 'application/json'
    return body, status, headers


class Graphite(Flask):
    @property
    def store(self):
        return self.config['GRAPHITE']['store']

    @property
    def searcher(self):
        return self.config['GRAPHITE']['searcher']

    @property
    def functions(self):
        return self.config['GRAPHITE']['functions']

    @property
    def logger(self):
        # Flask has its own logger that doesn't get any handler if we use
        # dictconfig(). Replace it with our structlog logger.
        return logger


app = Graphite(__name__)
try:
    configure(app)
except Exception:
    import traceback
    print(traceback.format_exc())
    raise

methods = ('GET', 'POST')


# No-op routes, non-essential for creating dashboards
@app.route('/dashboard/find', methods=methods)
def dashboard_find():
    return jsonify({'dashboards': []})


@app.route('/dashboard/load/<name>', methods=methods)
def dashboard_load(name):
    return jsonify({'error': "Dashboard '{0}' does not exist.".format(name)},
                   status=404)


@app.route('/events/get_data', methods=methods)
def events():
    return json.dumps([]), 200, {'Content-Type': 'application/json'}


# API calls that actually do something
@app.route('/metrics', methods=methods)
@app.route('/metrics/find', methods=methods)
def metrics_find():
    errors = {}
    from_time = None
    until_time = None
    wildcards = False

    try:
        wildcards = bool(int(RequestParams.get('wildcards', 0)))
    except ValueError:
        errors['wildcards'] = 'must be 0 or 1.'

    try:
        from_time = int(RequestParams.get('from', -1))
    except ValueError:
        errors['from'] = 'must be an epoch timestamp.'
    try:
        until_time = int(RequestParams.get('until', -1))
    except ValueError:
        errors['until'] = 'must be an epoch timestamp.'

    if from_time == -1:
        from_time = None
    if until_time == -1:
        until_time = None

    format = RequestParams.get('format', 'treejson')
    if format not in ['treejson', 'completer']:
        errors['format'] = 'unrecognized format: "{0}".'.format(format)

    if 'query' not in RequestParams:
        errors['query'] = 'this parameter is required.'

    if errors:
        return jsonify({'errors': errors}, status=400)

    query = RequestParams['query']
    matches = sorted(
        app.store.find(query, from_time, until_time),
        key=lambda node: node.name
    )

    base_path = query.rsplit('.', 1)[0] + '.' if '.' in query else ''

    if format == 'treejson':
        data = tree_json(matches, base_path, wildcards=wildcards)
        return (
            json.dumps(data),
            200,
            {'Content-Type': 'application/json'}
        )

    results = []
    for node in matches:
        node_info = {
            'path': node.path,
            'name': node.name,
            'is_leaf': int(node.is_leaf),  # XXX Y was this cast to str
        }
        if not node.is_leaf:
            node_info['path'] += '.'
        results.append(node_info)

    if len(results) > 1 and wildcards:
        results.append({'name': '*'})

    return jsonify({'metrics': results})


@app.route('/metrics/expand', methods=methods)
def metrics_expand():
    errors = {}
    try:
        group_by_expr = bool(int(RequestParams.get('groupByExpr', 0)))
    except ValueError:
        errors['groupByExpr'] = 'must be 0 or 1.'
    try:
        leaves_only = bool(int(RequestParams.get('leavesOnly', 0)))
    except ValueError:
        errors['leavesOnly'] = 'must be 0 or 1.'

    if 'query' not in RequestParams:
        errors['query'] = 'this parameter is required.'
    if errors:
        return jsonify({'errors': errors}, status=400)

    results = defaultdict(set)
    for query in RequestParams.getlist('query'):
        for node in app.store.find(query):
            if node.is_leaf or not leaves_only:
                results[query].add(node.path)

    if group_by_expr:
        for query, matches in results.items():
            results[query] = sorted(matches)
    else:
        new_results = set()
        for value in results.values():
            new_results = new_results.union(value)
        results = sorted(new_results)

    return jsonify({'results': results})


@app.route('/metrics/index.json', methods=methods)
def metrics_index():
    index = set()
    if os.path.exists(app.searcher.index_path):
        with open(app.searcher.index_path, 'r') as f:
            index = set([line.strip() for line in f if line])
        if not index:
            recurse('*', index)
    else:
        recurse('*', index)
    return jsonify(sorted(index))


def prune_datapoints(series, max_datapoints, start, end):
    time_range = end - start
    points = time_range // series.step
    if max_datapoints < points:
        values_per_point = int(
            math.ceil(float(points) / float(max_datapoints))
        )
        seconds_per_point = values_per_point * series.step
        nudge = (
            seconds_per_point +
            (series.start % series.step) -
            (series.start % seconds_per_point)
        )
        series.start += nudge
        values_to_lose = nudge // series.step
        del series[:values_to_lose-1]
        series.consolidate(values_per_point)
        step = seconds_per_point
    else:
        step = series.step

    timestamps = range(series.start, series.end + series.step, step)
    datapoints = zip(series, timestamps)
    return {'target': series.name, 'datapoints': datapoints}


def recurse(query, index):
    """
    Recursively walk across paths, adding leaves to the index as they're found.
    """
    for node in app.store.find(query):
        if node.is_leaf:
            index.add(node.path)
        else:
            recurse('{0}.*'.format(node.path), index)


@app.route('/index', methods=['POST', 'PUT'])
def build_index():
    index = set()
    recurse('*', index)
    with tempfile.NamedTemporaryFile(delete=False) as index_file:
        index_file.write('\n'.join(sorted(index)).encode('utf-8'))
    shutil.move(index_file.name, app.searcher.index_path)
    app.searcher.reload()
    return jsonify({'success': True, 'entries': len(index)})


@app.route('/render', methods=methods)
def render():
    errors = {}
    graph_options = {
        'width': 600,
        'height': 300,
    }
    request_options = {}
    graph_type = RequestParams.get('graphType', 'line')
    try:
        graph_class = GraphTypes[graph_type]
        request_options['graphType'] = graph_type
        request_options['graphClass'] = graph_class
    except KeyError:
        errors['graphType'] = (
            "Invalid graphType '{0}', must be one of '{1}'.".format(
                graph_type, "', '".join(sorted(GraphTypes.keys()))))
    request_options['pieMode'] = RequestParams.get('pieMode', 'average')
    targets = RequestParams.getlist('target')
    if not len(targets):
        errors['target'] = 'This parameter is required.'
    request_options['targets'] = targets

    if 'rawData' in RequestParams:
        request_options['format'] = 'raw'
    if 'format' in RequestParams:
        request_options['format'] = RequestParams['format']
        if 'jsonp' in RequestParams:
            request_options['jsonp'] = RequestParams['jsonp']
    if 'maxDataPoints' in RequestParams:
        try:
            request_options['maxDataPoints'] = int(
                float(RequestParams['maxDataPoints']))
        except ValueError:
            errors['maxDataPoints'] = 'Must be an integer.'

    if errors:
        return jsonify({'errors': errors}, status=400)

    for opt in graph_class.customizable:
        if opt in RequestParams:
            value = RequestParams[opt]
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    if value.lower() in ('true', 'false'):
                        value = value.lower() == 'true'
                    elif value.lower() == 'default' or not value:
                        continue
            graph_options[opt] = value

    tzinfo = pytz.timezone(app.config['TIME_ZONE'])
    tz = RequestParams.get('tz')
    if tz:
        try:
            tzinfo = pytz.timezone(tz)
        except pytz.UnknownTimeZoneError:
            errors['tz'] = "Unknown timezone: '{0}'.".format(tz)
    request_options['tzinfo'] = tzinfo

    until_time = parseATTime(RequestParams.get('until', 'now'), tzinfo)
    from_time = parseATTime(RequestParams.get('from', '-1d'), tzinfo)

    start_time = min(from_time, until_time)
    end_time = max(from_time, until_time)
    if start_time == end_time:
        errors['from'] = errors['until'] = 'Invalid empty time range'

    request_options['startTime'] = start_time
    request_options['endTime'] = end_time

    use_cache = app.cache is not None and 'noCache' not in RequestParams
    cache_timeout = RequestParams.get('cacheTimeout')
    if cache_timeout is not None:
        cache_timeout = int(cache_timeout)

    if errors:
        return jsonify({'errors': errors}, status=400)

    # Done with options.

    if use_cache:
        request_key = hash_request()
        response = app.cache.get(request_key)
        if response is not None:
            return response

    headers = {
        'Last-Modified': http_date(time.time()),
        'Expires': http_date(time.time() + (cache_timeout or 60)),
        'Cache-Control': 'max-age={0}'.format(cache_timeout or 60)
    } if use_cache else {
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
    }

    context = {
        'startTime': request_options['startTime'],
        'endTime': request_options['endTime'],
        'tzinfo': request_options['tzinfo'],
        'data': [],
    }

    # Gather all data to take advantage of backends with fetch_multi
    paths = []
    for target in request_options['targets']:
        if request_options['graphType'] == 'pie':
            if ':' in target:
                continue
        if target.strip():
            paths += pathsFromTarget(target)
    data_store = fetchData(context, paths)

    if request_options['graphType'] == 'pie':
        for target in request_options['targets']:
            if ':' in target:
                name, value = target.split(':', 1)
                try:
                    value = float(value)
                except ValueError:
                    errors['target'] = "Invalid target: '{0}'.".format(target)
                context['data'].append((name, value))
            else:
                series_list = evaluateTarget(context, target, data_store)

                for series in series_list:
                    func = app.functions[request_options['pieMode']]
                    context['data'].append((series.name,
                                            func(context, series) or 0))

        if errors:
            return jsonify({'errors': errors}, status=400)

    else:  # graphType == 'line'
        for target in request_options['targets']:
            if not target.strip():
                continue
            series_list = evaluateTarget(context, target, data_store)
            context['data'].extend(series_list)

        request_options['format'] = request_options.get('format')

        if request_options['format'] == 'csv':
            response = BytesIO() if six.PY2 else StringIO()
            writer = csv.writer(response, dialect='excel')
            for series in context['data']:
                for index, value in enumerate(series):
                    ts = datetime.fromtimestamp(
                        series.start + index * series.step,
                        request_options['tzinfo']
                    )
                    writer.writerow((series.name,
                                     ts.strftime("%Y-%m-%d %H:%M:%S"), value))
            response.seek(0)
            headers['Content-Type'] = 'text/csv'
            return response.read(), 200, headers

        if request_options['format'] == 'json':
            series_data = []
            if 'maxDataPoints' in request_options and any(context['data']):
                start_time = min([s.start for s in context['data']])
                end_time = max([s.end for s in context['data']])
                for series in context['data']:
                    series_data.append(prune_datapoints(
                        series, request_options['maxDataPoints'],
                        start_time, end_time))
            else:
                for series in context['data']:
                    timestamps = range(series.start, series.end + series.step,
                                       series.step)
                    datapoints = zip(series, timestamps)
                    series_data.append({'target': series.name,
                                        'datapoints': datapoints})

            return jsonify(series_data, headers=headers)

        if request_options['format'] == 'raw':
            response = StringIO()
            for series in context['data']:
                response.write(u"%s,%d,%d,%d|" % (
                    series.name, series.start, series.end, series.step))
                response.write(u','.join(map(repr, series)))
                response.write(u'\n')
            response.seek(0)
            headers['Content-Type'] = 'text/plain'
            return response.read(), 200, headers

        if request_options['format'] == 'svg':
            graph_options['outputFormat'] = 'svg'

    graph_options['data'] = context['data']
    image = doImageRender(request_options['graphClass'], graph_options)

    use_svg = graph_options.get('outputFormat') == 'svg'

    if use_svg and 'jsonp' in request_options:
        headers['Content-Type'] = 'text/javascript'
        response = ('{0}({1})'.format(request_options['jsonp'],
                                      json.dumps(image.decode('utf-8'))),
                    200, headers)
    else:
        ctype = 'image/svg+xml' if use_svg else 'image/png'
        headers['Content-Type'] = ctype
        response = image, 200, headers

    if use_cache:
        app.cache.add(request_key, response, cache_timeout)
    return response


def pathsFromTarget(target):
    tokens = grammar.parseString(target)
    return list(pathsFromTokens(tokens))


def pathsFromTokens(tokens):
    iters = []
    if tokens.expression:
        iters.append(pathsFromTokens(tokens.expression))
    elif tokens.pathExpression:
        iters.append([tokens.pathExpression])
    elif tokens.call:
        iters.extend([pathsFromTokens(arg)
                      for arg in tokens.call.args])
        iters.extend([pathsFromTokens(kwarg.args[0])
                      for kwarg in tokens.call.kwargs])
    for path in itertools.chain(*iters):
        yield(path)


def evaluateTarget(requestContext, target, data_store):
    tokens = grammar.parseString(target)
    result = evaluateTokens(requestContext, tokens, data_store)

    if isinstance(result, TimeSeries):
        return [result]  # we have to return a list of TimeSeries objects

    return result


def evaluateTokens(requestContext, tokens, data_store):
    if tokens.expression:
        return evaluateTokens(requestContext, tokens.expression, data_store)

    elif tokens.pathExpression:
        return data_store.get_series_list(tokens.pathExpression)

    elif tokens.call:
        func = app.functions[tokens.call.funcname]
        args = [evaluateTokens(requestContext,
                               arg, data_store) for arg in tokens.call.args]
        kwargs = dict([(kwarg.argname,
                        evaluateTokens(requestContext,
                                       kwarg.args[0],
                                       data_store))
                       for kwarg in tokens.call.kwargs])
        ret = func(requestContext, *args, **kwargs)
        return ret

    elif tokens.number:
        if tokens.number.integer:
            return int(tokens.number.integer)
        elif tokens.number.float:
            return float(tokens.number.float)
        elif tokens.number.scientific:
            return float(tokens.number.scientific[0])

    elif tokens.string:
        return tokens.string[1:-1]

    elif tokens.boolean:
        return tokens.boolean[0] == 'true'


def tree_json(nodes, base_path, wildcards=False):
    results = []

    branchNode = {
        'allowChildren': 1,
        'expandable': 1,
        'leaf': 0,
    }
    leafNode = {
        'allowChildren': 0,
        'expandable': 0,
        'leaf': 1,
    }

    # Add a wildcard node if appropriate
    if len(nodes) > 1 and wildcards:
        wildcardNode = {'text': '*', 'id': base_path + '*'}

        if any(not n.is_leaf for n in nodes):
            wildcardNode.update(branchNode)

        else:
            wildcardNode.update(leafNode)

        results.append(wildcardNode)

    found = set()
    results_leaf = []
    results_branch = []
    for node in nodes:  # Now let's add the matching children
        if node.name in found:
            continue

        found.add(node.name)
        resultNode = {
            'text': str(node.name),
            'id': base_path + str(node.name),
        }

        if node.is_leaf:
            resultNode.update(leafNode)
            results_leaf.append(resultNode)
        else:
            resultNode.update(branchNode)
            results_branch.append(resultNode)

    results.extend(results_branch)
    results.extend(results_leaf)
    return results


def doImageRender(graphClass, graphOptions):
    pngData = BytesIO()
    img = graphClass(**graphOptions)
    img.output(pngData)
    imageData = pngData.getvalue()
    pngData.close()
    return imageData
