"""Tests for per-scope AgentManager dict in config_routes.

Phase 4B: Verifies the singleton trap is eliminated — project-scope and
user-scope managers are independent instances, while same-scope calls
return the cached instance.
"""

from unittest.mock import MagicMock, patch

import claude_mpm.services.monitor.config_routes as routes


class TestAgentManagerScoping:
    """Verify per-scope AgentManager caching in config_routes."""

    def setup_method(self):
        """Clear per-scope dict before each test."""
        routes._agent_managers.clear()

    def teardown_method(self):
        """Clean up per-scope dict after each test."""
        routes._agent_managers.clear()

    @patch(
        "claude_mpm.services.agents.management.agent_management_service.AgentManager"
    )
    def test_project_and_user_managers_are_independent(self, mock_agent_manager_cls):
        """Ensure the singleton trap is gone: different scopes → different instances."""
        # Make the mock class return distinct instances per call
        mock_agent_manager_cls.side_effect = [
            MagicMock(name="proj"),
            MagicMock(name="user"),
        ]

        proj_mgr = routes._get_agent_manager("project")
        user_mgr = routes._get_agent_manager("user")

        assert proj_mgr is not user_mgr
        assert len(routes._agent_managers) == 2

    @patch(
        "claude_mpm.services.agents.management.agent_management_service.AgentManager"
    )
    def test_same_scope_returns_cached_manager(self, mock_agent_manager_cls):
        """Same scope called twice must return the same cached instance."""
        mock_agent_manager_cls.return_value = MagicMock(name="proj")

        a = routes._get_agent_manager("project")
        b = routes._get_agent_manager("project")

        assert a is b
        # AgentManager constructor should only be called once
        assert mock_agent_manager_cls.call_count == 1
