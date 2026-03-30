import asyncio
import logging

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import ResponseHandlingException
from qdrant_client.models import (Distance, FieldCondition, Filter,
                                  MatchValue, PointIdsList, PointStruct,
                                  VectorParams)

logger = logging.getLogger(__name__)


class QdrantStore:
    def __init__(
        self,
        client: AsyncQdrantClient,
        collection: str,
        retry_attempts: int,
        retry_backoff_seconds: float,
    ) -> None:
        self._client = client
        self._collection = collection
        self._retry_attempts = max(1, retry_attempts)
        self._retry_backoff_seconds = max(0.0, retry_backoff_seconds)

    @classmethod
    async def create(
        cls,
        host: str,
        port: int,
        collection: str,
        vector_size: int,
        retry_attempts: int = 5,
        retry_backoff_seconds: float = 0.5,
    ) -> "QdrantStore":
        client = AsyncQdrantClient(host=host, port=port)
        store = cls(
            client=client,
            collection=collection,
            retry_attempts=retry_attempts,
            retry_backoff_seconds=retry_backoff_seconds,
        )
        await store._ensure_collection(vector_size)

        return store

    async def _with_retry(self, operation: str, func):
        delay = self._retry_backoff_seconds
        for attempt in range(1, self._retry_attempts + 1):
            try:
                return await func()
            except ResponseHandlingException as exc:
                if attempt >= self._retry_attempts:
                    logger.error(
                        "Qdrant %s failed after %d attempts: %s",
                        operation,
                        self._retry_attempts,
                        exc,
                    )
                    raise
                logger.warning(
                    "Qdrant %s failed (%d/%d): %s. Retrying in %.2fs",
                    operation,
                    attempt,
                    self._retry_attempts,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)
                delay = delay * 2 if delay > 0 else 0

    async def _ensure_collection(self, vector_size: int) -> None:
        collections = await self._with_retry("get_collections", self._client.get_collections)
        existing = {c.name for c in collections.collections}
        if self._collection not in existing:
            async def _create_collection():
                return await self._client.create_collection(
                    collection_name=self._collection,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
                )

            await self._with_retry("create_collection", _create_collection)

    async def upsert(
        self,
        point_id: str,
        vector: list[float],
        payload: dict
    ) -> None:
        async def _upsert():
            return await self._client.upsert(
                collection_name=self._collection,
                points=[PointStruct(id=point_id, vector=vector, payload=payload)],
            )

        await self._with_retry("upsert", _upsert)

    async def delete(self, point_id: str) -> None:
        async def _delete():
            return await self._client.delete(
                collection_name=self._collection,
                points_selector=PointIdsList(points=[point_id]),
            )

        await self._with_retry("delete", _delete)

    async def close(self) -> None:
        await self._client.close()

    async def query_points_by_modality(
        self,
        vector: list[float],
        modality: str,
        limit: int,
    ) -> list:
        async def _query_points():
            return await self._client.query_points(
                collection_name=self._collection,
                query=vector,
                query_filter=Filter(
                    must=[FieldCondition(key="modality", match=MatchValue(value=modality))]
                ),
                limit=limit,
                with_payload=True,
            )

        results = await self._with_retry("query_points", _query_points)

        return results.points
