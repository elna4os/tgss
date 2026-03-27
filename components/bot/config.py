import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHANNEL_ID = int(os.environ["CHANNEL_ID"])
EMBEDDER_URL = os.environ["EMBEDDER_URL"]
QDRANT_HOST = os.environ["QDRANT_HOST"]
QDRANT_PORT = int(os.environ["QDRANT_PORT"])
QDRANT_COLLECTION = os.environ["QDRANT_COLLECTION"]
SEARCH_LIMIT = int(os.environ["SEARCH_LIMIT"])
