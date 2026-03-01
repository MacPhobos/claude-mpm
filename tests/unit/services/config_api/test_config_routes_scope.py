"""Tests for scope parameter on read-only config_routes endpoints.

Phase 6: Verifies that GET endpoints accept optional ?scope= query param,
default to "project", reject invalid scopes with HTTP 400, and include
scope in response bodies.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

import claude_mpm.services.monitor.config_routes as routes


def _make_app():
    """Create a minimal aiohttp app with config routes registered."""
    app = web.Application()
    routes.register_config_routes(app)
    return app


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset per-scope dict and singletons before/after each test."""
    routes._agent_managers.clear()
    routes._git_source_manager = None
    routes._skills_deployer_service = None
    routes._skill_to_agent_mapper = None
    routes._config_validation_service = None
    yield
    routes._agent_managers.clear()
    routes._git_source_manager = None
    routes._skills_deployer_service = None
    routes._skill_to_agent_mapper = None
    routes._config_validation_service = None


class TestDeployedAgentsScope:
    """GET /api/config/agents/deployed — scope validation."""

    @pytest.mark.asyncio
    async def test_without_scope_reads_project(self, tmp_path, monkeypatch):
        """No ?scope= defaults to project, returns scope in response."""
        monkeypatch.chdir(tmp_path)
        app = _make_app()

        mock_mgr = MagicMock()
        mock_mgr.list_agents.return_value = {}
        routes._agent_managers["project"] = mock_mgr

        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/config/agents/deployed")
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            assert body["scope"] == "project"

    @pytest.mark.asyncio
    async def test_valid_project_scope(self, tmp_path, monkeypatch):
        """?scope=project returns same as no scope."""
        monkeypatch.chdir(tmp_path)
        app = _make_app()

        mock_mgr = MagicMock()
        mock_mgr.list_agents.return_value = {}
        routes._agent_managers["project"] = mock_mgr

        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/config/agents/deployed?scope=project")
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            assert body["scope"] == "project"

    @pytest.mark.asyncio
    async def test_invalid_scope_returns_400(self):
        """?scope=user → 400 VALIDATION_ERROR."""
        app = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/config/agents/deployed?scope=user")
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"
            assert "user" in body["error"]

    @pytest.mark.asyncio
    async def test_invalid_scope_workspace_returns_400(self):
        """?scope=workspace → 400 VALIDATION_ERROR."""
        app = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/config/agents/deployed?scope=workspace")
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"


class TestDeployedSkillsScope:
    """GET /api/config/skills/deployed — scope validation."""

    @pytest.mark.asyncio
    async def test_without_scope_reads_project(self, tmp_path, monkeypatch):
        """No ?scope= defaults to project, returns scope in response."""
        monkeypatch.chdir(tmp_path)
        app = _make_app()

        mock_svc = MagicMock()
        mock_svc.check_deployed_skills.return_value = {
            "skills": [],
            "deployed_count": 0,
        }
        routes._skills_deployer_service = mock_svc

        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/config/skills/deployed")
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            assert body["scope"] == "project"

    @pytest.mark.asyncio
    async def test_valid_project_scope(self, tmp_path, monkeypatch):
        """?scope=project returns same as no scope."""
        monkeypatch.chdir(tmp_path)
        app = _make_app()

        mock_svc = MagicMock()
        mock_svc.check_deployed_skills.return_value = {
            "skills": [],
            "deployed_count": 0,
        }
        routes._skills_deployer_service = mock_svc

        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/config/skills/deployed?scope=project")
            assert resp.status == 200
            body = await resp.json()
            assert body["success"] is True
            assert body["scope"] == "project"

    @pytest.mark.asyncio
    async def test_invalid_scope_returns_400(self):
        """?scope=user → 400 VALIDATION_ERROR."""
        app = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/config/skills/deployed?scope=user")
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"
            assert "user" in body["error"]


class TestValidateScope:
    """GET /api/config/validate — scope validation."""

    @pytest.mark.asyncio
    async def test_invalid_scope_returns_400(self):
        """?scope=user → 400 VALIDATION_ERROR."""
        app = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/config/validate?scope=user")
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"


class TestProjectSummaryScope:
    """GET /api/config/project/summary — scope validation."""

    @pytest.mark.asyncio
    async def test_invalid_scope_returns_400(self):
        """?scope=user → 400 VALIDATION_ERROR."""
        app = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/config/project/summary?scope=user")
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"


class TestAgentDetailScope:
    """GET /api/config/agents/{name}/detail — scope validation."""

    @pytest.mark.asyncio
    async def test_invalid_scope_returns_400(self):
        """?scope=user → 400 VALIDATION_ERROR."""
        app = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/config/agents/test-agent/detail?scope=user")
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"


class TestSkillLinksScope:
    """GET /api/config/skill-links/ — scope validation."""

    @pytest.mark.asyncio
    async def test_invalid_scope_returns_400(self):
        """?scope=user → 400 VALIDATION_ERROR."""
        app = _make_app()
        async with TestClient(TestServer(app)) as client:
            resp = await client.get("/api/config/skill-links/?scope=user")
            assert resp.status == 400
            body = await resp.json()
            assert body["success"] is False
            assert body["code"] == "VALIDATION_ERROR"
