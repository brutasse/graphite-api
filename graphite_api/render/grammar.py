from distutils.version import StrictVersion
from pyparsing import (
    ParserElement, Forward, Combine, Optional, Word, Literal, CaselessKeyword,
    CaselessLiteral, Group, FollowedBy, LineEnd, OneOrMore, ZeroOrMore,
    nums, alphas, alphanums, printables, delimitedList, QuotedString,
    __version__
)

ParserElement.enablePackrat()
grammar = Forward()

expression = Forward()

# Literals
intNumber = Combine(
    Optional('-') + Word(nums)
)('integer')

floatNumber = Combine(
    Optional('-') + Word(nums) + Literal('.') + Word(nums)
)('float')

sciNumber = Combine(
    (floatNumber | intNumber) + CaselessLiteral('e') + intNumber
)('scientific')

aString = QuotedString(quoteChar="'\"", escChar="\\")('string')

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

args = delimitedList(~kwarg + arg)    # lookahead to prevent failing on equals
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

if StrictVersion(__version__) >= StrictVersion('2.0.0'):
    expression <<= Group(call | pathExpression)('expression')
    grammar <<= expression
else:
    expression << (Group(call | pathExpression)('expression'))
    grammar << expression
