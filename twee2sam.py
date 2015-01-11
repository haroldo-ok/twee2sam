#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import argparse, sys, os, glob, re, shutil, io
from operator import itemgetter
scriptPath = os.path.realpath(os.path.dirname(sys.argv[0]))
sys.path.append(os.path.join(scriptPath, 'tw'))
sys.path.append(os.path.join(scriptPath, 'lib'))
from tiddlywiki import TiddlyWiki
from twparser import TwParser
import twexpression

__version__ = "0.8.0"

def main (argv):

    parser = argparse.ArgumentParser(description="Convert twee source code into SAM source code")
    parser.add_argument("-a", "--author", default="twee")
    parser.add_argument("-m", "--merge", default="")
    parser.add_argument("-p", "--plugins", nargs="*", default=[])
    parser.add_argument("-r", "--rss", default="")
    parser.add_argument("-t", "--target", default="jonah")
    parser.add_argument("sources")
    parser.add_argument("destination")
    opts = parser.parse_args()

    # construct a TW object

    tw = TiddlyWiki(opts.author)

    # read in a file to be merged

    if opts.merge:
        with io.open(opts.merge, encoding="utf-8-sig") as f:
            tw.addHtml(f.read())

    # read source files

    sources = glob.glob(opts.sources)

    if not sources:
        print('twee2sam: no source files specified\n')
        sys.exit(2)

    for source in sources:
        with io.open(source, encoding="utf-8-sig") as f:
            tw.addTwee(f.read())

    src_dir = os.path.dirname(sources[0])

    #
    # Parse the file
    #

    twp = TwParser(tw)


    #
    # Number the passages
    #

    passage_indexes = {}

    def process_passage_index(passage):
        global next_seq

        if not passage.title in passage_indexes:
            passage_indexes[passage.title] = process_passage_index.next_seq
            process_passage_index.next_seq += 1

    process_passage_index.next_seq = 0

    # 'Start' _must_ be the first script
    if not 'Start' in twp.passages:
        print('twee2sam: "Start" passage not found.\n')
        sys.exit(2)

    process_passage_index(twp.passages['Start'])
    for passage in twp.passages.values():
        process_passage_index(passage)

    #
    # Generate the file list
    #
    passage_order = [psg for psg, idx in sorted(passage_indexes.items(), key=itemgetter(1))]


    def name_to_identifier(s):
        return re.sub(r'[^0-9A-Za-z]', '_', s)

    def script_name(s):
        return name_to_identifier(s) + '.twsam'

    if not os.path.exists(opts.destination):
        os.makedirs(opts.destination)
    with io.open(os.path.join(opts.destination, 'Script.list.txt'), 'w', encoding="utf-8") as f_list:
        for passage_name in passage_order:
            passage = twp.passages[passage_name]
            f_list.write(u"%s" % script_name(passage.title))
            f_list.write(u'\n')


    #
    # Generate SAM scripts
    #

    # A is used as a temp var for menu selection
    # B is used as a temp var for menu selection
    # C and above are available
    variables = VariableFactory(2)

    image_list = []
    music_list = []
    for passage in twp.passages.values():
        with io.open(os.path.join(opts.destination, script_name(passage.title)), 'w', encoding="utf-8") as script:

            def check_print():
                if check_print.pending:
                    script.write(u'!\n')
                    check_print.in_buffer = 0
                    check_print.pending = False

            check_print.pending = False
            check_print.in_buffer = 0

            def warning(msg):
                print('Warning on {0}: {1}'.format(passage.title, msg))

            def out_string(msg):
                MAX_LEN = 512
                # go through the string and replace characters
                msg = ''.join(map(lambda x: {'"': "'", '[': '{', ']':'}'}[x] if x in ('"','[','{') else x, msg))
                msg_len = len(msg)

                # Checks for buffer overflow
                if check_print.in_buffer + msg_len > MAX_LEN - 1:
                    warning("The text exceeds the maximum buffer size; try to intersperse the text with some <<pause>> macros")
                    remaining = max(0, MAX_LEN - 1 -  check_print.in_buffer)
                    msg = msg[:remaining]

                script.write(u'"{0}"'.format(msg))
                script.write(u'\n')

                check_print.in_buffer += len(msg)

            def out_set(cmd):
                out_expr(cmd.expr)
                script.write(u' ')
                target = variables.set_var(cmd.target)
                script.write(u"%s\n" % target)

            def out_if(cmd):
                out_expr(cmd.expr)
                script.write(u'[\n')
                process_command_list(cmd.children, True)
                script.write(u' 0]\n')

            def out_print(cmd):
                # print a numeric qvariable
                out_expr(cmd.expr)
                script.write(u'"\#"')

            def out_expr(expr):
                def var_locator(name):
                    return variables.get_var(name).replace(':', '')
                generated = twexpression.to_sam(expr, var_locator = var_locator)
                script.write(u"%s" % generated)

            def out_call(cmd):
                call_target = None
                for k in passage_indexes.keys():
                    if cmd.target == k:
                        call_target = passage_indexes[k]
                if call_target:
                    script.write(u"%s" % call_target)
                    script.write(u'c\n')

            # Outputs all the text

            links = []

            def register_link(cmd, is_conditional):
                temp_var = variables.new_temp_var() if is_conditional else None
                links.append((cmd, temp_var))
                if temp_var:
                    script.write(u'1%s' % variables.set_var(temp_var))

            def process_command_list(commands, is_conditional=False):
                for cmd in commands:
                    if cmd.kind == 'text':
                        text = cmd.text.strip()
                        if text:
                            out_string(text)
                            check_print.pending = True
                    elif cmd.kind == 'print':
                        out_print(cmd)
                    elif cmd.kind == 'image':
                        check_print()
                        if not cmd.path in image_list:
                            image_list.append(cmd.path)
                        script.write(u'{0}i\n'.format(image_list.index(cmd.path)))
                    elif cmd.kind == 'link':
                        register_link(cmd, is_conditional)
                        out_string(cmd.actual_label())
                    elif cmd.kind == 'list':
                        for lcmd in cmd.children:
                            if lcmd.kind == 'link':
                                register_link(lcmd, is_conditional)
                    elif cmd.kind == 'pause':
                        check_print.pending = True
                        check_print()
                    elif cmd.kind == 'set':
                        out_set(cmd)
                    elif cmd.kind == 'if':
                        out_if(cmd)
                    elif cmd.kind == 'call':
                        out_call(cmd)
                    elif cmd.kind == 'return':
                        script.write(u'$\n')
                    elif cmd.kind == 'music':
                        if not cmd.path in music_list:
                            music_list.append(cmd.path)
                        script.write(u'{0}m\n'.format(music_list.index(cmd.path)))
                    elif cmd.kind == 'display':
                        try:
                            target = twp.passages[cmd.target]
                        except KeyError:
                            print("Display macro target passage {0} not found!".format(cmd.target), file=sys.stderr)
                            return
                        process_command_list(target.commands)

            process_command_list(passage.commands)

            check_print()

            # Builds the menu from the links

            if links:
                # Outputs the options separated by line breaks, max 28 chars per line
                for link, temp_var in links:
                    if temp_var:
                        script.write(u'{0}['.format(variables.get_var(temp_var)))

                    out_string(link.actual_label()[:28] + '\n')

                    if temp_var:
                        script.write(u'0]\n')

                script.write(u'?A.\n')
                check_print.in_buffer = 0

                # Outputs the menu destinations
                script.write(u'0B.\n');

                for link, temp_var in links:
                    if temp_var:
                        script.write(u'{0}['.format(variables.get_var(temp_var)))

                    if not link.target in passage_indexes:
                        # TODO: Create a better exception
                        raise BaseException('Link points to a nonexisting passage: "{0}"'.format(link.target))

                    script.write(u'A:B:=[{0}j]'.format(passage_indexes[link.target]))
                    script.write(u'B:1+B.\n')

                    if temp_var:
                        script.write(u'0]\n')

            else:
                # No links? Generates an infinite loop.
                script.write(u'1[1]\n')



    #
    # Function to copy the files on a list and generate a list file
    #
    def copy_and_build_list(list_file_name, file_list, item_extension, item_suffix = '', empty_item = 'blank'):
        with io.open(os.path.join(opts.destination, list_file_name), 'w', encoding="utf-8") as list_file:
            for file_path in file_list:
                item_name = name_to_identifier(os.path.splitext(os.path.basename(file_path))[0])
                list_file.write("%s%s\n" % (item_name, item_suffix))
                shutil.copyfile(os.path.join(src_dir, file_path), os.path.join(opts.destination, '%s.%s' % (item_name, item_extension)))

            if not file_list:
                list_file.write(u"%s%s\n" % (empty_item, item_suffix))



    #
    # Copy images and builds the image list
    #
    copy_and_build_list('Images.txt', image_list, 'png')



    #
    # Copy music and builds the music list
    #
    copy_and_build_list('Music.list.txt', music_list, 'epsgmod', '.epsgmod', 'empty')



class VariableFactory(object):

    def __init__(self, first_available):
        self.next_available = first_available

        self.vars = {}
        self.never_used = []
        self.never_set = []

        self.next_temp = 0;
        self.temps = []

    def set_var(self, name):
        name = self._normalize_name(name)

        if not name in self.vars:
            self._create_var(name)
            self.never_used.append(name)

        if name in self.never_set:
            self.never_set.remove(name)

        return '{0}.'.format(self.vars[name])

    def get_var(self, name):
        name = self._normalize_name(name)

        if not name in self.vars:
            self._create_var(name)
            self.never_set.append(name)

        if name in self.never_used:
            self.never_used.remove(name)

        return '{0}:'.format(self.vars[name])

    def new_temp_var(self):
        if self.next_temp >= len(self.temps):
            self.temps.append('*temp{0}'.format(self.next_temp))

        temp = self.temps[self.next_temp]
        self.next_temp += 1

        return temp

    def clear_temp_vars(self):
        self.next_temp = 0

    def _create_var(self, name):
        self.vars[name] = self._num_to_ref(self.next_available)
        self.next_available += 1

    def _num_to_ref(self, num):
        return chr(ord('A') + num)

    def _normalize_name(self, name):
        return name.replace('$', '').strip()




if __name__ == '__main__':
    main(sys.argv)
