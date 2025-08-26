"""Simple in-memory user base used for demos/tests.

This module is not used for the production path (see db_connector for the
real user store). It exists to demonstrate a simple hashing approach.
"""
import hashlib

# Pre-hashed demo users (never store plain passwords!)
users = {
    "max": hashlib.sha256(b"12345").hexdigest(),
    "kim": hashlib.sha256(b"23456").hexdigest(),
    "ina": hashlib.sha256(b"34567").hexdigest(),
    "ulf": hashlib.sha256(b"45678").hexdigest(),
    "admin": hashlib.sha256(b"admin").hexdigest(),
}

def authenticate(username, password):
    """Return True if username exists and password matches the stored hash."""
    return username in users \
            and users[username] == hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_hash(password):
    """Return sha256 hash hex for the given password (demo utility)."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()