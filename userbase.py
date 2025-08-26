# Stub module for user authentication

import hashlib

users = {
    "max": hashlib.sha256(b"12345").hexdigest(),
    "kim": hashlib.sha256(b"23456").hexdigest(),
    "ina": hashlib.sha256(b"34567").hexdigest(),
    "ulf": hashlib.sha256(b"45678").hexdigest(),
    "admin": hashlib.sha256(b"admin").hexdigest(),
}

def authenticate(username, password):
    return username in users \
            and users[username] == hashlib.sha256(password.encode('utf-8')).hexdigest()

def get_hash(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()