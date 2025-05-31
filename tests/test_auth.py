import pytest

from auth import hash_password, check_password, create_session, get_user_from_session
from db import get_connection

@pytest.fixture(scope="module")
def temp_db(monkeypatch):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions;")
    conn.commit()
    cur.close()
    conn.close()
    return True

def test_hash_and_check_password():
    pw = "Str0ng!Pass"
    h = hash_password(pw)
    assert isinstance(h, bytes)
    assert check_password(h, pw)
    assert not check_password(h, "wrong!")

def test_create_and_retrieve_session(temp_db):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        ("tempuser", "temp@example.com", hash_password("Temp!Pass1"))
    )
    conn.commit()
    user_id = cur.lastrowid

    session_id = create_session(user_id, days=1)
    assert isinstance(session_id, str) and len(session_id) == 64

    user_row = get_user_from_session(session_id)
    assert isinstance(user_row, dict)
    assert user_row['id'] == user_id
    assert user_row['email'] == "temp@example.com"

    cur.execute("DELETE FROM sessions WHERE session_id = %s", (session_id,))
    cur.execute("DELETE FROM users WHERE id = %s", (user_id,))
    conn.commit()
    cur.close()
    conn.close()
