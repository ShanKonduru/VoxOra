from __future__ import annotations

import uuid
import inspect
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.models.participant import ParticipantStatus
from app.security.auth import create_refresh_token
from app.api import websocket as websocket_module


class _FakeRedis:
    async def setex(self, key: str, ttl: int, value: str) -> bool:  # noqa: ARG002
        return True


class _FakeResult:
    def __init__(self, value):
        self._value = value

    def scalar_one_or_none(self):
        return self._value

    def scalar_one(self):
        return self._value


class _FakeSession:
    def __init__(self, execute_values: list[object | None]):
        self._execute_values = execute_values
        self._idx = 0

    async def execute(self, *args, **kwargs):  # noqa: ANN002, ANN003
        if not self._execute_values:
            return _FakeResult(None)
        value = self._execute_values[min(self._idx, len(self._execute_values) - 1)]
        self._idx += 1
        return _FakeResult(value)

    def add(self, obj: object) -> None:
        # Simulate DB-assigned PK for session rows.
        if hasattr(obj, "id") and getattr(obj, "id", None) is None:
            setattr(obj, "id", uuid.uuid4())

    async def commit(self) -> None:
        return None

    async def refresh(self, obj: object) -> None:  # noqa: ARG002
        return None


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_routes_are_not_double_prefixed(client: AsyncClient) -> None:
    route_paths = {route.path for route in app.routes}

    assert "/api/auth/login" in route_paths
    assert "/api/sessions/init" in route_paths
    assert "/api/auth/api/auth/login" not in route_paths
    assert "/api/sessions/api/sessions/init" not in route_paths


@pytest.mark.asyncio
async def test_login_sets_refresh_cookie_and_returns_access_token(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.api.auth.verify_password", lambda plain, hashed: True)

    fake_admin = SimpleNamespace(
        username="testadmin",
        hashed_password="stubbed",
        is_active=True,
    )

    fake_db = _FakeSession([fake_admin])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    response = await client.post(
        "/api/auth/login",
        json={"username": "testadmin", "password": "testpass123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "voxora_refresh=" in response.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_refresh_requires_cookie(client: AsyncClient) -> None:
    fake_admin = SimpleNamespace(username="testadmin", is_active=True)
    fake_db = _FakeSession([fake_admin])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    response = await client.post("/api/auth/refresh")

    assert response.status_code == 401
    assert response.json()["detail"] == "No refresh token provided"


@pytest.mark.asyncio
async def test_refresh_with_cookie_returns_new_access_token(
    client: AsyncClient,
) -> None:
    fake_admin = SimpleNamespace(username="testadmin", is_active=True)
    fake_db = _FakeSession([fake_admin])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    refresh_token = create_refresh_token(subject="testadmin")
    refresh_response = await client.post(
        "/api/auth/refresh",
        cookies={"voxora_refresh": refresh_token},
    )
    assert refresh_response.status_code == 200

    body = refresh_response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "voxora_refresh=" in refresh_response.headers.get("set-cookie", "")


@pytest.mark.asyncio
async def test_session_init_contract_fields_present(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    participant_id = uuid.uuid4()
    survey_id = uuid.uuid4()
    invite_token = "test-invite-token"

    fake_participant = SimpleNamespace(
        id=participant_id,
        survey_id=survey_id,
        invite_token=invite_token,
        name="Test User",
        status=ParticipantStatus.PENDING,
    )
    fake_questions = [SimpleNamespace(id=uuid.uuid4(), order_index=1, question_text="Q1")]
    fake_survey = SimpleNamespace(id=survey_id, title="Test Survey", is_active=True, questions=fake_questions)

    fake_db = _FakeSession([fake_participant, fake_survey])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    async def _fake_get_redis() -> _FakeRedis:
        return _FakeRedis()

    monkeypatch.setattr("app.api.sessions.get_redis", _fake_get_redis)
    monkeypatch.setattr(
        "app.api.sessions.persona_manager.assign_random",
        lambda: SimpleNamespace(
            to_dict=lambda: {
                "name": "Aria",
                "gender": "female",
                "accent": "British RP",
                "voice_id": "nova",
                "greeting_style": "formal",
            }
        ),
    )

    response = await client.post(
        "/api/sessions/init",
        json={
            "invite_token": invite_token,
            "ip_address": "127.0.0.1",
            "user_agent": "pytest",
        },
    )

    assert response.status_code == 201
    body = response.json()

    assert "session_id" in body
    assert "session_token" in body
    assert "persona" in body
    assert body["participant_name"] == "Test User"
    assert "survey_title" in body
    assert body["total_questions"] >= 1
    assert body["current_question_index"] == 0
    assert body["state"] == "GREETING"


@pytest.mark.asyncio
async def test_rate_limit_enforced_on_login(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app.state.limiter._storage.reset()
    monkeypatch.setattr("app.api.auth.verify_password", lambda plain, hashed: True)

    fake_admin = SimpleNamespace(
        username="ratelimit-admin",
        hashed_password="stubbed",
        is_active=True,
    )
    fake_db = _FakeSession([fake_admin])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    statuses: list[int] = []
    for _ in range(6):
        response = await client.post(
            "/api/auth/login",
            json={"username": "ratelimit-admin", "password": "testpass123"},
        )
        statuses.append(response.status_code)

    assert statuses[:5] == [200, 200, 200, 200, 200]
    assert statuses[5] == 429


@pytest.mark.asyncio
async def test_rate_limit_enforced_on_session_init(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app.state.limiter._storage.reset()

    participant_id = uuid.uuid4()
    survey_id = uuid.uuid4()
    invite_token = "ratelimit-invite-token"

    fake_participant = SimpleNamespace(
        id=participant_id,
        survey_id=survey_id,
        invite_token=invite_token,
        name="Limit User",
        status=ParticipantStatus.PENDING,
    )
    fake_questions = [SimpleNamespace(id=uuid.uuid4(), order_index=1, question_text="Q1")]
    fake_survey = SimpleNamespace(id=survey_id, title="Limit Survey", is_active=True, questions=fake_questions)
    fake_db = _FakeSession([item for _ in range(11) for item in (fake_participant, fake_survey)])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    async def _fake_get_redis() -> _FakeRedis:
        return _FakeRedis()

    monkeypatch.setattr("app.api.sessions.get_redis", _fake_get_redis)
    monkeypatch.setattr(
        "app.api.sessions.persona_manager.assign_random",
        lambda: SimpleNamespace(
            to_dict=lambda: {
                "name": "Aria",
                "gender": "female",
                "accent": "British RP",
                "voice_id": "nova",
                "greeting_style": "formal",
            }
        ),
    )

    statuses: list[int] = []
    for _ in range(11):
        response = await client.post(
            "/api/sessions/init",
            json={
                "invite_token": invite_token,
                "ip_address": "127.0.0.1",
                "user_agent": "pytest",
            },
        )
        statuses.append(response.status_code)

    assert statuses[:10] == [201] * 10
    assert statuses[10] == 429


def test_websocket_response_logging_sets_question_index() -> None:
    source = inspect.getsource(websocket_module.voice_session_ws)
    assert "question_index=sm.current_question_index" in source
