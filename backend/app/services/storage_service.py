from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

try:
    import aioboto3
except ModuleNotFoundError:  # pragma: no cover - exercised in environments without S3 deps
    aioboto3 = None

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self) -> None:
        self._session = aioboto3.Session() if aioboto3 is not None else None

    def _object_key(self, session_id: str, question_index: int) -> str:
        return f"audio/{session_id}/q{question_index}.webm"

    def _object_url(self, key: str) -> str:
        if settings.s3_endpoint_url:
            base = settings.s3_endpoint_url.rstrip("/")
            return f"{base}/{settings.s3_bucket}/{quote(key)}"
        return f"https://{settings.s3_bucket}.s3.{settings.s3_region}.amazonaws.com/{quote(key)}"

    def _client_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "region_name": settings.s3_region,
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
        }
        if settings.s3_endpoint_url:
            kwargs["endpoint_url"] = settings.s3_endpoint_url
        return kwargs

    async def upload_audio(
        self,
        session_id: str,
        question_index: int,
        audio_bytes: bytes,
    ) -> str | None:
        if not settings.s3_bucket or self._session is None:
            return None

        key = self._object_key(session_id, question_index)
        content_type = "audio/webm"

        try:
            async with self._session.client("s3", **self._client_kwargs()) as client:
                await client.put_object(
                    Bucket=settings.s3_bucket,
                    Key=key,
                    Body=audio_bytes,
                    ContentType=content_type,
                )
        except Exception as exc:
            logger.warning("Audio upload failed for %s q%s: %s", session_id, question_index, exc)
            return None

        return self._object_url(key)


storage_service = StorageService()