"""
Characterization tests for API scope behavior.

WHY: Lock down current API scope assumptions BEFORE any refactoring. These
document that deploy handlers always use PROJECT scope and Path.cwd().

Phase: 0 (characterization)

NOTE: TC-0-09, TC-0-11, TC-0-12 were deleted after the scope-aware deployment
refactoring replaced the behavior they characterized. New tests in
test_agent_deployment_scope.py, test_config_routes_scope.py, and
test_agent_manager_scoping.py provide equivalent coverage.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

# ==============================================================================
# Phase 0-C: API Scope (Current Behavior)
# ==============================================================================


@pytest.mark.regression
class TestAPICurrentScopeAssumptions:
    """Characterization tests for API deployment handler scope assumptions."""

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
