import urllib.parse
import http.cookies

def parse_form(handler):
    length = int(handler.headers.get('Content-Length', 0))
    raw = handler.rfile.read(length).decode('utf-8')
    return urllib.parse.parse_qs(raw)

def send_html(handler, status_code, body, content_type='text/html; charset=utf-8'):
    handler.send_response(status_code)
    handler.send_header('Content-Type', content_type)
    handler.send_header('Content-Length', str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

def send_redirect(handler, location):
    handler.send_response(302)
    handler.send_header('Location', location)
    handler.end_headers()

def parse_cookies(handler):
    raw = handler.headers.get('Cookie', '')
    cookie = http.cookies.SimpleCookie()
    cookie.load(raw)
    return cookie

def set_cookie(handler, name, value, path='/', http_only=True, max_age=None):
    cookie = http.cookies.SimpleCookie()
    cookie[name] = value
    morsel = cookie[name]
    morsel['path'] = path
    if http_only:
        morsel['httponly'] = True
    if max_age is not None:
        morsel['max-age'] = str(max_age)
    for m in cookie.values():
        handler.send_header('Set-Cookie', m.OutputString())
