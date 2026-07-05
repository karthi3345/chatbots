from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env from project root (parent of app/)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")


class Settings:
    """Centralised configuration loaded from environment variables."""

    CALLMISSED_API_KEY: str = os.getenv("CALLMISSED_API_KEY", "")
    CALLMISSED_BASE_URL: str = os.getenv(
        "CALLMISSED_BASE_URL", "https://api.callmissed.com/v1"
    )
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Models — fixed per the spec
    CHAT_MODEL: str = "kimi-k2.7-code"
    IMAGE_MODEL: str = "flux-2-klein-9b"

    # Limits
    MAX_UPLOAD_BYTES: int = 20 * 1024 * 1024  # 20 MB

    @property
    def api_key_set(self) -> bool:
        return bool(self.CALLMISSED_API_KEY)


settings = Settings()