from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.database import engine
from app.models import Base  # noqa: F401 — registers all models with SQLAlchemy metadata
from app.security.rate_limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Voxora API",
    description="AI-Enabled Interactive Voice Survey Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)

# ── Middleware ────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.auth import router as auth_router  # noqa: E402
from app.api.surveys import router as surveys_router  # noqa: E402
from app.api.participants import router as participants_router  # noqa: E402
from app.api.sessions import router as sessions_router  # noqa: E402
from app.api.admin import router as admin_router  # noqa: E402
from app.api.websocket import router as ws_router  # noqa: E402

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(surveys_router, prefix="/api/surveys", tags=["surveys"])
app.include_router(participants_router, prefix="/api/participants", tags=["participants"])
app.include_router(sessions_router, prefix="/api/sessions", tags=["sessions"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(ws_router, tags=["websocket"])


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
