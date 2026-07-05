"""POST /v1/vision — image understanding via kimi-k2.7-code."""

from __future__ import annotations

import base64

from fastapi import APIRouter, File, Form, UploadFile, HTTPException

from app.schemas.vision import VisionResponse
from app.services.callmissed_client import get_client, CallMissedError
from app.config import settings

router = APIRouter(prefix="/v1/vision", tags=["vision"])


@router.post("", response_model=VisionResponse)
async def vision(
    file: UploadFile = File(..., description="Image file (png, jpg, webp, gif)"),
    question: str = Form(..., min_length=1, max_length=16_000),
):
    # --- Validate file type ---
    allowed = {"image/png", "image/jpeg", "image/webp", "image/gif"}
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: png, jpeg, webp, gif.",
        )

    # --- Read & size-check ---
    raw = await file.read()
    if len(raw) > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({len(raw)} bytes). Max {settings.MAX_UPLOAD_BYTES} bytes.",
        )

    # --- Base64-encode ---
    b64 = base64.b64encode(raw).decode("ascii")

    # --- Call upstream ---
    client = get_client()
    answer = client.vision(b64, question.strip())
    return VisionResponse(answer=answer)