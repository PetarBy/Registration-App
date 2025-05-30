import os
import hashlib
import hmac
import secrets
import datetime

from db import get_connection

def hash_password(password: str) -> bytes:

    salt = os.urandom(16)
    dk   = hashlib.pbkdf2_hmac(
        'sha256',                  # Hash algorithm
        password.encode('utf-8'),  # Convert password to bytes
        salt,                      # Provide the salt
        100_000                    # Number of iterations
    )
    return salt + dk

def check_password(stored: bytes, password: str) -> bool:
    """
    Verify a plaintext password against the stored (salt||dk).
    Uses hmac.compare_digest for timing-safe comparison.
    """
    salt        = stored[:16]
    expected_dk = stored[16:]
    new_dk      = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        100_000
    )
    return hmac.compare_digest(new_dk, expected_dk)

def create_session(user_id: int, days: int = 1) -> str:
    session_id = secrets.token_hex(32)  # 64-character hex token
    expires    = datetime.datetime.utcnow() + datetime.timedelta(days=days)

    conn = get_connection()
    cur  = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO sessions (session_id, user_id, expires) "
            "VALUES (%s, %s, %s)",
            (session_id, user_id, expires)
        )
        conn.commit()
    finally:
        cur.close()
        conn.close()

    return session_id

def get_user_from_session(session_id: str):
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT u.* FROM sessions s "
            "JOIN users u ON u.id = s.user_id "
            "WHERE s.session_id = %s AND s.expires > NOW()",
            (session_id,)
        )
        return cur.fetchone()
    finally:
        cur.close()
        conn.close()
