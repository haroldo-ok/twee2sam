#!/usr/bin/env python

from __future__ import print_function
import sys, os, getopt, glob
scriptPath = os.path.realpath(os.path.dirname(sys.argv[0]))
sys.path.append(os.sep.join([scriptPath, 'tw', 'lib']))
sys.path.append(os.sep.join([scriptPath, 'lib']))
from tiddlywiki import TiddlyWiki
from twparser import TwParser


def usage():
	print('usage: twee [-a author] [-t target] [-m mergefile]'+
			' [-r rss] source1 [source2..]')


def main (argv):

	# defaults

	author = 'twee'
	target = 'jonah'
	merge = rss_output = ''
	plugins = []

	# read command line switches

	try:
		opts, args = getopt.getopt(argv, 'a:m:p:r:t:', 
			['author=', 'merge=', 'plugins=', 'rss=', 'target='])
	except getopt.GetoptError:
		usage()
		sys.exit(2)

	for opt, arg in opts:
		if opt in ('-a', '--author'):
			author = arg
		elif opt in ('-m', '--merge'):
			merge = arg
		elif opt in ('-p', '--plugins'):
			plugins = arg.split(',')
		elif opt in ('-r', '--rss'):
			rss_output = arg
		elif opt in ('-t', '--target'):
			target = arg

	# construct a TW object

	tw = TiddlyWiki(author)

	# read in a file to be merged

	if not merge:
		with open(merge) as reader:
			tw.addHtml(reader.read())

	# read source files

	sources = []

	for arg in args:
		for file in glob.glob(arg):
			sources.append(file)

	if not sources:
		print('twee: no source files specified\n')
		sys.exit(2)

	for source in sources:
		with open(source) as reader:
			tw.addTwee(reader.read())

	# generate RSS if requested

	if rss_output != '':
		with open(rss_output, 'w') as rss_file:
			tw.toRss().write_xml(rss_file)

	# output the target header

#	if (target != 'none') and (target != 'plugin'):
#		with open(scriptPath + os.sep + 'targets' + os.sep + target \
#								+ os.sep + 'header.html') as reader:
#		print(file.read())

	# the tiddlers

	print(TwParser(tw))

#	print(tw.toHtml())

	# plugins

#	for plugin in plugins:
#		with open(scriptPath + os.sep + 'targets' + os.sep + target +
#								os.sep + 'plugins' + os.sep + plugin +
#								 os.sep + 'compiled.html') as reader:
#		print(reader.read())

	# and close it up

#	print('</div></html>')


if __name__ == '__main__':
	main(sys.argv[1:])

