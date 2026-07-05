"""POST /v1/chat/completions — streaming (SSE) and non-streaming chat."""

from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest
from app.services.callmissed_client import get_client, CallMissedError

router = APIRouter(prefix="/v1/chat", tags=["chat"])


def _sse_line(obj: dict | str) -> str:
    """Encode one SSE data line."""
    payload = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False)
    return f"data: {payload}\n\n"


@router.post("/completions")
async def chat_completions(body: ChatRequest):
    client = get_client()
    messages = [m.model_dump() for m in body.messages]

    if body.stream:
        # ── IMPORTANT: this MUST be a sync generator (def, not async def) ──
        # Starlette wraps sync generators in iterate_in_threadpool so the
        # sync OpenAI SDK iterator does NOT block the main event loop.
        def stream_response():
            try:
                for chunk in client.chat_stream(messages):
                    yield _sse_line(chunk)
                yield _sse_line("[DONE]")
            except CallMissedError as exc:
                yield _sse_line({"error": {"message": exc.detail, "type": "api_error"}})
                yield _sse_line("[DONE]")

        return StreamingResponse(
            stream_response(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",       # nginx
                "X-Content-Type-Options": "nosniff",
            },
        )
    else:
        return client.chat_non_stream(messages)