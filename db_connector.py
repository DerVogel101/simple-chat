import sqlite3
import random
from doughnut_wall import hash_password, verify_password

class DBConnector:
    def __init__(self, db_name='database.db'):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self._create_tables()

    def _create_tables(self):
        with open('create_tables.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        self.cursor.executescript(sql_script)
        self.connection.commit()

    def insert_user(self, name, password):
        pwhash, salt = hash_password(password)
        color = '#{:06x}'.format(random.randint(0, 0xFFFFFF))
        self.cursor.execute('INSERT INTO users (username, pwhash, salt, chat_color) VALUES (?, ?, ?, ?)', (name, pwhash, salt, color))
        self.connection.commit()

    def fetch_user(self, name):
        self.cursor.execute('SELECT username, chat_color FROM users WHERE username = ?', (name,))
        return self.cursor.fetchone()

    def fetch_messages(self, last_update: None | str = None):
        self.cursor.execute('SELECT messages.*, users.chat_color FROM messages JOIN users ON messages.username = users.username WHERE messages.id > ? ORDER BY timestamp ASC', (last_update,) if last_update else (0,))
        return self.cursor.fetchall()

    def insert_message(self, username, message):
        self.cursor.execute('INSERT INTO messages (username, message) VALUES (?, ?)', (username, message))
        self.connection.commit()

    def authenticate_user(self, name, pw):
        self.cursor.execute("SELECT salt, pwhash FROM users WHERE username = ?", (name,))
        row = self.cursor.fetchone()
        if row is None:
            return None
        salt, stored_hash = row
        return verify_password(stored_hash, salt, pw)


    def close(self):
        self.connection.close()

if __name__ == '__main__':

    users = {
        "max": "12345",
        "kim": "23456",
        "ina": "34567",
        "ulf": "45678",
        "admin": "admin",
    }

    db = DBConnector()
    for username, pwhash in users.items():
        try:
            db.insert_user(username, pwhash)
        except sqlite3.IntegrityError:
            pass
    print(db.authenticate_user("max", "12345"))  # True
    print(db.authenticate_user("max", "wrong"))  # False
    db.close()