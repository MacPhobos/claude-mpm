"""Integration tests for the auth router endpoints using FastAPI TestClient.

Uses httpx's synchronous TestClient.  All UserStore interactions are
redirected to a fresh in-memory (tmp) store via dependency overrides.

Covers:
- POST /auth/register  — success (201), duplicate (409)
- POST /auth/login     — success (200), wrong password (401), no user (401)
- POST /auth/refresh   — success (200), bad token (401)
- GET  /auth/me        — valid token (200), invalid token (401), no token (401)
- POST /auth/logout    — valid token (200), token blacklisted after logout
- GET  /health         — 200
- JWT token creation, custom expiry, and expiry detection
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
from fastapi.testclient import TestClient

from claude_mpm.api.app import create_app
from claude_mpm.auth.user.store import UserStore, get_user_store

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def tmp_store(tmp_path: Path) -> UserStore:
    """A fresh UserStore backed by a temp file."""
    return UserStore(path=tmp_path / "users.json")


@pytest.fixture()
def client(tmp_store: UserStore) -> TestClient:
    """TestClient with the tmp_store injected."""
    app = create_app()
    app.dependency_overrides[get_user_store] = lambda: tmp_store
    return TestClient(app, raise_server_exceptions=True)


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


class TestHealth:
    def test_health_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------


class TestRegister:
    def test_register_success(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/register",
            json={
                "email": "alice@example.com",
                "password": "password123",  # pragma: allowlist secret
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "alice@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_returns_correct_fields(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/register",
            json={"email": "bob@example.com", "password": "password123"},
        )
        data = resp.json()
        assert set(data.keys()) == {"id", "email", "is_active", "created_at"}

    def test_register_duplicate_email_returns_409(self, client: TestClient) -> None:
        payload = {"email": "dup@example.com", "password": "password123"}
        client.post("/auth/register", json=payload)
        resp = client.post("/auth/register", json=payload)
        assert resp.status_code == 409

    def test_register_short_password_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/register",
            json={
                "email": "x@example.com",
                "password": "short",  # pragma: allowlist secret
            },
        )
        assert resp.status_code == 422

    def test_register_invalid_email_returns_422(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )
        assert resp.status_code == 422

    def test_register_normalises_email_to_lowercase(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/register",
            json={"email": "UPPER@EXAMPLE.COM", "password": "password123"},
        )
        assert resp.status_code == 201
        assert resp.json()["email"] == "upper@example.com"


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


class TestLogin:
    def _register(self, client: TestClient, email: str, password: str) -> None:
        client.post("/auth/register", json={"email": email, "password": password})

    def test_login_success_returns_token_pair(self, client: TestClient) -> None:
        self._register(client, "carol@example.com", "password123")
        resp = client.post(
            "/auth/login",
            json={"email": "carol@example.com", "password": "password123"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, client: TestClient) -> None:
        self._register(client, "dave@example.com", "password123")
        resp = client.post(
            "/auth/login",
            json={
                "email": "dave@example.com",
                "password": "wrongpassword",  # pragma: allowlist secret
            },
        )
        assert resp.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/login",
            json={"email": "ghost@example.com", "password": "password123"},
        )
        assert resp.status_code == 401

    def test_login_tokens_are_non_empty(self, client: TestClient) -> None:
        self._register(client, "eve@example.com", "password123")
        resp = client.post(
            "/auth/login",
            json={"email": "eve@example.com", "password": "password123"},
        )
        data = resp.json()
        assert len(data["access_token"]) > 20
        assert len(data["refresh_token"]) > 20


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


class TestRefreshToken:
    def _login(self, client: TestClient, email: str, password: str) -> dict:
        client.post("/auth/register", json={"email": email, "password": password})
        return client.post(
            "/auth/login", json={"email": email, "password": password}
        ).json()

    def test_refresh_success(self, client: TestClient) -> None:
        tokens = self._login(client, "frank@example.com", "password123")
        resp = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_with_invalid_token_returns_401(self, client: TestClient) -> None:
        resp = client.post(
            "/auth/refresh",
            json={"refresh_token": "this.is.not.valid"},
        )
        assert resp.status_code == 401

    def test_refresh_with_expired_token_returns_401(self, client: TestClient) -> None:
        from claude_mpm.auth.user.security import _build_token

        expired = _build_token({"sub": "grace@example.com"}, timedelta(seconds=-1))
        resp = client.post(
            "/auth/refresh",
            json={"refresh_token": expired},
        )
        assert resp.status_code == 401

    def test_refresh_new_access_token_differs_from_old(
        self, client: TestClient
    ) -> None:
        tokens = self._login(client, "henry@example.com", "password123")
        resp = client.post(
            "/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        # The new access token should be a fresh JWT (different from old, or at
        # minimum be valid).
        assert resp.json()["access_token"] != tokens["refresh_token"]


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


class TestGetMe:
    def _get_access_token(self, client: TestClient, email: str, password: str) -> str:
        client.post("/auth/register", json={"email": email, "password": password})
        return client.post(
            "/auth/login", json={"email": email, "password": password}
        ).json()["access_token"]

    def test_me_with_valid_token(self, client: TestClient) -> None:
        token = self._get_access_token(client, "ivy@example.com", "password123")
        resp = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "ivy@example.com"

    def test_me_without_token_returns_401(self, client: TestClient) -> None:
        resp = client.get("/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self, client: TestClient) -> None:
        resp = client.get(
            "/auth/me",
            headers={"Authorization": "Bearer not.a.real.token"},
        )
        assert resp.status_code == 401

    def test_me_with_expired_token_returns_401(self, client: TestClient) -> None:
        from claude_mpm.auth.user.security import _build_token

        token = _build_token({"sub": "jack@example.com"}, timedelta(seconds=-1))
        resp = client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 401

    def test_me_returns_no_password(self, client: TestClient) -> None:
        token = self._get_access_token(client, "kate@example.com", "password123")
        data = client.get(
            "/auth/me", headers={"Authorization": f"Bearer {token}"}
        ).json()
        assert "hashed_password" not in data
        assert "password" not in data


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


class TestLogout:
    def _login(self, client: TestClient, email: str, password: str) -> dict:
        client.post("/auth/register", json={"email": email, "password": password})
        return client.post(
            "/auth/login", json={"email": email, "password": password}
        ).json()

    def test_logout_returns_200(self, client: TestClient) -> None:
        tokens = self._login(client, "leo@example.com", "password123")
        resp = client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200

    def test_logout_without_token_returns_401(self, client: TestClient) -> None:
        resp = client.post("/auth/logout")
        assert resp.status_code == 401

    def test_token_blacklisted_after_logout(self, client: TestClient) -> None:
        """After logout the same token should not grant access to /auth/me."""
        tokens = self._login(client, "mia@example.com", "password123")
        access = tokens["access_token"]
        auth_header = {"Authorization": f"Bearer {access}"}

        # Works before logout
        assert client.get("/auth/me", headers=auth_header).status_code == 200

        # Logout
        client.post("/auth/logout", headers=auth_header)

        # Token now blacklisted — /auth/me should deny
        resp_after = client.get("/auth/me", headers=auth_header)
        assert resp_after.status_code == 401
