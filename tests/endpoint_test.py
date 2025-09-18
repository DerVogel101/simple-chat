"""HTTP endpoint tests for the Simple Chat Bottle application.

These tests start a local WSGI server against the real Bottle app wrapped
with Beaker sessions and exercise all public endpoints via real HTTP
requests. A temporary SQLite database is injected into the app for each
test to ensure isolation and deterministic behavior.
"""
import json
import os
import tempfile
import threading
import time
import unittest as ut
from urllib import request as urr
from urllib import parse as urp
import http.cookiejar as cookiejar
from wsgiref.simple_server import make_server

import main  # The web app module (Bottle + Beaker)
from db_connector import DBConnector


class HTTPClient:
    """Small helper around urllib with cookie support and convenience methods."""
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.cj = cookiejar.CookieJar()
        self.opener = urr.build_opener(urr.HTTPCookieProcessor(self.cj))

    def url(self, path: str) -> str:
        if not path.startswith('/'):
            path = '/' + path
        return self.base_url + path

    def get(self, path: str):
        return self.opener.open(self.url(path))

    def post(self, path: str, data: dict[str, str]):
        enc = urp.urlencode(data).encode('utf-8')
        req = urr.Request(self.url(path), data=enc, method='POST')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        return self.opener.open(req)

    def put(self, path: str, data: dict[str, str]):
        enc = urp.urlencode(data).encode('utf-8')
        req = urr.Request(self.url(path), data=enc, method='PUT')
        req.add_header('Content-Type', 'application/x-www-form-urlencoded')
        return self.opener.open(req)


class TestEndpoints(ut.TestCase):
    """End-to-end HTTP tests covering all defined routes in main.py."""

    def setUp(self):
        # Prepare a fresh temporary database and inject it into the app
        fd, self.tmp_db = tempfile.mkstemp(prefix='simple_chat_http_', suffix='.db')
        os.close(fd)
        self.db = DBConnector(db_name=self.tmp_db)
        # Monkey-patch the global DB in the main module before starting server
        main.db.close()
        main.db = self.db

        # Start a local WSGI server on an ephemeral port
        self.server = make_server('127.0.0.1', 0, main.app)
        self.port = self.server.server_port
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

        # Wait briefly to ensure server is accepting connections
        time.sleep(0.05)

        self.client = HTTPClient(f'http://127.0.0.1:{self.port}')

    def tearDown(self):
        try:
            self.server.shutdown()
            self.thread.join(timeout=2)
        finally:
            try:
                self.db.close()
            finally:
                if os.path.exists(self.tmp_db):
                    os.remove(self.tmp_db)

    # ---- Helper flows ----
    def signup_user(self, email: str, username: str, password: str):
        resp = self.client.post('/signup', {
            'email': email,
            'email_confirm': email,
            'username': username,
            'username_confirm': username,
            'password': password,
            'password_confirm': password,
        })
        # Followed redirects end at '/'
        self.assertTrue(resp.geturl().endswith('/'))
        return resp

    def login_user(self, email: str, password: str):
        resp = self.client.post('/auth', {'email': email, 'password': password})
        return resp

    # ---- Tests ----
    def test_auth_page_and_static_assets(self):
        # GET /auth (login page)
        r = self.client.get('/auth')
        body = r.read().decode('utf-8')
        self.assertIn('Schätt Äbb', body)
        self.assertIn('value="Login"', body)

        # GET /style.css
        r2 = self.client.get('/style.css')
        css = r2.read().decode('utf-8')
        self.assertIn('body', css)

        # GET /fail (error page)
        r3 = self.client.get('/fail')
        fail_html = r3.read().decode('utf-8')
        self.assertTrue(len(fail_html) > 0)

    def test_signup_invalid_and_valid_flow(self):
        # Invalid email should redirect back to /signup
        r_invalid = self.client.post('/signup', {
            'email': 'not-an-email',
            'email_confirm': 'not-an-email',
            'username': 'u',
            'username_confirm': 'u',
            'password': 'p',
            'password_confirm': 'p',
        })
        self.assertTrue(r_invalid.geturl().endswith('/signup'))

        # Valid signup should end up at '/'
        r = self.signup_user('alice@example.com', 'alice', 'pw1')
        body = r.read().decode('utf-8')
        # After redirect to '/', index should render the template and contain username
        self.assertIn('alice', body)

    def test_login_wrong_and_right_password(self):
        # Create a user first via signup
        self.signup_user('bob@example.com', 'bob', 'pw2')
        # Logout to clear session
        r_logout = self.client.get('/logout')
        self.assertTrue(r_logout.geturl().endswith('/auth'))

        # Wrong credentials -> redirect to /fail
        r_wrong = self.login_user('bob@example.com', 'wrong')
        self.assertTrue(r_wrong.geturl().endswith('/fail'))

        # Correct credentials -> redirect to '/'
        r_right = self.login_user('bob@example.com', 'pw2')
        self.assertTrue(r_right.geturl().endswith('/'))
        body = r_right.read().decode('utf-8')
        self.assertIn('bob', body)

    def test_messages_lifecycle_and_filter(self):
        # Sign up and stay logged in
        self.signup_user('carol@example.com', 'carol', 'pw3')

        # PUT /messages to add a message
        r_put = self.client.put('/messages', {'msg': 'hello world'})
        txt = r_put.read().decode('utf-8')
        self.assertIn('Message added successfully', txt)

        # GET /messages to read all
        r_get = self.client.get('/messages')
        data = json.loads(r_get.read().decode('utf-8'))
        self.assertGreaterEqual(len(data), 1)
        # Row layout: [users.username, messages.id, messages.email, messages.message, messages.timestamp, users.chat_color]
        first = data[0]
        self.assertEqual(first[0], 'carol')
        self.assertRegex(first[-1], r'^#[0-9a-fA-F]{6}$')

        # Add another message and use last_id filter
        last_id = data[-1][1]
        self.client.put('/messages', {'msg': 'again'})
        r_get_new = self.client.get(f'/messages?last_id={last_id}')
        newer = json.loads(r_get_new.read().decode('utf-8'))
        self.assertTrue(all(row[1] > last_id for row in newer))
        self.assertTrue(any(row[3] == 'again' for row in newer))

    def test_protected_routes_require_auth_and_logout(self):
        # Accessing '/' unauthenticated should redirect to /auth
        r = self.client.get('/')
        self.assertTrue(r.geturl().endswith('/auth'))

        # After signup, '/' should be accessible
        self.signup_user('dave@example.com', 'dave', 'pw4')
        r2 = self.client.get('/')
        body = r2.read().decode('utf-8')
        self.assertIn('dave', body)

        # Logout clears session and protects again
        r3 = self.client.get('/logout')
        self.assertTrue(r3.geturl().endswith('/auth'))
        r4 = self.client.get('/')
        self.assertTrue(r4.geturl().endswith('/auth'))


if __name__ == '__main__':
    ut.main()
