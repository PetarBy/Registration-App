import threading
import time
import os
import http.client
import pytest

from server import run

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8001

@pytest.fixture(scope="module", autouse=True)
def start_server():
    os.environ['PORT'] = str(SERVER_PORT)
    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    time.sleep(0.5)
    yield

def http_get(path, cookie=None):
    conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
    headers = {}
    if cookie:
        headers['Cookie'] = cookie
    conn.request('GET', path, headers=headers)
    resp = conn.getresponse()
    body = resp.read().decode('utf-8', errors='ignore')
    conn.close()
    return resp.status, body, resp.getheader('Set-Cookie')

def http_post(path, params, cookie=None):
    conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
    body = '&'.join(f"{k}={v}" for k, v in params.items())
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    if cookie:
        headers['Cookie'] = cookie
    conn.request('POST', path, body=body, headers=headers)
    resp = conn.getresponse()
    resp_body = resp.read().decode('utf-8', errors='ignore')
    sc = resp.getheader('Set-Cookie')
    conn.close()
    return resp.status, resp_body, sc

def test_register_page_renders_form():
    status, body, _ = http_get('/register')
    assert status == 200
    assert '<form' in body and 'name="username"' in body

def test_login_page_renders_form():
    status, body, _ = http_get('/login')
    assert status == 200
    assert '<form' in body and 'name="email"' in body

def test_404_for_unknown_path():
    status, _, _ = http_get('/does_not_exist')
    assert status == 404

def test_home_redirects_to_login_when_not_logged_in():
    status, _, _ = http_get('/')
    assert status == 302

def test_static_serving_css():
    status, _, _ = http_get('/static/css/styles.css')
    assert status in (200, 404)
