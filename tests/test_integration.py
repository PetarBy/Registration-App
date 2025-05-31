# tests/test_integration.py
import threading
import time
import os
import re
import http.client
import subprocess
import pytest

from server import run
from db import get_connection
import captcha

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8002

@pytest.fixture(scope="module", autouse=True)
def setup_db_and_server():
    env = {
        'DB_NAME': 'registration_app_test',
        'DB_USER': os.getenv('DB_USER'),
        'DB_PASSWORD': os.getenv('DB_PASSWORD'),
        'DB_HOST': os.getenv('DB_HOST', 'localhost'),
        'DB_PORT': os.getenv('DB_PORT', '3306'),
        'PORT': str(SERVER_PORT)
    }
    os.environ.update(env)

    subprocess.run([
        'mysql', '-u', env['DB_USER'], f"-p{env['DB_PASSWORD']}",
        '-e', 'DROP DATABASE IF EXISTS registration_app_test;'
    ], check=True)
    subprocess.run([
        'mysql', '-u', env['DB_USER'], f"-p{env['DB_PASSWORD']}",
        '-e', 'CREATE DATABASE registration_app_test;'
    ], check=True)
    subprocess.run([
        'mysql', '-u', env['DB_USER'], f"-p{env['DB_PASSWORD']}",
        'registration_app_test'
    ], input=open('sql/init_db.sql','rb').read(), check=True)

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
    set_cookie = resp.getheader('Set-Cookie')
    conn.close()
    return resp.status, body, set_cookie

def http_post(path, params, cookie=None):
    conn = http.client.HTTPConnection(SERVER_HOST, SERVER_PORT)
    body = '&'.join(f"{k}={v}" for k, v in params.items())
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    if cookie:
        headers['Cookie'] = cookie
    conn.request('POST', path, body=body, headers=headers)
    resp = conn.getresponse()
    resp_body = resp.read().decode('utf-8', errors='ignore')
    set_cookie = resp.getheader('Set-Cookie')
    conn.close()
    return resp.status, resp_body, set_cookie

def extract_hidden_value(html: str, name: str) -> str:
    pattern = rf'<input[^>]+name="{name}"[^>]+value="([^"]+)"'
    m = re.search(pattern, html)
    if not m:
        return ''
    return m.group(1)

def test_full_registration_and_account_flow():
    status, body, _ = http_get('/register')
    assert status == 200
    captcha_id = extract_hidden_value(body, 'captcha_id')
    assert captcha_id

    expected_code = captcha._CAPTCHA_STORE.get(captcha_id)
    assert expected_code

    params = {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'Str0ng!Pass1',
        'captcha_id': captcha_id,
        'captcha_code': expected_code
    }
    status, _, _ = http_post('/register', params)
    assert status == 302

    status, _, set_cookie = http_post('/login', {
        'email': 'test@example.com',
        'password': 'Str0ng!Pass1'
    })
    assert status == 302
    assert 'session_id=' in (set_cookie or '')

    session_cookie = set_cookie.split(';', 1)[0]

    status, body, _ = http_get('/', session_cookie)
    assert status == 200
    assert 'Welcome' in body or 'welcome' in body.lower()

    status, _, _ = http_get('/account', session_cookie)
    assert status == 200

    status, _, _ = http_post('/account', {
        'action': 'nickname',
        'current_password': 'Str0ng!Pass1',
        'new_nickname': 'newuser'
    }, cookie=session_cookie)
    assert status == 302

    status, _, _ = http_post('/account', {
        'action': 'password',
        'current_password': 'Str0ng!Pass1',
        'new_password': 'An0ther!Pass2',
        'confirm_password': 'An0ther!Pass2'
    }, cookie=session_cookie)
    assert status == 302

    status, _, _ = http_get('/logout', session_cookie)
    assert status == 302

    status, _, _ = http_get('/', session_cookie)
    assert status == 302

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE email = %s", ('test@example.com',))
    conn.commit()
    cur.close()
    conn.close()
