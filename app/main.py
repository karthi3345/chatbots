"""Application entry-point."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chat, images, vision
from app.errors.handlers import callmissed_error_handler, generic_error_handler
from app.services.callmissed_client import CallMissedError

app = FastAPI(
    title="ChatMissed API",
    version="1.0.0",
    description="Chatbot + image generation + vision API backed by CallMissed.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(images.router)
app.include_router(vision.router)

app.add_exception_handler(CallMissedError, callmissed_error_handler)  # type: ignore[arg-type]
app.add_exception_handler(Exception, generic_error_handler)  # type: ignore[arg-type]


@app.get("/health", tags=["system"])
async def health():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("app/static/index.html")