"""
Characterization tests for CLI configure scope behavior.

WHY: Lock down current scope behavior BEFORE any refactoring. These tests are
regression anchors — if any test breaks after a refactor, the refactor changed
behavior unexpectedly.

Write-first, commit before refactoring.

Phase: 0 (characterization)
"""

from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_mpm.cli.commands.configure import ConfigureCommand
from claude_mpm.cli.commands.configure_navigation import ConfigNavigation

# ==============================================================================
# Phase 0-A: CLI Configure Scope (Current Behavior)
# ==============================================================================


@pytest.mark.regression
class TestConfigureScopeCurrentBehavior:
    """Characterization tests for ConfigureCommand scope handling."""

    def _make_cmd_with_scope(self, scope, project_dir, mock_tui=True):
        """Helper to create a ConfigureCommand with run() executed for a given scope.

        Args:
            scope: "project" or "user" scope string
            project_dir: Path to use as project_dir
            mock_tui: If True, mock _run_interactive_tui to prevent TUI launch
        """
        cmd = ConfigureCommand()
        args = Namespace(
            scope=scope,
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
        if mock_tui:
            with patch.object(cmd, "_run_interactive_tui", return_value=MagicMock()):
                cmd.run(args)
        return cmd

    # TC-0-01
    def test_project_scope_sets_config_dir_under_project(self, tmp_path):
        """run() with scope='project' sets agent_manager.config_dir to {project_dir}/.claude-mpm/."""
        project_dir = tmp_path / "my_project"
        project_dir.mkdir()

        cmd = self._make_cmd_with_scope("project", project_dir)

        assert cmd.agent_manager is not None
        assert cmd.agent_manager.config_dir == project_dir / ".claude-mpm"
        assert cmd.current_scope == "project"

    # TC-0-02
    def test_user_scope_sets_config_dir_under_home(self, tmp_path):
        """run() with scope='user' sets agent_manager.config_dir to ~/.claude-mpm/."""
        project_dir = tmp_path / "my_project"
        project_dir.mkdir()
        fake_home = tmp_path / "fake_home"
        fake_home.mkdir()

        with patch(
            "claude_mpm.cli.commands.configure.Path.home", return_value=fake_home
        ):
            cmd = self._make_cmd_with_scope("user", project_dir)

        assert cmd.agent_manager is not None
        assert cmd.agent_manager.config_dir == fake_home / ".claude-mpm"
        assert cmd.current_scope == "user"

    # TC-0-03
    def test_missing_scope_attr_defaults_to_project(self, tmp_path):
        """When args has no scope attribute, defaults to 'project'."""
        project_dir = tmp_path / "my_project"
        project_dir.mkdir()

        cmd = ConfigureCommand()
        # Create args WITHOUT scope attribute
        args = Namespace(
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
        # Note: no 'scope' in args — getattr(args, "scope", "project") returns "project"
        with patch.object(cmd, "_run_interactive_tui", return_value=MagicMock()):
            cmd.run(args)

        assert cmd.current_scope == "project"

    # TC-0-04: DELETED in Phase 4A — replaced by TC-2-01/TC-2-02 in test_configure_scope_behavior.py
    # TC-0-05: DELETED in Phase 4A — replaced by TC-2-07/TC-2-08 in test_configure_scope_behavior.py

    # TC-0-06
    def test_scope_toggle_only_switches_current_scope_string(self, tmp_path):
        """ConfigNavigation.switch_scope() simply flips current_scope string."""
        console = MagicMock()
        navigation = ConfigNavigation(console, tmp_path)
        assert navigation.current_scope == "project"

        # Patch Prompt.ask so it doesn't block
        with patch("claude_mpm.cli.commands.configure_navigation.Prompt.ask"):
            navigation.switch_scope()
            assert navigation.current_scope == "user"

            navigation.switch_scope()
            assert navigation.current_scope == "project"


# ==============================================================================
# Phase 0-B: CLI Skills Scope (Current Behavior)
# ==============================================================================


@pytest.mark.regression
class TestSkillsScopeCurrentBehavior:
    """Characterization tests for skills scope handling in ConfigureCommand."""

    # TC-0-07
    def test_get_deployed_skill_ids_reads_from_project_dir(self, tmp_path):
        """_get_deployed_skill_ids() reads from self._ctx.skills_dir (project scope)."""
        # Create skill dirs under tmp_path (simulating project dir)
        skills_dir = tmp_path / ".claude" / "skills"
        skills_dir.mkdir(parents=True)
        (skills_dir / "skill-alpha").mkdir()
        (skills_dir / "skill-beta").mkdir()

        cmd = ConfigureCommand()
        cmd.project_dir = tmp_path
        from claude_mpm.core.deployment_context import DeploymentContext

        cmd._ctx = DeploymentContext.from_project(tmp_path)

        result = cmd._get_deployed_skill_ids()

        assert "skill-alpha" in result
        assert "skill-beta" in result

    # TC-0-08
    def test_uninstall_skill_removes_from_project_dir(self, tmp_path):
        """_uninstall_skill_by_name() removes from self._ctx.skills_dir (project scope)."""
        # Create real skill dir under tmp_path (simulating project dir)
        skills_dir = tmp_path / ".claude" / "skills"
        skill_dir = skills_dir / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "skill.md").write_text("# My Skill")

        cmd = ConfigureCommand()
        cmd.project_dir = tmp_path
        from claude_mpm.core.deployment_context import DeploymentContext

        cmd._ctx = DeploymentContext.from_project(tmp_path)

        cmd._uninstall_skill_by_name("my-skill")

        # Verify skill directory was removed
        assert not skill_dir.exists()
