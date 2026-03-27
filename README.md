## tgss

Semantic search for Telegram channels. Users send `/search <query>` to the bot and get links to the most relevant posts, matched by text and image embeddings.

---

### Architecture

| Component    | Description                                                              |
| ------------ | ------------------------------------------------------------------------ |
| **bot**      | Handles `/search` commands, checks channel membership, queries Qdrant    |
| **indexer**  | Monitors channel for new/edited/deleted messages, embeds and stores them |
| **embedder** | FastAPI service wrapping Jina CLIP v2 (text + image embeddings)          |
| **qdrant**   | Vector database for similarity search                                    |
| **postgres** | Stores post metadata and tracks indexed parts                            |

---

### Prerequisites

- Docker & Docker Compose
- Telegram API credentials from [my.telegram.org](https://my.telegram.org) (`API_ID`, `API_HASH`)
- Telegram bot token from [@BotFather](https://t.me/BotFather)
- The bot must be added to the target channel as admin (with read permissions)

---

### Setup

**1. Configure environment files**

Each component has its own `.env.sample`. Copy and fill them in:

```bash
# Required for all components:
cp components/bot/.env.sample components/bot/.env
cp components/indexer/.env.sample components/indexer/.env
cp components/embedder/.env.sample components/embedder/.env
cp components/postgres/.env.sample components/postgres/.env
```

Key variables to fill:

| File            | Variable               | Description                                               |
| --------------- | ---------------------- | --------------------------------------------------------- |
| `bot/.env`      | `BOT_TOKEN`            | Bot token from BotFather                                  |
| `bot/.env`      | `CHANNEL_ID`           | Target channel ID (negative number, e.g. `-100123456789`) |
| `indexer/.env`  | `API_ID`               | Telegram API ID                                           |
| `indexer/.env`  | `API_HASH`             | Telegram API Hash                                         |
| `indexer/.env`  | `CHANNEL_ID`           | Same channel ID as bot                                    |
| `indexer/.env`  | `POSTGRES_DSN`         | e.g. `postgresql://tgss:<password>@postgres:5432/tgss`    |
| `indexer/.env`  | `INITIAL_INDEX_MONTHS` | `>0` = last N months, `0` = skip, `-1` = entire history   |
| `postgres/.env` | `POSTGRES_PASSWORD`    | Database password (must match DSN above)                  |
| `embedder/.env` | `EMBEDDER_MODEL`       | `jina-clip-v2` for production, `mock` for testing         |

**2. Create Telegram session**

The indexer uses a Telegram user session to read channel messages. Create it once:

```bash
cd components/indexer
pip install telethon python-dotenv
python auth.py
```

This will prompt for your phone number and confirmation code. The session file will be saved to `components/indexer/session/`.

**3. Start**

```bash
docker compose up --build -d
```

**4. Use**

In a private chat with the bot, send:

```
/search <query>
```

---

### To do

- [x] Embedding layer (mock)
- [x] Qdrant layer to store vectors + metadata
- [x] Posts indexing (initial/new/edited/deleted)
- [x] Search (limit usage to channel members)
- [x] Replace mock embedder with a real one (text + image, Russian support)
- [ ] Batch indexing (Triton server + ONNX?)
- [ ] Improve ranking quality (jina-clip-v2 is not really good for text-image matching)
- [ ] EmbedderClient: add timeouts
- [ ] Event handlers: add exceptions handling
- [ ] Better UX for search results
