import os
import hashlib
import hmac

def hash_password(password: str) -> bytes:
    salt = os.urandom(16)
    dk   = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100_000
    )
    return salt + dk

def check_password(stored: bytes, password: str) -> bool:
    salt, expected_dk = stored[:16], stored[16:]
    new_dk = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100_000
    )
    return hmac.compare_digest(new_dk, expected_dk)
