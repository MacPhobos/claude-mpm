"""
Shared aiohttp test client fixtures for API integration tests.

WHY: API tests need a consistent way to create test applications
with mocked dependencies. These fixtures provide reusable test
infrastructure for scope-aware API endpoint testing.

Phase: 0 (foundation for later phases)
"""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer


@pytest.fixture
def mock_config_event_handler():
    """Mock ConfigEventHandler for Socket.IO event emission."""
    handler = MagicMock()
    handler.emit_config_event = AsyncMock()
    return handler


@pytest.fixture
def mock_config_file_watcher():
    """Mock ConfigFileWatcher for mtime tracking."""
    watcher = MagicMock()
    watcher.update_mtime = MagicMock()
    return watcher


@pytest.fixture
def mock_server_instance(tmp_path):
    """Mock UnifiedMonitorServer instance with working_directory."""
    server = MagicMock()
    server.working_directory = tmp_path
    return server


@pytest.fixture
async def agent_deploy_app(mock_config_event_handler, mock_config_file_watcher):
    """Create an aiohttp app with agent deployment routes registered.

    Usage in later phase tests:
        async def test_deploy(agent_deploy_app):
            async with TestClient(TestServer(agent_deploy_app)) as client:
                resp = await client.post("/api/config/agents/deploy", json={...})
    """
    from claude_mpm.services.config_api.agent_deployment_handler import (
        register_agent_deployment_routes,
    )

    app = web.Application()
    register_agent_deployment_routes(
        app, mock_config_event_handler, mock_config_file_watcher
    )
    return app


@pytest.fixture
async def skill_deploy_app(mock_config_event_handler, mock_config_file_watcher):
    """Create an aiohttp app with skill deployment routes registered.

    Usage in later phase tests:
        async def test_deploy(skill_deploy_app):
            async with TestClient(TestServer(skill_deploy_app)) as client:
                resp = await client.post("/api/config/skills/deploy", json={...})
    """
    from claude_mpm.services.config_api.skill_deployment_handler import (
        register_skill_deployment_routes,
    )

    app = web.Application()
    register_skill_deployment_routes(
        app, mock_config_event_handler, mock_config_file_watcher
    )
    return app
