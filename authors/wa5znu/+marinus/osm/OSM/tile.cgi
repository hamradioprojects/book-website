#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import cgi
import cgitb
import re
import operator
import tile

cgitb.enable()

HEADERS = '\n'.join(
    [
	"Content-type: %s;",
	"Content-Disposition: attachment; filename=%s",
	"Content-Title: %s",
	"Content-Length: %i",
	"\n", # empty line to end headers
	]
    )

def sanitize_alphanumeric(x):
    return re.sub(r'[^a-zA-Z0-9]', '', x)

def sanitize_numeric(x):
    return int(re.sub(r'[^0-9]', '', x))

form = cgi.FieldStorage()

if "grid" not in form or "zoom" not in form or "n" not in form:
    print "Content-Type: text/html"
    print ""
    print "<html><head><title>Error</title></head>"
    print "<body>"
    print "<H1>Error</H1>"
    print "<p>Please press BACK and fill in the <code>grid</code> and <code>zoom</code> and <code>n</code> fields.</p>"
    print "</body>"
    print "</html>"
else:
    grid = sanitize_alphanumeric(form["grid"].value)
    zoom = sanitize_numeric(form["zoom"].value)
    n = sanitize_numeric(form["n"].value)
    style='mapquest'
    result = tile.tilezip(grid, zoom, n)
    length = len(result)
    name = "%s-%s-%d-%d.zip" % (grid, style, zoom, n)
    sys.stdout.write(HEADERS % ('application/zip', name, name, length))
    sys.stdout.write(result)    
