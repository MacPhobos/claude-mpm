"""
Tests for CLI configure scope-aware deployment behavior (Phase 4A).

WHY: Verify that --scope user/project correctly routes agent and skill
deployments to the appropriate directories. These tests replace the
deleted xfail characterization tests (TC-0-04, TC-0-05) and confirm
the scope bug is fixed.

File: tests/cli/commands/test_configure_scope_behavior.py
Phase: 4A (CLI Bug Fix)
"""

from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from claude_mpm.cli.commands.configure import ConfigureCommand
from claude_mpm.core.deployment_context import DeploymentContext

# Patch target for Path.home() — used by resolve functions in config_scope.py
_HOME_PATCH = "claude_mpm.core.config_scope.Path.home"


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def project_scope_dirs(tmp_path):
    """Create project-scope directory structure."""
    root = tmp_path / "my_project"
    root.mkdir()
    agents = root / ".claude" / "agents"
    agents.mkdir(parents=True)
    skills = root / ".claude" / "skills"
    skills.mkdir(parents=True)
    return {"root": root, "agents": agents, "skills": skills}


@pytest.fixture
def user_scope_dirs(tmp_path):
    """Create user-scope directory structure (fake home)."""
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    agents = fake_home / ".claude" / "agents"
    agents.mkdir(parents=True)
    skills = fake_home / ".claude" / "skills"
    skills.mkdir(parents=True)
    return {"home": fake_home, "agents": agents, "skills": skills}


@pytest.fixture
def source_agent_file(tmp_path):
    """Create a source agent .md file for deployment tests."""
    source = tmp_path / "source_agent.md"
    source.write_text("# Test Agent\nThis is a test agent.")
    return source


def _make_project_cmd(project_dir):
    """Create a ConfigureCommand with project-scope _ctx."""
    cmd = ConfigureCommand()
    cmd.current_scope = "project"
    cmd.project_dir = project_dir
    cmd._ctx = DeploymentContext.from_project(project_dir)
    return cmd


def _make_user_cmd(project_dir):
    """Create a ConfigureCommand with user-scope _ctx.

    NOTE: Callers MUST wrap method calls in:
        with patch(_HOME_PATCH, return_value=fake_home):
    because resolve_*() calls Path.home() at property access time.
    """
    cmd = ConfigureCommand()
    cmd.current_scope = "user"
    cmd.project_dir = project_dir
    cmd._ctx = DeploymentContext.from_user()
    return cmd


# ==============================================================================
# Phase 2-A: Agent Deploy Scope Tests
# ==============================================================================


class TestConfigureAgentScopeDeployment:
    """Tests for scope-aware agent deployment."""

    # TC-2-01
    def test_deploy_agent_project_scope_places_file_in_project_dir(
        self, project_scope_dirs, user_scope_dirs, source_agent_file
    ):
        """scope='project' deploys agent .md to {project_dir}/.claude/agents/."""
        cmd = _make_project_cmd(project_scope_dirs["root"])

        agent = Mock()
        agent.name = "engineer"
        agent.full_agent_id = "engineer"
        agent.source_dict = {"source_file": str(source_agent_file)}

        cmd._deploy_single_agent(agent, show_feedback=False)

        # Agent should be in project dir
        assert (project_scope_dirs["agents"] / "engineer.md").exists()
        # Agent should NOT be in user dir
        assert not (user_scope_dirs["agents"] / "engineer.md").exists()

    # TC-2-02
    def test_deploy_agent_user_scope_places_file_in_home_dir(
        self, project_scope_dirs, user_scope_dirs, source_agent_file
    ):
        """scope='user' deploys agent .md to ~/.claude/agents/."""
        cmd = _make_user_cmd(project_scope_dirs["root"])

        agent = Mock()
        agent.name = "engineer"
        agent.full_agent_id = "engineer"
        agent.source_dict = {"source_file": str(source_agent_file)}

        with patch(_HOME_PATCH, return_value=user_scope_dirs["home"]):
            cmd._deploy_single_agent(agent, show_feedback=False)

        # Agent should be in user home dir
        assert (user_scope_dirs["agents"] / "engineer.md").exists()
        # Agent should NOT be in project dir
        assert not (project_scope_dirs["agents"] / "engineer.md").exists()

    # TC-2-03
    def test_deploy_agent_project_scope_unchanged_from_before(
        self, project_scope_dirs, source_agent_file
    ):
        """After scope fix, project scope behavior is identical to pre-fix behavior."""
        cmd = _make_project_cmd(project_scope_dirs["root"])

        agent = Mock()
        agent.name = "engineer"
        agent.full_agent_id = "engineer"
        agent.source_dict = {"source_file": str(source_agent_file)}

        cmd._deploy_single_agent(agent, show_feedback=False)

        target_file = project_scope_dirs["agents"] / "engineer.md"
        assert target_file.exists()
        assert target_file.read_text() == "# Test Agent\nThis is a test agent."

    # TC-2-04
    def test_deploy_agent_missing_scope_defaults_to_project(
        self, project_scope_dirs, source_agent_file
    ):
        """Default ConfigureCommand (no explicit scope) deploys to project dir."""
        cmd = _make_project_cmd(project_scope_dirs["root"])

        agent = Mock()
        agent.name = "engineer"
        agent.full_agent_id = "engineer"
        agent.source_dict = {"source_file": str(source_agent_file)}

        cmd._deploy_single_agent(agent, show_feedback=False)

        assert (project_scope_dirs["agents"] / "engineer.md").exists()

    # TC-2-05
    def test_deploy_agent_source_file_missing_returns_false(self, project_scope_dirs):
        """_deploy_single_agent returns False when source file doesn't exist."""
        cmd = _make_project_cmd(project_scope_dirs["root"])

        agent = Mock()
        agent.name = "engineer"
        agent.full_agent_id = "engineer"
        agent.source_dict = {"source_file": "/nonexistent/agent.md"}

        result = cmd._deploy_single_agent(agent, show_feedback=False)
        assert result is False

    # TC-2-06
    def test_run_scope_user_propagates_to_deploy(self, tmp_path, user_scope_dirs):
        """Full run() with scope='user' sets _ctx.agents_dir to ~/.claude/agents/."""
        project_dir = tmp_path / "my_project"
        project_dir.mkdir()

        args = Namespace(
            scope="user",
            project_dir=str(project_dir),
            no_colors=False,
            list_agents=False,
            enable_agent=None,
            disable_agent=None,
            export_config=None,
            import_config=None,
            version_info=False,
            install_hooks=False,
            verify_hooks=False,
            uninstall_hooks=False,
            agents=False,
            templates=False,
            behaviors=False,
            startup=False,
        )

        cmd = ConfigureCommand()
        with patch(_HOME_PATCH, return_value=user_scope_dirs["home"]):
            with patch.object(cmd, "_run_interactive_tui", return_value=MagicMock()):
                cmd.run(args)
            # Check within patch scope since agents_dir calls Path.home()
            assert cmd.current_scope == "user"
            assert cmd._ctx.agents_dir == user_scope_dirs["agents"]
            assert cmd._ctx.skills_dir == user_scope_dirs["skills"]


# ==============================================================================
# Phase 2-B: Skill Deploy Scope Tests
# ==============================================================================


class TestConfigureSkillScopeDeployment:
    """Tests for scope-aware skill deployment."""

    # TC-2-07
    def test_install_skill_project_scope_places_dir_in_project(
        self, project_scope_dirs, user_scope_dirs
    ):
        """scope='project' installs skill to {project_dir}/.claude/skills/."""
        cmd = _make_project_cmd(project_scope_dirs["root"])

        skill_dict = {
            "name": "my-skill",
            "deployment_name": "my-skill",
            "content": "# My Skill\nSkill content here.",
        }
        cmd._install_skill_from_dict(skill_dict)

        assert (project_scope_dirs["skills"] / "my-skill" / "skill.md").exists()
        assert not (user_scope_dirs["skills"] / "my-skill" / "skill.md").exists()

    # TC-2-08
    def test_install_skill_user_scope_places_dir_in_home(
        self, project_scope_dirs, user_scope_dirs
    ):
        """scope='user' installs skill to ~/.claude/skills/."""
        cmd = _make_user_cmd(project_scope_dirs["root"])

        skill_dict = {
            "name": "my-skill",
            "deployment_name": "my-skill",
            "content": "# My Skill\nSkill content here.",
        }
        with patch(_HOME_PATCH, return_value=user_scope_dirs["home"]):
            cmd._install_skill_from_dict(skill_dict)

        assert (user_scope_dirs["skills"] / "my-skill" / "skill.md").exists()
        assert not (project_scope_dirs["skills"] / "my-skill" / "skill.md").exists()

    # TC-2-09
    def test_install_skill_missing_scope_defaults_to_project(self, project_scope_dirs):
        """Default (no scope set) installs skill to project dir."""
        cmd = _make_project_cmd(project_scope_dirs["root"])

        skill_dict = {
            "name": "my-skill",
            "deployment_name": "my-skill",
            "content": "# My Skill\nSkill content here.",
        }
        cmd._install_skill_from_dict(skill_dict)

        assert (project_scope_dirs["skills"] / "my-skill" / "skill.md").exists()

    # TC-2-10
    def test_get_deployed_skill_ids_project_scope(self, project_scope_dirs):
        """_get_deployed_skill_ids() with project scope lists project dir skills."""
        (project_scope_dirs["skills"] / "skill-one").mkdir()
        (project_scope_dirs["skills"] / "skill-two").mkdir()

        cmd = _make_project_cmd(project_scope_dirs["root"])
        result = cmd._get_deployed_skill_ids()

        assert "skill-one" in result
        assert "skill-two" in result

    # TC-2-11
    def test_get_deployed_skill_ids_user_scope(
        self, project_scope_dirs, user_scope_dirs
    ):
        """_get_deployed_skill_ids() with user scope lists ~/.claude/skills/."""
        (user_scope_dirs["skills"] / "user-skill").mkdir()
        (project_scope_dirs["skills"] / "project-skill").mkdir()

        cmd = _make_user_cmd(project_scope_dirs["root"])

        with patch(_HOME_PATCH, return_value=user_scope_dirs["home"]):
            result = cmd._get_deployed_skill_ids()

        assert "user-skill" in result
        assert "project-skill" not in result

    # TC-2-12
    def test_uninstall_skill_project_scope(self, project_scope_dirs):
        """_uninstall_skill_by_name() removes from project dir when scope=project."""
        skill_dir = project_scope_dirs["skills"] / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "skill.md").write_text("# Skill")

        cmd = _make_project_cmd(project_scope_dirs["root"])
        cmd._uninstall_skill_by_name("my-skill")

        assert not skill_dir.exists()

    # TC-2-13
    def test_uninstall_skill_user_scope(self, project_scope_dirs, user_scope_dirs):
        """_uninstall_skill_by_name() removes from ~/.claude/skills/ when scope=user."""
        user_skill = user_scope_dirs["skills"] / "my-skill"
        user_skill.mkdir()
        (user_skill / "skill.md").write_text("# Skill")

        project_skill = project_scope_dirs["skills"] / "my-skill"
        project_skill.mkdir()
        (project_skill / "skill.md").write_text("# Skill")

        cmd = _make_user_cmd(project_scope_dirs["root"])

        with patch(_HOME_PATCH, return_value=user_scope_dirs["home"]):
            cmd._uninstall_skill_by_name("my-skill")

        # User-scope skill should be removed
        assert not user_skill.exists()
        # Project-scope skill should be untouched
        assert project_skill.exists()


# ==============================================================================
# Phase 2-C: Scope Validation Tests
# ==============================================================================


class TestConfigureScopeValidation:
    """Tests for scope argument validation."""

    # TC-2-14
    def test_validate_args_accepts_project_scope(self):
        """validate_args passes with scope='project'."""
        cmd = ConfigureCommand()
        args = Namespace(
            scope="project",
            agents=False,
            templates=False,
            behaviors=False,
            startup=False,
            version_info=False,
            enable_agent=None,
            disable_agent=None,
        )
        error = cmd.validate_args(args)
        assert error is None

    # TC-2-15
    def test_validate_args_accepts_user_scope(self):
        """validate_args passes with scope='user'."""
        cmd = ConfigureCommand()
        args = Namespace(
            scope="user",
            agents=False,
            templates=False,
            behaviors=False,
            startup=False,
            version_info=False,
            enable_agent=None,
            disable_agent=None,
        )
        error = cmd.validate_args(args)
        assert error is None

    # TC-2-16
    def test_validate_args_rejects_invalid_scope(self):
        """validate_args returns error for scope='workspace'."""
        cmd = ConfigureCommand()
        args = Namespace(
            scope="workspace",
            agents=False,
            templates=False,
            behaviors=False,
            startup=False,
            version_info=False,
            enable_agent=None,
            disable_agent=None,
        )
        error = cmd.validate_args(args)
        assert error is not None
        assert "scope" in error.lower()

    # TC-2-17
    def test_validate_args_accepts_missing_scope_attr(self):
        """validate_args does not error when scope attribute is missing from Namespace."""
        cmd = ConfigureCommand()
        args = Namespace(
            agents=False,
            templates=False,
            behaviors=False,
            startup=False,
            version_info=False,
            enable_agent=None,
            disable_agent=None,
        )
        error = cmd.validate_args(args)
        assert error is None
