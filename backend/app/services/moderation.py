from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# Categories that trigger immediate session termination
FLAGGABLE_CATEGORIES = {
    "hate",
    "hate/threatening",
    "harassment",
    "harassment/threatening",
    "self-harm",
    "self-harm/intent",
    "self-harm/instructions",
    "sexual",
    "sexual/minors",
    "violence",
    "violence/graphic",
}


@dataclass
class ModerationResult:
    is_flagged: bool
    categories: dict = field(default_factory=dict)
    flagged_categories: list[str] = field(default_factory=list)
    raw_response: dict | None = None


class ModerationService:
    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def check(self, text: str) -> ModerationResult:
        """
        Check text against OpenAI Moderation API.
        Retries up to 3 times on transient failures.
        Fails open (returns not-flagged) if API is unavailable.
        """
        for attempt in range(3):
            try:
                response = await self._client.moderations.create(
                    input=text,
                    model=settings.openai_moderation_model,
                )
                result = response.results[0]
                categories = {k: v for k, v in result.categories.model_dump().items()}
                flagged_cats = [
                    k
                    for k, v in categories.items()
                    if v and k in FLAGGABLE_CATEGORIES
                ]
                return ModerationResult(
                    is_flagged=result.flagged,
                    categories=categories,
                    flagged_categories=flagged_cats,
                    raw_response=response.model_dump(),
                )
            except Exception as exc:
                if attempt == 2:
                    logger.warning(
                        "ModerationService failed after 3 attempts — failing open. Error: %s",
                        exc,
                    )
                    return ModerationResult(is_flagged=False)
                await asyncio.sleep(1.0 * (attempt + 1))

        return ModerationResult(is_flagged=False)


moderation_service = ModerationService()
