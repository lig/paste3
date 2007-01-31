# (c) 2005 Ben Bangert
# This module is part of the Python Paste Project and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php
from paste.fixture import *
from paste.request import *
from paste.wsgiwrappers import WSGIRequest
from py.test import raises

def simpleapp(environ, start_response):
    status = '200 OK'
    response_headers = [('Content-type','text/plain')]
    start_response(status, response_headers)
    request = WSGIRequest(environ)
    return ['Hello world!\n', 'The get is %s' % str(request.GET),
        ' and Val is %s' % request.GET.get('name'),
        'The languages are: %s' % request.languages,
        'The accepttypes is: %s' % request.match_accept(['text/html', 'application/xml'])]

def test_gets():
    app = TestApp(simpleapp)
    res = app.get('/')
    assert 'Hello' in res
    assert "get is MultiDict([])" in res
    
    res = app.get('/?name=george')
    res.mustcontain("get is MultiDict([('name', 'george')])")
    res.mustcontain("Val is george")

def test_language_parsing():
    app = TestApp(simpleapp)
    res = app.get('/')
    assert "The languages are: ['en-us']" in res
    
    res = app.get('/', headers={'Accept-Language':'da, en-gb;q=0.8, en;q=0.7'})
    assert "languages are: ['da', 'en-gb', 'en', 'en-us']" in res

    res = app.get('/', headers={'Accept-Language':'en-gb;q=0.8, da, en;q=0.7'})
    assert "languages are: ['da', 'en-gb', 'en', 'en-us']" in res

def test_mime_parsing():
    app = TestApp(simpleapp)
    res = app.get('/', headers={'Accept':'text/html'})
    assert "accepttypes is: ['text/html']" in res
    
    res = app.get('/', headers={'Accept':'application/xml'})
    assert "accepttypes is: ['application/xml']" in res
    
    res = app.get('/', headers={'Accept':'application/xml,*/*'})
    assert "accepttypes is: ['text/html', 'application/xml']" in res
