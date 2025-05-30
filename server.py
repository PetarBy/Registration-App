import os
import base64
import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

from db import get_connection
from templates import render
from utils import (
    parse_form,
    send_html,
    send_redirect,
    parse_cookies,
    set_cookie
)
from auth import (
    hash_password,
    check_password,
    create_session,
    get_user_from_session
)
from validation import (
    is_valid_email,
    is_valid_nickname,
    is_strong_password
)
from captcha import (
    generate_captcha,
    verify_captcha
)

# Directory for static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/static/'):
            return self.serve_static()

        if self.path == '/':
            return self.show_home()
        if self.path == '/register':
            return self.show_register()
        if self.path == '/login':
            return self.show_login()
        if self.path == '/account':
            return self.show_account()
        if self.path == '/profile':
            return self.show_profile()
        if self.path == '/logout':
            return self.handle_logout()

        return self.send_error(404)

    def do_POST(self):
        if self.path == '/register':
            return self.handle_register()
        if self.path == '/login':
            return self.handle_login()
        if self.path == '/account':
            return self.handle_account()

        return self.send_error(404)

    def serve_static(self):
        rel_path = self.path[len('/static/'):].lstrip('/')
        full_path = os.path.join(STATIC_DIR, rel_path)
        if not os.path.isfile(full_path):
            return self.send_error(404)

        # Basic content-type detection
        if full_path.endswith('.css'):
            content_type = 'text/css'
        elif full_path.endswith('.js'):
            content_type = 'application/javascript'
        else:
            content_type = 'application/octet-stream'

        try:
            with open(full_path, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception:
            return self.send_error(500)

    def current_user(self):
        cookie = parse_cookies(self)
        morsel = cookie.get('session_id')
        if not morsel:
            return None
        return get_user_from_session(morsel.value)

    def show_home(self):
        user = self.current_user()
        if not user:
            return send_redirect(self, '/login')
        body = render('home.html', username=user['username'])
        return send_html(self, 200, body)

    def show_register(self):
        captcha_id, img_bytes = generate_captcha()
        img_b64 = base64.b64encode(img_bytes).decode('ascii')
        body = render(
            'register.html',
            captcha_id=captcha_id,
            captcha_image=img_b64
        )
        return send_html(self, 200, body)

    def handle_register(self):
        form = parse_form(self)

        # CAPTCHA check
        captcha_id   = form.get('captcha_id',   [''])[0]
        captcha_code = form.get('captcha_code', [''])[0]
        if not verify_captcha(captcha_id, captcha_code):
            return send_html(self, 400, b'Invalid CAPTCHA')

        # Extract and validate fields
        username = form.get('username', [''])[0].strip()
        email    = form.get('email',    [''])[0].strip()
        password = form.get('password', [''])[0]

        if not is_valid_nickname(username):
            return send_html(self, 400, b'Invalid username')
        if not is_valid_email(email):
            return send_html(self, 400, b'Invalid email')
        if not is_strong_password(password):
            return send_html(self, 400, b'Weak password')

        pwd_hash = hash_password(password)

        conn = get_connection()
        cur  = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, pwd_hash)
            )
            conn.commit()
            return send_redirect(self, '/login')
        except Exception:
            conn.rollback()
            return send_html(self, 400, b'Registration failed')
        finally:
            cur.close()
            conn.close()

    def show_login(self):
        return send_html(self, 200, render('login.html'))

    def handle_login(self):
        form     = parse_form(self)
        email    = form.get('email',    [''])[0].strip()
        password = form.get('password', [''])[0]

        conn = get_connection()
        cur  = conn.cursor(dictionary=True)
        try:
            cur.execute(
                "SELECT id, password_hash FROM users WHERE email = %s",
                (email,)
            )
            row = cur.fetchone()
            if row and check_password(row['password_hash'], password):
                session_id = create_session(row['id'])
                self.send_response(302)
                set_cookie(self, 'session_id', session_id, max_age=86400)
                self.send_header('Location', '/')
                self.end_headers()
            else:
                return send_html(self, 401, b'Invalid credentials')
        except Exception:
            return send_html(self, 500, b'Login failed')
        finally:
            cur.close()
            conn.close()

    def show_account(self):
        user = self.current_user()
        if not user:
            return send_redirect(self, '/login')
        body = render('account.html', username=user['username'])
        return send_html(self, 200, body)

    def handle_account(self):
        user = self.current_user()
        if not user:
            return send_redirect(self, '/login')

        form             = parse_form(self)
        action           = form.get('action',           [''])[0]
        current_password = form.get('current_password', [''])[0]

        if not check_password(user['password_hash'], current_password):
            return send_html(self, 400, b'Invalid current password')

        conn = get_connection()
        cur  = conn.cursor()
        try:
            if action == 'nickname':
                new_nick = form.get('new_nickname', [''])[0].strip()
                if not is_valid_nickname(new_nick):
                    return send_html(self, 400, b'Invalid nickname')
                cur.execute(
                    "UPDATE users SET username=%s, updated_at=NOW() WHERE id=%s",
                    (new_nick, user['id'])
                )

            elif action == 'password':
                new_pwd = form.get('new_password',     [''])[0]
                confirm = form.get('confirm_password', [''])[0]
                if new_pwd != confirm:
                    return send_html(self, 400, b'New passwords do not match')
                if not is_strong_password(new_pwd):
                    return send_html(self, 400, b'Weak password')
                new_hash = hash_password(new_pwd)
                cur.execute(
                    "UPDATE users SET password_hash=%s, updated_at=NOW() WHERE id=%s",
                    (new_hash, user['id'])
                )

            else:
                return send_html(self, 400, b'Unknown action')

            conn.commit()
            return send_redirect(self, '/account')
        except Exception:
            conn.rollback()
            return send_html(self, 500, b'Update failed')
        finally:
            cur.close()
            conn.close()

    def show_profile(self):
        user = self.current_user()
        if not user:
            return send_redirect(self, '/login')

        created = user['created_at'].strftime('%Y-%m-%d %H:%M')
        updated = (user['updated_at'].strftime('%Y-%m-%d %H:%M')
                   if user['updated_at'] else 'Never')

        body = render(
            'profile.html',
            id=user['id'],
            username=user['username'],
            email=user['email'],
            created_at=created,
            updated_at=updated,
            is_active='Yes' if user['is_active'] else 'No'
        )
        return send_html(self, 200, body)

    def handle_logout(self):
        cookie = parse_cookies(self)
        morsel = cookie.get('session_id')
        if morsel:
            conn = get_connection()
            cur  = conn.cursor()
            try:
                cur.execute(
                    "DELETE FROM sessions WHERE session_id = %s",
                    (morsel.value,)
                )
                conn.commit()
            finally:
                cur.close()
                conn.close()

        self.send_response(302)
        set_cookie(self, 'session_id', '', max_age=0)
        self.send_header('Location', '/login')
        self.end_headers()


def run():
    port = int(os.getenv('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), Handler)
    print(f"Server listening on http://0.0.0.0:{port}")
    server.serve_forever()


if __name__ == '__main__':
    run()
