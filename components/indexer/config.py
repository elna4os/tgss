import os

# Telegram configuration
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])
SESSION_PATH = os.getenv("SESSION_PATH", "/data/bot")

# Embedder configuration
EMBEDDER_URL = os.getenv("EMBEDDER_URL", "http://embedder:8000")

# Qdrant configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "posts")

# PostgreSQL configuration
POSTGRES_DSN = os.environ["POSTGRES_DSN"]

# Indexer configuration
INITIAL_INDEX_MONTHS = int(os.getenv("INITIAL_INDEX_MONTHS", "3"))
