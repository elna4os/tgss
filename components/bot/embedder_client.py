import aiohttp


class EmbedderClient:
    """Provides an interface for interacting with an embedding service.
    """

    def __init__(self, base_url: str) -> None:
        """
        Args:
            base_url (str): The base URL of the embedding service.
        """

        self._base_url = base_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Gets the current aiohttp session, creating one if it doesn't exist or is closed.

        Returns:
            aiohttp.ClientSession: The current aiohttp session.
        """

        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

        return self._session

    async def embed_text(self, text: str) -> list[float]:
        """Embeds a given text using the embedding service.

        Args:
            text (str): The text to be embedded.

        Returns:
            list[float]: The embedding vector for the given text.
        """

        session = await self._get_session()
        async with session.post(
            f"{self._base_url}/embed/text",
            params={"text": text},
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

            return data["embedding"]

    async def embed_image(self, image_bytes: bytes) -> list[float]:
        """Embeds a given image using the embedding service.

        Args:
            image_bytes (bytes): The image data to be embedded.

        Returns:
            list[float]: The embedding vector for the given image.
        """

        session = await self._get_session()
        form = aiohttp.FormData()
        form.add_field("image", image_bytes, filename="image.jpg", content_type="image/jpeg")
        async with session.post(f"{self._base_url}/embed/image", data=form) as resp:
            resp.raise_for_status()
            data = await resp.json()

            return data["embedding"]

    async def close(self) -> None:
        """Closes the aiohttp session if it exists and is not already closed."""

        if self._session and not self._session.closed:
            await self._session.close()
