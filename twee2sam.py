#!/usr/bin/env python

import sys, os, getopt, glob, re, shutil
from operator import itemgetter
scriptPath = os.path.realpath(os.path.dirname(sys.argv[0]))
sys.path.append(os.sep.join([scriptPath, 'tw', 'lib']))
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
		tw.addTwee(file.read())
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

	image_list = []
	for passage in twp.passages.values():
		script = open(dest_dir + os.sep + script_name(passage.title), 'w')

		def check_print():
			if check_print.pending:
				script.write('!\n')
				check_print.pending = False

		check_print.pending = False

		def out_string(msg):
			msg = msg.replace('"', "'").replace('[', '{').replace(']', '}');
			script.write('"{0}"'.format(msg))
			script.write('\n')

		# Outputs all the text

		links = []
		for cmd in passage.commands:
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
				links.append(cmd)
				out_string(cmd.actual_label())
			elif cmd.kind == 'list':
				for lcmd in cmd.children:
					if lcmd.kind == 'link':
						links.append(lcmd)
			elif cmd.kind == 'pause':
				check_print.pending = True
				check_print()

		check_print()

		# Builds the menu from the links

		if links:
			# Outputs the options separated by line breaks, max 28 chars per line
			out_string('\n'.join([link.actual_label()[:28] for link in links]))
			script.write('?A.\n')

			nlink = 0
			for link in links:
				script.write('A:{0}=[{1}j]\n'.format(nlink, passage_indexes[link.target]))
				nlink += 1
		else:
			# No links? Generates an infinite loop.
			script.write('1[1]\n')

		script.close()


	#
	# Copy images and builds the image list
	#


	image_list_file = open(dest_dir + os.sep + 'Images.txt', 'w')

	for image_path in image_list:
		image_name = name_to_identifier(os.path.splitext(os.path.basename(image_path))[0])
		image_list_file.write(image_name + '\n');
		shutil.copyfile(src_dir + os.sep + image_path, dest_dir + os.sep + image_name + '.png')

	image_list_file.write('blank\n');
 	image_list_file.close()



if __name__ == '__main__':
	main(sys.argv[1:])

