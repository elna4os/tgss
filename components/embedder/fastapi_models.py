from typing import List

from pydantic import BaseModel


class EmbedResponse(BaseModel):
    """Response model for embedding API endpoints
    """

    embedding: List[float]
