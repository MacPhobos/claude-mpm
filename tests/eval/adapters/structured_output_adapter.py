"""Structured output adapter for Tier 2 delegation intent tests.

Wraps `claude -p` subprocess calls with --json-schema and --tools ""
to capture delegation intent without executing any tools.
"""

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

DELEGATION_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {
            "would_delegate": {
                "type": "boolean",
                "description": "Whether the PM would delegate this task to a specialist agent",
            },
            "target_agent": {
                "type": "string",
                "description": "The agent type to delegate to (e.g., 'research', 'engineer', 'local-ops', 'qa')",
            },
            "delegation_reasoning": {
                "type": "string",
                "description": "Why this agent was selected, referencing specific PM instructions",
            },
            "would_handle_directly": {
                "type": "boolean",
                "description": "Whether the PM would handle this directly per cost-conscious exceptions",
            },
            "direct_handling_justification": {
                "type": "string",
                "description": "If handling directly, which PM instruction permits it",
            },
        },
        "required": ["would_delegate", "target_agent", "delegation_reasoning"],
    }
)


class DelegationTestError(Exception):
    """Actual delegation regression - the PM made a wrong decision."""


class InfrastructureError(Exception):
    """API/network/auth failure - not a delegation bug."""


class DelegationIntentResult:
    """Result from a delegation intent query."""

    def __init__(
        self,
        delegation: Dict[str, Any],
        session_id: Optional[str],
        raw_output: Dict[str, Any],
        elapsed_seconds: float,
        cost_usd: Optional[float] = None,
    ):
        self.delegation = delegation
        self.session_id = session_id
        self.raw_output = raw_output
        self.elapsed_seconds = elapsed_seconds
        self.cost_usd = cost_usd

    @property
    def would_delegate(self) -> bool:
        return self.delegation.get("would_delegate", False)

    @property
    def target_agent(self) -> str:
        return self.delegation.get("target_agent", "").lower().replace(" ", "-")

    @property
    def reasoning(self) -> str:
        return self.delegation.get("delegation_reasoning", "")

    @property
    def would_handle_directly(self) -> bool:
        return self.delegation.get("would_handle_directly", False)


class StructuredOutputAdapter:
    """Test adapter using claude -p with --json-schema to capture delegation intent.

    Uses --tools "" to disable all tools (preventing execution) and
    --json-schema to force structured JSON output describing what the PM
    WOULD delegate without actually delegating.
    """

    def __init__(
        self,
        system_prompt_file: Optional[str] = None,
        max_budget_usd: float = 0.50,
        timeout: int = 30,
    ):
        self.system_prompt_file = system_prompt_file or self._default_prompt_file()
        self.max_budget_usd = max_budget_usd
        self.timeout = timeout
        self._invocation_count = 0
        self._total_cost = 0.0

    def _default_prompt_file(self) -> str:
        """Use cached PM instructions, or generate fresh via FrameworkLoader."""
        cached = Path(".claude-mpm/PM_INSTRUCTIONS.md")
        if cached.exists():
            return str(cached)
        # Fall back to generating fresh
        from claude_mpm.core.framework_loader import FrameworkLoader

        loader = FrameworkLoader(config={"validate_api_keys": False})
        content = loader.get_framework_instructions()
        cached.parent.mkdir(parents=True, exist_ok=True)
        cached.write_text(content)
        return str(cached)

    def query_delegation_intent(self, user_prompt: str) -> DelegationIntentResult:
        """Ask Claude PM who it would delegate to for this prompt.

        Args:
            user_prompt: The simulated user request

        Returns:
            DelegationIntentResult with structured delegation decision

        Raises:
            InfrastructureError: API/network/auth problems (not a test failure)
            DelegationTestError: Invalid response format (potential regression)
        """
        if not shutil.which("claude"):
            raise InfrastructureError("claude CLI not found in PATH")

        cmd = [
            "claude",
            "-p",
            "--output-format",
            "json",
            "--json-schema",
            DELEGATION_SCHEMA,
            "--tools",
            "",  # Disable all tools
            "--max-budget-usd",
            str(self.max_budget_usd),
            "--append-system-prompt-file",
            self.system_prompt_file,
            "--no-session-persistence",
            user_prompt,
        ]

        env = os.environ.copy()
        env.pop("CLAUDECODE", None)  # Prevent nested session error
        env["CI"] = "true"
        env["DISABLE_TELEMETRY"] = "1"

        start = time.monotonic()
        try:
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
            )
        except subprocess.TimeoutExpired as err:
            raise InfrastructureError(
                f"claude -p timed out after {self.timeout}s"
            ) from err

        elapsed = time.monotonic() - start
        self._invocation_count += 1

        if result.returncode != 0:
            stderr = result.stderr.strip()
            if "rate limit" in stderr.lower():
                raise InfrastructureError(f"Rate limited: {stderr}")
            if "authentication" in stderr.lower() or "api key" in stderr.lower():
                raise InfrastructureError(f"Auth error: {stderr}")
            raise InfrastructureError(
                f"claude -p failed (rc={result.returncode}): {stderr[:500]}"
            )

        try:
            output = json.loads(result.stdout.strip())
        except json.JSONDecodeError as err:
            raise DelegationTestError(
                f"Invalid JSON output from claude -p: {result.stdout[:500]}"
            ) from err

        # Extract structured_output from JSON response envelope
        structured = output.get("structured_output", output)

        # Extract cost if available
        cost = output.get("cost_usd") or output.get("usage", {}).get("cost_usd")
        if cost:
            self._total_cost += cost

        return DelegationIntentResult(
            delegation=structured,
            session_id=output.get("session_id"),
            raw_output=output,
            elapsed_seconds=elapsed,
            cost_usd=cost,
        )

    def query_with_consensus(
        self, user_prompt: str, required_agreement: int = 2, max_attempts: int = 3
    ) -> DelegationIntentResult:
        """Query with 2-of-3 consensus for LLM variance resilience.

        Runs up to max_attempts queries. Returns the first result that achieves
        required_agreement matching agent selections.

        Args:
            user_prompt: The simulated user request
            required_agreement: Number of matching results needed (default: 2)
            max_attempts: Maximum number of queries (default: 3)

        Returns:
            The consensus DelegationIntentResult

        Raises:
            DelegationTestError: No consensus reached after max_attempts
            InfrastructureError: All attempts failed due to infra issues
        """
        results: List[DelegationIntentResult] = []
        infra_errors: List[str] = []

        for i in range(max_attempts):
            try:
                result = self.query_delegation_intent(user_prompt)
                results.append(result)

                # Check if we have consensus
                agent_counts: Dict[str, List[DelegationIntentResult]] = {}
                for r in results:
                    key = r.target_agent if r.would_delegate else "__direct__"
                    agent_counts.setdefault(key, []).append(r)

                for agent, matching in agent_counts.items():
                    if len(matching) >= required_agreement:
                        return matching[0]  # Return first matching result

            except InfrastructureError as e:
                infra_errors.append(str(e))

        if not results:
            raise InfrastructureError(
                f"All {max_attempts} attempts failed: {'; '.join(infra_errors)}"
            )

        # No consensus - report what we got
        agents_seen = [r.target_agent for r in results]
        raise DelegationTestError(
            f"No consensus after {max_attempts} attempts. "
            f"Agents seen: {agents_seen}. "
            f"Prompt: '{user_prompt[:100]}...'"
        )

    @property
    def stats(self) -> Dict[str, Any]:
        """Return invocation statistics."""
        return {
            "invocation_count": self._invocation_count,
            "total_cost_usd": self._total_cost,
            "avg_cost_usd": self._total_cost / max(self._invocation_count, 1),
        }
