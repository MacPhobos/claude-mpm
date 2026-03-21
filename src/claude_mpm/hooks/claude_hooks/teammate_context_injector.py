"""Teammate context injection for Agent Teams integration.

Injects MPM behavioral protocols into teammate prompts when the PM
spawns teammates via the Agent tool with team_name parameter.

Activation (precedence order):
1. Constructor `enabled` parameter (for tests)
2. CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION env var (manual override: "1"/"0")
3. CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS env var (auto-detect: "1" enables)
4. Default: disabled
"""

import copy
import os

# Import _log helper to avoid stderr writes (which cause hook errors)
try:
    from .hook_handler import _log
except ImportError:
    # Fallback for direct execution or testing
    def _log(message: str) -> None:
        """Fallback logger when hook_handler not available."""


# SYNC: This block must match TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 3.
# Source of truth: docs-local/mpm-agent-teams/02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md
# Last synced: 2026-03-20 (Phase 1 production)
# Token budget: ~421 tokens (max 500)
TEAMMATE_PROTOCOL = """\
## MPM Teammate Protocol

You are operating as a teammate in an MPM-managed Agent Teams session. The team lead (PM) assigned you this task. Follow these rules strictly.

### Rule 1: Evidence-Based Completion (CB#3)
When reporting task completion, you MUST include:
- Specific commands you executed and their actual output
- File paths and line numbers of all changes made
- Test results with pass/fail counts (if applicable)
FORBIDDEN phrases: "should work", "appears to be working", "looks correct", "I believe this fixes". Use only verified facts.

### Rule 2: File Change Manifest (CB#4)
Before reporting completion, list ALL files you created, modified, or deleted:
- File path
- Action: created / modified / deleted
- One-line summary of the change
Omit nothing. The team lead will cross-reference against git status.

### Rule 3: QA Scope Honesty (CB#8)
If your role is implementation (not QA), you MUST state: "QA verification has not been performed" when reporting completion. Do NOT claim your work is fully verified unless you independently ran tests and included results per Rule 1.

### Rule 4: Self-Execution (CB#9)
Execute all work yourself using available tools. Never instruct the user or any teammate to run commands on your behalf.

### Rule 5: No Peer Delegation
Do NOT delegate your assigned task to another teammate via SendMessage. Do NOT orchestrate multi-step workflows with other teammates. If you cannot complete your task, report the blocker to the team lead — do not ask a peer to do it. You have ONE task. Complete it and report results to the team lead."""


class TeammateContextInjector:
    """Injects MPM behavioral protocols into teammate prompts at spawn time.

    Uses the PreToolUse hook on Agent tool calls to prepend a lightweight
    teammate protocol to the prompt parameter when team_name is present,
    indicating an Agent Teams session.

    Activation precedence:
    1. Constructor `enabled` param (for tests)
    2. CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION env var (manual override)
    3. CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS env var (auto-detect)
    4. Default: disabled
    """

    def __init__(self, enabled: bool | None = None) -> None:
        """Initialize the injector.

        Args:
            enabled: Explicit enable/disable. If None, uses env var detection.
                     Precedence: constructor param > manual override > auto-detect > disabled.
        """
        if enabled is not None:
            self._enabled = enabled
        else:
            # Manual override takes precedence
            manual = os.environ.get("CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION")
            if manual is not None:
                self._enabled = manual == "1"
            else:
                # Auto-detect: enable when Agent Teams is active
                self._enabled = (
                    os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "0") == "1"
                )

    def is_enabled(self) -> bool:
        """Return whether context injection is enabled."""
        return self._enabled

    def should_inject(self, tool_name: str, tool_input: dict) -> bool:
        """Determine if context should be injected into this tool call.

        Returns True when:
        - The injector is enabled
        - tool_name is "Agent"
        - tool_input contains a team_name key (indicating Agent Teams spawn)

        Args:
            tool_name: The name of the tool being called.
            tool_input: The tool's input parameters.

        Returns:
            True if protocol should be injected.
        """
        if not self._enabled:
            return False
        if tool_name != "Agent":
            return False
        if not isinstance(tool_input, dict):
            return False
        return "team_name" in tool_input

    def inject_context(self, tool_input: dict) -> dict:
        """Prepend TEAMMATE_PROTOCOL to the prompt in tool_input.

        Creates a shallow copy of tool_input and modifies the prompt field.
        The original dict is NOT mutated.

        Also logs a warning if subagent_type is not "research" (Phase 1
        supports Research teammates only). Injection still proceeds — the
        hook cannot block tool calls.

        Args:
            tool_input: The Agent tool's input parameters.

        Returns:
            A new dict with the protocol prepended to prompt.
        """
        modified = copy.copy(tool_input)

        # Log role violations (non-research subagent_type in Agent Teams)
        # Injection still proceeds — hook API cannot block, only observe
        team_name = tool_input.get("team_name", "")
        subagent_type = tool_input.get("subagent_type", "unknown")
        if subagent_type not in ("research", "Research"):
            _log(
                f"[AGENT_TEAMS] WARNING: Non-research subagent_type '{subagent_type}' "
                f"in Agent Teams call (team_name={team_name}). "
                f"Phase 1 supports Research only. Injection proceeds."
            )

        original_prompt = tool_input.get("prompt") or ""
        modified["prompt"] = TEAMMATE_PROTOCOL + "\n\n---\n\n" + original_prompt
        _log(
            f"TeammateContextInjector: Injected protocol into Agent tool prompt "
            f"(team_name={tool_input.get('team_name')}, "
            f"subagent_type={subagent_type}, "
            f"original_prompt_len={len(original_prompt)}, "
            f"new_prompt_len={len(modified['prompt'])})"
        )
        return modified
