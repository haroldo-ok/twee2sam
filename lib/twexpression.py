# -*- coding: utf-8 -*-

# Adapted from Fredrik Lundh's article "Simple Top-Down Parsing in Python"
# see http://effbot.org/zone/simple-top-down-parsing.htm

import sys
import re

import tokenize
from io import StringIO

#TODO: remove global usage
token = None
_next = None

# symbol (token type) registry

symbol_table = {}

class symbol_base(object):

    id = None
    value = None
    first = second = third = None

    def nud(self):
        raise SyntaxError("Syntax error (%r)." % self.id)

    def led(self, left):
        raise SyntaxError("Unknown operator (%r)." % self.id)

    def __repr__(self):
        if self.id in ("(name)","(literal)"):
            return "(%s %s)" % (self.id[1:-1], self.value)
        out = [self.id, self.first, self.second, self.third]
        out = map(str, filter(None, out))
        return "(%s)" % " ".join(out)

def symbol(id, bp=0):
    try:
        s = symbol_table[id]
    except KeyError:
        class s(symbol_base):
            pass
        s.__name__ = "symbol-" + id # for debugging
        s.id = id
        s.value = None
        s.lbp = bp
        symbol_table[id] = s
    else:
        s.lbp = max(bp, s.lbp)
    return s

# helpers

def infix(id, bp):
    def led(self, left):
        self.first = left
        self.second = expression(bp)
        return self
    symbol(id, bp).led = led

def infix_r(id, bp):
    def led(self, left):
        self.first = left
        self.second = expression(bp-1)
        return self
    symbol(id, bp).led = led

def prefix(id, bp):
    def nud(self):
        self.first = expression(bp)
        return self
    symbol(id).nud = nud

def advance(id=None):
    global token
    if id and token.id != id:
        raise SyntaxError("Expected %r" % id)
    token = _next()

def method(s):
    # decorator
    assert issubclass(s, symbol_base)
    def bind(fn):
        setattr(s, fn.__name__, fn)
    return bind

# python expression syntax

infix_r("or", 30); infix_r("and", 40); prefix("not", 50)

infix("is", 60);
infix("<", 60); infix("<=", 60)
infix(">", 60); infix(">=", 60)
infix("<>", 60); infix("!=", 60); infix("==", 60)

infix("+", 110); infix("-", 110)

infix("*", 120); infix("/", 120); infix("%", 120)

prefix("-", 130); prefix("+", 130)

symbol("(", 150)

# additional behaviour

symbol("(name)").nud = lambda self: self
symbol("(literal)").nud = lambda self: self

symbol("(end)")

symbol(")")

@method(symbol("("))
def nud(self):
    # parenthesized form; replaced by tuple former below
    expr = expression()
    advance(")")
    return expr

symbol(")"); symbol(",")

@method(symbol("("))
def led(self, left):
    self.first = left
    self.second = []
    if token.id != ")":
        while 1:
            self.second.append(expression())
            if token.id != ",":
                break
            advance(",")
    advance(")")
    return self

symbol(":"); symbol("=")

# constants

def constant(id):
    @method(symbol(id))
    def nud(self):
        self.id = "(literal)"
        self.value = id
        return self

constant("true")
constant("false")

# python tokenizer

def tokenize_python(program):
    type_map = {
        tokenize.NUMBER: "(literal)",
        tokenize.STRING: "(literal)",
        tokenize.OP: "(operator)",
        tokenize.NAME: "(name)"
        }
    try:
        tok = tokenize.generate_tokens(StringIO(u"%s" % program).__next__)
    except AttributeError:
        tok = tokenize.generate_tokens(StringIO(u"%s" % program).next)
    for t in tok:
        try:
            yield type_map[t[0]], t[1]
        except KeyError:
            if t[0] == tokenize.NL:
                continue
            if t[0] == tokenize.ENDMARKER:
                break
            else:
                raise SyntaxError("Syntax error")
    yield "(end)", "(end)"

def tokenizing(program):
    if isinstance(program, list):
        source = program
    else:
        # Hack to make JS boolean operators work with the Python tokenizer
        program = program.replace('&&', ' and ').replace('||', ' or ').replace('!', ' not ').replace('$', '').strip()
        source = tokenize_python(program)
    for id, value in source:
        if id == "(literal)":
            symbol = symbol_table[id]
            s = symbol()
            s.value = value
        else:
            # name or operator
            symbol = symbol_table.get(value)
            if symbol:
                s = symbol()
            elif id == "(name)":
                symbol = symbol_table[id]
                s = symbol()
                s.value = value
            else:
                raise SyntaxError("Unknown operator (%r)" % id)
        yield s

# parser engine

def expression(rbp=0):
    global token
    t = token
    token = _next()
    left = t.nud()
    while rbp < token.lbp:
        t = token
        token = _next()
        left = t.led(left)
    return left

def parse(program):
    global _next, token
    #import pdb; pdb.set_trace()
    try:
        _next = tokenizing(program).__next__
    except AttributeError:
        _next = tokenizing(program).next
    token = _next()
    return expression()

def test(program):
    print(">>>", program)
    print(parse(program))

#
# Code generation (maybe should be moved to another module)
#

CONST_TABLE = {
    'true': '1',
    'false': '0'
}

OPERATOR_TABLE = {
    'or': '+0>',
    'and': '*0>',
    'not': '0=',
    'is': '=',
    'is': '=',
    '==': '=',
    '<>': '=0=',
    '!=': '=0=',
    '<=': '>0=',
    '>=': '<0=',
    '%': '\\'
}

def to_sam(program, var_locator = lambda s: s + '?'):
    parsed = parse(program) if isinstance(program, str) else program

    def process_node(parsed):
        generated = []
        if parsed.id == '(literal)':
            # It's either a numeric literal or a constant
            generated.extend([CONST_TABLE.get(parsed.value, parsed.value), ' '])
        elif parsed.id == '(name)':
            # It's reading a variable
            var_name = var_locator(parsed.value)
            generated.extend([var_name, ' :' if var_name.isdigit() else ':'])
        elif parsed.id in ('+', '-'):
            # + and - can be either unary or binary.
            if parsed.second:
                # It's binary
                generated.extend([process_node(parsed.first), process_node(parsed.second), parsed.id])
            elif parsed.id == '-':
                # It's a negation
                generated.extend(['0 ', process_node(parsed.first), '-'])
            else:
                # It's a no-op
                generated.extend([process_node(parsed.first)])
        elif parsed.id == '(':
            # It's a function call
            function_name = parsed.first.value
            if function_name == 'random':
                params = parsed.second
                generated.extend(['r'])
                if len(params) == 1:
                    generated.extend([process_node(params[0]), '\\'])
                elif len(params) == 2:
                    generated.extend([process_node(params[1]), process_node(params[0]), '-1+\\', process_node(params[0]), '+'])
            else:
                raise SyntaxError("Unknown function (%r)" % function_name)
        elif parsed.second:
            # Assumes it's a binary operator
            generated.extend([process_node(parsed.first), process_node(parsed.second), OPERATOR_TABLE.get(parsed.id, parsed.id)])
        else:
            # Assumes it's an unary operator
            generated.extend([process_node(parsed.first), OPERATOR_TABLE.get(parsed.id, parsed.id)])

        return ''.join(generated)

    return process_node(parsed)