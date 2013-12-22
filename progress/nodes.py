#!/usr/bin/python
"""Nodes: print a heirarchical list of the nodes in an edX course, including the tag, id (hash) and name.

%InsertOptionParserUsage%

Example:
 nodes.py directory 2013_T3   # parses directory/course/2013_T3.xml

TODO:
figure out course_name on our own.
put node ids first, optional, easy to strip out, then indent for nesting level, then node type, optional, then name
protect against more KeyErrors etc via use of get() rather than indexing as in 
        self.name = self.e.attrib.get('display_name')

Sample xml file contents:

<vertical display_name="p1_search_q8_replanning">
  <html url_name="198b1913bbf74ee1a92345cd0e089d70"/>
</vertical>

"""

import os
import sys
import logging
from optparse import OptionParser
from datetime import datetime
import lxml.etree as ET

__author__ = "Neal McBurnett <http://neal.mcburnett.org/>"
__version__ = "0.2.0"
__date__ = "2013-10-14"
__copyright__ = "Copyright (c) 2013 Neal McBurnett"
__license__ = "GPL v3"

parser = OptionParser(prog="nodes.py", version=__version__, usage = "Usage: %prog [options] directory course_name")

parser.add_option("-d", "--debuglevel",
  type="int", default=logging.WARNING,
  help="Set logging level to debuglevel: DEBUG=10, INFO=20,\n WARNING=30 (the default), ERROR=40, CRITICAL=50")

# incorporate OptionParser usage documentation in our docstring
__doc__ = __doc__.replace("%InsertOptionParserUsage%\n", parser.format_help())

edxtags = "about chapter course html policies problem sequential static vertical video".split()

class Node():
    def __init__(self, tag, id):
        self.tag = tag
        self.id = id
        self.subs = []
        self.e = ET.parse(os.path.join(tag, id + ".xml")).getroot()
        self.name = self.e.attrib.get('display_name')

    def __str__(self):
        return("%s node %s: %s" % (self.tag, self.id, self.name))

    def getsubs(self):
        for sub in list(self.e):
            name = sub.attrib.get('url_name')
            if sub.tag in edxtags and name:
                node = Node(sub.tag, name)
                print node
                self.subs.append(node)
                node.getsubs()

def main(parser):
    "Run nodes with given OptionParser arguments"

    (options, args) = parser.parse_args()

    #configure the root logger.  Without filename, default is StreamHandler with output to stderr. Default level is WARNING
    logging.basicConfig(level=options.debuglevel)   # ..., format='%(message)s', filename= "/file/to/log/to", filemode='w' )

    logging.debug("options: %s; args: %s", options, args)

    directory = args[0]
    course_name = args[1]

    logging.debug("Directory: %s, course name: %s" % (directory, course_name))

    os.chdir(directory)

    r = Node('course', course_name)
    print r
    r.getsubs()

if __name__ == "__main__":
    main(parser)
