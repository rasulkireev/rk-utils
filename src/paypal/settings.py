"""Module with Paypal API Settings"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PAYPAL_URL = "https://api-m.sandbox.paypal.com"
PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

YAML_DATA_DIR = Path.cwd() / "data"
