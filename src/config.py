import os

from dotenv import load_dotenv

load_dotenv()

TYPESENSE_HOST = os.environ["TYPESENSE_HOST"]
TYPESENSE_API_KEY = os.environ["TYPESENSE_API_KEY"]

MONGO_DB_URI = os.environ["MONGO_DB_URI"]

GITHUB_PAT = os.environ["GITHUB_PAT"]
