from abc import ABC, abstractmethod
from typing import List


class EmbedderBase(ABC):
    """Abstract base class for embedding models
    """

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Convert a single text string into an embedding vector"""
        pass

    @abstractmethod
    def embed_image(self, image_path: str) -> List[float]:
        """Convert an image file into an embedding vector"""
        pass


class MockEmbedder(EmbedderBase):
    """A mock embedder for deveopment purposes
    """

    def __init__(self, size: int = 32):
        super().__init__()
        self.size = size

    def embed_text(self, text: str) -> List[float]:
        return [0] * self.size

    def embed_image(self, image_path: str) -> List[float]:
        return [0] * self.size


def create_embedder(model_name: str) -> EmbedderBase:
    """Factory function to create an embedder instance based on the model name
    """

    if model_name == "mock":
        return MockEmbedder()
    else:
        raise ValueError(f"Unsupported embedder model: {model_name}")
