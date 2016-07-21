import itertools
import re
import six

from .render.datalib import fetchData, TimeSeries
from .render.grammar import grammar


def pathsFromTarget(requestContext, target):
    tokens = grammar.parseString(target)
    paths = list(pathsFromTokens(requestContext, tokens))
    return paths


def pathsFromTokens(requestContext, tokens, replacements=None):
    iters = []

    if tokens.template:
        arglist = dict()
        if tokens.template.kwargs:
            for kwarg in tokens.template.kwargs:
                arg = kwarg.args[0]
                if arg.string:
                    arglist[kwarg.argname] = arg.string[1:-1]
        if tokens.template.args:
            for i, arg in enumerate(tokens.template.args):
                if arg.string:
                    arglist[str(i + 1)] = arg.string[1:-1]
        if 'template' in requestContext:
            arglist.update(requestContext['template'])
        iters.append(pathsFromTokens(requestContext, tokens.template, arglist))

    elif tokens.expression:
        iters.append(pathsFromTokens(requestContext, tokens.expression,
                                     replacements))

    elif tokens.pathExpression:
        expression = tokens.pathExpression
        if replacements:
            for name in replacements:
                val = replacements[name]
                expression = expression.replace('$'+name, str(val))
        iters.append([expression])

    elif tokens.call:
        if tokens.call.funcname == 'template':
            # if template propagates down here, it means the grammar didn't
            # match the invocation as tokens.template. this generally happens
            # if you try to pass non-numeric/string args
            raise ValueError("invalid template() syntax, only string/numeric "
                             "arguments are allowed")

        iters.extend([pathsFromTokens(requestContext, arg, replacements)
                      for arg in tokens.call.args])
        iters.extend([pathsFromTokens(requestContext, kwarg.args[0],
                                      replacements)
                      for kwarg in tokens.call.kwargs])

    for path in itertools.chain(*iters):
        yield path


def evaluateTarget(requestContext, target, data_store=None):
    tokens = grammar.parseString(target)

    if data_store is None:
        paths = list(pathsFromTokens(requestContext, tokens))
        data_store = fetchData(requestContext, paths)

    result = evaluateTokens(requestContext, tokens, data_store)
    if isinstance(result, TimeSeries):
        return [result]  # we have to return a list of TimeSeries objects

    return result


def evaluateTokens(requestContext, tokens, data_store=None, replacements=None):
    if data_store is None:
        paths = list(pathsFromTokens(requestContext, tokens))
        data_store = fetchData(requestContext, paths)

    if tokens.template:
        arglist = dict()
        if tokens.template.kwargs:
            args = [(kwarg.argname, evaluateTokens(requestContext,
                                                   kwarg.args[0],
                                                   data_store))
                    for kwarg in tokens.template.kwargs]
            arglist.update(dict(args))
        if tokens.template.args:
            args = [(str(i + 1), evaluateTokens(requestContext, arg,
                                                data_store))
                    for i, arg in enumerate(tokens.template.args)]
            arglist.update(dict(args))
        if 'template' in requestContext:
            arglist.update(requestContext['template'])
        return evaluateTokens(requestContext, tokens.template, data_store,
                              arglist)

    elif tokens.expression:
        return evaluateTokens(requestContext, tokens.expression, data_store,
                              replacements)

    elif tokens.pathExpression:
        expression = tokens.pathExpression
        if replacements:
            for name in replacements:
                val = replacements[name]
                if expression == '$'+name:
                    if not isinstance(val, six.string_types):
                        return val
                    elif re.match('^-?[\d.]+$', val):
                        return float(val)
                    else:
                        return val
                else:
                    expression = expression.replace('$'+name, str(val))
        return data_store.get_series_list(expression)

    elif tokens.call:
        if tokens.call.funcname == 'template':
            # if template propagates down here, it means the grammar didn't
            # match the invocation as tokens.template. this generally happens
            # if you try to pass non-numeric/string args
            raise ValueError("invalid template() syntax, only string/numeric "
                             "arguments are allowed")

        func = app.functions[tokens.call.funcname]
        args = [evaluateTokens(requestContext, arg, data_store, replacements)
                for arg in tokens.call.args]
        requestContext['args'] = tokens.call.args
        kwargs = dict([(kwarg.argname,
                        evaluateTokens(requestContext, kwarg.args[0],
                                       data_store, replacements))
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

    else:
        raise ValueError("unknown token in target evaluator")

from .app import app  # noqa
