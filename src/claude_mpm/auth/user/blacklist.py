"""In-memory token blacklist for logout support.

A module-level set so that both the router (which adds tokens) and
the dependency injection layer (which checks tokens) share the same
state without circular imports.

Note: This is in-memory only and does not survive restarts.  A
production system should use a shared store such as Redis.
"""

from __future__ import annotations

_blacklisted_tokens: set[str] = set()


def blacklist_token(token: str) -> None:
    """Add a token to the blacklist.

    Args:
        token: The raw JWT string to invalidate.
    """
    _blacklisted_tokens.add(token)


def is_blacklisted(token: str) -> bool:
    """Check whether a token has been blacklisted.

    Args:
        token: The raw JWT string to check.

    Returns:
        True if the token was revoked via logout, False otherwise.
    """
    return token in _blacklisted_tokens
