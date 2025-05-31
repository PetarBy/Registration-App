import random
import string
import uuid
from PIL import Image, ImageDraw, ImageFont
import io

_CAPTCHA_STORE = {}

def generate_captcha():
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    captcha_id = str(uuid.uuid4())

    img = Image.new('RGB', (120, 30), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()
    draw.text((5, 5), code, font=font, fill=(0, 0, 0))

    buf = io.BytesIO()
    img.save(buf, format='PNG')
    image_bytes = buf.getvalue()

    _CAPTCHA_STORE[captcha_id] = code
    return captcha_id, image_bytes

def verify_captcha(captcha_id: str, user_input: str) -> bool:
    expected = _CAPTCHA_STORE.get(captcha_id)
    if expected and expected.lower() == user_input.strip().lower():
        del _CAPTCHA_STORE[captcha_id]
        return True
    return False
