## tgss

This project enables semantic search functionality within a Telegram group or channel. Users can query the bot with text, and it will return links to the most relevant posts based on semantic similarity.

---

<ins>Status</ins>: in progress

---

<ins>How to run:</ins>

- Create a Telegram bot through BotFather and add it to the target group/channel as admin (with read permissions)
- Create Telegram user session (needed for indexing posts):
  ```bash
  cd components/indexer
  API_ID=... API_HASH=... python auth.py
  ```
- Start:
  ```bash
  docker compose up --build -d
  ```
- In bot chat, use `/search <query>` to get relevant posts

---

<ins>To do</ins>:

- [Done] ~~Embedding layer (mock)~~
- [Done] ~~Qdrant layer to store vectors + metadata~~
- [Done] ~~Posts indexing (initial/new/edited/deleted)~~
- [Done] ~~Search (limit usage to channel members)~~
- [To do] Replace embedding model with a real one (text + image, Russian support)
- [To do] Better UX for search results
