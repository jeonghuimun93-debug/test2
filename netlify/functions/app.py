from pathlib import Path
import sys

FUNC_DIR = Path(__file__).resolve().parent
if str(FUNC_DIR) not in sys.path:
    sys.path.insert(0, str(FUNC_DIR))

from serverless_wsgi import handle_request
from web_app import app


def handler(event, context):
    return handle_request(app, event, context)
