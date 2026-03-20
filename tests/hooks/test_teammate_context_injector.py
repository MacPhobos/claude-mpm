#!/usr/bin/env python3
"""Tests for TeammateContextInjector.

Validates that MPM behavioral protocols are correctly injected into
teammate prompts when the PM spawns teammates via Agent tool with team_name.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from claude_mpm.hooks.claude_hooks.teammate_context_injector import (
    TEAMMATE_PROTOCOL,
    TeammateContextInjector,
)


class TestTeammateContextInjector:
    """Unit tests for TeammateContextInjector."""

    def test_injection_when_team_name_present(self):
        """Agent call with team_name gets protocol injected into prompt."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "research",
            "prompt": "Investigate the auth module",
            "team_name": "my-team",
        }

        result = injector.inject_context(tool_input)

        assert TEAMMATE_PROTOCOL in result["prompt"]
        assert "Investigate the auth module" in result["prompt"]

    def test_no_injection_when_team_name_absent(self):
        """Regular Agent call without team_name should not trigger injection."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "research",
            "prompt": "Investigate the auth module",
        }

        assert injector.should_inject("Agent", tool_input) is False

    def test_no_injection_when_not_agent_tool(self):
        """Non-Agent tools should not trigger injection."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "command": "ls -la",
            "team_name": "my-team",
        }

        assert injector.should_inject("Bash", tool_input) is False
        assert injector.should_inject("Read", tool_input) is False
        assert injector.should_inject("Write", tool_input) is False
        assert injector.should_inject("Task", tool_input) is False

    def test_feature_flag_disabled(self):
        """When disabled, should_inject returns False even for valid Agent+team_name."""
        injector = TeammateContextInjector(enabled=False)
        tool_input = {
            "subagent_type": "research",
            "prompt": "Investigate the auth module",
            "team_name": "my-team",
        }

        assert injector.should_inject("Agent", tool_input) is False
        assert injector.is_enabled() is False

    def test_feature_flag_enabled(self):
        """When enabled, should_inject returns True for Agent+team_name."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "research",
            "prompt": "Investigate the auth module",
            "team_name": "my-team",
        }

        assert injector.should_inject("Agent", tool_input) is True
        assert injector.is_enabled() is True

    def test_feature_flag_from_env_enabled(self, monkeypatch):
        """When env var CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION=1, injection is enabled."""
        monkeypatch.setenv("CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION", "1")
        injector = TeammateContextInjector()

        assert injector.is_enabled() is True

    def test_feature_flag_from_env_disabled(self, monkeypatch):
        """When env var is '0' or unset, injection is disabled."""
        monkeypatch.setenv("CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION", "0")
        injector = TeammateContextInjector()

        assert injector.is_enabled() is False

    def test_feature_flag_from_env_unset(self, monkeypatch):
        """When env var is not set at all, injection defaults to disabled."""
        monkeypatch.delenv("CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION", raising=False)
        monkeypatch.delenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", raising=False)
        injector = TeammateContextInjector()

        assert injector.is_enabled() is False

    def test_auto_detect_agent_teams_env(self, monkeypatch):
        """Injection enables automatically when Agent Teams env var is set."""
        monkeypatch.delenv("CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION", raising=False)
        monkeypatch.setenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "1")
        injector = TeammateContextInjector()
        assert injector.is_enabled()

    def test_manual_override_disables_over_auto_detect(self, monkeypatch):
        """Manual override can disable even when Agent Teams is active."""
        monkeypatch.setenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "1")
        monkeypatch.setenv("CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION", "0")
        injector = TeammateContextInjector()
        assert not injector.is_enabled()

    def test_no_env_vars_disabled(self, monkeypatch):
        """Injection disabled when no env vars are set."""
        monkeypatch.delenv("CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION", raising=False)
        monkeypatch.delenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", raising=False)
        injector = TeammateContextInjector()
        assert not injector.is_enabled()

    def test_original_prompt_preserved(self):
        """Original prompt text appears after protocol in the injected prompt."""
        injector = TeammateContextInjector(enabled=True)
        original_prompt = "Research the payment gateway integration patterns"
        tool_input = {
            "subagent_type": "research",
            "prompt": original_prompt,
            "team_name": "my-team",
        }

        result = injector.inject_context(tool_input)

        # Protocol comes first, then separator, then original prompt
        protocol_end = result["prompt"].index("---\n\n")
        original_start = result["prompt"].index(original_prompt)
        assert original_start > protocol_end

    def test_empty_prompt_handled(self):
        """If prompt is empty or None, protocol is still injected."""
        injector = TeammateContextInjector(enabled=True)

        # Empty string prompt
        tool_input_empty = {
            "subagent_type": "research",
            "prompt": "",
            "team_name": "my-team",
        }
        result_empty = injector.inject_context(tool_input_empty)
        assert TEAMMATE_PROTOCOL in result_empty["prompt"]

        # Missing prompt key entirely
        tool_input_missing = {
            "subagent_type": "research",
            "team_name": "my-team",
        }
        result_missing = injector.inject_context(tool_input_missing)
        assert TEAMMATE_PROTOCOL in result_missing["prompt"]

    def test_tool_input_not_mutated(self):
        """Original tool_input dict is not modified — inject_context returns a copy."""
        injector = TeammateContextInjector(enabled=True)
        original_prompt = "Investigate the auth module"
        tool_input = {
            "subagent_type": "research",
            "prompt": original_prompt,
            "team_name": "my-team",
        }

        result = injector.inject_context(tool_input)

        # Original is unchanged
        assert tool_input["prompt"] == original_prompt
        # Result is different
        assert result["prompt"] != original_prompt
        assert result is not tool_input

    def test_protocol_content_present(self):
        """Key phrases from TEAMMATE_PROTOCOL appear in the injected prompt."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "engineer",
            "prompt": "Implement the feature",
            "team_name": "my-team",
        }

        result = injector.inject_context(tool_input)
        prompt = result["prompt"]

        # Key behavioral phrases must be present
        assert "MPM Teammate Protocol" in prompt
        assert "Evidence-Based Completion" in prompt
        assert "File Change Manifest" in prompt
        assert "QA Scope Honesty" in prompt
        assert "Self-Execution" in prompt
        assert "No Peer Delegation" in prompt
        assert "FORBIDDEN phrases" in prompt

    def test_should_inject_with_invalid_tool_input(self):
        """should_inject handles non-dict tool_input gracefully."""
        injector = TeammateContextInjector(enabled=True)

        assert injector.should_inject("Agent", None) is False
        assert injector.should_inject("Agent", "string") is False
        assert injector.should_inject("Agent", []) is False

    def test_other_tool_input_fields_preserved(self):
        """All other fields in tool_input are preserved in the result."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "engineer",
            "prompt": "Build the thing",
            "team_name": "my-team",
            "model": "sonnet",
            "run_in_background": True,
            "description": "Build the thing",
        }

        result = injector.inject_context(tool_input)

        assert result["subagent_type"] == "engineer"
        assert result["team_name"] == "my-team"
        assert result["model"] == "sonnet"
        assert result["run_in_background"] is True
        assert result["description"] == "Build the thing"


class TestPreToolUseIntegration:
    """Integration test: TeammateContextInjector wired into EventHandlers."""

    def _create_event_handlers(self, injector_enabled: bool = True):
        """Create EventHandlers with a mock hook_handler and controlled injector."""
        mock_handler = MagicMock()
        mock_handler._git_branch_cache = {}
        mock_handler._git_branch_cache_time = {}
        mock_handler._emit_socketio_event = MagicMock()
        mock_handler.auto_pause_handler = None

        from claude_mpm.hooks.claude_hooks.event_handlers import EventHandlers

        handlers = EventHandlers(mock_handler)
        # Override the injector with controlled enabled state
        handlers._teammate_injector = TeammateContextInjector(enabled=injector_enabled)
        return handlers

    def test_pretooluse_returns_modified_input_for_agent_teams(self):
        """PreToolUse handler returns modified tool_input when Agent+team_name."""
        handlers = self._create_event_handlers(injector_enabled=True)

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

        result = handlers.handle_pre_tool_fast(event)

        assert result is not None
        assert TEAMMATE_PROTOCOL in result["prompt"]
        assert "Investigate X" in result["prompt"]

    def test_pretooluse_returns_none_for_regular_agent(self):
        """PreToolUse handler returns None for regular Agent calls (no team_name)."""
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

        result = handlers.handle_pre_tool_fast(event)

        assert result is None

    def test_pretooluse_returns_none_for_non_agent_tools(self):
        """PreToolUse handler returns None for non-Agent tools."""
        handlers = self._create_event_handlers(injector_enabled=True)

        event = {
            "hook_event_name": "PreToolUse",
            "tool_name": "Bash",
            "tool_input": {
                "command": "ls -la",
            },
            "session_id": "test-session",
            "cwd": "/tmp/test",
        }

        result = handlers.handle_pre_tool_fast(event)

        assert result is None

    def test_pretooluse_no_injection_when_disabled(self):
        """PreToolUse handler does not inject when feature flag is disabled."""
        handlers = self._create_event_handlers(injector_enabled=False)

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

        result = handlers.handle_pre_tool_fast(event)

        assert result is None
