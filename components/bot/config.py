import os

# Bot configuration
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])

# Embedder configuration
EMBEDDER_URL = os.getenv("EMBEDDER_URL", "http://embedder:8000")

# Qdrant configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "posts")

# Search configuration
SEARCH_LIMIT = int(os.getenv("SEARCH_LIMIT", "5"))
