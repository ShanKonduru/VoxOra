from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin_user import AdminUser
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
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=settings.app_env != "development",
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 86400,
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
    username: str = payload["sub"]
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
            detail="User not found",
        )
    new_access = create_access_token(subject=admin.username)
    new_refresh = create_refresh_token(subject=admin.username)
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=new_refresh,
        httponly=True,
        secure=settings.app_env != "development",
        samesite="strict",
        max_age=settings.refresh_token_expire_days * 86400,
    )
    return TokenResponse(access_token=new_access, token_type="bearer")


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def logout(
    request: Request,
    response: Response,
    _: AdminUser = Depends(get_current_admin),
) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE)
