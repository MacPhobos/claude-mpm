"""Password hashing and JWT utilities for user authentication.

Environment variables consumed:
    SECRET_KEY                 Signing key for JWTs (required in production).
    ALGORITHM                  JWT algorithm, defaults to "HS256".
    ACCESS_TOKEN_EXPIRE_MINUTES Short-lived token TTL, defaults to 30.
    REFRESH_TOKEN_EXPIRE_DAYS  Long-lived token TTL, defaults to 7.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

# ---------------------------------------------------------------------------
# Configuration (from environment with sane defaults for development)
# ---------------------------------------------------------------------------

SECRET_KEY: str = os.environ.get(
    "SECRET_KEY", "CHANGE_ME_IN_PRODUCTION_this_is_only_for_dev"
)
ALGORITHM: str = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# ---------------------------------------------------------------------------
# Password hashing (using bcrypt directly; passlib is unmaintained)
# ---------------------------------------------------------------------------


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Args:
        plain_password: The raw password supplied by the user.
        hashed_password: The stored bcrypt hash to compare against.

    Returns:
        True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """Hash a plain-text password with bcrypt.

    Args:
        password: The raw password to hash.

    Returns:
        A bcrypt hash string suitable for storage.
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


# ---------------------------------------------------------------------------
# JWT creation
# ---------------------------------------------------------------------------


def _build_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    """Internal helper: encode a JWT with an expiry claim.

    Args:
        data: Claims to embed in the token payload.
        expires_delta: How long until the token expires.

    Returns:
        A signed JWT string.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    payload["exp"] = expire
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a short-lived access JWT.

    Args:
        data: Claims to include (typically ``{"sub": email}``).
        expires_delta: Custom TTL; falls back to
            ``ACCESS_TOKEN_EXPIRE_MINUTES`` if not provided.

    Returns:
        A signed JWT access token string.
    """
    delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return _build_token(data, delta)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a longer-lived refresh JWT.

    Args:
        data: Claims to include (typically ``{"sub": email}``).

    Returns:
        A signed JWT refresh token string.
    """
    delta = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return _build_token(data, delta)


# ---------------------------------------------------------------------------
# JWT decoding
# ---------------------------------------------------------------------------


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, returning its payload.

    Args:
        token: The JWT string to decode.

    Returns:
        The decoded payload dictionary.

    Raises:
        JWTError: If the token is invalid, expired, or tampered with.
    """
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
