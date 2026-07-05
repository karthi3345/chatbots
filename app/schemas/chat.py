from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field, field_validator


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class ImageURLContent(BaseModel):
    type: Literal["image_url"] = "image_url"
    image_url: dict


class ChatMessage(BaseModel):
    """
    Accepts simple string content OR multi-modal content blocks.
    
    Simple:  {"role": "user", "content": "Hello"}
    Image:   {"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
                {"type": "text", "text": "What is this?"}
             ]}
    """
    role: Literal["user", "assistant", "system"] = "user"
    content: str | list[TextContent | ImageURLContent] = Field(...)

    @field_validator("content", mode="before")
    @classmethod
    def validate_content(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("content must not be empty")
        elif isinstance(v, list):
            if not v:
                raise ValueError("content list must not be empty")
        return v


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1, max_length=100)
    stream: bool = True