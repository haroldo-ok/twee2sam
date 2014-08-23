#!/usr/bin/env python

import sys, os, getopt, glob, re, shutil, textwrap
from operator import itemgetter
scriptPath = os.path.realpath(os.path.dirname(sys.argv[0]))
sys.path.append(os.sep.join([scriptPath, 'tw']))
sys.path.append(os.sep.join([scriptPath, 'lib']))
from tiddlywiki import TiddlyWiki
from twparser import TwParser


def usage():
	print 'usage: twee2sam sourcefile destdir'


def main (argv):

	# defaults

	author = 'twee'
	target = 'jonah'
	merge = rss_output = ''
	plugins = []

	# read command line switches

	try:
		opts, args = getopt.getopt(argv, 'a:m:p:r:t:', ['author=', 'merge=', 'plugins=', 'rss=', 'target='])
	except getopt.GetoptError:
		usage()
		sys.exit(2)

	for opt, arg in opts:
		if (opt in ('-a', '--author')):
			author = arg
		elif (opt in ('-m', '--merge')):
			merge = arg
		elif (opt in ('-p', '--plugins')):
			plugins = arg.split(',')
		elif (opt in ('-r', '--rss')):
			rss_output = arg
		elif (opt in ('-t', '--target')):
			target = arg

	# construct a TW object

	tw = TiddlyWiki(author)

	# read in a file to be merged

	if merge != '':
		file = open(merge)
		tw.addHtml(file.read())
		file.close()

	# read source files

	sources = []

	for file in glob.glob(args[0]):
		sources.append(file)

	if len(sources) == 0:
		print 'twee2sam: no source files specified\n'
		sys.exit(2)

	if len(args) < 2:
		print 'twee2sam: no destination directory specified\n'
		sys.exit(2)

	for source in sources:
		file = open(source)
		tw.addTwee(file.read().decode('utf-8-sig'))
		file.close()

	src_dir = os.path.dirname(sources[0])
	dest_dir = args[1]

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
		print 'twee2sam: "Start" passage not found.\n'
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

	f_list = open(dest_dir + os.sep + 'Script.list.txt', 'w')

	for passage_name in passage_order:
 		passage = twp.passages[passage_name]
		f_list.write(script_name(passage.title))
		f_list.write('\n')

	f_list.close()


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
		script = open(dest_dir + os.sep + script_name(passage.title), 'w')

		def check_print():
			if check_print.pending:
				script.write('!\n')
				check_print.in_buffer = 0
				check_print.pending = False

		check_print.pending = False
		check_print.in_buffer = 0

		def warning(msg):
			print 'Warning on {0}: {1}'.format(passage.title, msg)

		def out_string(msg):
			msg = msg.replace('"', "'").replace('[', '{').replace(']', '}');
			# Only 29 characters fit per line - make sure to break lines
			# so they don't wrap in the middle of a word.
			msg = textwrap.fill(msg, 29)
			msg_len = len(msg)

			# Checks for buffer overflow
			if check_print.in_buffer + msg_len > 511:
				warning("The text exceeds the maximum buffer size; try to intersperse the text with some <<pause>> macros")
				remaining = max(0, 511 - check_print.in_buffer)
				msg = msg[:remaining]

			script.write('"{0}"'.format(msg))
			script.write('\n')

			check_print.in_buffer += len(msg)

		def out_expr(expr):
			op, val = expr

			if val is True:
				script.write('1')
			elif val is False:
				script.write('0')
			else:
				script.write(variables.get_var(val))

			if op == 'not':
				script.write(' 0=')

		# Outputs all the text

		links = []

		def register_link(cmd, is_conditional):
			temp_var = variables.new_temp_var() if is_conditional else None
			links.append((cmd, temp_var))
			if temp_var:
				script.write('1' + variables.set_var(temp_var))

		def process_command_list(commands, is_conditional=False):
			for cmd in commands:
				if cmd.kind == 'text':
					text = cmd.text.strip()
					if text:
						out_string(text)
						check_print.pending = True
				elif cmd.kind == 'image':
					check_print()
					if not cmd.path in image_list:
						image_list.append(cmd.path)
					script.write('{0}i\n'.format(image_list.index(cmd.path)))
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
					out_expr(cmd.expr)
					script.write(variables.set_var(cmd.target) + '\n')
				elif cmd.kind == 'if':
					out_expr(cmd.expr)
					script.write('[\n')
					process_command_list(cmd.children, True)
					script.write(' 0]\n')
				elif cmd.kind == 'music':
					if not cmd.path in music_list:
						music_list.append(cmd.path)
					script.write('{0}m\n'.format(music_list.index(cmd.path)))

		process_command_list(passage.commands)

		check_print()

		# Builds the menu from the links

		if links:
			# Outputs the options separated by line breaks, max 28 chars per line
			for link, temp_var in links:
				if temp_var:
					script.write('{0}['.format(variables.get_var(temp_var)))

				out_string(link.actual_label()[:28] + '\n')

				if temp_var:
					script.write('0]\n')

			script.write('?A.\n')
			check_print.in_buffer = 0

			# Outputs the menu destinations
			script.write('0B.\n');

			for link, temp_var in links:
				if temp_var:
					script.write('{0}['.format(variables.get_var(temp_var)))

				if not link.target in passage_indexes:
					# TODO: Create a better exception
					raise BaseException('Link points to a nonexisting passage: "{0}"'.format(link.target))

				script.write('A:B:=[{0}j]'.format(passage_indexes[link.target]))
				script.write('B:1+B.\n')

				if temp_var:
					script.write('0]\n')

		else:
			# No links? Generates an infinite loop.
			script.write('1[1]\n')

		script.close()


	#
	# Function to copy the files on a list and generate a list file
	#
	def copy_and_build_list(list_file_name, file_list, item_extension, item_suffix = '', empty_item = 'blank'):
		list_file = open(dest_dir + os.sep + list_file_name, 'w')

		for file_path in file_list:
			item_name = name_to_identifier(os.path.splitext(os.path.basename(file_path))[0])
			list_file.write(item_name + item_suffix + '\n')
			shutil.copyfile(src_dir + os.sep + file_path, dest_dir + os.sep + item_name + '.' + item_extension)

		if not file_list:
			list_file.write(empty_item + item_suffix + '\n')

		list_file.close()



	#
	# Copy images and builds the image list
	#
 	copy_and_build_list('Images.txt', image_list, 'png')



	#
	# Copy music and builds the music list
	#
 	copy_and_build_list('Music.list.txt', music_list, 'epsgmod', '.epsgmod', 'empty')



class VariableFactory:

	def __init__(self, first_available):
		self.next_available = first_available

		self.vars = {}
		self.never_used = []
		self.never_set = []

		self.next_temp = 0;
		self.temps = []

	def set_var(self, name):
		if not name in self.vars:
			self._create_var(name)
			self.never_used.append(name)

		if name in self.never_set:
			self.never_set.remove(name)

		return '{0}.'.format(self.vars[name])

	def get_var(self, name):
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




if __name__ == '__main__':
	main(sys.argv[1:])

