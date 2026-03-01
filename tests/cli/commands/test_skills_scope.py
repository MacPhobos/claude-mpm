"""
Tests for skills command scope-aware deployment (Phase 7).

WHY: Verify that --scope user/project correctly routes skill deployments
to the appropriate directories via DeploymentContext.

File: tests/cli/commands/test_skills_scope.py
Phase: 7 (Code Cleanup + Skills Scope)
"""

from argparse import Namespace
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from claude_mpm.cli.commands.skills import SkillsManagementCommand
from claude_mpm.core.deployment_context import DeploymentContext

# Patch target for Path.home() — used by resolve functions in config_scope.py
_HOME_PATCH = "claude_mpm.core.config_scope.Path.home"


# ==============================================================================
# Fixtures
# ==============================================================================


@pytest.fixture
def skills_dirs(tmp_path):
    """Create project and user skill directory structures."""
    project_root = tmp_path / "my_project"
    project_root.mkdir()
    project_skills = project_root / ".claude" / "skills"
    project_skills.mkdir(parents=True)

    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    user_skills = fake_home / ".claude" / "skills"
    user_skills.mkdir(parents=True)

    return {
        "project_root": project_root,
        "project_skills": project_skills,
        "fake_home": fake_home,
        "user_skills": user_skills,
    }


# ==============================================================================
# TC-2-18 through TC-2-22: Skills Scope Tests
# ==============================================================================


class TestSkillsDeployFromGithubScope:
    """Tests for scope-aware GitHub skills deployment."""

    # TC-2-18
    def test_deploy_from_github_user_scope_passes_user_skills_dir(self, skills_dirs):
        """scope='user' passes ~/.claude/skills/ to deployer."""
        cmd = SkillsManagementCommand()
        mock_deployer = MagicMock()
        mock_deployer.deploy_skills.return_value = {
            "deployed_count": 0,
            "deployed_skills": [],
            "skipped_count": 0,
            "skipped_skills": [],
            "errors": [],
        }
        cmd._skills_deployer = mock_deployer

        args = Namespace(
            skills_command="deploy-from-github",
            collection=None,
            toolchain=None,
            categories=None,
            force=False,
            all=False,
            scope="user",
            project_dir=str(skills_dirs["project_root"]),
        )

        with patch(_HOME_PATCH, return_value=skills_dirs["fake_home"]):
            cmd._deploy_from_github(args)

        # Verify skills_dir was passed to deployer
        call_kwargs = mock_deployer.deploy_skills.call_args[1]
        assert call_kwargs["skills_dir"] == skills_dirs["user_skills"]

    # TC-2-19
    def test_deploy_from_github_project_scope_passes_project_skills_dir(
        self, skills_dirs
    ):
        """scope='project' passes {project}/.claude/skills/ to deployer."""
        cmd = SkillsManagementCommand()
        mock_deployer = MagicMock()
        mock_deployer.deploy_skills.return_value = {
            "deployed_count": 0,
            "deployed_skills": [],
            "skipped_count": 0,
            "skipped_skills": [],
            "errors": [],
        }
        cmd._skills_deployer = mock_deployer

        args = Namespace(
            skills_command="deploy-from-github",
            collection=None,
            toolchain=None,
            categories=None,
            force=False,
            all=False,
            scope="project",
            project_dir=str(skills_dirs["project_root"]),
        )

        cmd._deploy_from_github(args)

        call_kwargs = mock_deployer.deploy_skills.call_args[1]
        assert call_kwargs["skills_dir"] == skills_dirs["project_skills"]

    # TC-2-20
    def test_deploy_from_github_default_scope_is_user(self, skills_dirs):
        """Missing scope attribute defaults to 'user' for GitHub deployment."""
        cmd = SkillsManagementCommand()
        mock_deployer = MagicMock()
        mock_deployer.deploy_skills.return_value = {
            "deployed_count": 0,
            "deployed_skills": [],
            "skipped_count": 0,
            "skipped_skills": [],
            "errors": [],
        }
        cmd._skills_deployer = mock_deployer

        # No scope attr — getattr defaults to "user"
        args = Namespace(
            skills_command="deploy-from-github",
            collection=None,
            toolchain=None,
            categories=None,
            force=False,
            all=False,
            project_dir=str(skills_dirs["project_root"]),
        )

        with patch(_HOME_PATCH, return_value=skills_dirs["fake_home"]):
            cmd._deploy_from_github(args)

        call_kwargs = mock_deployer.deploy_skills.call_args[1]
        assert call_kwargs["skills_dir"] == skills_dirs["user_skills"]

    # TC-2-21
    def test_deployment_context_from_user_resolves_home_skills(self, skills_dirs):
        """DeploymentContext.from_user() resolves to ~/.claude/skills/."""
        with patch(_HOME_PATCH, return_value=skills_dirs["fake_home"]):
            ctx = DeploymentContext.from_user()
            assert ctx.skills_dir == skills_dirs["user_skills"]

    # TC-2-22
    def test_deployment_context_from_project_resolves_project_skills(self, skills_dirs):
        """DeploymentContext.from_project() resolves to {project}/.claude/skills/."""
        ctx = DeploymentContext.from_project(skills_dirs["project_root"])
        assert ctx.skills_dir == skills_dirs["project_skills"]
