from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin_user import AdminUser
from app.models.refresh_token import RefreshToken
from app.schemas.auth import LoginRequest, TokenResponse
from app.security.auth import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_token,
    verify_password,
    get_current_admin,
)
from app.security.rate_limiter import limiter
from app.config import settings


def _refresh_token_expiry() -> int:
    return settings.refresh_token_expire_days * 86400


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _jwt_exp_to_datetime(value: int) -> datetime:
    return datetime.fromtimestamp(value, tz=timezone.utc)


async def _store_refresh_token(
    db: AsyncSession,
    admin: AdminUser,
    refresh_token: str,
) -> None:
    payload = decode_token(refresh_token, expected_type="refresh")
    token_record = RefreshToken(
        admin_user_id=admin.id,
        token_hash=hash_token(refresh_token),
        expires_at=_jwt_exp_to_datetime(payload["exp"]),
    )
    db.add(token_record)

router = APIRouter(prefix="/api/auth", tags=["auth"])

_REFRESH_COOKIE = "voxora_refresh"


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    result = await db.execute(
        select(AdminUser).where(AdminUser.username == body.username)
    )
    admin: AdminUser | None = result.scalar_one_or_none()
    if not admin or not verify_password(body.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled",
        )
    access_token = create_access_token(subject=admin.username)
    refresh_token = create_refresh_token(subject=admin.username)
    await _store_refresh_token(db, admin, refresh_token)
    await db.commit()
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=settings.app_env != "development",
        samesite="strict",
        max_age=_refresh_token_expiry(),
    )
    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh_access_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
) -> TokenResponse:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided",
        )
    payload = decode_token(refresh_token, expected_type="refresh")
    token_hash = hash_token(refresh_token)
    result = await db.execute(
        select(RefreshToken, AdminUser).join(AdminUser).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > _utcnow(),
            AdminUser.is_active == True,  # noqa: E712
        )
    )
    row = result.first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or revoked",
        )
    stored_token, admin = row
    stored_token.revoked_at = _utcnow()
    new_access = create_access_token(subject=admin.username)
    new_refresh = create_refresh_token(subject=admin.username)
    await _store_refresh_token(db, admin, new_refresh)
    await db.commit()
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=new_refresh,
        httponly=True,
        secure=settings.app_env != "development",
        samesite="strict",
        max_age=_refresh_token_expiry(),
    )
    return TokenResponse(access_token=new_access, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
    _: AdminUser = Depends(get_current_admin),
) -> None:
    if refresh_token:
        payload = decode_token(refresh_token, expected_type="refresh")
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(refresh_token),
                RefreshToken.revoked_at.is_(None),
            )
        )
        stored_token = result.scalar_one_or_none()
        if stored_token:
            stored_token.revoked_at = _utcnow()
            await db.commit()
    response.delete_cookie(key=_REFRESH_COOKIE)
