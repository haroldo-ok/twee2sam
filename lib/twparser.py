# -*- coding: utf-8 -*-

from __future__ import print_function
import sys, re, twexpression

__version__ = "0.2"

class TwParser(object):
    """Parses a TiddlyWiki object into an AST"""

    def __init__(self, tw):
        self.passages = {}
        self._parse(tw)

    def __repr__(self):
#		return "<TwParser\n" + '\n'.join(["\t" + str(psg) for psg in self.passages.values()]) + ">"
        return "<TwParser {0}>".format(ident_list(self.passages.values()))

    def _parse(self, tw):
        """Parses the TiddlyWiki object"""
        for tiddler in tw.tiddlers.values():
            self._parse_tiddler(tiddler)

    def _parse_tiddler(self, tiddler):
        """Parses a Tiddler object"""
        passage = Passage(tiddler)
        self.passages[passage.title] = passage


class Passage(object):
    """Represents a parsed passage"""

    RE_ITEM_LIST = re.compile(r'^([#\*])\s(.*)$', flags=re.MULTILINE)
    RE_MACRO = re.compile(r'\<\<(\w+)(\s*.*?)\>\>')
    RE_LINK = re.compile(r'\[\[(.*?)\]\]')
    RE_IMG = re.compile(r'\[img\[(.*?)\]\]')
    RE_TEXT = re.compile(r'(.*)', flags=re.DOTALL)

    def __init__(self, tiddler):
        self.title = tiddler.title
        self.commands = []
        self._parse(tiddler)

    def __repr__(self):
        return "<Passage {0}{1}>".format(self.title, ident_list(self.commands))

    def _parse(self, tiddler):
        tokens = self._tokenize(tiddler)
        self._block_stack = []
        self.commands += self._parse_commands(tokens)

    def _parse_commands(self, tokens):
        commands = []
        close_block = False

        while tokens and not close_block:
            token = tokens.pop(0)
            tk_type = token[0]
            if tk_type == 'tx':
                commands.append(TextCmd(token))
            elif tk_type == 'mc':
                macro = self._parse_macro(token, tokens)
                if macro:
                    if isinstance(macro, EndMacro):
                        close_block = True
                    else:
                        commands.append(macro)
            elif tk_type == 'im':
                commands.append(ImageCmd(token))
            elif tk_type == 'lk':
                commands.append(LinkCmd(token))
            elif tk_type in ('ul','ol'):
                commands.append(ListCmd(token, self._parse_commands(token[1])))

        return commands

    # Well, it's not really a tokenizer, more like a 1st level parser, but meh.
    def _tokenize(self, tiddler):
        # Remove the line continuations (\ followed by line break)
        source = re.sub(r'\\[ \t]*\n', '', tiddler.text)
        return self._tokenize_string(source)

    def _tokenize_string(self, string):
        def test_command(string, remaining_tests):
            # Determine what will be checked
            if not remaining_tests:
                return []

            regex, action, skipped_chars = remaining_tests[0]
            remaining_tests = remaining_tests[1:]

            # Starts checking for snippets matching the regex
            tokens = []

            st_pos = 0
            st_len = len(string)
            for item in regex.finditer(string):
                # Processes preceding non-matching text
                it_st = item.start()
                if st_pos < it_st and st_pos < st_len:
                    tokens += test_command(string[st_pos:it_st], remaining_tests)
                st_pos = item.end() + skipped_chars

                # Executes the action
                tokens += action(item)

            # Processes remaining text, if any.
            if st_pos < st_len:
                tokens += test_command(string[st_pos:st_len], remaining_tests)

            return tokens

        def process_item_list(match):
            kind = match.group(1)
            contents = match.group(2)
            list_type = 'ul' if kind == '*' else 'ol'
            return [(list_type, self._tokenize_string(contents.strip()))]

        def process_macro(match):
            return [('mc', (match.group(1), match.group(2)))]

        def process_image(match):
            return [('im', match.group(1))]

        def process_link(match):
            return [('lk', match.group(1))]

        def process_text(match):
            return [('tx', match.group(1))]

        tests = [
            (Passage.RE_ITEM_LIST, process_item_list, 1),
            (Passage.RE_MACRO, process_macro, 0),
            (Passage.RE_IMG, process_image, 0),
            (Passage.RE_LINK, process_link, 0),
            (Passage.RE_TEXT, process_text, 0)
        ]

        return test_command(string, tests)

    def _parse_macro(self, token, tokens):
        kind, params = token[1]
        if kind == 'set':
            macro = SetMacro(token)
        elif kind == 'print':
            macro = PrintMacro(token)
        elif kind == 'pause':
            macro = PauseMacro(token)
        elif kind == 'if':
            macro = self._parse_if(token, tokens)
        elif kind == 'call':
            macro = CallMacro(token)
        elif kind == 'return':
            macro = ReturnMacro(token)
        elif kind == 'endif':
            if self._block_stack and self._block_stack[-1].kind == 'if':
                self._block_stack.pop()
            else:
                self._warning('<<endif>> without <<if>>')
            macro = EndMacro(token)
        elif kind == 'music':
            macro = MusicMacro(token)
        elif kind == 'display':
            macro = DisplayMacro(token)
        else:
            macro = InvalidMacro(token, 'unknown macro: ' + kind)

        if macro and macro.error:
            self._warning(macro.error)
            return InvalidMacro(token, macro.error)

        return macro

    def _parse_if(self, token, tokens):
        if_macro = IfMacro(token)
        self._block_stack.append(if_macro)
        if_macro.children = self._parse_commands(tokens)
        return if_macro

    def _warning(self, msg):
        print('Warning on {0}: {1}'.format(self.title, msg))

class AbstractCmd(object):
    """Base class for the different kinds of commands"""

    def __init__(self, kind, token, children=None):
        self.kind = kind
        self.children = children
        self._parse(token)

    def __repr__(self):
        return '<cmd {0}>'.format(self.kind)

class TextCmd(AbstractCmd):
    """Class for text commands"""

    def __init__(self, token):
        AbstractCmd.__init__(self, 'text', token)

    def __repr__(self):
        return '<cmd {0}{1}>'.format(self.kind, ident_list([self.text]))

    def _parse(self, token):
        self.text = token[1]


class ImageCmd(AbstractCmd):
    """Class for image commands"""

    def __init__(self, token):
        AbstractCmd.__init__(self, 'image', token)

    def __repr__(self):
        return '<cmd {0}{1}>'.format(self.kind, ident_list([self.path]))

    def _parse(self, token):
        self.path = token[1]


class LinkCmd(AbstractCmd):
    """Class for link commands"""

    def __init__(self, token):
        AbstractCmd.__init__(self, 'link', token)

    def __repr__(self):
        return '<cmd {0}\n\ttarget: {1}\n\tlabel: {2}\n\ton_click: {3}>'.format(self.kind, self.target, self.label, self.on_click)

    def _parse(self, token):
        text = token[1]

        link_action = text.split('][')
        self.on_click = link_action[1] if len(link_action) > 1 else None

        lbl_tgt = link_action[0].split('|')
        if len(lbl_tgt) > 1:
            self.target = lbl_tgt[-1]
            self.label = '|'.join(lbl_tgt[:-1])
        else:
            self.target = link_action[0]
            self.label = None

    def actual_label(self):
        return self.label if self.label else self.target


class ListCmd(AbstractCmd):
    """Class for list commands"""

    def __init__(self, token, children):
        AbstractCmd.__init__(self, 'list', token, children)

    def __repr__(self):
        return '<cmd {0} ordered: {1}{2}>'.format(self.kind, self.ordered, ident_list(self.children))

    def _parse(self, token):
        self.ordered = token[0] != 'ul'

class AbstractMacro(AbstractCmd):
    """Class for macros """

    RE_EXPRESSION = re.compile(r'(not\s+|\!\s*|)(true|false|[A-Z0-9_\$]+)', flags=re.IGNORECASE)
    RE_PRINT = re.compile(r'(\$[A-Za-z0-9_]+)', flags=re.IGNORECASE)

    def __init__(self, token, children=[]):
        self.params = token[1][1]
        self.error = None
        AbstractCmd.__init__(self, token[1][0], token, children)

    def __repr__(self):
        return '<cmd {0}{1}>'.format(self.kind, ident_list([self.text]))

    def _parse(self, token):
        pass

    def _parse_expression(self, expr):
        try:
            return twexpression.parse(expr)
        except SyntaxError as e:
            self.error = 'invalid expression: {0}: {1}'.format(str(e), expr)

class InvalidMacro(AbstractMacro):
    """Class for invalid macros"""

    def __init__(self, token, error=None):
        AbstractMacro.__init__(self, token)
        self.kind = 'invalid'
        self.error = error

class SetMacro(AbstractMacro):
    """Class for the 'set' macro"""

    RE_ATTRIBUTION = re.compile(r'\s*([\w\$]+)\s*(?:=|\sto\s)\s*(.*)')

    def _parse(self, token):
        kind, params = token[1]

        match = SetMacro.RE_ATTRIBUTION.match(params)
        if not match:
            self.error = 'invalid "set" expression: ' + params
            return

        self.target = match.group(1)
        self.expr = self._parse_expression(match.group(2))

class PauseMacro(AbstractMacro):
    """Class for the 'pause' macro"""

class PrintMacro(AbstractMacro):
    """Class for a 'print' macro which displays the value of a variable"""

    def _parse(self, token):
        kind, params = token[1]
        self.expr = self._parse_expression(params.lstrip())
        self.target = self.expr

class DisplayMacro(AbstractMacro):
    """Class for the 'display' macro"""

    def _parse(self, token):
        kind, params = token[1]
        self.target = params.replace('"', '').strip()

    def __repr__(self):
        return "<cmd display: {0}>".format(self.target)

class CallMacro(AbstractMacro):
    """Class for a jump/call subroutine macro"""

    RE_CALL = re.compile(r'\s*([A-Za-z0-9_]+)\s*$')

    def _parse(self, token):

        kind, params = token[1]

        match = CallMacro.RE_CALL.match(params.lstrip().rstrip())
        if match:
            print("CallMacro: Call subroutine %s %s" % (kind, params))
            self.target = match.group(1)
            self.expr = self.target
            return

class ReturnMacro(AbstractMacro):
    """Class for a return-from-subroutine macro"""

    def _parse(self, token):
        print("ReturnMacro: Return from subroutine")
        self.expr = True
        return

class IfMacro(AbstractMacro):
    """Class for the 'if' macro"""

    def _parse(self, token):
        kind, params = token[1]
        self.expr = self._parse_expression(params)
        self.children = []
        self.else_block = []

class EndMacro(AbstractMacro):
    """Class for closing the current macro"""

class MusicMacro(AbstractMacro):
    """Class for the 'music' macro"""

    def _parse(self, token):
        kind, params = token[1]
        self.path = params.replace('"', '').strip()

def ident_list(list):
    parts = []
    for o in list:
        for s in str(o).split('\n'):
            parts.append('\n\t' + s)

    return ''.join(parts)
