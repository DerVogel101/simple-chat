"""Unit tests for the DBConnector SQLite data access layer.

These tests use a temporary on-disk SQLite database that is removed after
execution. They cover:
- User insertion and retrieval (including color format).
- Duplicate username constraint handling via IntegrityError.
- Authentication happy-path, wrong password, and missing user (None).
- Message insertion and retrieval with join to users.chat_color and the
  last_update filter.
"""
import os
import sqlite3
import tempfile
import unittest as ut
from db_connector import DBConnector


class TestDBConnector(ut.TestCase):
    """Integration-style tests against a temporary SQLite database file."""

    def setUp(self):
        """Create a fresh temporary DB file and open connector for each test."""
        # Create a temporary file path to use as a database
        fd, self.tmp_path = tempfile.mkstemp(prefix='simple_chat_test_', suffix='.db')
        os.close(fd)  # Close the OS-level handle; sqlite will open its own
        self.db = DBConnector(db_name=self.tmp_path)

    def tearDown(self):
        """Close the connector and remove the temporary DB file."""
        # Ensure DB is closed and temp file is deleted
        try:
            self.db.close()
        finally:
            if os.path.exists(self.tmp_path):
                os.remove(self.tmp_path)

    def test_insert_and_fetch_user(self):
        """insert_user + fetch_user return expected username and a color value."""
        username = 'alice'
        email = 'alice@alice.com'
        pw = 'pw1'
        self.db.insert_user(email, username, pw)
        row = self.db.fetch_user(email)
        self.assertIsNotNone(row)
        uname, color = row
        self.assertEqual(uname, username)
        self.assertRegex(color, r'^#[0-9a-fA-F]{6}$')

    def test_duplicate_user_raises_integrity_error(self):
        """Inserting the same username twice should raise sqlite3.IntegrityError."""
        username = 'bob'
        email = 'bob@bob.bob'
        pw = 'pw2'
        self.db.insert_user(email, username, pw)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.insert_user(email, username, pw)

    def test_authenticate_user(self):
        """authenticate_user returns (False, None) for missing, (True/False, username) otherwise."""
        self.assertEqual(self.db.authenticate_user('missing', 'x'), (False, None))
        email = 'carol@carol.mail'
        username = "carol"
        pw = 'pw3'
        self.db.insert_user(email, username, pw)
        self.assertTrue(self.db.authenticate_user(email, pw)[0])
        self.assertFalse(self.db.authenticate_user(email, 'wrong')[0])

    def test_insert_and_fetch_messages_with_join_and_filter(self):
        """Message flow end-to-end, join color, ordering, and last_update filter."""
        # Prepare two users
        self.db.insert_user('u1@u1.u', 'u1',  'a')
        self.db.insert_user('u2@u2.u', 'u2', 'b')
        # Insert messages
        self.db.insert_message('u1@u1.u', 'hello')
        self.db.insert_message('u2@u2.u', 'world')
        msgs = self.db.fetch_messages()
        # Expect list of tuples; schema: messages.* + users.chat_color
        self.assertGreaterEqual(len(msgs), 2)
        # columns: id, username, message, timestamp, color (from messages), chat_color (from users)
        # Verify join color is present at the last position
        last_cols = msgs[0]
        self.assertGreaterEqual(len(last_cols), 6)
        self.assertRegex(last_cols[-1], r'^#[0-9a-fA-F]{6}$')
        # Check ordering by timestamp ASC implied; IDs increasing
        ids = [row[1] for row in msgs]
        self.assertEqual(ids, sorted(ids))
        # Test last_update filter: fetch only messages with id > last_id_of_first_list
        last_id = ids[-1]
        # Add one more message
        self.db.insert_message('u1@u1.u', 'again')
        newer = self.db.fetch_messages(last_update=last_id)
        self.assertTrue(all(row[1] > last_id for row in newer))
        self.assertTrue(any(row[3] == 'again' for row in newer))


if __name__ == '__main__':
    ut.main()