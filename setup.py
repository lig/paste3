# If true, then the svn revision won't be used to calculate the
# revision (set to True for real releases)
RELEASE = False

__version__ = "0.0"

from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

setup(name="Paste",
      version=__version__,
      description="Tools for using a Web Server Gateway Interface stack",
      long_description="""\
These provide several pieces of "middleware" that can be nested to build
web applications.  Each piece of middleware uses the WSGI (`PEP 333`_)
interface, and should be compatible with other middleware based on those
interfaces.

.. _PEP 333: http://www.python.org/peps/pep-0333.html

As an example (and a working implementation), a version Webware
(http://webwareforpython.org) is included, built from these tools with
wrappers to provide the Webware API on top of the middleware
functionality.
""",
      classifiers=["Development Status :: 3 - Alpha",
                   "Intended Audience :: Developers",
                   "License :: OSI Approved :: Python Software Foundation License",
                   "Programming Language :: Python",
                   "Topic :: Internet :: WWW/HTTP",
                   "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
                   "Topic :: Software Development :: Libraries :: Python Modules",
                   ],
      keywords='web wsgi application server webware wareweb',
      author="Ian Bicking",
      author_email="ianb@colorstudy.com",
      url="http://pythonpaste.org",
      license="PSF",
      packages=find_packages(exclude=['ez_setup', 'examples', 'packages']),
      scripts=['scripts/paster'],
      download_url="",
      package_data={'': ['*.txt', '*.html', '*.conf'],
                    'paste.app_templates': ['*.*_tmpl'],
                    },
      zip_safe=False,
      entry_points={
        'paste.app_factory1': """
        cgi=paste.cgiapp:CGIApplication
        """,
        'paste.composit_factory1': """
        urlmap=paste.urlmap:urlmap_factory
        cascade=paste.cascade:make_cascade
        """,
        'paste.filter_app_factory1': """
        error_catcher=paste.exceptions.errormiddleware:ErrorMiddleware
        cgitb=paste.cgitb_catcher:CgitbMiddleware
        flup_session=paste.flup_session:SessionMiddleware
        gzip=paste.gzipper:middleware
        httpexceptions=paste.httpexceptions:middleware
        lint=paste.lint:middleware
        login=paste.login:middleware
        """,
        },
      )

# Send announce to:
#   web-sig@python.org
#   python-announce@python.org
#   python-list@python.org
