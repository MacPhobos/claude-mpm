"""FastAPI dependency functions for user authentication.

Provides injectable dependencies that extract and validate the current
authenticated user from the ``Authorization: Bearer <token>`` header.

Usage in route handlers::

    @router.get("/protected")
    async def protected(user: User = Depends(get_current_active_user)):
        ...
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError

from claude_mpm.auth.user.blacklist import is_blacklisted
from claude_mpm.auth.user.models import User  # noqa: TC001
from claude_mpm.auth.user.security import decode_token
from claude_mpm.auth.user.store import UserStore, get_user_store  # noqa: TC001

# The token URL matches the login endpoint defined in router.py
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    store: UserStore = Depends(get_user_store),
) -> User:
    """Extract and validate the current user from a Bearer JWT.

    Args:
        token: JWT extracted from the ``Authorization`` header by FastAPI.
        store: The UserStore to look up the user in.

    Returns:
        The authenticated User record.

    Raises:
        HTTPException(401): If the token is missing, invalid, expired,
            or the referenced user no longer exists.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if is_blacklisted(token):
        raise credentials_exception
    try:
        payload = decode_token(token)
        email: str | None = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception from None

    user = await store.get_user_by_email(email)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Extend get_current_user by asserting the account is active.

    Args:
        current_user: The validated user from get_current_user.

    Returns:
        The same user if their account is active.

    Raises:
        HTTPException(400): If the account has been deactivated.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )
    return current_user
