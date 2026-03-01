"""Tests for scope parameter on agent deployment endpoints.

Phase 5: Verifies that all agent deployment mutation endpoints accept an
optional scope parameter, default to "project", reject invalid scopes
with HTTP 400, and include scope in response bodies and event data.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

import claude_mpm.services.config_api.agent_deployment_handler as handler


def _make_app():
    """Create a minimal aiohttp app with agent deployment routes."""
    app = web.Application()
    event_handler = MagicMock()
    event_handler.emit_config_event = AsyncMock()
    file_watcher = MagicMock()
    handler.register_agent_deployment_routes(app, event_handler, file_watcher)
    return app, event_handler


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset lazy singletons before/after each test."""
    handler._backup_manager = None
    handler._operation_journal = None
    handler._deployment_verifier = None
    handler._agent_deployment_service = None
    yield
    handler._backup_manager = None
    handler._operation_journal = None
    handler._deployment_verifier = None
    handler._agent_deployment_service = None


class TestDeployAgentScope:
    """POST /api/config/agents/deploy — scope validation."""

    @pytest.mark.asyncio
    async def test_invalid_scope_returns_400(self):
        """scope=user → 400 VALIDATION_ERROR."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/api/config/agents/deploy",
                json={"agent_name": "test-agent", "scope": "user"},
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
                "/api/config/agents/deploy",
                json={"agent_name": "nonexistent", "scope": None},
            )
            # Should NOT be 400 for scope — scope validated as "project"
            assert resp.status != 400 or "scope" not in (await resp.json()).get(
                "error", ""
            )

    @pytest.mark.asyncio
    async def test_missing_scope_defaults_to_project(self):
        """No scope field → defaults to "project"."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/api/config/agents/deploy",
                json={"agent_name": "nonexistent"},
            )
            # Should NOT be 400 for scope — may be 500 for missing agent in cache
            assert resp.status != 400 or "scope" not in (await resp.json()).get(
                "error", ""
            )

    @pytest.mark.asyncio
    async def test_scope_in_response_on_success(self, tmp_path, monkeypatch):
        """Successful deploy includes scope in response."""
        monkeypatch.chdir(tmp_path)
        app, _event_handler = _make_app()

        mock_backup = MagicMock()
        mock_backup.create_backup.return_value = MagicMock(backup_id="bk-123")
        mock_journal = MagicMock()
        mock_journal.begin_operation.return_value = "op-1"
        mock_verify_result = MagicMock()
        mock_verify_result.passed = True
        mock_verify_result.timestamp = "2026-02-28T00:00:00"
        mock_verify_result.checks = []
        mock_verifier = MagicMock()
        mock_verifier.verify_agent_deployed.return_value = mock_verify_result
        mock_svc = MagicMock()
        mock_svc.deploy_agent.return_value = True

        handler._backup_manager = mock_backup
        handler._operation_journal = mock_journal
        handler._deployment_verifier = mock_verifier
        handler._agent_deployment_service = mock_svc

        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/api/config/agents/deploy",
                json={"agent_name": "test-agent", "scope": "project"},
            )
            assert resp.status == 201
            body = await resp.json()
            assert body["scope"] == "project"


class TestUndeployAgentScope:
    """DELETE /api/config/agents/{agent_name} — scope validation."""

    @pytest.mark.asyncio
    async def test_invalid_scope_returns_400(self):
        """scope=user query param → 400 VALIDATION_ERROR."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.delete(
                "/api/config/agents/test-agent?scope=user",
            )
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"
            assert "user" in body["error"]

    @pytest.mark.asyncio
    async def test_missing_scope_defaults_to_project(self):
        """No scope query param → defaults to "project"."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.delete("/api/config/agents/nonexistent")
            # Should not be 400 for scope; will be 404 for missing agent
            assert resp.status in (403, 404)


class TestDeployCollectionScope:
    """POST /api/config/agents/deploy-collection — scope validation."""

    @pytest.mark.asyncio
    async def test_invalid_scope_returns_400(self):
        """scope=user → 400 VALIDATION_ERROR."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/api/config/agents/deploy-collection",
                json={"agent_names": ["a"], "scope": "user"},
            )
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    async def test_null_scope_defaults_to_project(self):
        """scope=null → defaults to "project"."""
        app, _ = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.post(
                "/api/config/agents/deploy-collection",
                json={"agent_names": ["a"], "scope": None},
            )
            # Should NOT be 400 for scope
            assert resp.status != 400 or "scope" not in (await resp.json()).get(
                "error", ""
            )
