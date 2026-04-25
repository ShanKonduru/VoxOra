from __future__ import annotations

import uuid
import inspect
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.models.participant import ParticipantStatus
from app.security.auth import create_refresh_token, get_current_admin, hash_token
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

    def first(self):
        return self._value


class _FakeSession:
    def __init__(self, execute_values: list[object | None]):
        self._execute_values = execute_values
        self._idx = 0
        self.added: list[object] = []
        self.commits = 0

    async def execute(self, *args, **kwargs):  # noqa: ANN002, ANN003
        if not self._execute_values:
            return _FakeResult(None)
        value = self._execute_values[min(self._idx, len(self._execute_values) - 1)]
        self._idx += 1
        return _FakeResult(value)

    def add(self, obj: object) -> None:
        self.added.append(obj)
        # Simulate DB-assigned PK for session rows.
        if hasattr(obj, "id") and getattr(obj, "id", None) is None:
            setattr(obj, "id", uuid.uuid4())

    async def commit(self) -> None:
        self.commits += 1
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
        id=uuid.uuid4(),
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
    assert len(fake_db.added) == 1
    assert getattr(fake_db.added[0], "token_hash", None)
    assert fake_db.commits == 1


@pytest.mark.asyncio
async def test_login_rejects_invalid_credentials(client: AsyncClient) -> None:
    app.state.limiter._storage.reset()

    fake_db = _FakeSession([None])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    response = await client.post(
        "/api/auth/login",
        json={"username": "missing", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


@pytest.mark.asyncio
async def test_login_rejects_inactive_admin(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app.state.limiter._storage.reset()
    monkeypatch.setattr("app.api.auth.verify_password", lambda plain, hashed: True)

    fake_admin = SimpleNamespace(
        id=uuid.uuid4(),
        username="inactive-admin",
        hashed_password="stubbed",
        is_active=False,
    )
    fake_db = _FakeSession([fake_admin])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    response = await client.post(
        "/api/auth/login",
        json={"username": "inactive-admin", "password": "testpass123"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Account is disabled"


@pytest.mark.asyncio
async def test_refresh_requires_cookie(client: AsyncClient) -> None:
    fake_admin = SimpleNamespace(id=uuid.uuid4(), username="testadmin", is_active=True)
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
    fake_admin = SimpleNamespace(id=uuid.uuid4(), username="testadmin", is_active=True)
    refresh_token = create_refresh_token(subject="testadmin")
    fake_stored_token = SimpleNamespace(
        token_hash=hash_token(refresh_token),
        revoked_at=None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    fake_db = _FakeSession([(fake_stored_token, fake_admin)])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    refresh_response = await client.post(
        "/api/auth/refresh",
        cookies={"voxora_refresh": refresh_token},
    )
    assert refresh_response.status_code == 200

    body = refresh_response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert "voxora_refresh=" in refresh_response.headers.get("set-cookie", "")
    assert fake_stored_token.revoked_at is not None
    assert len(fake_db.added) == 1
    assert fake_db.commits == 1


@pytest.mark.asyncio
async def test_refresh_rejects_untracked_cookie_token(client: AsyncClient) -> None:
    fake_db = _FakeSession([None])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    refresh_token = create_refresh_token(subject="testadmin")
    response = await client.post(
        "/api/auth/refresh",
        cookies={"voxora_refresh": refresh_token},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Refresh token is invalid or revoked"


@pytest.mark.asyncio
async def test_logout_without_cookie_returns_204(client: AsyncClient) -> None:
    fake_db = _FakeSession([])

    async def _override_get_db():
        yield fake_db

    async def _override_current_admin():
        return SimpleNamespace(username="testadmin", is_active=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_admin] = _override_current_admin

    response = await client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer fake-access"},
    )

    assert response.status_code == 204
    assert fake_db.commits == 0


@pytest.mark.asyncio
async def test_logout_with_cookie_revokes_stored_refresh_token(client: AsyncClient) -> None:
    fake_stored_token = SimpleNamespace(revoked_at=None)
    fake_db = _FakeSession([fake_stored_token])

    async def _override_get_db():
        yield fake_db

    async def _override_current_admin():
        return SimpleNamespace(username="testadmin", is_active=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_admin] = _override_current_admin

    refresh_token = create_refresh_token(subject="testadmin")
    response = await client.post(
        "/api/auth/logout",
        headers={"Authorization": "Bearer fake-access"},
        cookies={"voxora_refresh": refresh_token},
    )

    assert response.status_code == 204
    assert fake_stored_token.revoked_at is not None
    assert fake_db.commits == 1


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
async def test_session_init_rejects_completed_participant(client: AsyncClient) -> None:
    app.state.limiter._storage.reset()
    fake_participant = SimpleNamespace(status=ParticipantStatus.COMPLETED)
    fake_db = _FakeSession([fake_participant])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    response = await client.post(
        "/api/sessions/init",
        json={"invite_token": "completed-token"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Survey already completed"


@pytest.mark.asyncio
async def test_session_init_rejects_invalid_invite_token(client: AsyncClient) -> None:
    app.state.limiter._storage.reset()
    fake_db = _FakeSession([None])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    response = await client.post(
        "/api/sessions/init",
        json={"invite_token": "missing-token"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Invalid invite token"


@pytest.mark.asyncio
async def test_session_init_rejects_expired_participant(client: AsyncClient) -> None:
    app.state.limiter._storage.reset()
    fake_participant = SimpleNamespace(status=ParticipantStatus.EXPIRED)
    fake_db = _FakeSession([fake_participant])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    response = await client.post(
        "/api/sessions/init",
        json={"invite_token": "expired-token"},
    )

    assert response.status_code == 410
    assert response.json()["detail"] == "Invite token has expired"


@pytest.mark.asyncio
async def test_session_init_rejects_missing_or_inactive_survey(client: AsyncClient) -> None:
    app.state.limiter._storage.reset()
    fake_participant = SimpleNamespace(
        id=uuid.uuid4(),
        survey_id=uuid.uuid4(),
        invite_token="missing-survey",
        name="User",
        status=ParticipantStatus.PENDING,
    )
    fake_db = _FakeSession([fake_participant, None])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    response = await client.post(
        "/api/sessions/init",
        json={"invite_token": "missing-survey"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Survey not found or inactive"


@pytest.mark.asyncio
async def test_session_init_rejects_survey_with_no_questions(client: AsyncClient) -> None:
    app.state.limiter._storage.reset()
    fake_participant = SimpleNamespace(
        id=uuid.uuid4(),
        survey_id=uuid.uuid4(),
        invite_token="empty-survey",
        name="User",
        status=ParticipantStatus.PENDING,
    )
    fake_survey = SimpleNamespace(id=fake_participant.survey_id, title="Empty", is_active=True, questions=[])
    fake_db = _FakeSession([fake_participant, fake_survey])

    async def _override_get_db():
        yield fake_db

    app.dependency_overrides[get_db] = _override_get_db

    response = await client.post(
        "/api/sessions/init",
        json={"invite_token": "empty-survey"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Survey has no questions"


@pytest.mark.asyncio
async def test_session_init_returns_503_when_redis_unavailable(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app.state.limiter._storage.reset()

    fake_participant = SimpleNamespace(
        id=uuid.uuid4(),
        survey_id=uuid.uuid4(),
        invite_token="redis-down",
        name="Redis User",
        status=ParticipantStatus.PENDING,
    )
    fake_questions = [SimpleNamespace(id=uuid.uuid4(), order_index=1, question_text="Q1")]
    fake_survey = SimpleNamespace(id=fake_participant.survey_id, title="Survey", is_active=True, questions=fake_questions)
    fake_db = _FakeSession([fake_participant, fake_survey])

    async def _override_get_db():
        yield fake_db

    async def _failing_get_redis():
        raise RuntimeError("redis unavailable")

    app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr("app.api.sessions.get_redis", _failing_get_redis)
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
            "invite_token": "redis-down",
            "ip_address": "127.0.0.1",
            "user_agent": "pytest",
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Session store unavailable; please retry."


@pytest.mark.asyncio
async def test_get_session_state_not_found(client: AsyncClient) -> None:
    fake_db = _FakeSession([None])

    async def _override_get_db():
        yield fake_db

    async def _override_current_admin():
        return SimpleNamespace(username="testadmin", is_active=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_admin] = _override_current_admin

    response = await client.get(f"/api/sessions/{uuid.uuid4()}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found"


@pytest.mark.asyncio
async def test_get_session_state_participant_not_found(client: AsyncClient) -> None:
    fake_session = SimpleNamespace(
        id=uuid.uuid4(),
        participant_id=uuid.uuid4(),
        state="GREETING",
        current_question_index=0,
        persona={"name": "Aria"},
        is_flagged=False,
        started_at=datetime.now(timezone.utc),
    )
    fake_db = _FakeSession([fake_session, None])

    async def _override_get_db():
        yield fake_db

    async def _override_current_admin():
        return SimpleNamespace(username="testadmin", is_active=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_admin] = _override_current_admin

    response = await client.get(f"/api/sessions/{fake_session.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


@pytest.mark.asyncio
async def test_get_session_state_survey_not_found(client: AsyncClient) -> None:
    fake_session = SimpleNamespace(
        id=uuid.uuid4(),
        participant_id=uuid.uuid4(),
        state="GREETING",
        current_question_index=0,
        persona={"name": "Aria"},
        is_flagged=False,
        started_at=datetime.now(timezone.utc),
    )
    fake_participant = SimpleNamespace(id=fake_session.participant_id, survey_id=uuid.uuid4())
    fake_db = _FakeSession([fake_session, fake_participant, None])

    async def _override_get_db():
        yield fake_db

    async def _override_current_admin():
        return SimpleNamespace(username="testadmin", is_active=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_admin] = _override_current_admin

    response = await client.get(f"/api/sessions/{fake_session.id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Survey not found"


@pytest.mark.asyncio
async def test_get_session_state_success(client: AsyncClient) -> None:
    session_id = uuid.uuid4()
    participant_id = uuid.uuid4()
    survey_id = uuid.uuid4()

    fake_session = SimpleNamespace(
        id=session_id,
        participant_id=participant_id,
        state="LOGGING",
        current_question_index=1,
        persona={
            "name": "Aria",
            "gender": "female",
            "accent": "British RP",
            "voice_id": "nova",
            "greeting_style": "formal",
        },
        is_flagged=True,
        started_at=datetime.now(timezone.utc),
    )
    fake_participant = SimpleNamespace(id=participant_id, survey_id=survey_id)
    fake_survey = SimpleNamespace(id=survey_id, questions=[object(), object(), object()])
    fake_db = _FakeSession([fake_session, fake_participant, fake_survey])

    async def _override_get_db():
        yield fake_db

    async def _override_current_admin():
        return SimpleNamespace(username="testadmin", is_active=True)

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_admin] = _override_current_admin

    response = await client.get(f"/api/sessions/{session_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == str(session_id)
    assert body["state"] == "LOGGING"
    assert body["current_question_index"] == 1
    assert body["total_questions"] == 3
    assert body["is_flagged"] is True


@pytest.mark.asyncio
async def test_rate_limit_enforced_on_login(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app.state.limiter._storage.reset()
    monkeypatch.setattr("app.api.auth.verify_password", lambda plain, hashed: True)

    fake_admin = SimpleNamespace(
        id=uuid.uuid4(),
        username="ratelimit-admin",
        hashed_password="stubbed",
        is_active=True,
    )
    # Supply enough entries so every login's execute() returns fake_admin.
    # 5 successful requests × 1 execute each; _FakeSession also clamps to last item
    # once the list is exhausted, so a single-item list also works — but being
    # explicit here makes the intent clearer.
    fake_db = _FakeSession([fake_admin] * 5)

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
