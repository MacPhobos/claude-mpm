"""
Characterization tests for API scope behavior.

WHY: Lock down current API scope assumptions BEFORE any refactoring. These
document that deploy handlers always use PROJECT scope and Path.cwd().

Phase: 0 (characterization)
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from claude_mpm.core.config_scope import ConfigScope

# ==============================================================================
# Phase 0-C: API Scope (Current Behavior)
# ==============================================================================


@pytest.mark.regression
class TestAPICurrentScopeAssumptions:
    """Characterization tests for API deployment handler scope assumptions."""

    # TC-0-09
    def test_deploy_agent_handler_hardcodes_project_scope(self):
        """agent_deployment_handler.deploy_agent() always calls
        resolve_agents_dir(ConfigScope.PROJECT, Path.cwd()).

        The handler does NOT accept a scope parameter from the request body.
        """
        with patch(
            "claude_mpm.services.config_api.agent_deployment_handler.resolve_agents_dir"
        ) as mock_resolve:
            mock_resolve.return_value = Path("/fake/agents")

            # Import after patching so the module picks up the mock
            # Verify the module-level call pattern by inspecting the source directly
            import inspect

            from claude_mpm.services.config_api import agent_deployment_handler
            from claude_mpm.services.config_api.agent_deployment_handler import (
                resolve_agents_dir as _,
            )

            source = inspect.getsource(agent_deployment_handler)

            # The deploy_agent handler uses ConfigScope.PROJECT hardcoded
            assert "resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())" in source, (
                "deploy_agent handler should hardcode ConfigScope.PROJECT"
            )

    # TC-0-10
    def test_deploy_skill_handler_hardcodes_project_scope(self):
        """skill_deployment_handler uses Path.cwd()/.claude-mpm/configuration.yaml
        (hardcoded project path) for config operations.

        The _get_config_path() function always returns Path.cwd()-based path.
        """
        from claude_mpm.services.config_api.skill_deployment_handler import (
            _get_config_path,
        )

        fake_cwd = Path("/fake/project")
        with patch(
            "claude_mpm.services.config_api.skill_deployment_handler.Path.cwd",
            return_value=fake_cwd,
        ):
            config_path = _get_config_path()

        assert config_path == fake_cwd / ".claude-mpm" / "configuration.yaml"

    # TC-0-11
    def test_config_routes_deployed_list_reads_from_cwd(self):
        """_get_agent_manager() in config_routes.py creates AgentManager
        with Path.cwd()/.claude/agents as project_dir by default.
        """
        import claude_mpm.services.monitor.config_routes as config_routes_module

        # Reset the singleton so we can test fresh initialization
        original_manager = config_routes_module._agent_manager
        config_routes_module._agent_manager = None

        fake_cwd = Path("/fake/project")
        try:
            with patch(
                "claude_mpm.services.monitor.config_routes.Path.cwd",
                return_value=fake_cwd,
            ):
                with patch(
                    "claude_mpm.services.agents.management.agent_management_service.AgentManager"
                ) as MockAgentManager:
                    mock_instance = MagicMock()
                    MockAgentManager.return_value = mock_instance

                    result = config_routes_module._get_agent_manager()

                    # Should be called with cwd-based agents dir
                    MockAgentManager.assert_called_once_with(
                        project_dir=fake_cwd / ".claude" / "agents"
                    )
                    assert result is mock_instance
        finally:
            # Restore original singleton state
            config_routes_module._agent_manager = original_manager

    # TC-0-12
    def test_agent_manager_singleton_initializes_once_with_project_path(self):
        """_get_agent_manager() is a singleton — second call returns same object."""
        import claude_mpm.services.monitor.config_routes as config_routes_module

        # Reset the singleton
        original_manager = config_routes_module._agent_manager
        config_routes_module._agent_manager = None

        fake_cwd = Path("/fake/project")
        try:
            with patch(
                "claude_mpm.services.monitor.config_routes.Path.cwd",
                return_value=fake_cwd,
            ):
                with patch(
                    "claude_mpm.services.agents.management.agent_management_service.AgentManager"
                ) as MockAgentManager:
                    mock_instance = MagicMock()
                    MockAgentManager.return_value = mock_instance

                    first = config_routes_module._get_agent_manager()
                    second = config_routes_module._get_agent_manager()

                    # Same object returned both times (singleton pattern)
                    assert first is second
                    # Constructor called only once
                    MockAgentManager.assert_called_once()
        finally:
            config_routes_module._agent_manager = original_manager
