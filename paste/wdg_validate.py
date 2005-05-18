"""
Middleware that checks HTML and appends messages about the validity of
the HTML.  Uses: http://www.htmlhelp.com/tools/validator/ -- interacts
with the command line client.  Use the configuration ``wdg_path`` to
override the path (default: looks for ``validate`` in $PATH).

To install, in your web context's __init__.py::

    def urlparser_wrap(environ, start_response, app):
        return wdg_validate.WDGValidateMiddleware(app)(
            environ, start_response)
"""

from cStringIO import StringIO
import subprocess
from paste import wsgilib
import re
import cgi

class WDGValidateMiddleware(object):

    _end_body_regex = re.compile(r'</body>', re.I)

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        output = StringIO()
        response = []

        def writer_start_response(status, headers, exc_info=None):
            response.extend((status, headers))
            start_response(status, headers, exc_info)
            return output.write

        app_iter = self.app(environ, writer_start_response)
        try:
            for s in app_iter:
                output.write(s)
        finally:
            if hasattr(app_iter, 'close'):
                app_iter.close()
        page = output.getvalue()
        status, headers = response
        v = wsgilib.header_value(headers, 'content-type')
        if (not v.startswith('text/html')
            and not v.startswith('text/xhtml+xml')):
            # Can't validate
            # @@: Should validate CSS too... but using what?
            return [page]
        ops = []
        if v.startswith('text/xhtml+xml'):
            ops.append('--xml')
        # @@: Should capture encoding too
        conf = environ['paste.config']
        html_errors = self.call_wdg_validate(
            conf.get('wdg_path', 'validate'), ops, page)
        if not html_errors:
            return [page]
        return self.add_error(page, html_errors)
    
    def call_wdg_validate(self, wdg_path, ops, page):
        proc = subprocess.Popen([wdg_path] + ops,
                                shell=False,
                                close_fds=True,
                                stdout=subprocess.PIPE,
                                stdin=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
        stdout = proc.communicate(page)[0]
        proc.wait()
        return stdout
            
    def add_error(self, html_page, html_errors):
        add_text = ('<pre style="background-color: #ffd; color: #600; '
                    'border: 1px solid #000;">%s</pre>'
                    % cgi.escape(html_errors))
        match = self._end_body_regex.search(html_page)
        if match:
            return [html_page[:match.start()]
                    + add_text
                    + html_page[match.end():]]
        else:
            return [html_page + add_text]