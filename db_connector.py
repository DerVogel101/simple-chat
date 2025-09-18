"""Database access layer for the Simple Chat app using SQLite.

Provides helper methods for creating tables, inserting/fetching users and
messages, and verifying user credentials with salted password hashes.
"""
import sqlite3
import random
from warnings import deprecated

from doughnut_wall import hash_password, verify_password

class DBConnector:
    """Thin wrapper around sqlite3 for the app's persistence needs."""
    def __init__(self, db_name='database.db'):
        """Open a connection to the SQLite database and ensure schema exists."""
        # Allow usage from server threads in tests/endpoints by disabling thread check
        self.connection = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.connection.cursor()
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they do not exist yet.

        The SQL is read from the 'create_tables.sql' file to keep schema
        changes centralized.
        """
        with open('create_tables.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        self.cursor.executescript(sql_script)
        self.connection.commit()

    def insert_user(self, email, name, password):
        """Insert a new user with a random chat color and a salted pw hash."""
        pwhash, salt = hash_password(password)
        color = '#{:06x}'.format(random.randint(0, 0xFFFFFF))
        self.cursor.execute('INSERT INTO users (username, email, pwhash, salt, chat_color) VALUES (?, ?, ?, ?, ?)', (name, email, pwhash, salt, color))
        self.connection.commit()

    @deprecated("Only for testing purposes; use authenticate_user instead.")
    def fetch_user(self, email):
        """Return (username, chat_color) for the given email or None. (Deprecated)"""
        self.cursor.execute('SELECT username, chat_color FROM users WHERE email = ?', (email,))
        return self.cursor.fetchone()

    def fetch_messages(self, last_update: None | str = None):
        """Fetch messages joined with user color, optionally newer than last_update."""
        self.cursor.execute('SELECT users.username, messages.*, users.chat_color FROM messages JOIN users ON messages.email = users.email WHERE messages.id > ? ORDER BY timestamp ASC', (last_update,) if last_update else (0,))
        return self.cursor.fetchall()

    def insert_message(self, email, message):
        """Persist a new message authored by the user identified by the given email."""
        self.cursor.execute('INSERT INTO messages (email, message) VALUES (?, ?)', (email, message))
        self.connection.commit()

    def authenticate_user(self, email, pw):
        """Authenticate a user by email and password.

        Returns a tuple (is_valid, username):
        - is_valid: True if the password matches; False if it does not or the user does not exist.
        - username: The stored username for the account if it exists; otherwise None.
        """
        self.cursor.execute("SELECT salt, pwhash, username FROM users WHERE email = ?", (email,))
        row = self.cursor.fetchone()
        if row is None:
            return False, None
        salt, stored_hash, username = row
        return verify_password(stored_hash, salt, pw), username


    def close(self):
        """Close the underlying SQLite connection."""
        self.connection.close()

if __name__ == '__main__':

    users = {
        ("max@mail.com", "max"): "12345",
        ("kim@mail.com", "kim"): "23456",
        ("ina@mail.com", "ina"): "34567",
        ("ulf@mail.com", "ulf"): "45678",
        ("admin@mail.com", "admin"): "admin",
    }

    db = DBConnector()
    for username, pwhash in users.items():
        email, username = username
        try:
            db.insert_user(email, username, pwhash)
        except sqlite3.IntegrityError:
            pass
    print(db.authenticate_user("max@mail.com", "12345"))  # True
    print(db.authenticate_user("max@mail.com", "wrong"))  # False
    db.close()