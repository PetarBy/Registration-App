# tests/test_captcha.py
import pytest
from captcha import generate_captcha, verify_captcha, _CAPTCHA_STORE

def test_generate_and_verify_captcha():
    captcha_id, img_bytes = generate_captcha()
    assert isinstance(captcha_id, str) and len(captcha_id) > 0
    assert isinstance(img_bytes, bytes) and img_bytes.startswith(b'\x89PNG')

    assert not verify_captcha(captcha_id, "WRONG")

    expected_code = _CAPTCHA_STORE.get(captcha_id)
    assert expected_code is not None

    assert verify_captcha(captcha_id, expected_code)
    assert not verify_captcha(captcha_id, expected_code)
