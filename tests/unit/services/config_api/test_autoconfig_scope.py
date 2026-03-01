"""Tests for scope guard on auto-configure endpoints.

Phase 5 (Task 5.7): Verifies that all 3 autoconfig POST endpoints reject
scope=user with HTTP 400 SCOPE_NOT_SUPPORTED while accepting project scope.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

import claude_mpm.services.config_api.autoconfig_handler as handler


def _make_app():
    """Create a minimal aiohttp app with autoconfig routes."""
    app = web.Application()
    event_handler = MagicMock()
    event_handler.emit_config_event = AsyncMock()
    file_watcher = MagicMock()
    handler.register_autoconfig_routes(app, event_handler, file_watcher)
    return app, event_handler


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset lazy singletons before/after each test."""
    handler._toolchain_analyzer = None
    handler._auto_config_manager = None
    handler._backup_manager = None
    handler._skills_deployer = None
    yield
    handler._toolchain_analyzer = None
    handler._auto_config_manager = None
    handler._backup_manager = None
    handler._skills_deployer = None


class TestAutoconfigScopeGuard:
    """All 3 autoconfig endpoints reject scope=user."""

    @pytest.mark.asyncio
    async def test_detect_rejects_user_scope(self):
        """POST /api/config/auto-configure/detect with scope=user → 400."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/api/config/auto-configure/detect",
                json={"scope": "user"},
            )
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "SCOPE_NOT_SUPPORTED"
            assert "user" in body["error"]

    @pytest.mark.asyncio
    async def test_preview_rejects_user_scope(self):
        """POST /api/config/auto-configure/preview with scope=user → 400."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/api/config/auto-configure/preview",
                json={"scope": "user"},
            )
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "SCOPE_NOT_SUPPORTED"

    @pytest.mark.asyncio
    async def test_apply_rejects_user_scope(self):
        """POST /api/config/auto-configure/apply with scope=user → 400."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/api/config/auto-configure/apply",
                json={"scope": "user"},
            )
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "SCOPE_NOT_SUPPORTED"

    @pytest.mark.asyncio
    async def test_detect_accepts_project_scope(self, tmp_path, monkeypatch):
        """POST /api/config/auto-configure/detect with scope=project passes validation."""
        monkeypatch.chdir(tmp_path)
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/api/config/auto-configure/detect",
                json={"scope": "project", "project_path": str(tmp_path)},
            )
            # Should NOT be 400 for scope — may be 500 from toolchain analyzer
            assert resp.status != 400

    @pytest.mark.asyncio
    async def test_detect_null_scope_defaults_to_project(self, tmp_path, monkeypatch):
        """POST /api/config/auto-configure/detect with scope=null → project."""
        monkeypatch.chdir(tmp_path)
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/api/config/auto-configure/detect",
                json={"scope": None, "project_path": str(tmp_path)},
            )
            # Should NOT be 400 for scope
            assert resp.status != 400
