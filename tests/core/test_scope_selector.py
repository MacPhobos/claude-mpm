"""
Tests for DeploymentContext value object (Phase 1 TDD → Phase 2 implementation).

Originally written as xfail TDD placeholders in Phase 1. Updated in Phase 2 to
remove xfail markers and adapt from_string tests to from_request_scope per team
lead decision (no from_string alias exists).
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from claude_mpm.core.config_scope import ConfigScope
from claude_mpm.core.deployment_context import DeploymentContext


class TestDeploymentContextFactories:
    """Test factory methods for creating DeploymentContext instances."""

    def test_from_project_uses_project_scope(self):
        """from_project(path) creates context with scope=ConfigScope.PROJECT."""
        ctx = DeploymentContext.from_project(Path("/tmp/my_project"))
        assert ctx.scope == ConfigScope.PROJECT
        assert ctx.project_path == Path("/tmp/my_project")

    def test_from_project_defaults_to_cwd_when_no_path(self):
        """from_project() without args uses Path.cwd() as project_path."""
        ctx = DeploymentContext.from_project()
        assert ctx.project_path == Path.cwd()

    def test_from_user_uses_user_scope(self):
        """from_user() creates context with scope=ConfigScope.USER."""
        ctx = DeploymentContext.from_user()
        assert ctx.scope == ConfigScope.USER

    def test_from_request_scope_project(self):
        """from_request_scope('project', path) -> scope=PROJECT."""
        ctx = DeploymentContext.from_request_scope("project", Path("/tmp/proj"))
        assert ctx.scope == ConfigScope.PROJECT

    def test_from_request_scope_user_raises_value_error(self):
        """from_request_scope('user') raises ValueError (MUST-1: project-only)."""
        with pytest.raises(ValueError):
            DeploymentContext.from_request_scope("user")

    def test_from_request_scope_invalid_raises_value_error(self):
        """from_request_scope('workspace') raises ValueError."""
        with pytest.raises(ValueError):
            DeploymentContext.from_request_scope("workspace")

    def test_from_request_scope_empty_string_raises_value_error(self):
        """from_request_scope('') raises ValueError."""
        with pytest.raises(ValueError):
            DeploymentContext.from_request_scope("")


class TestDeploymentContextPathProperties:
    """Test path resolution properties of DeploymentContext."""

    def test_agents_dir_project_scope(self):
        """ctx.agents_dir resolves to project/.claude/agents."""
        ctx = DeploymentContext.from_project(Path("/my/project"))
        assert ctx.agents_dir == Path("/my/project/.claude/agents")

    def test_agents_dir_user_scope(self, tmp_path):
        """ctx.agents_dir resolves to ~/.claude/agents for user scope."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch("claude_mpm.core.config_scope.Path.home", return_value=fake_home):
            ctx = DeploymentContext.from_user()
            assert ctx.agents_dir == fake_home / ".claude" / "agents"

    def test_skills_dir_project_scope(self):
        """ctx.skills_dir resolves to project/.claude/skills."""
        ctx = DeploymentContext.from_project(Path("/my/project"))
        assert ctx.skills_dir == Path("/my/project/.claude/skills")

    def test_skills_dir_user_scope(self, tmp_path):
        """ctx.skills_dir resolves to ~/.claude/skills for user scope."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch("claude_mpm.core.config_scope.Path.home", return_value=fake_home):
            ctx = DeploymentContext.from_user()
            assert ctx.skills_dir == fake_home / ".claude" / "skills"

    def test_config_dir_project_scope(self):
        """ctx.config_dir resolves to project/.claude-mpm."""
        ctx = DeploymentContext.from_project(Path("/my/project"))
        assert ctx.config_dir == Path("/my/project/.claude-mpm")

    def test_config_dir_user_scope(self, tmp_path):
        """ctx.config_dir resolves to ~/.claude-mpm for user scope."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch("claude_mpm.core.config_scope.Path.home", return_value=fake_home):
            ctx = DeploymentContext.from_user()
            assert ctx.config_dir == fake_home / ".claude-mpm"


class TestDeploymentContextImmutability:
    """Test that DeploymentContext is a frozen (immutable) dataclass."""

    def test_frozen_dataclass_cannot_modify_scope(self):
        """Attempting to set scope raises FrozenInstanceError."""
        ctx = DeploymentContext.from_project(Path("/tmp/proj"))
        with pytest.raises(AttributeError):
            ctx.scope = ConfigScope.USER

    def test_frozen_dataclass_cannot_modify_project_path(self):
        """Attempting to set project_path raises FrozenInstanceError."""
        ctx = DeploymentContext.from_project(Path("/tmp/proj"))
        with pytest.raises(AttributeError):
            ctx.project_path = Path("/other")


class TestDeploymentContextEdgeCases:
    """Edge cases and cross-scope isolation tests."""

    def test_project_and_user_contexts_are_isolated(self, tmp_path):
        """project_ctx.agents_dir and user_ctx.agents_dir do not overlap."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        project = tmp_path / "my_project"
        project.mkdir()

        project_ctx = DeploymentContext.from_project(project)
        with patch("claude_mpm.core.config_scope.Path.home", return_value=fake_home):
            user_ctx = DeploymentContext.from_user()

        assert project_ctx.agents_dir != user_ctx.agents_dir

    def test_two_project_contexts_same_path_are_equal(self):
        """Two from_project(same_path) instances should be equal."""
        ctx1 = DeploymentContext.from_project(Path("/tmp/proj"))
        ctx2 = DeploymentContext.from_project(Path("/tmp/proj"))
        assert ctx1 == ctx2

    def test_context_is_hashable(self):
        """DeploymentContext can be used as dict key (frozen dataclass)."""
        ctx = DeploymentContext.from_project(Path("/tmp/proj"))
        d = {ctx: "value"}
        assert d[ctx] == "value"
