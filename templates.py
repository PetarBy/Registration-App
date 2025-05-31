# templates.py

import os

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

def _load_raw(name: str) -> str:
    path = os.path.join(TEMPLATE_DIR, name)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise RuntimeError(f"Template not found: {name}")

def render(template_name: str, **context) -> bytes:

    raw_child = _load_raw(template_name)
    try:
        child_html = raw_child.format(**context)
    except KeyError as e:
        raise RuntimeError(f"Missing template variable: {e.args[0]} in {template_name}")

    raw_base = _load_raw('base.html')

    full_context = dict(context)
    full_context['content'] = child_html

    try:
        final_html = raw_base.format(**full_context)
    except KeyError as e:
        raise RuntimeError(f"Missing template variable: {e.args[0]} in base.html")

    return final_html.encode('utf-8')
