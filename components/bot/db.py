from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import asyncpg


@dataclass
class PostPart:
    """Represents a part of a post in the database.

    Attributes:
        id (int): The unique identifier of the post part.
        post_id (int): The ID of the Telegram message (post) this part belongs to.
        chat_id (int): The ID of the Telegram chat (channel) this post belongs to.
        modality (str): The modality of the part, e.g., "text" or "image".
        qdrant_point_id (str): The ID of the corresponding point in Qdrant.
    """

    id: int
    post_id: int
    chat_id: int
    modality: str
    qdrant_point_id: str


class Database:
    """Provides an interface for interacting with the PostgreSQL database used by the bot.
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        """
        Args:
            pool (asyncpg.Pool): The connection pool for the PostgreSQL database.
        """

        self._pool = pool

    @classmethod
    async def create(cls, dsn: str) -> "Database":
        """Creates a new Database instance by establishing a connection pool to the PostgreSQL database.

        Args:
            dsn (str): The Data Source Name (DSN) for connecting to the PostgreSQL database.

        Returns:
            Database: A new instance of the Database class.
        """

        pool = await asyncpg.create_pool(dsn)
        db = cls(pool)
        await db._migrate()

        return db

    async def _migrate(self) -> None:
        """Ensures that the necessary tables exist in the database, creating them if they do not."""

        async with self._pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    post_id     BIGINT NOT NULL,
                    chat_id     BIGINT NOT NULL,
                    created_at  TIMESTAMPTZ NOT NULL,
                    PRIMARY KEY (post_id, chat_id)
                )
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS post_parts (
                    id               SERIAL PRIMARY KEY,
                    post_id          BIGINT NOT NULL,
                    chat_id          BIGINT NOT NULL,
                    modality         TEXT NOT NULL,
                    qdrant_point_id  TEXT NOT NULL,
                    FOREIGN KEY (post_id, chat_id)
                        REFERENCES posts (post_id, chat_id) ON DELETE CASCADE
                )
            """)

    async def upsert_post(
        self,
        post_id: int,
        chat_id: int,
        created_at: datetime
    ) -> None:
        """Inserts a new post into the database or does nothing if a post with the same post_id and chat_id already exists.

        Args:
            post_id (int): The ID of the Telegram message (post).
            chat_id (int): The ID of the Telegram chat (channel).
            created_at (datetime): The timestamp when the post was created.
        """

        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO posts (post_id, chat_id, created_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (post_id, chat_id) DO NOTHING
            """, post_id, chat_id, created_at)

    async def delete_post(
        self,
        post_id: int,
        chat_id: int
    ) -> None:
        """Deletes a post from the database.

        Args:
            post_id (int): The ID of the Telegram message (post) to delete.
            chat_id (int): The ID of the Telegram chat (channel) the post belongs to.
        """

        async with self._pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM posts WHERE post_id = $1 AND chat_id = $2",
                post_id, chat_id,
            )

    async def get_post_parts(
        self,
        post_id: int,
        chat_id: int
    ) -> list[PostPart]:
        """Retrieves all parts of a post from the database.

        Args:
            post_id (int): The ID of the Telegram message (post) to retrieve parts for.
            chat_id (int): The ID of the Telegram chat (channel) the post belongs to.

        Returns:
            list[PostPart]: A list of PostPart instances representing the parts of the post.
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM post_parts WHERE post_id = $1 AND chat_id = $2",
                post_id, chat_id,
            )
            return [PostPart(**dict(r)) for r in rows]

    async def insert_part(
        self,
        post_id: int,
        chat_id: int,
        modality: str,
        qdrant_point_id: str,
    ) -> None:
        """Inserts a new part of a post into the database.

        Args:
            post_id (int): The ID of the Telegram message (post) the part belongs to.
            chat_id (int): The ID of the Telegram chat (channel) the part belongs to.
            modality (str): The modality of the part (e.g., "image", "text").
            qdrant_point_id (str): The ID of the corresponding Qdrant point.
        """

        async with self._pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO post_parts (post_id, chat_id, modality, qdrant_point_id)
                VALUES ($1, $2, $3, $4)
            """, post_id, chat_id, modality, qdrant_point_id)

    async def get_max_post_id(self, chat_id: int) -> Optional[int]:
        """Retrieves the maximum post_id for a given chat_id from the database. This is used to determine where to resume indexing from.

        Args:
            chat_id (int): The ID of the Telegram chat (channel) to retrieve the maximum post_id for.

        Returns:
            Optional[int]: The maximum post_id for the given chat_id, or None if there are no posts for that chat_id.
        """

        async with self._pool.acquire() as conn:
            return await conn.fetchval(
                "SELECT MAX(post_id) FROM posts WHERE chat_id = $1",
                chat_id,
            )

    async def delete_part(self, part_id: int) -> None:
        """Deletes a part of a post from the database.

        Args:
            part_id (int): The ID of the part to delete.
        """

        async with self._pool.acquire() as conn:
            await conn.execute("DELETE FROM post_parts WHERE id = $1", part_id)

    async def close(self) -> None:
        """Closes the database connection pool.
        """

        await self._pool.close()
