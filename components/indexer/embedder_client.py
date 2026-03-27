import aiohttp


class EmbedderClient:
    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()

        return self._session

    async def embed_text(self, text: str) -> list[float]:
        session = await self._get_session()
        async with session.post(
            f"{self._base_url}/embed/text",
            params={"text": text},
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()

            return data["embedding"]

    async def embed_image(self, image_bytes: bytes) -> list[float]:
        session = await self._get_session()
        form = aiohttp.FormData()
        form.add_field("image", image_bytes, filename="image.jpg", content_type="image/jpeg")
        async with session.post(f"{self._base_url}/embed/image", data=form) as resp:
            resp.raise_for_status()
            data = await resp.json()

            return data["embedding"]

    async def get_vector_size(self) -> int:
        session = await self._get_session()
        async with session.get(f"{self._base_url}/vector_size") as resp:
            resp.raise_for_status()
            data = await resp.json()

            return int(data["vector_size"])

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
