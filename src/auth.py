import typesense
from pymongo import MongoClient

from src.config import MONGO_DB_URI, TYPESENSE_API_KEY, TYPESENSE_HOST

typesense_client = typesense.Client(
    {
        "nodes": [{"host": TYPESENSE_HOST, "port": "443", "protocol": "https"}],
        "api_key": TYPESENSE_API_KEY,
        "connection_timeout_seconds": 2,
    }
)

mongo_client = MongoClient(MONGO_DB_URI)
