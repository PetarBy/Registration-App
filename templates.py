import os

# Directory where .html templates live
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

def render(template_name: str, **context) -> bytes:
    """
    Load the given template, substitute {placeholders} via str.format(),
    and return the result as UTF-8 bytes.
    """
    path = os.path.join(TEMPLATE_DIR, template_name)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        raise RuntimeError(f"Template not found: {template_name}")

    try:
        rendered = template.format(**context)
    except KeyError as e:
        missing = e.args[0]
        raise RuntimeError(f"Missing template variable: {missing} in {template_name}")

    return rendered.encode('utf-8')
