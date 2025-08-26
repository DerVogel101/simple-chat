"""Password hashing utilities using scrypt.

Provides helpers to create a random salt, hash a password with scrypt, and
verify a password against a stored scrypt hash. Hex encoding is used for
storing hash and salt in the database.
"""
import os
import hashlib

# Create salt
def make_salt() -> bytes:
    """Return a new 16-byte cryptographically secure salt."""
    return os.urandom(16)  # 16 bytes = 128 bits

# Hash password with scrypt
def hash_password(password: str, salt: bytes | None = None) -> tuple[str, str]:
    """Return a tuple of (hash_hex, salt_hex) for the given password.

    Parameters use scrypt with sensible defaults:
    - n (CPU/memory cost): 2**14 balances security and performance
    - r (block size): 8
    - p (parallelism): 2
    - dklen (derived key length): 64 bytes
    """
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
def verify_password(stored_hash: str, stored_salt: str, input_password: str) -> bool:
    """Return True if input_password matches the stored scrypt hash."""
    salt = bytes.fromhex(stored_salt)
    input_hash, _ = hash_password(input_password, salt)
    return input_hash == stored_hash


if __name__ == '__main__':
    # ---- Example Usage ----
    # Register user:
    hashed, salt = hash_password("mysecretpassword")
    # Store hashed and salt

    # Check password:
    is_valid = verify_password(hashed, salt, "mysecretpassword")  # True
    is_invalid = verify_password(hashed, salt, "wrongpassword")   # False