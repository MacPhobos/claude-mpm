"""Unit tests for the UserStore (in-memory + file-backed).

Tests use a temporary directory so they never touch ~/.claude-mpm.

Covers:
- create_user success and duplicate rejection
- get_user_by_email: found and not-found
- authenticate_user: success, wrong password, nonexistent user
- delete_user: success and not-found
- Persistence: data survives creating a second UserStore from same path
"""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
import pytest_asyncio

from claude_mpm.auth.user.models import UserCreate
from claude_mpm.auth.user.store import UserStore

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_store(tmp_path: Path) -> UserStore:
    """A fresh UserStore backed by a temp file (isolated per test)."""
    return UserStore(path=tmp_path / "users.json")


# ---------------------------------------------------------------------------
# create_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestCreateUser:
    async def test_creates_user_successfully(self, tmp_store: UserStore) -> None:
        user = await tmp_store.create_user(
            UserCreate(
                email="alice@example.com",
                password="password1",  # pragma: allowlist secret
            )
        )
        assert user.email == "alice@example.com"
        assert user.id  # non-empty UUID string

    async def test_password_is_hashed(self, tmp_store: UserStore) -> None:
        user = await tmp_store.create_user(
            UserCreate(
                email="bob@example.com",
                password="secret123",  # pragma: allowlist secret
            )
        )
        assert user.hashed_password != "secret123"

    async def test_email_normalised_to_lowercase(self, tmp_store: UserStore) -> None:
        user = await tmp_store.create_user(
            UserCreate(email="UPPER@EXAMPLE.COM", password="password1")
        )
        assert user.email == "upper@example.com"

    async def test_duplicate_email_raises(self, tmp_store: UserStore) -> None:
        await tmp_store.create_user(
            UserCreate(email="dup@example.com", password="password1")
        )
        with pytest.raises(ValueError, match="already exists"):
            await tmp_store.create_user(
                UserCreate(email="dup@example.com", password="password1")
            )

    async def test_is_active_by_default(self, tmp_store: UserStore) -> None:
        user = await tmp_store.create_user(
            UserCreate(email="carol@example.com", password="password1")
        )
        assert user.is_active is True

    async def test_created_at_is_set(self, tmp_store: UserStore) -> None:
        user = await tmp_store.create_user(
            UserCreate(email="dave@example.com", password="password1")
        )
        assert user.created_at is not None


# ---------------------------------------------------------------------------
# get_user_by_email
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGetUserByEmail:
    async def test_finds_existing_user(self, tmp_store: UserStore) -> None:
        await tmp_store.create_user(
            UserCreate(email="eve@example.com", password="password1")
        )
        user = await tmp_store.get_user_by_email("eve@example.com")
        assert user is not None
        assert user.email == "eve@example.com"

    async def test_case_insensitive_lookup(self, tmp_store: UserStore) -> None:
        await tmp_store.create_user(
            UserCreate(email="Frank@Example.COM", password="password1")
        )
        user = await tmp_store.get_user_by_email("frank@example.com")
        assert user is not None

    async def test_returns_none_for_missing_user(self, tmp_store: UserStore) -> None:
        result = await tmp_store.get_user_by_email("nobody@example.com")
        assert result is None


# ---------------------------------------------------------------------------
# authenticate_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestAuthenticateUser:
    async def test_valid_credentials(self, tmp_store: UserStore) -> None:
        await tmp_store.create_user(
            UserCreate(
                email="grace@example.com",
                password="correct_password",  # pragma: allowlist secret
            )
        )
        user = await tmp_store.authenticate_user(
            "grace@example.com", "correct_password"
        )
        assert user is not None
        assert user.email == "grace@example.com"

    async def test_wrong_password_returns_none(self, tmp_store: UserStore) -> None:
        await tmp_store.create_user(
            UserCreate(email="henry@example.com", password="correct_password")
        )
        result = await tmp_store.authenticate_user(
            "henry@example.com", "wrong_password"
        )
        assert result is None

    async def test_nonexistent_user_returns_none(self, tmp_store: UserStore) -> None:
        result = await tmp_store.authenticate_user("ghost@example.com", "anypassword")
        assert result is None

    async def test_empty_password_wrong(self, tmp_store: UserStore) -> None:
        await tmp_store.create_user(
            UserCreate(
                email="ivy@example.com",
                password="realpassword",  # pragma: allowlist secret
            )
        )
        result = await tmp_store.authenticate_user("ivy@example.com", "")
        assert result is None


# ---------------------------------------------------------------------------
# delete_user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestDeleteUser:
    async def test_deletes_existing_user(self, tmp_store: UserStore) -> None:
        await tmp_store.create_user(
            UserCreate(email="jack@example.com", password="password1")
        )
        deleted = await tmp_store.delete_user("jack@example.com")
        assert deleted is True
        assert await tmp_store.get_user_by_email("jack@example.com") is None

    async def test_returns_false_for_missing_user(self, tmp_store: UserStore) -> None:
        result = await tmp_store.delete_user("nobody@example.com")
        assert result is False


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestPersistence:
    async def test_survives_reload(self, tmp_path: Path) -> None:
        """Users written by one store instance should load in a new instance."""
        store_path = tmp_path / "users.json"
        store1 = UserStore(path=store_path)
        await store1.create_user(
            UserCreate(email="persistent@example.com", password="password1")
        )

        store2 = UserStore(path=store_path)
        user = await store2.get_user_by_email("persistent@example.com")
        assert user is not None
        assert user.email == "persistent@example.com"

    async def test_json_file_created(self, tmp_path: Path) -> None:
        store_path = tmp_path / "subdir" / "users.json"
        store = UserStore(path=store_path)
        await store.create_user(UserCreate(email="x@example.com", password="password1"))
        assert store_path.exists()
        data = json.loads(store_path.read_text())
        assert len(data) == 1
        assert data[0]["email"] == "x@example.com"
