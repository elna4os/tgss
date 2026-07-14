import io
from abc import ABC, abstractmethod
from typing import List

import numpy as np
import onnxruntime as ort
import torch
from huggingface_hub import hf_hub_download
from PIL import Image
from transformers import AutoImageProcessor, AutoModel, AutoTokenizer

EMB_SIZE = {"mock": 32, "jina-clip-v2": 1024, "jina-clip-v2-onnx-int8": 1024}


def to_numpy(x):
    if isinstance(x, torch.Tensor):
        return x.numpy()
    return np.asarray(x)


class EmbedderBase(ABC):
    """Abstract base class for embedding models"""

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
    """Mock embedder that generates random vectors. Used for testing and development."""

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

    def __init__(self, size: int = 1024):
        self.size = size
        self.model_repo = "jinaai/jina-clip-v2"
        self.model = AutoModel.from_pretrained(self.model_repo, trust_remote_code=True)
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


class JinaClipV2_ONNX_INT8(EmbedderBase):
    """
    - jina-clip-v2 (ONNX + int8)
    - Matryoshka embeddings allow to cut original emgedding to arbitrary first N dimensions
    """

    def __init__(self, size: int = 1024):
        self.size = size
        self.model_repo = "jinaai/jina-clip-v2"
        local_path = hf_hub_download(
            repo_id=self.model_repo,
            subfolder="onnx",
            filename="model_int8.onnx",
        )
        # Text/image preprocessors
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_repo,
            trust_remote_code=True
        )
        self.image_processor = AutoImageProcessor.from_pretrained(
            self.model_repo,
            trust_remote_code=True
        )
        # Create ONNX runtime session
        options = ort.SessionOptions()
        # Suppress verbose logging from ONNX Runtime
        options.log_severity_level = 3
        self.session = ort.InferenceSession(local_path, sess_options=options)

    def embed_text(self, text: str) -> List[float]:
        input_ids = to_numpy(self.tokenizer(text, return_tensors='np', padding=True, truncation=True)['input_ids'])
        embedding = self.session.run(
            None,
            {'input_ids': input_ids, 'pixel_values': np.zeros((0, 3, 512, 512), dtype=np.float32)}
        )[2][0, :self.size]
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.tolist()

    def embed_image(self, image: bytes) -> List[float]:
        pixel_values = to_numpy(self.image_processor(Image.open(io.BytesIO(image)), return_tensors='np')['pixel_values'])
        embedding = self.session.run(
            None,
            {'input_ids': np.zeros((1, 1), dtype=np.int64), 'pixel_values': pixel_values}
        )[3][0, :self.size]
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.tolist()
    
    def get_vector_size(self) -> int:
        return self.size


def create_embedder(model_name: str) -> EmbedderBase:
    if model_name == "mock":
        return MockEmbedder(size=EMB_SIZE["mock"])
    elif model_name == "jina-clip-v2":
        return JinaClipV2(size=EMB_SIZE["jina-clip-v2"])
    elif model_name == "jina-clip-v2-onnx-int8":
        return JinaClipV2_ONNX_INT8(size=EMB_SIZE["jina-clip-v2-onnx-int8"])
    else:
        raise ValueError(f"Unsupported embedder model: {model_name}")
