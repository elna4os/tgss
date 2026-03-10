import logging
from dataclasses import dataclass
from typing import Optional
from uuid import uuid4

from db import Database
from embedder_client import EmbedderClient
from qdrant import QdrantStore
from telethon import TelegramClient
from telethon.tl.types import Message, MessageMediaPhoto

logger = logging.getLogger(__name__)


@dataclass
class _Part:
    """Represents a part of a message, which can be either text or image.

    Attributes:
        modality (str): The modality of the part, e.g., "text" or "image".
        text (Optional[str]): The text content if modality is "text", otherwise None.
    """

    modality: str
    text: Optional[str] = None


class Indexer:
    """Handles the indexing of messages into the database and Qdrant.
    """

    def __init__(
        self,
        db: Database,
        qdrant: QdrantStore,
        embedder: EmbedderClient,
        tg_client: TelegramClient,
    ) -> None:
        """
        Args:
            db (Database): The database instance.
            qdrant (QdrantStore): The Qdrant store instance.
            embedder (EmbedderClient): The embedder client instance.
            tg_client (TelegramClient): The Telegram client instance.
        """

        self.db = db
        self._qdrant = qdrant
        self._embedder = embedder
        self._tg_client = tg_client

    async def index_message(self, message: Message) -> None:
        """Indexes a message into the database and Qdrant.

        Args:
            message (Message): The message to be indexed.
        """

        parts = self._extract_parts(message=message)
        if not parts:
            return

        # Delete existing parts first (full re-index)
        await self.delete_message(post_id=message.id, chat_id=message.chat_id)

        await self.db.upsert_post(post_id=message.id, chat_id=message.chat_id, created_at=message.date)

        for part in parts:
            if part.modality == "text":
                vector = await self._embedder.embed_text(text=part.text)
            else:
                image_bytes = await self._tg_client.download_media(message=message, file=bytes)
                vector = await self._embedder.embed_image(image_bytes=image_bytes)

            point_id = str(uuid4())
            payload = {"post_id": message.id, "chat_id": message.chat_id}
            await self._qdrant.upsert(point_id=point_id, vector=vector, payload=payload)
            await self.db.insert_part(
                post_id=message.id,
                chat_id=message.chat_id,
                modality=part.modality,
                qdrant_point_id=point_id,
            )

    async def delete_message(self, post_id: int, chat_id: int) -> None:
        """Deletes a message from the database and Qdrant.

        Args:
            post_id (int): The ID of the Telegram message (post) to delete.
            chat_id (int): The ID of the Telegram chat (channel) the post belongs to.
        """

        parts = await self.db.get_post_parts(post_id=post_id, chat_id=chat_id)
        for part in parts:
            await self._qdrant.delete(point_id=part.qdrant_point_id)
        await self.db.delete_post(post_id=post_id, chat_id=chat_id)

    def _extract_parts(self, message: Message) -> list[_Part]:
        """Extracts the parts of a message, which can include text and images.

        Args:
            message (Message): The message to extract parts from.

        Returns:
            list[_Part]: A list of parts extracted from the message.
        """

        parts: list[_Part] = []

        text = message.text or message.message
        if text and text.strip():
            parts.append(_Part(modality="text", text=text))

        if isinstance(message.media, MessageMediaPhoto):
            parts.append(_Part(modality="image"))

        return parts
