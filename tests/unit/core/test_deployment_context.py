"""Unit tests for DeploymentContext frozen dataclass.

Tests TC-1-01 through TC-1-23 from the test plan. Covers factory methods,
path properties, immutability, and edge cases.

NOTE: The test plan originally specified `from_string()` tests (TC-1-04 through
TC-1-08). Per team lead decision, `from_string()` does NOT exist. These tests
are adapted to test `from_request_scope()` with MUST-1 project-only validation.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from claude_mpm.core.config_scope import ConfigScope
from claude_mpm.core.deployment_context import DeploymentContext


class TestDeploymentContextFactories:
    """Test factory methods for creating DeploymentContext instances."""

    # TC-1-01
    def test_from_project_uses_project_scope(self):
        """from_project(path) creates context with scope=ConfigScope.PROJECT."""
        ctx = DeploymentContext.from_project(Path("/tmp/my_project"))
        assert ctx.scope == ConfigScope.PROJECT
        assert ctx.project_path == Path("/tmp/my_project")

    # TC-1-02
    def test_from_project_defaults_to_cwd_when_no_path(self):
        """from_project() without args uses Path.cwd() as project_path."""
        ctx = DeploymentContext.from_project()
        assert ctx.project_path == Path.cwd()

    # TC-1-03
    def test_from_user_uses_user_scope(self):
        """from_user() creates context with scope=ConfigScope.USER."""
        ctx = DeploymentContext.from_user()
        assert ctx.scope == ConfigScope.USER

    # TC-1-04 (adapted: from_string → from_request_scope)
    def test_from_request_scope_project(self):
        """from_request_scope('project', path) -> scope=PROJECT."""
        ctx = DeploymentContext.from_request_scope("project", Path("/tmp/proj"))
        assert ctx.scope == ConfigScope.PROJECT
        assert ctx.project_path == Path("/tmp/proj")

    # TC-1-05 (adapted: from_string("user") → from_request_scope("user") raises)
    def test_from_request_scope_user_raises_value_error(self):
        """from_request_scope('user') raises ValueError (MUST-1: project-only API)."""
        with pytest.raises(ValueError, match="only 'project' is supported"):
            DeploymentContext.from_request_scope("user")

    # TC-1-06 (adapted: from_string → from_request_scope)
    def test_from_request_scope_invalid_raises_value_error(self):
        """from_request_scope('workspace') raises ValueError."""
        with pytest.raises(ValueError, match="Invalid scope 'workspace'"):
            DeploymentContext.from_request_scope("workspace")

    # TC-1-07 (adapted: from_string → from_request_scope)
    def test_from_request_scope_empty_string_raises_value_error(self):
        """from_request_scope('') raises ValueError."""
        with pytest.raises(ValueError):
            DeploymentContext.from_request_scope("")

    # TC-1-08 (adapted: from_string → from_request_scope)
    def test_from_request_scope_none_raises_type_error(self):
        """from_request_scope(None) raises TypeError (not in tuple check)."""
        with pytest.raises((TypeError, ValueError)):
            DeploymentContext.from_request_scope(None)


class TestDeploymentContextPathProperties:
    """Test path resolution properties of DeploymentContext."""

    # TC-1-09
    def test_agents_dir_project_scope(self):
        """ctx.agents_dir resolves to project/.claude/agents."""
        ctx = DeploymentContext.from_project(Path("/my/project"))
        assert ctx.agents_dir == Path("/my/project/.claude/agents")

    # TC-1-10
    def test_agents_dir_user_scope(self, tmp_path):
        """ctx.agents_dir resolves to ~/.claude/agents for user scope."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch("claude_mpm.core.config_scope.Path.home", return_value=fake_home):
            ctx = DeploymentContext.from_user()
            assert ctx.agents_dir == fake_home / ".claude" / "agents"

    # TC-1-11
    def test_skills_dir_project_scope(self):
        """ctx.skills_dir resolves to project/.claude/skills."""
        ctx = DeploymentContext.from_project(Path("/my/project"))
        assert ctx.skills_dir == Path("/my/project/.claude/skills")

    # TC-1-12
    def test_skills_dir_user_scope(self, tmp_path):
        """ctx.skills_dir resolves to ~/.claude/skills for user scope."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch("claude_mpm.core.config_scope.Path.home", return_value=fake_home):
            ctx = DeploymentContext.from_user()
            assert ctx.skills_dir == fake_home / ".claude" / "skills"

    # TC-1-13
    def test_archive_dir_project_scope(self):
        """ctx.archive_dir resolves to project/.claude/agents/unused."""
        ctx = DeploymentContext.from_project(Path("/my/project"))
        assert ctx.archive_dir == Path("/my/project/.claude/agents/unused")

    # TC-1-14
    def test_archive_dir_user_scope(self, tmp_path):
        """ctx.archive_dir resolves to ~/.claude/agents/unused for user scope."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch("claude_mpm.core.config_scope.Path.home", return_value=fake_home):
            ctx = DeploymentContext.from_user()
            assert ctx.archive_dir == fake_home / ".claude" / "agents" / "unused"

    # TC-1-15
    def test_config_dir_project_scope(self):
        """ctx.config_dir resolves to project/.claude-mpm."""
        ctx = DeploymentContext.from_project(Path("/my/project"))
        assert ctx.config_dir == Path("/my/project/.claude-mpm")

    # TC-1-16
    def test_config_dir_user_scope(self, tmp_path):
        """ctx.config_dir resolves to ~/.claude-mpm for user scope."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch("claude_mpm.core.config_scope.Path.home", return_value=fake_home):
            ctx = DeploymentContext.from_user()
            assert ctx.config_dir == fake_home / ".claude-mpm"

    # TC-1-17
    def test_configuration_yaml_project_scope(self):
        """ctx.configuration_yaml resolves to project/.claude-mpm/configuration.yaml."""
        ctx = DeploymentContext.from_project(Path("/my/project"))
        assert ctx.configuration_yaml == Path(
            "/my/project/.claude-mpm/configuration.yaml"
        )

    # TC-1-18
    def test_configuration_yaml_user_scope(self, tmp_path):
        """ctx.configuration_yaml resolves to ~/.claude-mpm/configuration.yaml."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()
        with patch("claude_mpm.core.config_scope.Path.home", return_value=fake_home):
            ctx = DeploymentContext.from_user()
            assert (
                ctx.configuration_yaml
                == fake_home / ".claude-mpm" / "configuration.yaml"
            )


class TestDeploymentContextImmutability:
    """Test that DeploymentContext is a frozen (immutable) dataclass."""

    # TC-1-19
    def test_frozen_dataclass_cannot_modify_scope(self):
        """Attempting to set scope raises FrozenInstanceError."""
        ctx = DeploymentContext.from_project(Path("/tmp/proj"))
        with pytest.raises(AttributeError):
            ctx.scope = ConfigScope.USER

    # TC-1-20
    def test_frozen_dataclass_cannot_modify_project_path(self):
        """Attempting to set project_path raises FrozenInstanceError."""
        ctx = DeploymentContext.from_project(Path("/tmp/proj"))
        with pytest.raises(AttributeError):
            ctx.project_path = Path("/other")


class TestDeploymentContextEdgeCases:
    """Edge cases and cross-scope isolation tests."""

    # TC-1-21
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

    # TC-1-22
    def test_two_project_contexts_same_path_are_equal(self):
        """Two from_project(same_path) instances should be equal."""
        ctx1 = DeploymentContext.from_project(Path("/tmp/proj"))
        ctx2 = DeploymentContext.from_project(Path("/tmp/proj"))
        assert ctx1 == ctx2

    # TC-1-23
    def test_context_is_hashable(self):
        """DeploymentContext can be used as dict key (frozen dataclass)."""
        ctx = DeploymentContext.from_project(Path("/tmp/proj"))
        d = {ctx: "value"}
        assert d[ctx] == "value"
