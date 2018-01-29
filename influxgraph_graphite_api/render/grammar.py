from distutils.version import StrictVersion

from pyparsing import (
    __version__, alphanums, alphas, CaselessKeyword, CaselessLiteral, Combine,
    delimitedList, FollowedBy, Forward, Group, LineEnd, Literal, OneOrMore,
    Optional, printables, quotedString, Regex, Word, ZeroOrMore,
)

grammar = Forward()

expression = Forward()

# Literals
intNumber = Regex(r'-?\d+')('integer')

floatNumber = Regex(r'-?\d+\.\d+')('float')

sciNumber = Combine(
    (floatNumber | intNumber) + CaselessLiteral('e') + intNumber
)('scientific')

aString = quotedString('string')

# Use lookahead to match only numbers in a list (can't remember why this
# is necessary)
afterNumber = FollowedBy(",") ^ FollowedBy(")") ^ FollowedBy(LineEnd())
number = Group(
    (sciNumber + afterNumber) |
    (floatNumber + afterNumber) |
    (intNumber + afterNumber)
)('number')

boolean = Group(
    CaselessKeyword("true") |
    CaselessKeyword("false")
)('boolean')

argname = Word(alphas + '_', alphanums + '_')('argname')
funcname = Word(alphas + '_', alphanums + '_')('funcname')

# Symbols
leftParen = Literal('(').suppress()
rightParen = Literal(')').suppress()
comma = Literal(',').suppress()
equal = Literal('=').suppress()

# Function calls

# Symbols
leftBrace = Literal('{')
rightBrace = Literal('}')
leftParen = Literal('(').suppress()
rightParen = Literal(')').suppress()
comma = Literal(',').suppress()
equal = Literal('=').suppress()
backslash = Literal('\\').suppress()

symbols = '''(){},=.'"\\'''
arg = Group(
    boolean |
    number |
    aString |
    expression
)('args*')
kwarg = Group(argname + equal + arg)('kwargs*')

# lookahead to prevent failing on equals
args = delimitedList(~kwarg + arg)
kwargs = delimitedList(kwarg)

call = Group(
    funcname + leftParen +
    Optional(
        args + Optional(
            comma + kwargs
        )
    ) + rightParen
)('call')

# Metric pattern (aka. pathExpression)
validMetricChars = ''.join((set(printables) - set(symbols)))
escapedChar = backslash + Word(symbols, exact=1)
partialPathElem = Combine(
    OneOrMore(
        escapedChar | Word(validMetricChars)
    )
)

matchEnum = Combine(
    leftBrace +
    delimitedList(partialPathElem, combine=True) +
    rightBrace
)

pathElement = Combine(
    Group(partialPathElem | matchEnum) +
    ZeroOrMore(matchEnum | partialPathElem)
)
pathExpression = delimitedList(pathElement,
                               delim='.', combine=True)('pathExpression')

litarg = Group(
    number | aString
)('args*')
litkwarg = Group(argname + equal + litarg)('kwargs*')

# lookahead to prevent failing on equals
litargs = delimitedList(~litkwarg + litarg)
litkwargs = delimitedList(litkwarg)

template = Group(
    Literal('template') + leftParen +
    (call | pathExpression) +
    Optional(comma + (litargs | litkwargs)) +
    rightParen
)('template')

if StrictVersion(__version__) >= StrictVersion('2.0.0'):
    expression <<= Group(template | call | pathExpression)('expression')
    grammar <<= expression
else:
    expression << (Group(template | call | pathExpression)('expression'))
    grammar << expression
