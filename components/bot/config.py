import os

BOT_TOKEN = os.environ["BOT_TOKEN"]

CHANNEL_ID = int(os.environ["CHANNEL_ID"])

EMBEDDER_URL = os.getenv("EMBEDDER_URL", "http://embedder:8000")

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "posts")

SEARCH_LIMIT = int(os.getenv("SEARCH_LIMIT", "5"))
