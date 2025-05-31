import http.cookies
import io
import urllib.parse
import pytest

from utils import parse_form, parse_cookies, set_cookie, send_redirect, send_html

class DummyHandler:

    def __init__(self, headers=None):
        self.headers = headers or {}
        self._sent_headers = []
        self.rfile = None
        self.wfile = None

    def send_response(self, status_code):
        self._sent_headers.append(('__status__', status_code))

    def send_header(self, key, value):
        self._sent_headers.append((key, value))

    def end_headers(self):
        self._sent_headers.append(('__end__', None))

    def write(self, data):
        # For send_html, wfile.write calls this
        if not hasattr(self, 'body'):
            self.body = b""
        self.body += data

@pytest.fixture
def form_handler(tmp_path):
    data = {"foo": ["bar", "baz"], "key": ["value"]}
    encoded = urllib.parse.urlencode([('foo', 'bar'), ('foo', 'baz'), ('key', 'value')])
    handler = DummyHandler({'Content-Length': str(len(encoded))})
    handler.rfile = io.BytesIO(encoded.encode('utf-8'))
    return handler

def test_parse_form(form_handler):
    result = parse_form(form_handler)
    assert result == {"foo": ["bar", "baz"], "key": ["value"]}

def test_parse_cookies_basic():
    headers = {'Cookie': 'sid=ABC123; theme=light'}
    handler = DummyHandler(headers)
    cookie = parse_cookies(handler)
    assert cookie['sid'].value == 'ABC123'
    assert cookie['theme'].value == 'light'

def test_set_cookie_and_retrieve():
    handler = DummyHandler()
    set_cookie(handler, 'sid', 'XYZ789', path='/app', http_only=False, max_age=3600)
    has_set_cookie = any(k == 'Set-Cookie' for k, _ in handler._sent_headers)
    assert has_set_cookie

    header_value = next(v for k, v in handler._sent_headers if k == 'Set-Cookie')
    morsel = http.cookies.SimpleCookie()
    morsel.load(header_value)
    assert morsel['sid'].value == 'XYZ789'
    assert morsel['sid']['path'] == '/app'
    assert 'httponly' not in morsel['sid'].keys() or morsel['sid']['httponly'] == ''
    assert morsel['sid']['max-age'] == '3600'

def test_send_redirect_and_send_html(monkeypatch):
    handler = DummyHandler()
    handler.wfile = handler
    send_redirect(handler, '/target')
    assert ('__status__', 302) in handler._sent_headers
    assert ('Location', '/target') in handler._sent_headers

    handler = DummyHandler()
    handler.wfile = handler
    body = b"<h1>Hello</h1>"
    send_html(handler, 200, body)
    assert ('__status__', 200) in handler._sent_headers
    assert ('Content-Type', 'text/html; charset=utf-8') in handler._sent_headers
    assert ('Content-Length', str(len(body))) in handler._sent_headers
    assert handler.body == body
