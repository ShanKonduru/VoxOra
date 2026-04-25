from __future__ import annotations

from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ── Application ───────────────────────────────────────────────────────────
    app_env: str = "development"
    secret_key: str = "change-me-in-production-minimum-32-characters-required"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://voxora:password@localhost:5432/voxora_db"

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── Object Storage ────────────────────────────────────────────────────────
    s3_bucket: str = ""
    s3_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    s3_endpoint_url: str = ""

    # ── OpenAI ───────────────────────────────────────────────────────────────
    openai_api_key: str = ""
    openai_moderation_model: str = "text-moderation-stable"
    openai_realtime_model: str = "gpt-4o-realtime-preview"
    openai_tts_model: str = "tts-1-hd"
    openai_stt_model: str = "whisper-1"
    openai_chat_model: str = "gpt-4o"

    # ── ElevenLabs (optional TTS) ─────────────────────────────────────────────
    elevenlabs_api_key: str = ""
    elevenlabs_enabled: bool = False

    # ── SMTP / Reminder Service ───────────────────────────────────────────────
    smtp_host: str = "smtp.sendgrid.net"
    smtp_port: int = 587
    smtp_user: str = "apikey"
    smtp_password: str = ""
    from_email: str = "noreply@voxora.io"

    # ── Security ──────────────────────────────────────────────────────────────
    max_ws_connections_per_ip: int = 5
    whisper_confidence_threshold: float = 0.70
    input_max_length: int = 2000
    jailbreak_blocklist_path: str = "./security/jailbreak_blocklist.txt"

    # ── CORS ──────────────────────────────────────────────────────────────────
    allowed_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()
