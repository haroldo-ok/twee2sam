#
# TiddlyWiki.py
#
# A Python implementation of the Twee compiler.
#
# This code was written by Chris Klimas <klimas@gmail.com>
# It is licensed under the GNU General Public License v2
# http://creativecommons.org/licenses/GPL/2.0/
#
# This file defines two classes: Tiddler and TiddlyWiki. These match what
# you'd normally see in a TiddlyWiki; the goal here is to provide classes
# that translate between Twee and TiddlyWiki output seamlessly.
#

import re
import datetime
import time
from os.path import join
import PyRSS2Gen as rss


class TiddlyWiki(object):
    """An entire TiddlyWiki."""
    
    def __init__(self, author='twee'):
        """Optionally pass an author name."""
        self.author = author
        self.tiddlers = {}

    def tryGetting(self, names, default=''):
        """Tries retrieving the text of several tiddlers by name; returns default if none exist."""
        for name in names:
            if name in self.tiddlers:
                return self.tiddlers[name].text
                
        return default
        
    def toTwee(self, order=None):
        """Returns Twee source code for this TiddlyWiki."""
        if not order: 
            order = self.tiddlers.keys()		
        
        output = "".join([self.tiddlers[i].toTwee() for i in order])
        
        return output
        
    def toHtml(self, app = None, target = None, order = None):
        """Returns HTML code for this TiddlyWiki. If target is passed, adds a header."""
        if not order: 
            order = self.tiddlers.keys()
        
        output = ''
        if target:
            with open(join(app.getPath(), 'targets', target, 'header.html')) as header:
                output = header.read()
    
        output += "".join([self.tiddlers[i].toHtml(self.author) for i in order])
        
        if target:
            output += '</div></body></html>'
        
        return output
    
    def toRtf(self, order=None):
        """Returns RTF source code for this TiddlyWiki."""
        if not order: 
            order = self.tiddlers.keys()
        
        # preamble
        output = r'{\rtf1\ansi\ansicpg1251' + '\n'
        output += r'{\fonttbl\f0\fswiss\fcharset0 Arial;}' + '\n'
        output += r'{\colortbl;\red128\green128\blue128;}' + '\n'
        output += r'\margl1440\margr1440\vieww9000\viewh8400\viewkind0' + '\n'
        output += r'\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx792' + '\n'
        output += r'\tx8640\ql\qnatural\pardirnatural\pgnx720\pgny720' + '\n'
        
        # content
        for i in order:
            text = self.tiddlers[i].text.replace(r'\n', '\\\n') # newlines
            text = re.sub(r'\[\[(.*?)\]\]', r'\ul \1\ulnone ', text) # links
            text = re.sub(r'\/\/(.*?)\/\/', r'\i \1\i0 ', text) # italics
            text = re.sub(r'(\<\<.*?\>\>)', r'\cf1 \i \1\i0 \cf0', text) # macros

            output += r'\fs24\b1' + self.tiddlers[i].title + r'\b0\fs20' + '\\\n'
            output += text + '\\\n\\\n'
        
        output += '}'
            
        return output
        
    def toRss(self, num_items=5):
        """Returns an RSS2 object of recently changed tiddlers."""
        url = self.tryGetting(['StoryUrl', 'SiteUrl'])
        title = self.tryGetting(['StoryTitle', 'SiteTitle'], 'Untitled Story')
        subtitle = self.tryGetting(['StorySubtitle', 'SiteSubtitle'])
        
        # build a date-sorted list of tiddler titles
        sorted_keys = self.tiddlers.keys()
        sorted_keys.sort(key = lambda i: self.tiddlers[i].modified)
                
        # and then generate our items
        rss_items = map(lambda x: self.tiddlers[x].toRss(), sorted_keys[:num_items])
             
        return rss.RSS2(
            title = title,
            link = url,
            description = subtitle,
            pubDate = datetime.datetime.now(),
            items = rss_items
            )
        
    def addTwee(self, source):
        """Adds Twee source code to this TiddlyWiki."""
        for i in source.replace("\r\n", "\n").split('\n::'):
            self.addTiddler(Tiddler('::' + i))
            
    def addHtml(self, source):
        """Adds HTML source code to this TiddlyWiki."""
        divs_re = re.compile(r'<div id="storeArea">(.*)</div>\s*</html>',
                                                 re.DOTALL)
        divs = divs_re.search(source)

        if divs:
            for div in divs.group(1).split('<div'):
                self.addTiddler(Tiddler('<div' + div, 'html'))

    def addTiddler(self, tiddler):
        """Adds a Tiddler object to this TiddlyWiki."""
        
        if tiddler.title in self.tiddlers:
            if (tiddler == self.tiddlers[tiddler.title] and 
                 tiddler.modified > self.tiddlers[tiddler.title].modified):
                self.tiddlers[tiddler.title] = tiddler
        else:
            self.tiddlers[tiddler.title] = tiddler
        
class Tiddler(object):
    """A single tiddler in a TiddlyWiki."""
    
    def __init__(self, source, type='twee'):
        """Pass source code, and optionally 'twee' or 'html'"""
        if type == 'twee':
            self.initTwee(source)
        else:
            self.initHtml(source)

    def __repr__(self):
        return "<Tiddler '" + self.title + "'>"

    def __cmp__(self, other):
        """Compares a Tiddler to another."""
        return self.text == other.text
    
    def initTwee(self, source):
        """Initializes a Tiddler from Twee source code."""
    
        # we were just born
        self.created = self.modified = time.localtime()
        
        # figure out our title
                
        lines = source.strip().split('\n')
                
        meta_bits = lines[0].split('[')
        self.title = meta_bits[0].strip(' :')
                
        # find tags
        self.tags = []
        if len(meta_bits) > 1:
            tag_bits = meta_bits[1].split(' ')
            self.tags = map(lambda x: x.strip("[]"), tag_bits)
                
        # and then the body text
        self.text = "".join(map(lambda x: "%s\n" % x, lines[1:])).strip()
        
        
    def initHtml(self, source):
        """Initializes a Tiddler from HTML source code."""
    
        # title
        self.title = 'untitled passage'
        title_re = re.compile(r'tiddler="(.*?)"')
        title = title_re.search(source)
        if title:
            self.title = title.group(1)
                    
        # tags
        self.tags = []
        tags = re.compile(r'tags="(.*?)"').search(source)
        if tags and tags.group(1):
            self.tags = tags.group(1).split(' ')
                    
        # creation date
        self.created = time.localtime()
        created = re.compile(r'created="(.*?)"').search(source)
        if created:
            self.created = decode_date(created.group(1))
        
        # modification date
        
        self.modified = time.localtime()
        modified = re.compile(r'modified="(.*?)"').search(source)
        if modified:
            self.modified = decode_date(modified.group(1))
        
        # body text
        text = re.compile(r'<div.*?>(.*)</div>').search(source)
        if text:
            self.text = decode_text(text.group(1))
                
        
    def toHtml(self, author='twee'):
        """Returns an HTML representation of this tiddler."""
            
        now = time.localtime()
        output = '<div tiddler="%s" tags="' % self.title
        
        output += "%s" % "".join(map(lambda x: "%s " % x, self.tags))[:-1]
            
        output += '" modified="%s"' % encode_date(self.modified)
        output += ' created="%s"' % encode_date(self.created)
        output += ' modifier="%s">' % author
        output += encode_text(self.text) + '</div>'
        
        return output
        
        
    def toTwee(self):
        """Returns a Twee representation of this tiddler."""
        output = ':: %s' % self.title
        
        if self.tags:
            output += " [%s]" % "".join(map(lambda x: "%s " % x, self.tags))[:-1]
            
        output += "\n%s\n\n\n" % self.text
        return output
        
        
    def toRss(self, author = 'twee'):
        """Returns an RSS representation of this tiddler."""
        return rss.RSSItem(
            title=self.title,
            link='',
            description=self.text,
            pubDate=datetime.datetime.now()
        )

    def links(self, includeExternal=False):
        """
        Returns a list of all passages linked to by this one. By default,
        only returns internal links, but you can override it with the includeExternal
        parameter.
        """

        # regular hyperlinks
        links = re.findall(r'\[\[(.+?)\]\]', self.text)
        
        # check for [[title|target]] formats
        links = map(lambda x: re.sub('.*\|', '', x) if '|' in x else x, links)
        if not includeExternal: 
            # remove external links
            links = filter(not re.match('http://', text), links)

        # <<display ''>>
        displays = re.findall(r'\<\<display\s+[\'"](.+?)[\'"]\s?\>\>', self.text, re.IGNORECASE)
        
        # <<choice ''>>
        choices = re.findall(r'\<\<choice\s+[\'"](.+?)[\'"]\s?\>\>', self.text, re.IGNORECASE)

        # <<actions ''>>
        actions = []
        for block in re.findall(r'\<\<actions\s+(.*?)\s?\>\>', self.text, re.IGNORECASE):
            actions.extend(re.findall(r'[\'"](.*?)[\'"]', block))
        
        # remove duplicates by converting to a set
        return list(set(links + displays + choices + actions))


def encode_text(text):
    """Encodes a string for use in HTML output."""
    text = re.sub(r'\r?\n', r'\\n', text.replace('\\', '\s'))
    replace = {'<':'&lt;', '>':'&gt;', '"':'&quot;'}
    
    return "".join(map(lambda x: replace[x] if x in list(replace.keys) else x, text))

    
def decode_text(text):
    """Decodes a string from HTML."""
    
    replace = {'\\n':'\n', '\s':'\\', '&lt;':'<', '&gt;':'>', '&quot;':'"'}
    return "".join(map(lambda x: replace[x] if x in list(replace.keys) else x, text))
    
    
def encode_date(date):
    """Encodes a datetime in TiddlyWiki format."""
    return time.strftime('%Y%m%d%H%M', date)
    

def decode_date(date):
    """Decodes a datetime from TiddlyWiki format."""
    return time.strptime(date, '%Y%m%d%H%M')
