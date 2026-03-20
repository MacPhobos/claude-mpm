#!/usr/bin/env python3
"""Tests for Agent Teams event logging (Phase 1 production).

Validates that TeammateIdle, TaskCompleted, and PreToolUse handlers
log Agent Teams events via _log() when DEBUG mode is enabled.
Phase 0 used _validation_log() to /tmp/; Phase 1 uses standard _log().
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
    TeammateContextInjector,
)


def _create_event_handlers(injector_enabled: bool = False):
    """Create EventHandlers with a mock hook_handler."""
    mock_handler = MagicMock()
    mock_handler._git_branch_cache = {}
    mock_handler._git_branch_cache_time = {}
    mock_handler._emit_socketio_event = MagicMock()
    mock_handler.auto_pause_handler = None

    from claude_mpm.hooks.claude_hooks.event_handlers import EventHandlers

    handlers = EventHandlers(mock_handler)
    handlers._teammate_injector = TeammateContextInjector(enabled=injector_enabled)
    return handlers


class TestTeammateIdleLogging:
    """Test logging in handle_teammate_idle_fast."""

    @patch("claude_mpm.hooks.claude_hooks.event_handlers.DEBUG", True)
    @patch("claude_mpm.hooks.claude_hooks.event_handlers._log")
    def test_teammate_idle_logs_raw_event_in_debug(self, mock_log):
        """TeammateIdle handler logs raw event via _log when DEBUG is True."""
        handlers = _create_event_handlers()

        event = {
            "hook_event_name": "TeammateIdle",
            "session_id": "test-session-123",
            "cwd": "/tmp/test",
            "teammate_id": "teammate-abc",
            "teammate_type": "research",
            "reason": "waiting_for_input",
        }

        handlers.handle_teammate_idle_fast(event)

        # Check that _log was called with Agent Teams event info
        log_calls = [str(call) for call in mock_log.call_args_list]
        log_text = " ".join(log_calls)
        assert "AGENT_TEAMS" in log_text or "TeammateIdle" in log_text

    @patch("claude_mpm.hooks.claude_hooks.event_handlers.DEBUG", False)
    @patch("claude_mpm.hooks.claude_hooks.event_handlers._log")
    def test_teammate_idle_no_debug_log_when_debug_off(self, mock_log):
        """TeammateIdle raw event NOT logged when DEBUG is False."""
        handlers = _create_event_handlers()

        event = {
            "hook_event_name": "TeammateIdle",
            "session_id": "test-session-123",
            "cwd": "/tmp/test",
            "teammate_id": "teammate-abc",
            "teammate_type": "research",
            "reason": "waiting_for_input",
        }

        handlers.handle_teammate_idle_fast(event)

        # The raw event debug log should NOT fire, but INFO-level logs still may
        log_calls = [str(call) for call in mock_log.call_args_list]
        raw_event_calls = [
            c for c in log_calls if "AGENT_TEAMS" in c and "raw event" in c
        ]
        assert len(raw_event_calls) == 0

    def test_teammate_idle_emits_socketio(self):
        """TeammateIdle handler emits teammate_idle event to dashboard."""
        handlers = _create_event_handlers()

        event = {
            "hook_event_name": "TeammateIdle",
            "session_id": "s1",
            "cwd": "/tmp",
            "teammate_id": "r1",
            "teammate_type": "Research",
            "reason": "idle",
        }

        handlers.handle_teammate_idle_fast(event)

        handlers.hook_handler._emit_socketio_event.assert_called_once()
        call_args = handlers.hook_handler._emit_socketio_event.call_args
        assert call_args[0][1] == "teammate_idle"
        assert call_args[0][2]["teammate_id"] == "r1"


class TestTaskCompletedLogging:
    """Test logging in handle_task_completed_fast."""

    @patch("claude_mpm.hooks.claude_hooks.event_handlers.DEBUG", True)
    @patch("claude_mpm.hooks.claude_hooks.event_handlers._log")
    def test_task_completed_logs_raw_event_in_debug(self, mock_log):
        """TaskCompleted handler logs raw event via _log when DEBUG is True."""
        handlers = _create_event_handlers()

        event = {
            "hook_event_name": "TaskCompleted",
            "session_id": "test-session-789",
            "cwd": "/tmp/test",
            "task_id": "task-42",
            "task_title": "Implement auth module",
            "completed_by": "engineer-1",
            "status": "completed",
        }

        handlers.handle_task_completed_fast(event)

        log_calls = [str(call) for call in mock_log.call_args_list]
        log_text = " ".join(log_calls)
        assert "AGENT_TEAMS" in log_text or "TaskCompleted" in log_text

    @patch("claude_mpm.hooks.claude_hooks.event_handlers.DEBUG", False)
    @patch("claude_mpm.hooks.claude_hooks.event_handlers._log")
    def test_task_completed_no_debug_log_when_debug_off(self, mock_log):
        """TaskCompleted raw event NOT logged when DEBUG is False."""
        handlers = _create_event_handlers()

        event = {
            "hook_event_name": "TaskCompleted",
            "session_id": "test-session-789",
            "cwd": "/tmp/test",
            "task_id": "task-42",
            "task_title": "Implement auth module",
            "completed_by": "engineer-1",
            "status": "completed",
        }

        handlers.handle_task_completed_fast(event)

        log_calls = [str(call) for call in mock_log.call_args_list]
        raw_event_calls = [
            c for c in log_calls if "AGENT_TEAMS" in c and "raw event" in c
        ]
        assert len(raw_event_calls) == 0

    def test_task_completed_emits_socketio(self):
        """TaskCompleted handler emits task_completed event to dashboard."""
        handlers = _create_event_handlers()

        event = {
            "hook_event_name": "TaskCompleted",
            "session_id": "s1",
            "cwd": "/tmp",
            "task_id": "t1",
            "task_title": "Research auth",
            "completed_by": "r1",
            "status": "completed",
        }

        handlers.handle_task_completed_fast(event)

        handlers.hook_handler._emit_socketio_event.assert_called_once()
        call_args = handlers.hook_handler._emit_socketio_event.call_args
        assert call_args[0][1] == "task_completed"
        assert call_args[0][2]["task_id"] == "t1"


class TestPreToolUseAgentTeamsLogging:
    """Test Agent Teams logging in handle_pre_tool_fast."""

    @patch("claude_mpm.hooks.claude_hooks.event_handlers.DEBUG", True)
    @patch("claude_mpm.hooks.claude_hooks.event_handlers._log")
    def test_pretooluse_logs_agent_tool_with_team_name_in_debug(self, mock_log):
        """PreToolUse logs Agent tool interception when DEBUG is True."""
        handlers = _create_event_handlers(injector_enabled=True)

        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": "research",
                "prompt": "Investigate X",
                "team_name": "my-team",
            },
            "session_id": "test-session",
            "cwd": "/tmp/test",
        }

        handlers.handle_pre_tool_fast(event)

        log_calls = [str(call) for call in mock_log.call_args_list]
        log_text = " ".join(log_calls)
        assert "team_name_present=True" in log_text
        assert "context_injection_applied=True" in log_text

    @patch("claude_mpm.hooks.claude_hooks.event_handlers.DEBUG", True)
    @patch("claude_mpm.hooks.claude_hooks.event_handlers._log")
    def test_pretooluse_logs_agent_tool_without_team_name(self, mock_log):
        """PreToolUse logs Agent tool without team_name when DEBUG is True."""
        handlers = _create_event_handlers(injector_enabled=True)

        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Agent",
            "tool_input": {
                "subagent_type": "engineer",
                "prompt": "Build feature Y",
            },
            "session_id": "test-session",
            "cwd": "/tmp/test",
        }

        handlers.handle_pre_tool_fast(event)

        log_calls = [str(call) for call in mock_log.call_args_list]
        log_text = " ".join(log_calls)
        assert "team_name_present=False" in log_text
        assert "context_injection_applied=False" in log_text

    @patch("claude_mpm.hooks.claude_hooks.event_handlers.DEBUG", False)
    @patch("claude_mpm.hooks.claude_hooks.event_handlers._log")
    def test_pretooluse_no_agent_teams_log_for_non_agent_tools(self, mock_log):
        """PreToolUse does NOT log Agent Teams entries for non-Agent tools."""
        handlers = _create_event_handlers(injector_enabled=True)

        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {"command": "ls -la"},
            "session_id": "test-session",
            "cwd": "/tmp/test",
        }

        handlers.handle_pre_tool_fast(event)

        log_calls = [str(call) for call in mock_log.call_args_list]
        agent_teams_calls = [c for c in log_calls if "AGENT_TEAMS" in c]
        assert len(agent_teams_calls) == 0
