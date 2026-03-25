## tgss

This project enables semantic search functionality within a Telegram group or channel. Users can query the bot with text, and it will return links to the most relevant posts based on semantic similarity.

---

**Status**: in progress

---

**How to run**:

- Create a Telegram bot through BotFather and add it to the target group/channel as admin (with read permissions)
- Create Telegram user session (needed for indexing posts):
  ```bash
  cd components/indexer
  API_ID=... API_HASH=... python auth.py
  ```
- Create your own `.env` file with the required parameters (see [.env_sample](.env_sample) for reference)
- Start:
  ```bash
  docker compose up --build -d
  ```
- In bot chat, use `/search <query>` to get relevant posts

---

**To do**:

- [Done] Embedding layer (mock)
- [Done] Qdrant layer to store vectors + metadata
- [Done] Posts indexing (initial/new/edited/deleted)
- [Done] Search (limit usage to channel members)
- [Done] Replace mock embedder with a real one (text + image, Russian support)
- [Todo] Quantize Jina text/image encoders (int8 or FP16), convert to ONNX
- [Todo] Get rid of magic constants
- [Todo] Better UX for search results
