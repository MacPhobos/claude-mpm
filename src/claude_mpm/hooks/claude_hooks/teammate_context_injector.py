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
# Last synced: 2026-03-20 (Phase 2 role-aware routing)
# Token budget: base ~330 tokens, base+addendum <500 tokens each role
TEAMMATE_PROTOCOL_BASE = """\
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
Omit nothing. The team lead will cross-reference against your commit.

### Rule 3: Self-Execution (CB#9)
Execute all work yourself using available tools. Never instruct the user or any teammate to run commands on your behalf.

### Rule 4: No Peer Delegation
Do NOT delegate your assigned task to another teammate via SendMessage. Do NOT orchestrate multi-step workflows with other teammates. If you cannot complete your task, report the blocker to the team lead -- do not ask a peer to do it. You have ONE task. Complete it and report results to the team lead."""

TEAMMATE_PROTOCOL_ENGINEER = """\
### Engineer Rules
- You MUST state "QA verification has not been performed" when reporting completion. Do NOT claim your work is fully verified.
- Declare intended file scope BEFORE starting work. Do not modify files outside that scope.
- Run linting/formatting checks before reporting completion.
- You MUST commit your changes with a descriptive message before reporting completion. Use: git add <your-files> && git commit -m "feat: <description>"
- Include git diff summary (files changed, insertions, deletions) in your completion report.
- You are in an isolated worktree. Do not modify files in the main working tree."""

TEAMMATE_PROTOCOL_QA = """\
### QA Rules
- You ARE the QA verification layer. Your evidence must be independent of the Engineer's claims.
- Run tests in a clean state (no uncommitted changes from your own edits).
- Report the full test command AND its complete output, not just pass/fail counts.
- When verifying an Engineer's work, explicitly state which Engineer and which files you are verifying.
- Test against the MERGED code when verifying work from multiple Engineers."""

TEAMMATE_PROTOCOL_RESEARCH = """\
### Research Rules
- Do not modify source code files. Your deliverable is analysis, not implementation.
- Cite specific file paths and line numbers for every claim about the codebase."""

_ROLE_ADDENDA = {
    "engineer": TEAMMATE_PROTOCOL_ENGINEER,
    "engineer-agent": TEAMMATE_PROTOCOL_ENGINEER,
    "qa": TEAMMATE_PROTOCOL_QA,
    "qa-agent": TEAMMATE_PROTOCOL_QA,
    "research": TEAMMATE_PROTOCOL_RESEARCH,
    "research-agent": TEAMMATE_PROTOCOL_RESEARCH,
}

# Backward-compat alias: TEAMMATE_PROTOCOL still importable.
# Phase 2 changed: this now points to the base (Rule 3 removed, renumbered).
TEAMMATE_PROTOCOL = TEAMMATE_PROTOCOL_BASE


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
        """Prepend role-appropriate TEAMMATE_PROTOCOL to the prompt in tool_input.

        Creates a shallow copy of tool_input and modifies the prompt field.
        The original dict is NOT mutated.

        Assembles protocol from TEAMMATE_PROTOCOL_BASE plus the role-specific
        addendum determined by subagent_type. Unknown roles get base only.

        Args:
            tool_input: The Agent tool's input parameters.

        Returns:
            A new dict with the protocol prepended to prompt.
        """
        modified = copy.copy(tool_input)

        team_name = tool_input.get("team_name", "")
        subagent_type = tool_input.get("subagent_type") or "unknown"

        # Build role-appropriate protocol
        protocol = TEAMMATE_PROTOCOL_BASE
        addendum = _ROLE_ADDENDA.get(subagent_type.lower(), "")
        if addendum:
            protocol += "\n\n" + addendum

        # Log injection details
        _log(
            f"TeammateContextInjector: Injected protocol "
            f"(team_name={team_name}, subagent_type={subagent_type}, "
            f"addendum={'yes' if addendum else 'none'})"
        )

        original_prompt = tool_input.get("prompt") or ""
        modified["prompt"] = protocol + "\n\n---\n\n" + original_prompt
        return modified
