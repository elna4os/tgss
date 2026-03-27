import io
from abc import ABC, abstractmethod
from typing import List

import numpy as np
import torch
from PIL import Image
from transformers import AutoModel

EMB_SIZE = {
    "mock": 32,
    "jina-clip-v2": 64
}


class EmbedderBase(ABC):
    """Abstract base class for embedding models
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def embed_image(self, image: bytes) -> List[float]:
        pass

    @abstractmethod
    def get_vector_size(self) -> int:
        pass


class MockEmbedder(EmbedderBase):
    """Mock embedder that generates random vectors. Used for testing and development.
    """

    def __init__(self, size: int = 32):
        super().__init__()
        self.size = size

    def embed_text(self, text: str) -> List[float]:
        return np.random.rand(self.size).tolist()

    def embed_image(self, image: bytes) -> List[float]:
        return np.random.rand(self.size).tolist()

    def get_vector_size(self) -> int:
        return self.size


class JinaClipV2(EmbedderBase):
    """
    - jina-clip-v2 (PyTorch)
    - Matryoshka embeddings allow to cut original emgedding to arbitrary first N dimensions
    """

    def __init__(self, size: int = 64):
        self.size = size
        self.model = AutoModel.from_pretrained(
            "jinaai/jina-clip-v2",
            trust_remote_code=True
        )
        self.model.eval()

    def embed_text(self, text: str) -> List[float]:
        with torch.no_grad():
            embedding = self.model.encode_text(
                text,
                truncate_dim=self.size
            )

        return embedding.tolist()

    def embed_image(self, image: bytes) -> List[float]:
        with torch.no_grad():
            embedding = self.model.encode_image(
                Image.open(io.BytesIO(image)),
                truncate_dim=self.size
            )

        return embedding.tolist()

    def get_vector_size(self) -> int:
        return self.size


def create_embedder(model_name: str) -> EmbedderBase:
    if model_name == "mock":
        return MockEmbedder(size=EMB_SIZE["mock"])
    elif model_name == "jina-clip-v2":
        return JinaClipV2(size=EMB_SIZE["jina-clip-v2"])
    else:
        raise ValueError(f"Unsupported embedder model: {model_name}")
