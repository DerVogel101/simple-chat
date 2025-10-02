import sqlite3
import random
from doughnut_wall import hash_password, verify_password


class UserManager:
    """
    Class that handles authentication with database backend
    """
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

    def create_user(self, username: str, password: str) -> bool:
        """
        Create a new user in the database
        :param username: logon name
        :param password: password to save
        :return: True if user was created
        """
        pwhash, salt = hash_password(password)
        color = '#{:06x}'.format(random.randint(0, 0xFFFFFF))
        try:
            self.cursor.execute('INSERT INTO users (username, email, pwhash, salt, chat_color) VALUES (?, ?, ?, ?, ?)',
                                (username, username, pwhash, salt, color))
            self.connection.commit()
        except sqlite3.Error:
            return False  # Username already exists
        return True

    def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate against the database
        :param username: username to check
        :param password: password to check
        :return: True if authenticated
        """
        pw = password
        email = username
        self.cursor.execute("SELECT salt, pwhash FROM users WHERE email = ?", (email,))
        row = self.cursor.fetchone()
        if row is None:
            return False
        salt, stored_hash = row
        return verify_password(stored_hash, salt, pw)

    def delete_user(self, username: str) -> bool:
        """
        Delete a user from the database
        :param username: username to delete
        :return: True on success
        """
        try:
            self.cursor.execute('DELETE FROM users WHERE email = ?', (username,))
            self.connection.commit()
            return self.cursor.rowcount > 0  # True if a row was deleted
        except sqlite3.Error:
            return False

    def change_user_password(self, username: str, password: str) -> bool:
        """
        Change the password for a user
        :param username: username to change
        :param password: new password
        :return: True on success
        """
        pwhash, salt = hash_password(password)
        try:
            self.cursor.execute('UPDATE users SET pwhash = ?, salt = ? WHERE email = ?', (pwhash, salt, username))
            self.connection.commit()
            return self.cursor.rowcount > 0  # True if a row was updated
        except sqlite3.Error:
            return False

    def check_user_exists(self, username: str) -> bool:
        """
        Check if a user exists in the database
        :param username: logon name to look for
        :return: True if user exists
        """
        self.cursor.execute('SELECT 1 FROM users WHERE email = ?', (username,))
        return self.cursor.fetchone() is not None

    def close(self):
        """Close the underlying SQLite connection."""
        self.connection.close()
