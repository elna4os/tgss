from datetime import datetime
from typing import Optional

import asyncpg


class Database:
    """Provides an interface for interacting with the PostgreSQL database used by the bot.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @classmethod
    async def create(cls, dsn: str) -> "Database":
        pool = await asyncpg.create_pool(dsn)
        db = cls(pool)
        await db._migrate()

        return db

    async def _migrate(self) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS post_parts (
                    post_id          BIGINT NOT NULL,
                    chat_id          BIGINT NOT NULL,
                    created_at       TIMESTAMPTZ NOT NULL,
                    modality         TEXT NOT NULL,
                    qdrant_point_id  TEXT NOT NULL PRIMARY KEY
                )
            """)

    async def insert_part(
        self,
        post_id: int,
        chat_id: int,
        created_at: datetime,
        modality: str,
        qdrant_point_id: str,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO post_parts (post_id, chat_id, created_at, modality, qdrant_point_id)
                VALUES ($1, $2, $3, $4, $5)
            """, post_id, chat_id, created_at, modality, qdrant_point_id)

    async def delete_parts(self, post_id: int, chat_id: int) -> list[str]:
        """Deletes all parts for a post and returns their qdrant_point_ids."""
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "DELETE FROM post_parts WHERE post_id = $1 AND chat_id = $2 RETURNING qdrant_point_id",
                post_id, chat_id,
            )

            return [r["qdrant_point_id"] for r in rows]

    async def get_max_post_id(self, chat_id: int) -> Optional[int]:
        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT MAX(post_id) FROM post_parts WHERE chat_id = $1",
                chat_id,
            )

    async def close(self) -> None:
        await self._pool.close()
