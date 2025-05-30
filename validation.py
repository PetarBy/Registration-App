import re

# Email must look like local@domain.tld
_EMAIL_REGEX = re.compile(
    r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"
)
# Nickname: 3–50 chars, letters, digits, underscores
_NICKNAME_REGEX = re.compile(r"^[A-Za-z0-9_]{3,50}$")

def is_valid_email(email: str) -> bool:
    """Return True if email has a valid format."""
    return bool(_EMAIL_REGEX.fullmatch(email))

def is_valid_nickname(nick: str) -> bool:
    """Return True if nickname meets length and character rules."""
    return bool(_NICKNAME_REGEX.fullmatch(nick))

def is_strong_password(pw: str) -> bool:
    """
    Return True if pw is at least 8 chars and contains:
      - one uppercase letter
      - one lowercase letter
      - one digit
      - one special character
    """
    if len(pw) < 8:
        return False
    if not re.search(r"[A-Z]", pw):
        return False
    if not re.search(r"[a-z]", pw):
        return False
    if not re.search(r"[0-9]", pw):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pw):
        return False
    return True
