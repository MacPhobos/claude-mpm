"""Thread-safe, file-backed in-memory user store.

Users are persisted as JSON to ``~/.claude-mpm/users.json``.  All public
methods are async to integrate cleanly with FastAPI dependency injection,
though the underlying I/O is synchronous (the file is tiny).

Usage:
    store = UserStore()
    user = await store.create_user(UserCreate(email="a@b.com", password="s3cret!"))  # pragma: allowlist secret
    authenticated = await store.authenticate_user("a@b.com", "s3cret!")
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from claude_mpm.auth.user.models import User
from claude_mpm.auth.user.security import get_password_hash, verify_password

if TYPE_CHECKING:
    from claude_mpm.auth.user.models import UserCreate

logger = logging.getLogger(__name__)

_DEFAULT_STORE_PATH = Path.home() / ".claude-mpm" / "users.json"


class UserStore:
    """Async, thread-safe user store backed by a JSON file.

    The store keeps a dict of ``{email: User}`` in memory and flushes
    to disk after every write.  A single ``asyncio.Lock`` prevents
    concurrent writes from corrupting the file.

    Attributes:
        _path: Filesystem path of the backing JSON file.
        _users: In-memory mapping of lowercase email to User.
        _lock: Async mutex for write operations.
    """

    def __init__(self, path: Path | None = None) -> None:
        """Initialise the store, loading any existing users from disk.

        Args:
            path: Override the default ``~/.claude-mpm/users.json`` path.
                  Useful in tests.
        """
        self._path: Path = path or _DEFAULT_STORE_PATH
        self._users: dict[str, User] = {}
        self._lock: asyncio.Lock = asyncio.Lock()
        self._load()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load users from the JSON file into memory (sync, called once)."""
        if not self._path.exists():
            return
        try:
            raw: list[dict] = json.loads(self._path.read_text(encoding="utf-8"))
            for record in raw:
                user = User(**record)
                self._users[user.email.lower()] = user
        except Exception:
            logger.exception("Failed to load user store from %s", self._path)

    def _save(self) -> None:
        """Flush in-memory users to the JSON file (sync, called under lock)."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = [json.loads(u.model_dump_json()) for u in self._users.values()]
        self._path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def create_user(self, user_create: UserCreate) -> User:
        """Create a new user, hashing their password before storage.

        Args:
            user_create: Validated registration payload.

        Returns:
            The newly created User record.

        Raises:
            ValueError: If a user with the same email already exists.
        """
        email = user_create.email.lower()
        async with self._lock:
            if email in self._users:
                raise ValueError(f"User with email '{email}' already exists.")
            user = User(
                email=email,
                hashed_password=get_password_hash(user_create.password),
            )
            self._users[email] = user
            self._save()
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Look up a user by email address (case-insensitive).

        Args:
            email: The email address to search for.

        Returns:
            The User if found, or None.
        """
        return self._users.get(email.lower())

    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Verify credentials and return the User on success.

        Args:
            email: The email address to look up.
            password: Plain-text password to verify against the stored hash.

        Returns:
            The authenticated User, or None if credentials are invalid.
        """
        user = await self.get_user_by_email(email)
        if user is None:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    async def get_all_users(self) -> list[User]:
        """Return all users (for internal/admin use).

        Returns:
            A list of all User records in insertion order.
        """
        return list(self._users.values())

    async def delete_user(self, email: str) -> bool:
        """Remove a user by email.

        Args:
            email: Email address of the user to remove.

        Returns:
            True if the user was removed, False if they were not found.
        """
        email = email.lower()
        async with self._lock:
            if email not in self._users:
                return False
            del self._users[email]
            self._save()
        return True


# ---------------------------------------------------------------------------
# Module-level singleton (used by FastAPI dependency injection)
# ---------------------------------------------------------------------------

_default_store: UserStore | None = None


def get_user_store() -> UserStore:
    """Return the module-level UserStore singleton.

    Creates it on first call using the default file path.  Inject a
    different instance in tests by calling FastAPI's ``app.dependency_overrides``.

    Returns:
        The shared UserStore instance.
    """
    global _default_store
    if _default_store is None:
        _default_store = UserStore()
    return _default_store
