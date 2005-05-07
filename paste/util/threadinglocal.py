try:
    import threading
except ImportError:
    # No threads, so "thread local" means process-global
    class local(object):
        pass
else:
    try:
        local = threading.local
    except AttributeError:
        # Added in 2.4, but now we'll have to define it ourselves
        import thread
        class local(object):

            def __init__(self):
                self.__dict__['__objs'] = {}

            def __getattr__(self, attr, g=thread.get_ident):
                try:
                    return self.__dict__['__objs'][g()][attr]
                except KeyError:
                    raise AttributeError(
                        "No variable %s defined for the thread %s"
                        % (attr, g()))

            def __setattr__(self, attr, value, g=thread.get_ident):
                self.__dict__['__objs'].setdefault(g(), {})[attr] = value

            def __delattr__(self, attr, g=thread.get_ident):
                try:
                    del self.__dict__['__objs'][g()][attr]
                except KeyError:
                    raise AttributeError(
                        "No variable %s defined for thread %s"
                        % (attr, g()))

# All the Paste thread-local stuff goes in this dictionary:
local.wsgi = {}