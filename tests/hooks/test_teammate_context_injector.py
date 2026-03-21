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
    TEAMMATE_PROTOCOL_BASE,
    TEAMMATE_PROTOCOL_ENGINEER,
    TEAMMATE_PROTOCOL_QA,
    TEAMMATE_PROTOCOL_RESEARCH,
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

        assert TEAMMATE_PROTOCOL_BASE in result["prompt"]
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
        assert TEAMMATE_PROTOCOL_BASE in result_empty["prompt"]

        # Missing prompt key entirely
        tool_input_missing = {
            "subagent_type": "research",
            "team_name": "my-team",
        }
        result_missing = injector.inject_context(tool_input_missing)
        assert TEAMMATE_PROTOCOL_BASE in result_missing["prompt"]

    def test_tool_input_not_mutated(self):
        """Original tool_input dict is not modified -- inject_context returns a copy."""
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

    def test_protocol_content_base(self):
        """Base protocol headings appear; QA Scope Honesty is NOT in base injection."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "research",
            "prompt": "Investigate the auth module",
            "team_name": "my-team",
        }

        result = injector.inject_context(tool_input)
        prompt = result["prompt"]

        # Base headings must be present
        assert "Evidence-Based Completion" in prompt
        assert "File Change Manifest" in prompt
        assert "Self-Execution" in prompt
        assert "No Peer Delegation" in prompt
        # QA Scope Honesty removed from base in Phase 2
        assert "QA Scope Honesty" not in prompt

    def test_protocol_content_engineer(self):
        """Engineer injection contains base + Engineer Rules + QA-not-performed."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "engineer",
            "prompt": "Implement the feature",
            "team_name": "my-team",
        }

        result = injector.inject_context(tool_input)
        prompt = result["prompt"]

        # Base headings
        assert "Evidence-Based Completion" in prompt
        assert "File Change Manifest" in prompt
        # Engineer-specific
        assert "Engineer Rules" in prompt
        assert "QA verification has not been performed" in prompt

    def test_protocol_content_qa(self):
        """QA injection contains base + QA Rules + verification layer."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "qa",
            "prompt": "Verify the feature",
            "team_name": "my-team",
        }

        result = injector.inject_context(tool_input)
        prompt = result["prompt"]

        # Base headings
        assert "Evidence-Based Completion" in prompt
        assert "File Change Manifest" in prompt
        # QA-specific
        assert "QA Rules" in prompt
        assert "You ARE the QA verification layer" in prompt

    def test_protocol_content_research(self):
        """Research injection contains base + Research Rules + no source code modification."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "research",
            "prompt": "Investigate the auth module",
            "team_name": "my-team",
        }

        result = injector.inject_context(tool_input)
        prompt = result["prompt"]

        # Base headings
        assert "Evidence-Based Completion" in prompt
        assert "File Change Manifest" in prompt
        # Research-specific
        assert "Research Rules" in prompt
        assert "Do not modify source code" in prompt

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

    def test_engineer_role_gets_base_and_addendum(self):
        """Non-research subagent_type in Agent Teams call gets base + appropriate addendum."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "engineer",
            "prompt": "Build the feature",
            "team_name": "my-team",
        }

        result = injector.inject_context(tool_input)

        # Base protocol is injected
        assert TEAMMATE_PROTOCOL_BASE in result["prompt"]
        # Engineer addendum content is present
        assert "Engineer Rules" in result["prompt"]
        assert "Build the feature" in result["prompt"]

    def test_injection_proceeds_despite_non_research_role(self):
        """Protocol injection proceeds for any subagent_type -- base always present."""
        injector = TeammateContextInjector(enabled=True)

        for role in ["engineer", "qa", "Engineer", "QA", "unknown", ""]:
            tool_input = {
                "subagent_type": role,
                "prompt": f"Task for {role}",
                "team_name": "my-team",
            }
            result = injector.inject_context(tool_input)
            assert TEAMMATE_PROTOCOL_BASE in result["prompt"], (
                f"Base protocol not injected for subagent_type='{role}'"
            )

    def test_protocol_matches_source_of_truth(self):
        """TEAMMATE_PROTOCOL_BASE constant matches TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 3."""
        protocol_doc = Path(__file__).parent.parent.parent / (
            "docs-local/mpm-agent-teams/02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md"
        )
        if not protocol_doc.exists():
            pytest.skip("TEAM_CIRCUIT_BREAKER_PROTOCOL.md not in workspace")

        content = protocol_doc.read_text()
        # Phase 2: base has 4 rules (QA Scope Honesty removed from base)
        for rule_heading in [
            "Evidence-Based Completion",
            "File Change Manifest",
            "Self-Execution",
            "No Peer Delegation",
        ]:
            assert rule_heading in content, (
                f"Rule '{rule_heading}' not found in TEAM_CIRCUIT_BREAKER_PROTOCOL.md -- "
                f"TEAMMATE_PROTOCOL_BASE may be out of sync with source of truth"
            )

    def test_qa_scope_in_engineer_addendum(self):
        """QA Scope Honesty content moved to engineer addendum in Phase 2."""
        # The engineer addendum contains the QA-not-performed declaration
        assert "QA verification has not been performed" in TEAMMATE_PROTOCOL_ENGINEER
        # The base no longer contains QA Scope Honesty
        assert "QA Scope Honesty" not in TEAMMATE_PROTOCOL_BASE


class TestPhase2RoleAddenda:
    """Phase 2: Role-specific protocol addenda tests."""

    def test_engineer_addendum_injected(self):
        """Engineer subagent_type gets base + engineer addendum."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "engineer",
            "prompt": "Build it",
            "team_name": "my-team",
        }
        result = injector.inject_context(tool_input)
        prompt = result["prompt"]

        assert TEAMMATE_PROTOCOL_BASE in prompt
        assert TEAMMATE_PROTOCOL_ENGINEER in prompt

    def test_qa_addendum_injected(self):
        """QA subagent_type gets base + QA addendum."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "qa",
            "prompt": "Test it",
            "team_name": "my-team",
        }
        result = injector.inject_context(tool_input)
        prompt = result["prompt"]

        assert TEAMMATE_PROTOCOL_BASE in prompt
        assert TEAMMATE_PROTOCOL_QA in prompt

    def test_research_addendum_injected(self):
        """Research subagent_type gets base + research addendum."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "research",
            "prompt": "Investigate it",
            "team_name": "my-team",
        }
        result = injector.inject_context(tool_input)
        prompt = result["prompt"]

        assert TEAMMATE_PROTOCOL_BASE in prompt
        assert TEAMMATE_PROTOCOL_RESEARCH in prompt

    def test_unknown_role_gets_base_only(self):
        """Unknown subagent_type gets base protocol without any addendum."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": "unknown",
            "prompt": "Do something",
            "team_name": "my-team",
        }
        result = injector.inject_context(tool_input)
        prompt = result["prompt"]

        assert TEAMMATE_PROTOCOL_BASE in prompt
        # No role-specific addendum
        assert "Engineer Rules" not in prompt
        assert "QA Rules" not in prompt
        assert "Research Rules" not in prompt

    def test_role_routing_case_insensitive(self):
        """'Engineer' and 'engineer' both route to engineer addendum."""
        injector = TeammateContextInjector(enabled=True)

        for role in ["Engineer", "engineer", "ENGINEER"]:
            tool_input = {
                "subagent_type": role,
                "prompt": "Build it",
                "team_name": "my-team",
            }
            result = injector.inject_context(tool_input)
            assert "Engineer Rules" in result["prompt"], (
                f"Engineer addendum not injected for subagent_type='{role}'"
            )

    def test_backward_compat_alias(self):
        """TEAMMATE_PROTOCOL constant still importable and contains base text."""
        assert TEAMMATE_PROTOCOL is TEAMMATE_PROTOCOL_BASE
        assert "MPM Teammate Protocol" in TEAMMATE_PROTOCOL
        assert "Evidence-Based Completion" in TEAMMATE_PROTOCOL

    def test_token_budget_engineer(self):
        """Base + engineer addendum stays under 2000 chars (~500 tokens)."""
        combined = TEAMMATE_PROTOCOL_BASE + "\n\n" + TEAMMATE_PROTOCOL_ENGINEER
        assert len(combined) < 2000, (
            f"Base + engineer addendum is {len(combined)} chars, exceeds 2000 char budget"
        )

    def test_token_budget_qa(self):
        """Base + QA addendum stays under 2000 chars (~500 tokens)."""
        combined = TEAMMATE_PROTOCOL_BASE + "\n\n" + TEAMMATE_PROTOCOL_QA
        assert len(combined) < 2000, (
            f"Base + QA addendum is {len(combined)} chars, exceeds 2000 char budget"
        )

    def test_token_budget_research(self):
        """Base + research addendum stays under 2000 chars (~500 tokens)."""
        combined = TEAMMATE_PROTOCOL_BASE + "\n\n" + TEAMMATE_PROTOCOL_RESEARCH
        assert len(combined) < 2000, (
            f"Base + research addendum is {len(combined)} chars, exceeds 2000 char budget"
        )

    def test_base_does_not_contain_qa_scope_rule(self):
        """Rule 3 (QA Scope Honesty) removed from base protocol."""
        assert "QA Scope Honesty" not in TEAMMATE_PROTOCOL_BASE
        # Verify base has 4 rules, not 5
        assert "Rule 1:" in TEAMMATE_PROTOCOL_BASE
        assert "Rule 2:" in TEAMMATE_PROTOCOL_BASE
        assert "Rule 3:" in TEAMMATE_PROTOCOL_BASE
        assert "Rule 4:" in TEAMMATE_PROTOCOL_BASE
        assert "Rule 5:" not in TEAMMATE_PROTOCOL_BASE

    def test_engineer_contains_qa_not_performed(self):
        """Engineer addendum includes QA-not-performed declaration."""
        assert "QA verification has not been performed" in TEAMMATE_PROTOCOL_ENGINEER

    def test_engineer_contains_commit_instruction(self):
        """Engineer addendum includes commit instruction with git commands."""
        assert "MUST commit your changes" in TEAMMATE_PROTOCOL_ENGINEER
        assert "git add" in TEAMMATE_PROTOCOL_ENGINEER
        assert "git commit" in TEAMMATE_PROTOCOL_ENGINEER

    def test_qa_contains_verification_layer(self):
        """QA addendum includes 'you ARE the QA verification layer'."""
        assert "You ARE the QA verification layer" in TEAMMATE_PROTOCOL_QA

    def test_subagent_type_none_handled(self):
        """subagent_type=None in tool_input does not crash."""
        injector = TeammateContextInjector(enabled=True)
        tool_input = {
            "subagent_type": None,
            "prompt": "Do something",
            "team_name": "my-team",
        }
        result = injector.inject_context(tool_input)
        assert "MPM Teammate Protocol" in result["prompt"]
        assert "Engineer Rules" not in result["prompt"]
        assert "QA Rules" not in result["prompt"]
        assert "Research Rules" not in result["prompt"]


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
        assert TEAMMATE_PROTOCOL_BASE in result["prompt"]
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
