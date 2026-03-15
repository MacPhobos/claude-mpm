"""FastAPI router exposing user authentication endpoints.

Endpoints
---------
POST /auth/register  — Create a new account, returns UserResponse (201).
POST /auth/login     — Authenticate and return a Token pair (200).
POST /auth/refresh   — Exchange a refresh token for a new access token (200).
GET  /auth/me        — Return the current user's profile (200, protected).
POST /auth/logout    — Blacklist the current access token (200, protected).

Token blacklisting is in-memory and does not survive restarts; it is
intentionally lightweight for this file-backed implementation.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError

from claude_mpm.auth.user.blacklist import blacklist_token, is_blacklisted
from claude_mpm.auth.user.dependencies import (
    get_current_active_user,
    get_current_user,
    oauth2_scheme,
)
from claude_mpm.auth.user.models import (  # noqa: TC001
    Token,
    User,
    UserCreate,
    UserResponse,
)
from claude_mpm.auth.user.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from claude_mpm.auth.user.store import UserStore, get_user_store  # noqa: TC001

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: UserCreate,
    store: Annotated[UserStore, Depends(get_user_store)],
) -> UserResponse:
    """Create a new user account.

    Args:
        payload: Registration data (email + password).
        store: Injected user store.

    Returns:
        The created user's public profile.

    Raises:
        HTTPException(409): If the email address is already registered.
    """
    try:
        user = await store.create_user(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    logger.info("Registered new user: %s", user.email)
    return UserResponse.from_user(user)


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and obtain a token pair",
)
async def login(
    payload: UserCreate,
    store: Annotated[UserStore, Depends(get_user_store)],
) -> Token:
    """Authenticate with email + password and receive access/refresh tokens.

    We accept a ``UserCreate`` body (email + password) rather than
    ``OAuth2PasswordRequestForm`` so the API uses JSON consistently.
    The ``OAuth2PasswordBearer`` scheme still works because the token
    endpoint is declared via ``tokenUrl`` in dependencies.py.

    Args:
        payload: Login credentials.
        store: Injected user store.

    Returns:
        A Token pair (access_token + refresh_token).

    Raises:
        HTTPException(401): If credentials are incorrect.
    """
    user = await store.authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access = create_access_token({"sub": user.email})
    refresh = create_refresh_token({"sub": user.email})
    return Token(access_token=access, refresh_token=refresh)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Obtain a new access token using a refresh token",
)
async def refresh_token(
    payload: dict[str, str],
    store: Annotated[UserStore, Depends(get_user_store)],
) -> Token:
    """Exchange a valid refresh token for a new access/refresh token pair.

    Expects a JSON body ``{"refresh_token": "<token>"}``.

    Args:
        payload: Dictionary containing the ``refresh_token`` key.
        store: Injected user store.

    Returns:
        A fresh Token pair.

    Raises:
        HTTPException(401): If the refresh token is invalid, expired, or
            blacklisted.
    """
    raw_token = payload.get("refresh_token", "")
    if is_blacklisted(raw_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = decode_token(raw_token)
        email: str | None = claims.get("sub")
        if not email:
            raise ValueError("Missing sub claim")
    except (JWTError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await store.get_user_by_email(email)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access = create_access_token({"sub": email})
    new_refresh = create_refresh_token({"sub": email})
    return Token(access_token=access, refresh_token=new_refresh)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Return the currently authenticated user's profile",
)
async def get_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> UserResponse:
    """Return the profile of the currently authenticated user.

    Args:
        current_user: Extracted and validated by the dependency chain.

    Returns:
        The authenticated user's public profile.
    """
    return UserResponse.from_user(current_user)


@router.post(
    "/logout",
    summary="Invalidate the current access token",
)
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    token: Annotated[str, Depends(oauth2_scheme)],
) -> dict[str, str]:
    """Blacklist the current access token so it can no longer be used.

    Args:
        current_user: Validated to confirm the token was active.
        token: The raw token string from the Authorization header.

    Returns:
        A JSON confirmation message.
    """
    blacklist_token(token)
    logger.info("User %s logged out", current_user.email)
    return {"detail": "Successfully logged out"}
