README.md
ChatMissed API
A production-quality chatbot backend with a ChatGPT-style frontend, backed by CallMissed.

Models
Endpoint	Model	Purpose
POST /v1/chat/completions	kimi-k2.7-code	Chat (streaming & non-streaming) + Vision
POST /v1/images/generations	flux-2-klein-9b	Image generation from text prompt
POST /v1/vision	kimi-k2.7-code	Image understanding (upload + question)
Getting Started
1. Get a CallMissed API Key
Go to docs.callmissed.com.
Sign up for a free account.
Navigate to API Keys in your dashboard and create a key.
2. Configure
cp .env.example .env# Edit .env and paste your key:# CALLMISSED_API_KEY=sk-xxxx
3. Run
bash

pip install -r requirements.txt
uvicorn app.main:app --reload
Open http://localhost:8000 — you'll see the ChatGPT-style UI.

4. Docker
bash

docker build -t chatmissed .
docker run -p 8000:8000 --env-file .env chatmissed
API Reference
Chat — POST /v1/chat/completions
Streaming (SSE):

bash

curl -N http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Write a Python hello world"}
    ],
    "stream": true
  }'
Response: text/event-stream with data: {...} chunks ending with data: [DONE].

Non-streaming:

bash

curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What is 2+2?"}
    ],
    "stream": false
  }'
Image Generation — POST /v1/images/generations
bash

curl http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A futuristic city at sunset, cyberpunk style"}'
Response:

json

{
  "created": 1720000000,
  "data": [{"b64_json": "iVBORw0KGgo..."}]
}
Save the image:

bash

curl -s http://localhost:8000/v1/images/generations \
  -H "Content-Type: application/json" \
  -d '{"prompt": "A cat"}' \
  | jq -r '.data[0].b64_json' \
  | base64 -d > cat.png
Vision — POST /v1/vision
bash

curl http://localhost:8000/v1/vision \
  -F "file=@photo.jpg" \
  -F "question=What is in this image?"
Response:

json

{"answer": "The image shows a red bicycle parked on a cobblestone street."}
Health Check — GET /health
bash

curl http://localhost:8000/health
# {"status": "ok"}
Interactive Docs
Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc
Error Handling
All errors return a clean JSON shape — no raw upstream errors or API keys are leaked:

json

{
  "error": {
    "message": "Rate limited. Please retry later.",
    "type": "rate_limit_error"
  }
}
Status
Type
Meaning
400	invalid_request_error	Bad input to upstream
401	authentication_error	Invalid or missing API key
402	payment_required	Account needs top-up
413	(FastAPI)	Uploaded file too large (20 MB limit)
422	invalid_request_error	Validation error or unsupported image
429	rate_limit_error	Too many requests (may include Retry-After header)
502	upstream_error	CallMissed service error

Project Structure
text

app/
├── main.py              # FastAPI app, routers, error handlers, static mount
├── config.py            # Settings from env vars
├── routers/
│   ├── chat.py          # POST /v1/chat/completions (SSE + non-stream)
│   ├── images.py        # POST /v1/images/generations
│   └── vision.py        # POST /v1/vision (multipart upload)
├── services/
│   └── callmissed_client.py  # OpenAI SDK wrapper, domain exceptions
├── schemas/
│   ├── chat.py          # Pydantic models for chat
│   ├── images.py        # Pydantic models for image gen
│   └── vision.py        # Pydantic models for vision
├── errors/
│   └── handlers.py      # Exception → JSON response mappers
└── static/
    └── index.html       # ChatGPT-style SPA frontend
tests/
├── conftest.py
├── test_chat.py
├── test_images.py
└── test_vision.py
Running Tests
bash

pip install pytest pytest-asyncio
pytest -v
Frontend
The UI at / has three modes:

Chat — Full conversation interface with streaming responses, conversation sidebar (persisted to localStorage), and an image-attach button that routes through the vision endpoint.
Image Gen — Text prompt → generated image with download button.
Vision — Drag-and-drop (or click) image upload + question → text answer.
Design Decisions
OpenAI SDK over raw httpx — The CallMissed API is OpenAI-compatible, so the SDK gives us type hints, retry logic, and streaming helpers for free.
Domain exceptions — All upstream errors are caught in the client layer and re-raised as typed exceptions. The error handler never sees raw SDK errors, so secrets can't leak.
SSE in-band errors — When streaming, if the upstream fails mid-stream, we send an error event before [DONE] so the frontend can display it inline.
No model selector — The spec fixes two models. Hardcoding them removes a class of user errors.
LocalStorage conversations — Good enough for a demo; a production version would use a database.
Single HTML file frontend — Zero build step, works immediately, easy to customize.




Where AI Was Used
AI assisted with:

Initial project scaffolding and boilerplate
Frontend CSS styling (ChatGPT dark theme approximation)
Test fixture design (FakeStream, FakeChunk helpers)
All logic, error handling, API design, and architectural decisions were made manually.
