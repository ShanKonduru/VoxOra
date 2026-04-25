from __future__ import annotations

import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.models.admin_user import AdminUser
from app.models.participant import Participant
from app.models.question import Question
from app.models.survey import Survey
from app.security.auth import hash_password, create_access_token
import bcrypt as _bcrypt


@pytest.fixture(autouse=True)
def _reset_rate_limiter() -> None:
    """Reset in-memory rate-limit counters before every test to prevent carryover."""
    try:
        app.state.limiter._storage.reset()
    except AttributeError:
        pass

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def event_loop_policy():
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="session")
async def engine():
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture
async def db(engine) -> AsyncGenerator[AsyncSession, None]:
    TestingSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_admin(db: AsyncSession) -> AdminUser:
    # Use bcrypt directly to avoid passlib ↔ bcrypt-5.x incompatibility in tests.
    admin = AdminUser(
        username="testadmin",
        hashed_password=_bcrypt.hashpw(b"testpass123", _bcrypt.gensalt()).decode(),
        is_active=True,
    )
    db.add(admin)
    await db.flush()
    await db.refresh(admin)
    return admin


@pytest.fixture
def admin_token(sample_admin: AdminUser) -> str:
    return create_access_token(subject=sample_admin.username)


@pytest_asyncio.fixture
async def sample_survey(db: AsyncSession, sample_admin: AdminUser) -> Survey:
    survey = Survey(
        title="Test Survey",
        description="A test survey",
        created_by=str(sample_admin.id),
    )
    db.add(survey)
    await db.flush()

    for i in range(1, 4):
        question = Question(
            survey_id=survey.id,
            order_index=i,
            question_text=f"Test question {i}?",
            question_type="open_ended",
        )
        db.add(question)

    await db.flush()
    await db.refresh(survey)
    return survey


@pytest_asyncio.fixture
async def sample_participant(db: AsyncSession, sample_survey: Survey) -> Participant:
    import secrets

    participant = Participant(
        survey_id=sample_survey.id,
        email="test@example.com",
        name="Test User",
        invite_token=secrets.token_urlsafe(32),
    )
    db.add(participant)
    await db.flush()
    await db.refresh(participant)
    return participant
