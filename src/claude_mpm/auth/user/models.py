"""Pydantic v2 data models for user authentication.

Defines all request/response models used by the user auth module,
keeping passwords out of response payloads and providing typed JWT
payload representation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, EmailStr, Field  # noqa: TC002


class User(BaseModel):
    """Full internal user record including the hashed password.

    This model is used for storage and internal logic only.
    Never expose this over the API — use UserResponse instead.

    Attributes:
        id: Unique user identifier (UUID string).
        email: Normalised lowercase email address.
        hashed_password: bcrypt hash of the user's password.
        is_active: Whether the account is allowed to authenticate.
        created_at: UTC timestamp when the account was created.
    """

    model_config = ConfigDict(frozen=False)

    id: str = Field(default_factory=lambda: str(uuid4()))
    email: str
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserCreate(BaseModel):
    """Payload for registering a new user.

    Attributes:
        email: Valid email address for the new account.
        password: Plain-text password (min 8 characters).
    """

    model_config = ConfigDict(frozen=True)

    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Payload for authenticating an existing user.

    Attributes:
        email: Registered email address.
        password: Plain-text password to verify.
    """

    model_config = ConfigDict(frozen=True)

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Safe public representation of a user — no password fields.

    Attributes:
        id: Unique user identifier.
        email: User's email address.
        is_active: Whether the account is active.
        created_at: Account creation timestamp.
    """

    model_config = ConfigDict(frozen=True)

    id: str
    email: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_user(cls, user: User) -> UserResponse:
        """Construct a safe response from an internal User record."""
        return cls(
            id=user.id,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
        )


class Token(BaseModel):
    """JWT token pair returned after a successful login or refresh.

    Attributes:
        access_token: Short-lived JWT for authenticating API requests.
        refresh_token: Longer-lived JWT for obtaining new access tokens.
        token_type: Always "bearer".
    """

    model_config = ConfigDict(frozen=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded payload extracted from a JWT.

    Attributes:
        email: Subject claim — the authenticated user's email.
        exp: Expiry timestamp as a Unix epoch integer.
    """

    model_config = ConfigDict(frozen=True)

    email: str
    exp: int
