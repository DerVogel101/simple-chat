import os
import hashlib

# Create salt
def make_salt():
    return os.urandom(16)  # 16 bytes = 128 bits

# Hash password with scrypt
def hash_password(password, salt=None):
    if salt is None:
        salt = make_salt()
    pw_hash = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=2**14,     # CPU/memory cost factor (16384) - reasonable default
        r=8,         # block size - default
        p=2,         # parallelism factor
        dklen=64     # desired key length in bytes
    )
    return pw_hash.hex(), salt.hex()  # Store hex strings in DB

# Verify password
def verify_password(stored_hash, stored_salt, input_password):
    salt = bytes.fromhex(stored_salt)
    input_hash, _ = hash_password(input_password, salt)
    return input_hash == stored_hash

# ---- Example Usage ----
# Register user:
hashed, salt = hash_password("mysecretpassword")
# Store hashed and salt

# Check password:
is_valid = verify_password(hashed, salt, "mysecretpassword")  # True
is_invalid = verify_password(hashed, salt, "wrongpassword")   # False