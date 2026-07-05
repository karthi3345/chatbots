from __future__ import annotations

from pydantic import BaseModel, Field


class VisionRequest(BaseModel):
    """JSON part of the multipart vision request."""

    question: str = Field(..., min_length=1, max_length=16_000)


class VisionResponse(BaseModel):
    answer: str