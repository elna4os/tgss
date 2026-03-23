import os

import uvicorn
from embedders import EmbedderBase, create_embedder
from fastapi import FastAPI, File, UploadFile
from fastapi_models import EmbedResponse


def create_app(embedder: EmbedderBase) -> FastAPI:
    app = FastAPI(title="Embedder API")

    @app.post("/embed/text")
    async def embed_text(text: str) -> EmbedResponse:
        return EmbedResponse(embedding=embedder.embed_text(text))

    @app.post("/embed/image")
    async def embed_image(image: UploadFile = File(...)) -> EmbedResponse:
        return EmbedResponse(embedding=embedder.embed_image(await image.read()))

    @app.get("/vector_size")
    async def get_vector_size():
        return {"vector_size": embedder.get_vector_size()}

    @app.get("/health")
    async def health_check():
        return {
            "status": "ok",
            "embedder": embedder.__class__.__name__
        }

    return app


if __name__ == "__main__":
    model_name = os.getenv("EMBEDDER_MODEL", "mock")
    embedder = create_embedder(model_name)
    app = create_app(embedder)
    uvicorn.run(app, host="0.0.0.0", port=8000)
