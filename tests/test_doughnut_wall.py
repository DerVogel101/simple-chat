"""Unit tests for doughnut_wall password utilities.

These tests validate:
- Salt generation returns 16 random bytes.
- Password hashing returns hex strings with expected lengths.
- Hashing is deterministic when the same salt is reused.
- Password verification works for correct and incorrect inputs.
"""
import unittest as ut
from doughnut_wall import make_salt, hash_password, verify_password, validate_email


class TestDoughnutWall(ut.TestCase):
    """Tests for make_salt, hash_password, and verify_password."""

    def test_make_salt_length_and_randomness(self):
        """Salt should be 16 bytes and random across calls."""
        s1 = make_salt()
        s2 = make_salt()
        self.assertIsInstance(s1, (bytes, bytearray))
        self.assertEqual(len(s1), 16)
        self.assertEqual(len(s2), 16)
        # High probability they differ
        self.assertNotEqual(s1, s2)

    def test_hash_password_outputs_hex_and_lengths(self):
        """hash_password returns hex strings with correct lengths (128/32)."""
        pw = 'secret-password'
        hash_hex, salt_hex = hash_password(pw)
        # Hex strings
        self.assertRegex(hash_hex, r'^[0-9a-f]+$')
        self.assertRegex(salt_hex, r'^[0-9a-f]+$')
        # Lengths: dklen=64 bytes -> 128 hex chars; salt=16 bytes -> 32 hex chars
        self.assertEqual(len(hash_hex), 128)
        self.assertEqual(len(salt_hex), 32)

    def test_hash_password_deterministic_with_same_salt(self):
        """Reusing the same salt for the same password yields same hash."""
        pw = 'another-pass'
        # Generate a salt once, then reuse
        _, salt_hex = hash_password(pw)
        salt_bytes = bytes.fromhex(salt_hex)
        h1, _ = hash_password(pw, salt_bytes)
        h2, _ = hash_password(pw, salt_bytes)
        self.assertEqual(h1, h2)

    def test_verify_password_true_and_false(self):
        """verify_password returns True for correct PW and False for wrong one."""
        pw = 'correct-horse-battery-staple'
        stored_hash, stored_salt = hash_password(pw)
        self.assertTrue(verify_password(stored_hash, stored_salt, pw))
        self.assertFalse(verify_password(stored_hash, stored_salt, 'wrong'))

    def test_validate_email(self):
        """validate_email returns True for valid emails, False otherwise."""
        valid_emails = [
            "valid@mail.com",
            "miml@asssddahbbashhsabfhsabfhbfhdbhuasafbhasfbhufb345433232ß4059849320.de"
        ]
        invalid_emails = [
            "invalidmail.com",
            "invalid@mailcom",
            "invalid@ mail.com",
            "invalid@@mail.com",
            "invalid@mail..com",
            "invalid@.com",
            "invalid@a.com ",
            "@mail.com",
            "plainaddress",
            "missing@domain",
            "missingatsign.com"
        ]
        for email in valid_emails:
            self.assertTrue(validate_email(email), f"Should be valid: {email}")
        for email in invalid_emails:
            self.assertFalse(validate_email(email), f"Should be invalid: {email}")


if __name__ == '__main__':
    ut.main()