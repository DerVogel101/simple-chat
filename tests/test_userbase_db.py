import unittest as ut
import os
import sqlite3
import tempfile
from userbase_db import UserManager


class TestUserManager(ut.TestCase):
    """Integration-style tests for UserManager using a temporary SQLite file."""

    def setUp(self):
        """Create a fresh temporary DB file and open manager for each test."""
        fd, self.tmp_path = tempfile.mkstemp(prefix='simple_chat_test_', suffix='.db')
        os.close(fd)  # Close the OS-level handle; sqlite will open its own
        self.db = UserManager(db_name=self.tmp_path)

    def tearDown(self):
        """Close the manager and remove the temporary DB file."""
        try:
            self.db.close()
        finally:
            if os.path.exists(self.tmp_path):
                os.remove(self.tmp_path)

    def test_create_and_authenticate_user(self):
        """Happy-path: create_user -> authenticate True, wrong pw -> False, missing -> False."""
        email = 'alice@example.com'  # In UserManager, the "username" parameter is used as email
        pw = 'secret1'
        self.assertTrue(self.db.create_user(email, pw))
        # Correct password
        self.assertTrue(self.db.authenticate(email, pw))
        # Wrong password
        self.assertFalse(self.db.authenticate(email, 'wrong'))
        # Missing user
        self.assertFalse(self.db.authenticate('missing@example.com', 'x'))

    def test_duplicate_user_returns_false(self):
        """Creating the same user twice should return False (IntegrityError handled)."""
        email = 'bob@example.com'
        pw = 'pw2'
        self.assertTrue(self.db.create_user(email, pw))
        # Second insert should be handled and return False
        self.assertFalse(self.db.create_user(email, pw))

    def test_delete_user(self):
        """Delete an existing user -> True, authenticate then fails; deleting again -> False."""
        email = 'carol@example.com'
        pw = 'pw3'
        self.db.create_user(email, pw)
        # Delete should succeed
        self.assertTrue(self.db.delete_user(email))
        # Authentication should now fail
        self.assertFalse(self.db.authenticate(email, pw))
        # Deleting again should report False (no row deleted)
        self.assertFalse(self.db.delete_user(email))

    def test_change_password(self):
        """Changing password updates credentials accordingly."""
        email = 'dave@example.com'
        pw_old = 'oldpw'
        pw_new = 'newpw'
        self.db.create_user(email, pw_old)
        # Initially authenticates with old password
        self.assertTrue(self.db.authenticate(email, pw_old))
        # Change password
        self.assertTrue(self.db.change_user_password(email, pw_new))
        # Old password should fail now
        self.assertFalse(self.db.authenticate(email, pw_old))
        # New password should succeed
        self.assertTrue(self.db.authenticate(email, pw_new))

    def test_check_user_exists(self):
        """check_user_exists reflects presence/absence of a user by email."""
        email = 'eve@example.com'
        self.assertFalse(self.db.check_user_exists(email))
        self.assertTrue(self.db.create_user(email, 'pw'))
        self.assertTrue(self.db.check_user_exists(email))


if __name__ == '__main__':
    ut.main()