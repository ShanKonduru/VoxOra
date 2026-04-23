from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.admin_user import AdminUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

_ALGORITHM = settings.algorithm
_SECRET_KEY = settings.secret_key
_ISSUER = "voxora"


# ── Password helpers ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── Token creation ────────────────────────────────────────────────────────────

def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": "access",
        "iss": _ISSUER,
    }
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": "refresh",
        "iss": _ISSUER,
    }
    return jwt.encode(payload, _SECRET_KEY, algorithm=_ALGORITHM)


def hash_token(token: str) -> str:
    """Store only a SHA-256 hash of refresh tokens — never the raw token."""
    return hashlib.sha256(token.encode()).hexdigest()


# ── Token validation ──────────────────────────────────────────────────────────

def decode_token(token: str, expected_type: str = "access") -> dict[str, Any]:
    """
    Decode and validate a JWT.
    Raises HTTP 401 on any validation failure.
    Explicitly rejects the 'none' algorithm to prevent algorithm-confusion attacks.
    """
    try:
        header = jwt.get_unverified_header(token)
        if header.get("alg", "").lower() == "none":
            raise JWTError("Algorithm 'none' is not permitted")

        payload: dict[str, Any] = jwt.decode(
            token, _SECRET_KEY, algorithms=[_ALGORITHM]
        )
        if payload.get("type") != expected_type:
            raise JWTError(f"Expected token type '{expected_type}'")
        if payload.get("iss") != _ISSUER:
            raise JWTError("Invalid token issuer")
        return payload
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ── FastAPI dependency ────────────────────────────────────────────────────────

async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> AdminUser:
    payload = decode_token(credentials.credentials, expected_type="access")
    username: str | None = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    result = await db.execute(
        select(AdminUser).where(
            AdminUser.username == username,
            AdminUser.is_active == True,  # noqa: E712
        )
    )
    admin = result.scalar_one_or_none()
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin user not found or is inactive",
        )
    return admin
