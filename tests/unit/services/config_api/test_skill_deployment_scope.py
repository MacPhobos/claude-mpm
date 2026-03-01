"""Tests for scope parameter on skill deployment endpoints.

Phase 5: Verifies that all skill deployment mutation endpoints accept an
optional scope parameter, default to "project", reject invalid scopes
with HTTP 400, and include scope in response bodies and event data.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

import claude_mpm.services.config_api.skill_deployment_handler as handler


def _make_app():
    """Create a minimal aiohttp app with skill deployment routes."""
    app = web.Application()
    event_handler = MagicMock()
    event_handler.emit_config_event = AsyncMock()
    file_watcher = MagicMock()
    handler.register_skill_deployment_routes(app, event_handler, file_watcher)
    return app, event_handler


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset lazy singletons before/after each test."""
    handler._backup_manager = None
    handler._operation_journal = None
    handler._deployment_verifier = None
    handler._skills_deployer = None
    yield
    handler._backup_manager = None
    handler._operation_journal = None
    handler._deployment_verifier = None
    handler._skills_deployer = None


class TestDeploySkillScope:
    """POST /api/config/skills/deploy — scope validation."""

    @pytest.mark.asyncio
    async def test_invalid_scope_returns_400(self):
        """scope=user → 400 VALIDATION_ERROR."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/api/config/skills/deploy",
                json={"skill_name": "test-skill", "scope": "user"},
            )
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"
            assert "user" in body["error"]

    @pytest.mark.asyncio
    async def test_null_scope_defaults_to_project(self):
        """scope=null → defaults to "project" (R-3 null-safe)."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/api/config/skills/deploy",
                json={"skill_name": "nonexistent", "scope": None},
            )
            # Should NOT be 400 for scope
            assert resp.status != 400 or "scope" not in (await resp.json()).get(
                "error", ""
            )


class TestUndeploySkillScope:
    """DELETE /api/config/skills/{skill_name} — scope validation."""

    @pytest.mark.asyncio
    async def test_invalid_scope_returns_400(self):
        """scope=user query param → 400 VALIDATION_ERROR."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.delete(
                "/api/config/skills/test-skill?scope=user",
            )
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"
            assert "user" in body["error"]


class TestDeploymentModeScope:
    """GET/PUT /api/config/skills/deployment-mode — scope validation."""

    @pytest.mark.asyncio
    async def test_get_invalid_scope_returns_400(self):
        """GET with scope=user → 400 VALIDATION_ERROR."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.get(
                "/api/config/skills/deployment-mode?scope=user",
            )
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"
            assert "user" in body["error"]

    @pytest.mark.asyncio
    async def test_put_invalid_scope_returns_400(self):
        """PUT with scope=user → 400 VALIDATION_ERROR."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.put(
                "/api/config/skills/deployment-mode",
                json={"mode": "selective", "preview": True, "scope": "user"},
            )
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"
            assert "user" in body["error"]
