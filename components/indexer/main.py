import asyncio
import logging
from datetime import datetime, timezone

import config
from dateutil.relativedelta import relativedelta
from db import Database
from embedder_client import EmbedderClient
from indexer import Indexer
from qdrant import QdrantStore
from telethon import TelegramClient, events

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


async def main():
    db = None
    embedder = None
    qdrant = None
    tg_client = None
    try:
        db = await Database.create(dsn=config.POSTGRES_DSN)
        embedder = EmbedderClient(base_url=config.EMBEDDER_URL)
        vector_size = await embedder.get_vector_size()

        qdrant = await QdrantStore.create(
            host=config.QDRANT_HOST,
            port=config.QDRANT_PORT,
            collection=config.QDRANT_COLLECTION,
            vector_size=vector_size,
            retry_attempts=config.QDRANT_RETRY_ATTEMPTS,
            retry_backoff_seconds=config.QDRANT_RETRY_BACKOFF_SECONDS,
        )

        tg_client = TelegramClient(
            session=config.SESSION_PATH,
            api_id=config.API_ID,
            api_hash=config.API_HASH
        )
        await tg_client.start()

        indexer = Indexer(
            db=db,
            qdrant=qdrant,
            embedder=embedder,
            tg_client=tg_client
        )

        @tg_client.on(events.NewMessage(chats=config.CHANNEL_ID))
        async def on_new_message(event):
            logger.info("New message: %d", event.message.id)
            await indexer.index_message(message=event.message)

        @tg_client.on(events.MessageEdited(chats=config.CHANNEL_ID))
        async def on_message_edited(event):
            logger.info("Edited message: %d", event.message.id)
            await indexer.index_message(message=event.message)

        @tg_client.on(events.MessageDeleted(chats=config.CHANNEL_ID))
        async def on_message_deleted(event):
            chat_id = event.chat_id or config.CHANNEL_ID
            for msg_id in event.deleted_ids:
                logger.info("Deleted message: %d", msg_id)
                await indexer.delete_message(post_id=msg_id, chat_id=chat_id)

        await _initial_index(client=tg_client, indexer=indexer)

        logger.info("Bot is running")
        await tg_client.run_until_disconnected()
    finally:
        if tg_client is not None:
            await tg_client.disconnect()
        if db is not None:
            await db.close()
        if qdrant is not None:
            await qdrant.close()
        if embedder is not None:
            await embedder.close()


async def _initial_index(client: TelegramClient, indexer: Indexer) -> None:
    logger.info("Starting initial indexing (INITIAL_INDEX_MONTHS=%d)...", config.INITIAL_INDEX_MONTHS)

    max_indexed_id = await indexer.db.get_max_post_id(config.CHANNEL_ID)
    kwargs: dict = {'reverse': True}
    if max_indexed_id:
        kwargs["min_id"] = max_indexed_id
        logger.info("Resuming from post_id=%d", max_indexed_id)
    elif config.INITIAL_INDEX_MONTHS == 0:
        logger.info("INITIAL_INDEX_MONTHS=0, skipping initial indexing")
        return
    elif config.INITIAL_INDEX_MONTHS > 0:
        cutoff = datetime.now(timezone.utc) - relativedelta(months=config.INITIAL_INDEX_MONTHS)
        kwargs["offset_date"] = cutoff

    count = 0
    async for message in client.iter_messages(config.CHANNEL_ID, **kwargs):
        await indexer.index_message(message)
        count += 1
        logger.info("Indexed %d messages", count)

    logger.info("Initial indexing complete: %d messages processed", count)


if __name__ == "__main__":
    asyncio.run(main())
