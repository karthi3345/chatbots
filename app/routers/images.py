"""POST /v1/images/generations — image generation via flux-2-klein-9b."""

from __future__ import annotations

import time

from fastapi import APIRouter

from app.schemas.images import ImageRequest, ImageResponse, ImageData
from app.services.callmissed_client import get_client

router = APIRouter(prefix="/v1/images", tags=["images"])


@router.post("/generations", response_model=ImageResponse)
async def generate_image(body: ImageRequest):
    client = get_client()
    b64 = client.generate_image(body.prompt)
    return ImageResponse(
        created=int(time.time()),
        data=[ImageData(b64_json=b64)],
    )