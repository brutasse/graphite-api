import itertools

from .render.datalib import fetchData, TimeSeries
from .render.grammar import grammar


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
        yield path


def evaluateTarget(requestContext, target, data_store=None):
    if data_store is None:
        paths = pathsFromTarget(target)
        data_store = fetchData(requestContext, paths)

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

from .app import app  # noqa
