"""
CallMissed API client.

Wraps the OpenAI Python SDK pointed at api.callmissed.com.
All upstream errors are translated into domain exceptions so
the routing layer never leaks raw responses or the API key.
"""

from __future__ import annotations

import base64
import time
import uuid

from openai import OpenAI, APIError, APIConnectionError, RateLimitError, AuthenticationError

from app.config import settings


# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------

class CallMissedError(Exception):
    def __init__(self, detail: str, status: int = 502):
        self.detail = detail
        self.status = status
        super().__init__(detail)


class CallMissedAuthError(CallMissedError):
    def __init__(self):
        super().__init__("Authentication failed. Check your API key.", 401)


class CallMissedPaymentError(CallMissedError):
    def __init__(self):
        super().__init__("Payment required — please top up your account.", 402)


class CallMissedRateLimitError(CallMissedError):
    def __init__(self, retry_after: float | None = None):
        super().__init__("Rate limited. Please retry later.", 429)
        self.retry_after = retry_after


class CallMissedUnsupportedError(CallMissedError):
    def __init__(self, detail: str = "Unsupported input for this model."):
        super().__init__(detail, 422)


class CallMissedUpstreamError(CallMissedError):
    def __init__(self):
        super().__init__("Upstream service error.", 502)


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class CallMissedClient:
    def __init__(self) -> None:
        if not settings.api_key_set:
            raise CallMissedAuthError()
        self._client = OpenAI(
            api_key=settings.CALLMISSED_API_KEY,
            base_url=settings.CALLMISSED_BASE_URL,
        )
        self._chat_model = settings.CHAT_MODEL
        self._image_model = settings.IMAGE_MODEL

    def _translate_error(self, exc: Exception) -> CallMissedError:
        if isinstance(exc, AuthenticationError):
            return CallMissedAuthError()
        if isinstance(exc, RateLimitError):
            return CallMissedRateLimitError(getattr(exc, "retry_after", None))
        if isinstance(exc, APIError):
            status = getattr(exc, "status_code", None)
            if status == 402:
                return CallMissedPaymentError()
            if status and 400 <= status < 500:
                body = getattr(exc, "body", None) or ""
                body_str = body if isinstance(body, str) else str(body)
                if "unsupported_image_input" in body_str.lower():
                    return CallMissedUnsupportedError(
                        "The provided image is not supported by this model."
                    )
                return CallMissedError("Invalid request to upstream.", 400)
            return CallMissedUpstreamError()
        if isinstance(exc, APIConnectionError):
            return CallMissedUpstreamError()
        return CallMissedUpstreamError()

    # -- chat (supports both text and multi-modal messages) ------------------

    def chat_stream(self, messages: list[dict]) -> "ChatStreamIterator":
        try:
            resp = self._client.chat.completions.create(
                model=self._chat_model,
                messages=messages,
                stream=True,
            )
        except Exception as exc:
            raise self._translate_error(exc) from exc
        return ChatStreamIterator(resp, model=self._chat_model)

    def chat_non_stream(self, messages: list[dict]) -> dict:
        try:
            resp = self._client.chat.completions.create(
                model=self._chat_model,
                messages=messages,
                stream=False,
            )
        except Exception as exc:
            raise self._translate_error(exc) from exc
        return {
            "id": resp.id,
            "object": "chat.completion",
            "created": resp.created,
            "model": resp.model,
            "choices": [
                {
                    "index": c.index,
                    "delta": {"role": c.message.role, "content": c.message.content},
                    "finish_reason": c.finish_reason,
                }
                for c in resp.choices
            ],
        }

    # -- image generation ----------------------------------------------------

    def generate_image(self, prompt: str) -> str:
        try:
            resp = self._client.images.generate(
                model=self._image_model,
                prompt=prompt,
                n=1,
                response_format="b64_json",
            )
        except Exception as exc:
            raise self._translate_error(exc) from exc
        data = resp.data[0]
        if hasattr(data, "b64_json") and data.b64_json:
            return data.b64_json
        if hasattr(data, "url") and data.url:
            import httpx
            return base64.b64encode(httpx.get(data.url, timeout=30).content).decode()
        raise CallMissedError("No image data returned from upstream.", 502)

    # -- vision (standalone, for the /v1/vision endpoint) --------------------

    def vision(self, image_b64: str, question: str) -> str:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                    {"type": "text", "text": question},
                ],
            }
        ]
        try:
            resp = self._client.chat.completions.create(
                model=self._chat_model,
                messages=messages,
                stream=False,
            )
        except Exception as exc:
            raise self._translate_error(exc) from exc
        if not resp.choices:
            raise CallMissedError("No response from vision model.", 502)
        return resp.choices[0].message.content or ""


class ChatStreamIterator:
    def __init__(self, stream, model: str):
        self._stream = stream
        self._model = model
        self._id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
        self._created = int(time.time())

    def __iter__(self):
        return self

    def __next__(self) -> dict:
        chunk = next(self._stream)
        choices = []
        for c in chunk.choices:
            delta = {}
            if c.delta.role:
                delta["role"] = c.delta.role
            if c.delta.content is not None:
                delta["content"] = c.delta.content
            choices.append({
                "index": c.index,
                "delta": delta,
                "finish_reason": c.finish_reason,
            })
        return {
            "id": self._id,
            "object": "chat.completion.chunk",
            "created": self._created,
            "model": self._model,
            "choices": choices,
        }


_client: CallMissedClient | None = None


def get_client() -> CallMissedClient:
    global _client
    if _client is None:
        _client = CallMissedClient()
    return _client