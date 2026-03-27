from typing import List

from pydantic import BaseModel


class EmbedResponse(BaseModel):
    embedding: List[float]
