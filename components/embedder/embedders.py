from abc import ABC, abstractmethod
from typing import List

import numpy as np


EMB_SIZE = {
    "mock": 32
}


class EmbedderBase(ABC):
    """Abstract base class for embedding models
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Convert a single text string into an embedding vector"""
        pass

    @abstractmethod
    def embed_image(self, image: bytes) -> List[float]:
        """Convert an image file into an embedding vector"""
        pass

    @abstractmethod
    def get_vector_size(self) -> int:
        """Returns the size of the embedding vectors produced by this embedder"""
        pass


class MockEmbedder(EmbedderBase):
    """A mock embedder for development purposes
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


def create_embedder(model_name: str) -> EmbedderBase:
    """Factory function to create an embedder instance based on the model name
    """

    if model_name == "mock":
        return MockEmbedder(size=EMB_SIZE["mock"])
    else:
        raise ValueError(f"Unsupported embedder model: {model_name}")
