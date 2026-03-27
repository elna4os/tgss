import os

from dotenv import load_dotenv

load_dotenv()

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])
SESSION_PATH = os.environ["SESSION_PATH"]
EMBEDDER_URL = os.environ["EMBEDDER_URL"]
QDRANT_HOST = os.environ["QDRANT_HOST"]
QDRANT_PORT = int(os.environ["QDRANT_PORT"])
QDRANT_COLLECTION = os.environ["QDRANT_COLLECTION"]
POSTGRES_DSN = os.environ["POSTGRES_DSN"]
INITIAL_INDEX_MONTHS = int(os.environ["INITIAL_INDEX_MONTHS"])
