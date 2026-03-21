#!/usr/bin/env python3
"""Tests for Agent Teams compliance logging.

Validates that _compliance_log() writes structured JSONL records
to the compliance directory for Gate 1 audit.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestComplianceLog:
    """Tests for the _compliance_log() function."""

    def test_compliance_log_creates_directory(self, tmp_path):
        """_compliance_log creates the compliance directory on first call."""
        log_dir = tmp_path / "compliance"
        assert not log_dir.exists()

        with patch(
            "claude_mpm.hooks.claude_hooks.event_handlers._COMPLIANCE_LOG_DIR",
            log_dir,
        ):
            from claude_mpm.hooks.claude_hooks.event_handlers import _compliance_log

            _compliance_log({"event_type": "injection", "team_name": "test"})

        assert log_dir.exists()

    def test_compliance_log_writes_json_line(self, tmp_path):
        """_compliance_log writes a valid JSON line with all fields."""
        log_dir = tmp_path / "compliance"

        with patch(
            "claude_mpm.hooks.claude_hooks.event_handlers._COMPLIANCE_LOG_DIR",
            log_dir,
        ):
            from claude_mpm.hooks.claude_hooks.event_handlers import _compliance_log

            _compliance_log(
                {
                    "event_type": "injection",
                    "session_id": "sess-123",
                    "team_name": "research-auth",
                    "subagent_type": "research",
                    "teammate_name": "auth-researcher",
                    "injection_applied": True,
                }
            )

        # Find the log file
        log_files = list(log_dir.glob("agent-teams-*.jsonl"))
        assert len(log_files) == 1

        content = log_files[0].read_text().strip()
        record = json.loads(content)

        assert record["event_type"] == "injection"
        assert record["session_id"] == "sess-123"
        assert record["team_name"] == "research-auth"
        assert record["injection_applied"] is True
        assert "timestamp" in record

    def test_compliance_log_appends(self, tmp_path):
        """_compliance_log appends to existing file, does not overwrite."""
        log_dir = tmp_path / "compliance"

        with patch(
            "claude_mpm.hooks.claude_hooks.event_handlers._COMPLIANCE_LOG_DIR",
            log_dir,
        ):
            from claude_mpm.hooks.claude_hooks.event_handlers import _compliance_log

            _compliance_log({"event_type": "injection", "team_name": "team-1"})
            _compliance_log({"event_type": "task_completed", "task_id": "t1"})

        log_files = list(log_dir.glob("agent-teams-*.jsonl"))
        lines = log_files[0].read_text().strip().split("\n")
        assert len(lines) == 2

        record1 = json.loads(lines[0])
        record2 = json.loads(lines[1])
        assert record1["event_type"] == "injection"
        assert record2["event_type"] == "task_completed"

    def test_compliance_log_includes_timestamp(self, tmp_path):
        """_compliance_log adds ISO timestamp automatically."""
        log_dir = tmp_path / "compliance"

        with patch(
            "claude_mpm.hooks.claude_hooks.event_handlers._COMPLIANCE_LOG_DIR",
            log_dir,
        ):
            from claude_mpm.hooks.claude_hooks.event_handlers import _compliance_log

            _compliance_log({"event_type": "injection"})

        log_files = list(log_dir.glob("agent-teams-*.jsonl"))
        record = json.loads(log_files[0].read_text().strip())
        assert "timestamp" in record
        # ISO format contains T separator
        assert "T" in record["timestamp"]

    def test_compliance_log_handles_write_error(self):
        """_compliance_log silently handles write errors."""
        with patch(
            "claude_mpm.hooks.claude_hooks.event_handlers._COMPLIANCE_LOG_DIR",
            Path("/nonexistent/deeply/nested/path"),
        ):
            from claude_mpm.hooks.claude_hooks.event_handlers import _compliance_log

            # Should not raise
            _compliance_log({"event_type": "injection"})

    def test_compliance_log_respects_env_override(self, tmp_path, monkeypatch):
        """CLAUDE_MPM_COMPLIANCE_LOG_DIR env var overrides default path."""
        custom_dir = tmp_path / "custom_compliance"
        monkeypatch.setenv("CLAUDE_MPM_COMPLIANCE_LOG_DIR", str(custom_dir))

        # Re-import to pick up new env var
        with patch(
            "claude_mpm.hooks.claude_hooks.event_handlers._COMPLIANCE_LOG_DIR",
            custom_dir,
        ):
            from claude_mpm.hooks.claude_hooks.event_handlers import _compliance_log

            _compliance_log({"event_type": "injection", "team_name": "test"})

        assert custom_dir.exists()
        log_files = list(custom_dir.glob("agent-teams-*.jsonl"))
        assert len(log_files) == 1

    def test_stratum_from_env_var(self, tmp_path, monkeypatch):
        """CLAUDE_MPM_COMPLIANCE_STRATUM env var appears in compliance records."""
        log_dir = tmp_path / "compliance"
        monkeypatch.setenv("CLAUDE_MPM_COMPLIANCE_STRATUM", "medium")

        with patch(
            "claude_mpm.hooks.claude_hooks.event_handlers._COMPLIANCE_LOG_DIR",
            log_dir,
        ):
            from claude_mpm.hooks.claude_hooks.event_handlers import _compliance_log

            _compliance_log(
                {
                    "event_type": "injection",
                    "stratum": os.environ.get("CLAUDE_MPM_COMPLIANCE_STRATUM"),
                }
            )

        log_files = list(log_dir.glob("agent-teams-*.jsonl"))
        record = json.loads(log_files[0].read_text().strip())
        assert record["stratum"] == "medium"


class TestComplianceLogEventHandlerIntegration:
    """Test that event handlers call _compliance_log correctly."""

    def _create_event_handlers(self, injector_enabled: bool = True):
        """Create EventHandlers with a mock hook_handler."""
        mock_handler = MagicMock()
        mock_handler._git_branch_cache = {}
        mock_handler._git_branch_cache_time = {}
        mock_handler._emit_socketio_event = MagicMock()
        mock_handler.auto_pause_handler = None

        from claude_mpm.hooks.claude_hooks.event_handlers import EventHandlers
        from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
            TeammateContextInjector,
        )

        handlers = EventHandlers(mock_handler)
        handlers._teammate_injector = TeammateContextInjector(enabled=injector_enabled)
        return handlers

    @patch("claude_mpm.hooks.claude_hooks.event_handlers._compliance_log")
    def test_pretooluse_calls_compliance_log_on_injection(self, mock_compliance_log):
        """PreToolUse calls _compliance_log when injection fires."""
        handlers = self._create_event_handlers(injector_enabled=True)

        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": "research",
                "prompt": "Investigate X",
                "team_name": "my-team",
                "name": "auth-researcher",
            },
            "session_id": "test-session",
            "cwd": "/tmp/test",
        }

        handlers.handle_pre_tool_fast(event)

        mock_compliance_log.assert_called_once()
        record = mock_compliance_log.call_args[0][0]
        assert record["event_type"] == "injection"
        assert record["team_name"] == "my-team"
        assert record["subagent_type"] == "research"
        assert record["injection_applied"] is True

    @patch("claude_mpm.hooks.claude_hooks.event_handlers._compliance_log")
    def test_pretooluse_no_compliance_log_without_injection(self, mock_compliance_log):
        """PreToolUse does NOT call _compliance_log for non-team Agent calls."""
        handlers = self._create_event_handlers(injector_enabled=True)

        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": "research",
                "prompt": "Investigate X",
            },
            "session_id": "test-session",
            "cwd": "/tmp/test",
        }

        handlers.handle_pre_tool_fast(event)

        mock_compliance_log.assert_not_called()

    @patch("claude_mpm.hooks.claude_hooks.event_handlers._compliance_log")
    def test_task_completed_calls_compliance_log(self, mock_compliance_log):
        """TaskCompleted handler calls _compliance_log."""
        handlers = self._create_event_handlers()

        event = {
            "hook_event_name": "TaskCompleted",
            "session_id": "test-session",
            "cwd": "/tmp/test",
            "task_id": "task-42",
            "task_title": "Research auth",
            "completed_by": "auth-researcher",
            "status": "completed",
        }

        handlers.handle_task_completed_fast(event)

        mock_compliance_log.assert_called_once()
        record = mock_compliance_log.call_args[0][0]
        assert record["event_type"] == "task_completed"
        assert record["task_id"] == "task-42"
        assert record["completed_by"] == "auth-researcher"
