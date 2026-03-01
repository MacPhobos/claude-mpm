"""Tests for BackupManager receiving scope-resolved directory paths.

Phase 4B (MUST-3): Verifies that handler singletons pass explicit
agents_dir / skills_dir from DeploymentContext to BackupManager,
rather than relying on BackupManager's internal hardcoded defaults.
"""

from unittest.mock import MagicMock, patch

import claude_mpm.services.config_api.agent_deployment_handler as agent_handler
import claude_mpm.services.config_api.skill_deployment_handler as skill_handler


class TestBackupManagerScope:
    """Verify BackupManager is constructed with scope-resolved paths."""

    def teardown_method(self):
        """Reset singletons after each test."""
        agent_handler._backup_manager = None
        skill_handler._backup_manager = None

    @patch("claude_mpm.services.config_api.backup_manager.BackupManager")
    def test_agent_handler_backup_manager_receives_scope_resolved_agents_dir(
        self, mock_backup_cls, tmp_path, monkeypatch
    ):
        """BackupManager in agent handler gets agents_dir from DeploymentContext."""
        monkeypatch.chdir(tmp_path)
        agent_handler._backup_manager = None

        mock_backup_cls.return_value = MagicMock(name="backup_mgr")

        agent_handler._get_backup_manager()

        # Verify BackupManager was called with explicit agents_dir kwarg
        mock_backup_cls.assert_called_once()
        call_kwargs = mock_backup_cls.call_args
        assert "agents_dir" in call_kwargs.kwargs
        expected_agents_dir = tmp_path / ".claude" / "agents"
        assert call_kwargs.kwargs["agents_dir"] == expected_agents_dir

    @patch("claude_mpm.services.config_api.backup_manager.BackupManager")
    def test_skill_handler_backup_manager_receives_scope_resolved_skills_dir(
        self, mock_backup_cls, tmp_path, monkeypatch
    ):
        """BackupManager in skill handler gets skills_dir from DeploymentContext."""
        monkeypatch.chdir(tmp_path)
        skill_handler._backup_manager = None

        mock_backup_cls.return_value = MagicMock(name="backup_mgr")

        skill_handler._get_backup_manager()

        # Verify BackupManager was called with explicit skills_dir kwarg
        mock_backup_cls.assert_called_once()
        call_kwargs = mock_backup_cls.call_args
        assert "skills_dir" in call_kwargs.kwargs
        expected_skills_dir = tmp_path / ".claude" / "skills"
        assert call_kwargs.kwargs["skills_dir"] == expected_skills_dir
