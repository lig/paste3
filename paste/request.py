# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
# (c) 2005 Ian Bicking and contributors
# This module is part of the Python Paste Project and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php
"""
This module provides helper routines with work directly on a WSGI
environment to solve common requirements.

   * get_cookies(environ)
   * parse_querystring(environ)
   * parse_formvars(environ, all_as_list=False, include_get_vars=True)
   * construct_url(environ, with_query_string=True, with_path_info=True,
                   script_name=None, path_info=None, querystring=None)
   * path_info_split(path_info)
   * path_info_pop(environ)
   * resolve_relative_url(url, environ)

"""
import cgi
import textwrap
from Cookie import SimpleCookie
import urlparse
from util.UserDict24 import DictMixin, IterableUserDict, UserDict
from paste.util.multidict import multidict

__all__ = ['get_cookies', 'get_cookie_dict', 'parse_querystring',
           'parse_formvars', 'construct_url', 'path_info_split',
           'path_info_pop', 'resolve_relative_url', 'EnvironHeaders']

def get_cookies(environ):
    """
    Gets a cookie object (which is a dictionary-like object) from the
    request environment; caches this value in case get_cookies is
    called again for the same request.

    """
    header = environ.get('HTTP_COOKIE', '')
    if environ.has_key('paste.cookies'):
        cookies, check_header = environ['paste.cookies']
        if check_header == header:
            return cookies
    cookies = SimpleCookie()
    cookies.load(header)
    environ['paste.cookies'] = (cookies, header)
    return cookies

def get_cookie_dict(environ):
    """Return a *plain* dictionary of cookies as found in the request.

    Unlike ``get_cookies`` this returns a dictionary, not a
    ``SimpleCookie`` object.  For incoming cookies a dictionary fully
    represents the information.  Like ``get_cookies`` this caches and
    checks the cache.
    """
    header = environ.get('HTTP_COOKIE')
    if not header:
        return {}
    if environ.has_key('paste.cookies.dict'):
        cookies, check_header = environ['paste.cookies.dict']
        if check_header == header:
            return cookies
    cookies = SimpleCookie()
    cookies.load(header)
    result = {}
    for name in cookies:
        result[name] = cookies[name].value
    environ['paste.cookies.dict'] = (result, header)
    return result

def parse_querystring(environ):
    """
    Parses a query string into a list like ``[(name, value)]``.
    Caches this value in case parse_querystring is called again
    for the same request.

    You can pass the result to ``dict()``, but be aware that keys that
    appear multiple times will be lost (only the last value will be
    preserved).

    """
    source = environ.get('QUERY_STRING', '')
    if not source:
        return []
    if 'paste.parsed_querystring' in environ:
        parsed, check_source = environ['paste.parsed_querystring']
        if check_source == source:
            return parsed
    parsed = cgi.parse_qsl(source, keep_blank_values=True,
                           strict_parsing=False)
    environ['paste.parsed_querystring'] = (parsed, source)
    return parsed

def parse_dict_querystring(environ):
    """Parses a query string like parse_querystring, but returns a multidict

    Caches this value in case parse_dict_querystring is called again
    for the same request.

    Example::

        #environ['QUERY_STRING'] -  day=Monday&user=fred&user=jane
        >>> parsed = parse_dict_querystring(environ)

        >>> parsed['day']
        'Monday'
        >>> parsed['user']
        'fred'
        >>> parsed.getlist['user']
        ['fred', 'jane']

    """
    source = environ.get('QUERY_STRING', '')
    if not source:
        return {}
    if 'paste.parsed_dict_querystring' in environ:
        parsed, check_source = environ['paste.parsed_dict_querystring']
        if check_source == source:
            return parsed
    parsed = cgi.parse_qsl(source, keep_blank_values=True,
                           strict_parsing=False)
    multi = multidict(parsed)
    environ['paste.parsed_dict_querystring'] = (multi, source)
    return multi

def parse_formvars(environ, all_as_list=False, include_get_vars=True):
    """Parses the request, returning a dictionary of the keys.

    If ``all_as_list`` is true, then all values will be lists.  If
    not, then only values that show up multiple times will be lists.

    If ``include_get_vars`` is true and this was a POST request, then
    GET (query string) variables will also be folded into the
    dictionary.

    All values should be strings, except for file uploads which are
    left as FieldStorage instances.

    If the request was not a normal form request (e.g., a POST with an
    XML body) then the body of the request will be put into
    ``'__body__'``.  Other variables from the URL (GET) variables may
    also be present.
    """
    source = (environ.get('QUERY_STRING', ''),
              environ['wsgi.input'], environ['REQUEST_METHOD'],
              all_as_list, include_get_vars)
    if 'paste.parsed_formvars' in environ:
        parsed, check_source = environ['paste.parsed_formvars']
        if check_source == source:
            return parsed
    fs = cgi.FieldStorage(fp=environ['wsgi.input'],
                          environ=environ,
                          keep_blank_values=1)
    formvars = {}
    if not isinstance(fs.value, list):
        # Non-HTML form submission, so we just
        # return the field
        formvars['__body__'] = fs.value
    else:
        for name in fs.keys():
            values = fs[name]
            if not isinstance(values, list):
                values = [values]
            for value in values:
                if not value.filename:
                    value = value.value
                if name in formvars:
                    if isinstance(formvars[name], list):
                        formvars[name].append(value)
                    else:
                        formvars[name] = [formvars[name], value]
                elif all_as_list:
                    formvars[name] = [value]
                else:
                    formvars[name] = value
    if environ['REQUEST_METHOD'] == 'POST' and include_get_vars:
        for name, value in parse_querystring(environ):
            if name in formvars:
                if isinstance(formvars[name], list):
                    formvars[name].append(value)
                else:
                    formvars[name] = [formvars[name], value]
            elif all_as_list:
                formvars[name] = [value]
            else:
                formvars[name] = value
    environ['paste.parsed_formvars'] = (formvars, source)
    return formvars

def construct_url(environ, with_query_string=True, with_path_info=True,
                  script_name=None, path_info=None, querystring=None):
    """Reconstructs the URL from the WSGI environment.

    You may override SCRIPT_NAME, PATH_INFO, and QUERYSTRING with
    the keyword arguments.

    """
    url = environ['wsgi.url_scheme']+'://'

    if environ.get('HTTP_HOST'):
        url += environ['HTTP_HOST'].split(':')[0]
    else:
        url += environ['SERVER_NAME']

    if environ['wsgi.url_scheme'] == 'https':
        if environ['SERVER_PORT'] != '443':
            url += ':' + environ['SERVER_PORT']
    else:
        if environ['SERVER_PORT'] != '80':
            url += ':' + environ['SERVER_PORT']

    if script_name is None:
        url += environ.get('SCRIPT_NAME','')
    else:
        url += script_name
    if with_path_info:
        if path_info is None:
            url += environ.get('PATH_INFO','')
        else:
            url += path_info
    if with_query_string:
        if querystring is None:
            if environ.get('QUERY_STRING'):
                url += '?' + environ['QUERY_STRING']
        elif querystring:
            url += '?' + querystring
    return url

def resolve_relative_url(url, environ):
    """
    Resolve the given relative URL as being relative to the
    location represented by the environment.  This can be used
    for redirecting to a relative path.  Note: if url is already
    absolute, this function will (intentionally) have no effect
    on it.

    """
    cur_url = construct_url(environ, with_query_string=False)
    return urlparse.urljoin(cur_url, url)

def path_info_split(path_info):
    """
    Splits off the first segment of the path.  Returns (first_part,
    rest_of_path).  first_part can be None (if PATH_INFO is empty), ''
    (if PATH_INFO is '/'), or a name without any /'s.  rest_of_path
    can be '' or a string starting with /.

    """
    if not path_info:
        return None, ''
    assert path_info.startswith('/'), (
        "PATH_INFO should start with /: %r" % path_info)
    path_info = path_info.lstrip('/')
    if '/' in path_info:
        first, rest = path_info.split('/', 1)
        return first, '/' + rest
    else:
        return path_info, ''

def path_info_pop(environ):
    """
    'Pops' off the next segment of PATH_INFO, pushing it onto
    SCRIPT_NAME, and returning that segment.

    For instance::

        >>> def call_it(script_name, path_info):
        ...     env = {'SCRIPT_NAME': script_name, 'PATH_INFO': path_info}
        ...     result = path_info_pop(env)
        ...     print 'SCRIPT_NAME=%r; PATH_INFO=%r; returns=%r' % (
        ...         env['SCRIPT_NAME'], env['PATH_INFO'], result)
        >>> call_it('/foo', '/bar')
        SCRIPT_NAME='/foo/bar'; PATH_INFO=''; returns='bar'
        >>> call_it('/foo/bar', '')
        SCRIPT_NAME='/foo/bar'; PATH_INFO=''; returns=None
        >>> call_it('/foo/bar', '/')
        SCRIPT_NAME='/foo/bar/'; PATH_INFO=''; returns=''
        >>> call_it('', '/1/2/3')
        SCRIPT_NAME='/1'; PATH_INFO='/2/3'; returns='1'
        >>> call_it('', '//1/2')
        SCRIPT_NAME='//1'; PATH_INFO='/2'; returns='1'

    """
    path = environ.get('PATH_INFO', '')
    if not path:
        return None
    while path.startswith('/'):
        environ['SCRIPT_NAME'] += '/'
        path = path[1:]
    if '/' not in path:
        environ['SCRIPT_NAME'] += path
        environ['PATH_INFO'] = ''
        return path
    else:
        segment, path = path.split('/', 1)
        environ['PATH_INFO'] = '/' + path
        environ['SCRIPT_NAME'] += segment
        return segment

_parse_headers_special = {
    # This is a Zope convention, but we'll allow it here:
    'HTTP_CGI_AUTHORIZATION': 'Authorization',
    'CONTENT_LENGTH': 'Content-Length',
    'CONTENT_TYPE': 'Content-Type',
    }

def parse_headers(environ):
    """
    Parse the headers in the environment (like ``HTTP_HOST``) and
    yield a sequence of those (header_name, value) tuples.
    """
    # @@: Maybe should parse out comma-separated headers?
    for cgi_var, value in environ.iteritems():
        if cgi_var in _parse_headers_special:
            yield _parse_headers_special[cgi_var], value
        elif cgi_var.startswith('HTTP_'):
            yield cgi_var[5:].title().replace('_', '-'), value

class EnvironHeaders(DictMixin):
    """An object that represents the headers as present in a
    WSGI environment.

    This object is a wrapper (with no internal state) for a WSGI
    request object, representing the CGI-style HTTP_* keys as a
    dictionary.  Because a CGI environment can only hold one value for
    each key, this dictionary is single-valued (unlike outgoing
    headers).
    """

    def __init__(self, environ):
        self.environ = environ
        
    def __getitem__(self, item):
        item = item.replace('-', '_').upper()
        return self.environ['HTTP_'+item]

    def __setitem__(self, item, value):
        # @@: Should this dictionary be writable at all?
        item = item.replace('-', '_').upper()
        self.environ['HTTP_'+item] = value

    def __delitem__(self, item):
        item = item.replace('-', '_').upper()
        del self.environ['HTTP_'+item]

    def __iter__(self):
        for key in self.environ:
            if not key.startswith('HTTP_'):
                continue
            key = key[5:].replace('_', '-').title()
            yield key

    def keys(self):
        return list(self)

    def __contains__(self, item):
        item = item.replace('-', '_').upper()
        return 'HTTP_'+item in self.environ


if __name__ == '__main__':
    import doctest
    doctest.testmod()
