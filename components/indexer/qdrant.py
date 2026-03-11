from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (Distance, PointIdsList, PointStruct,
                                  VectorParams)


class QdrantStore:
    """Provides an interface for interacting with a Qdrant vector database.
    """

    def __init__(
        self,
        client: AsyncQdrantClient,
        collection: str
    ) -> None:
        """
        Args:
            client (AsyncQdrantClient): The Qdrant client instance.
            collection (str): The name of the Qdrant collection.
        """

        self._client = client
        self._collection = collection

    @classmethod
    async def create(
        cls,
        host: str,
        port: int,
        collection: str,
        vector_size: int
    ) -> "QdrantStore":
        """Creates a new QdrantStore instance by establishing a connection to the Qdrant server and ensuring the collection exists.

        Args:
            host (str): The hostname of the Qdrant server.
            port (int): The port of the Qdrant server.
            collection (str): The name of the Qdrant collection.
            vector_size (int): The size of the vectors to be stored in the collection.

        Returns:
            QdrantStore: A new instance of the QdrantStore class.
        """

        client = AsyncQdrantClient(host=host, port=port)
        store = cls(client, collection)
        await store._ensure_collection(vector_size)

        return store

    async def _ensure_collection(self, vector_size: int) -> None:
        """Ensures that the Qdrant collection exists, creating it if it does not.

        Args:
            vector_size (int): The size of the vectors to be stored in the collection.
        """

        collections = await self._client.get_collections()
        existing = {c.name for c in collections.collections}
        if self._collection not in existing:
            await self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )

    async def upsert(
        self,
        point_id: str,
        vector: list[float],
        payload: dict
    ) -> None:
        """Inserts or updates a point in the Qdrant collection.

        Args:
            point_id (str): The unique identifier of the point.
            vector (list[float]): The vector representation of the point.
            payload (dict): Additional data associated with the point.
        """

        await self._client.upsert(
            collection_name=self._collection,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )

    async def delete(self, point_id: str) -> None:
        """Deletes a point from the Qdrant collection.

        Args:
            point_id (str): The unique identifier of the point to be deleted.
        """

        await self._client.delete(
            collection_name=self._collection,
            points_selector=PointIdsList(points=[point_id]),
        )

    async def close(self) -> None:
        """Closes the connection to the Qdrant client.
        """

        await self._client.close()
