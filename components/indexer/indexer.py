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
    modality: str
    text: Optional[str] = None


class Indexer:
    def __init__(
        self,
        db: Database,
        qdrant: QdrantStore,
        embedder: EmbedderClient,
        tg_client: TelegramClient,
    ) -> None:
        self.db = db
        self._qdrant = qdrant
        self._embedder = embedder
        self._tg_client = tg_client

    async def index_message(self, message: Message) -> None:
        parts = self._extract_parts(message=message)
        if not parts:
            return

        await self.delete_message(post_id=message.id, chat_id=message.chat_id)
        for part in parts:
            if part.modality == "text":
                vector = await self._embedder.embed_text(text=part.text)
            else:
                image_bytes = await self._tg_client.download_media(message=message, file=bytes)
                vector = await self._embedder.embed_image(image_bytes=image_bytes)
            point_id = str(uuid4())
            payload = {"post_id": message.id, "chat_id": message.chat_id, "modality": part.modality}
            await self._qdrant.upsert(point_id=point_id, vector=vector, payload=payload)
            await self.db.insert_part(
                post_id=message.id,
                chat_id=message.chat_id,
                created_at=message.date,
                modality=part.modality,
                qdrant_point_id=point_id,
            )

    async def delete_message(self, post_id: int, chat_id: int) -> None:
        point_ids = await self.db.delete_parts(post_id=post_id, chat_id=chat_id)
        for point_id in point_ids:
            await self._qdrant.delete(point_id=point_id)

    def _extract_parts(self, message: Message) -> list[_Part]:
        parts = []
        text = message.text or message.message
        if text and text.strip():
            parts.append(_Part(modality="text", text=text))
        if isinstance(message.media, MessageMediaPhoto):
            parts.append(_Part(modality="image"))

        return parts
