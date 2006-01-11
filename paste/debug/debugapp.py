# (c) 2005 Clark C. Evans
# This module is part of the Python Paste Project and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php
# This code was written with funding by http://prometheusresearch.com
"""
Various Applications for Debugging/Testing Purposes
"""

import time
__all__ = ['SimpleApplication', 'SlowConsumer']


class SimpleApplication:
    """
    Produces a simple web page
    """
    def __call__(self, environ, start_response):
        body = "<html><body>simple</body></html>"
        start_response("200 OK",[('Content-Type','text/html'),
                                 ('Content-Length',len(body))])
        return [body]

class SlowConsumer:
    """
    Consumes an upload slowly...

    NOTE: This should use the iterator form of ``wsgi.input``,
          but it isn't implemented in paste.httpserver.
    """
    def __init__(self, chunk_size = 4096, delay = 1, progress = True):
        self.chunk_size = chunk_size
        self.delay = delay
        self.progress = True

    def __call__(self, environ, start_response):
        size = 0
        total  = environ.get('CONTENT_LENGTH')
        if total:
            remaining = int(total)
            while remaining > 0:
                if self.progress:
                    print "%s of %s remaining" % (remaining, total)
                if remaining > 4096:
                    chunk = environ['wsgi.input'].read(4096)
                else:
                    chunk = environ['wsgi.input'].read(remaining)
                if not chunk:
                    break
                size += len(chunk)
                remaining -= len(chunk)
                if self.delay:
                    time.sleep(self.delay)
            body = "<html><body>%d bytes</body></html>" % size
        else:
            body = ('<html><body>\n'
                '<form method="post" enctype="multipart/form-data">\n'
                '<input type="file" name="file">\n'
                '<input type="submit" >\n'
                '</form></body></html>\n')
        print "bingles"
        start_response("200 OK",[('Content-Type', 'text/html'),
                                 ('Content-Length', len(body))])
        return [body]
