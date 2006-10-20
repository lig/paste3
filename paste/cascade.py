# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php

"""
Cascades through several applications, so long as applications
return ``404 Not Found``.
"""
from paste import httpexceptions
from paste.util import converters

__all__ = ['Cascade']

def make_cascade(loader, global_conf, catch='404', **local_conf):
    """
    Expects configuration like:

    [composit:cascade]
    use = egg:Paste#cascade
    # all start with 'app' and are sorted alphabetically
    app1 = foo
    app2 = bar
    ...
    catch = 404 500 ...
    """
    catch = map(int, converters.aslist(catch))
    apps = []
    for name, value in local_conf.items():
        if not name.startswith('app'):
            raise ValueError(
                "Bad configuration key %r (=%r); all configuration keys "
                "must start with 'app'"
                % (name, value))
        app = loader.get_app(value, global_conf=global_conf)
        apps.append((name, app))
    apps.sort()
    apps = [app for name, app in apps]
    return Cascade(apps, catch=catch)
    
class Cascade(object):

    """
    Passed a list of applications, ``Cascade`` will try each of them
    in turn.  If one returns a status code listed in ``catch`` (by
    default just ``404 Not Found``) then the next application is
    tried.

    If all applications fail, then the last application's failure
    response is used.
    """

    def __init__(self, applications, catch=(404,)):
        self.apps = applications
        self.catch_codes = {}
        self.catch_exceptions = []
        for error in catch:
            if isinstance(error, str):
                error = int(error.split(None, 1)[0])
            if isinstance(error, httpexceptions.HTTPException):
                exc = error
                code = error.code
            else:
                exc = httpexceptions.get_exception(error)
                code = error
            self.catch_codes[code] = exc
            self.catch_exceptions.append(exc)
        self.catch_exceptions = tuple(self.catch_exceptions)
                
    def __call__(self, environ, start_response):
        failed = []
        def repl_start_response(status, headers, exc_info=None):
            code = int(status.split(None, 1)[0])
            if code in self.catch_codes:
                failed.append(None)
                return _consuming_writer
            return start_response(status, headers, exc_info)

        for app in self.apps[:-1]:
            environ_copy = environ.copy()
            failed = []
            try:
                v = app(environ_copy, repl_start_response)
                if not failed:
                    return v
                else:
                    if hasattr(v, 'close'):
                        # Exhaust the iterator first:
                        list(v)
                        # then close:
                        v.close()
            except self.catch_exceptions, e:
                pass
        return self.apps[-1](environ, start_response)

def _consuming_writer(s):
    pass
