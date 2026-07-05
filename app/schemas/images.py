from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ImageRequest(BaseModel):
    """Body for POST /v1/images/generations."""

    prompt: str = Field(..., min_length=1, max_length=4_000)

    @field_validator("prompt")
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        return v.strip()


class ImageData(BaseModel):
    b64_json: str


class ImageResponse(BaseModel):
    created: int
    data: list[ImageData]