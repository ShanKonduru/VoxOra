from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from app.services.moderation import ModerationResult, ModerationService


@pytest.mark.asyncio
async def test_clean_content_not_flagged() -> None:
    service = ModerationService()
    mock_result = MagicMock()
    mock_result.flagged = False
    mock_result.categories.model_dump.return_value = {}

    mock_response = MagicMock()
    mock_response.results = [mock_result]
    mock_response.model_dump.return_value = {}

    with patch.object(service._client.moderations, "create", AsyncMock(return_value=mock_response)):
        result = await service.check("I appreciate working remotely.")
    assert result.is_flagged is False


@pytest.mark.asyncio
async def test_violent_content_flagged() -> None:
    from unittest.mock import MagicMock

    service = ModerationService()
    mock_result = MagicMock()
    mock_result.flagged = True
    mock_result.categories.model_dump.return_value = {"violence": True, "hate": False}

    mock_response = MagicMock()
    mock_response.results = [mock_result]
    mock_response.model_dump.return_value = {}

    with patch.object(service._client.moderations, "create", AsyncMock(return_value=mock_response)):
        result = await service.check("violent content here")
    assert result.is_flagged is True
    assert "violence" in result.flagged_categories


@pytest.mark.asyncio
async def test_api_failure_fails_open() -> None:
    service = ModerationService()

    with patch.object(
        service._client.moderations,
        "create",
        AsyncMock(side_effect=Exception("API unavailable")),
    ):
        result = await service.check("any content")
    # Fail open — should not be flagged when API is down
    assert result.is_flagged is False


# MagicMock import fix
from unittest.mock import MagicMock
