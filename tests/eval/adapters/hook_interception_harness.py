"""Hook interception harness for Tier 3 behavioral delegation tests.

Manages the lifecycle of a delegation interceptor hook inside a temporary
workspace so that ``claude-mpm run`` invocations have their Task/Agent
tool calls captured (and optionally blocked) before any sub-agent is
spawned.

The harness:
  1. Copies the interceptor script into the workspace.
  2. Writes ``.claude/settings.local.json`` with a PreToolUse hook entry.
  3. Provides ``run_prompt()`` to invoke ``uv run claude-mpm run`` with the
     correct environment variables.
  4. Reads the JSONL capture file to return structured delegation records.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any

# Resolve interceptor script relative to project root:
#   tests/eval/adapters/hook_interception_harness.py
#   -> tests/eval/adapters -> tests/eval -> tests -> <project_root>
#   -> src/claude_mpm/testing/delegation_interceptor.py
INTERCEPTOR_SCRIPT_PATH = (
    Path(__file__).parent.parent.parent.parent
    / "src"
    / "claude_mpm"
    / "testing"
    / "delegation_interceptor.py"
)


class HookInterceptionHarness:
    """Manages interceptor lifecycle for behavioural delegation tests.

    Parameters
    ----------
    workspace_dir:
        Optional pre-existing directory to use as workspace.  When *None*,
        a fresh temporary directory is created.
    """

    def __init__(self, workspace_dir: Path | None = None) -> None:
        if workspace_dir is not None:
            self.workspace = workspace_dir
            self._owns_workspace = False
        else:
            self.workspace = Path(tempfile.mkdtemp(prefix="tier3_"))
            self._owns_workspace = True

        self.capture_file = self.workspace / "delegation-captures.jsonl"
        self.interceptor_path = self.workspace / "delegation_interceptor.py"
        self.settings_path = self.workspace / ".claude" / "settings.local.json"

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup(self) -> None:
        """Prepare workspace: install interceptor script and hook config."""
        # 1. Copy (or embed) interceptor script
        if INTERCEPTOR_SCRIPT_PATH.exists():
            shutil.copy2(INTERCEPTOR_SCRIPT_PATH, self.interceptor_path)
        else:
            # Embedded fallback -- minimal interceptor that captures and blocks
            self.interceptor_path.write_text(
                _EMBEDDED_INTERCEPTOR_FALLBACK,
                encoding="utf-8",
            )

        # 2. Make executable
        self.interceptor_path.chmod(
            self.interceptor_path.stat().st_mode
            | stat.S_IXUSR
            | stat.S_IXGRP
            | stat.S_IXOTH
        )

        # 3. Write .claude/settings.local.json with PreToolUse hook
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings: dict[str, Any] = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Task",
                        "command": f"python3 {self.interceptor_path}",
                    }
                ]
            }
        }
        self.settings_path.write_text(
            json.dumps(settings, indent=2),
            encoding="utf-8",
        )

        # 4. Clean capture file (start fresh)
        if self.capture_file.exists():
            self.capture_file.unlink()

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run_prompt(
        self,
        prompt: str,
        timeout: int = 60,
        max_turns: int = 3,
    ) -> subprocess.CompletedProcess[str]:
        """Invoke ``uv run claude-mpm run`` with interception active.

        Parameters
        ----------
        prompt:
            The user prompt to send to the PM.
        timeout:
            Maximum wall-clock seconds before the process is killed.
        max_turns:
            Passed as ``CLAUDE_CODE_MAX_TURNS`` to limit LLM iterations.

        Returns
        -------
        subprocess.CompletedProcess
            The completed process with stdout/stderr captured as text.
        """
        cmd = [
            "uv",
            "run",
            "claude-mpm",
            "run",
            "-i",
            prompt,
            "--non-interactive",
        ]

        env = os.environ.copy()

        # Interception env vars
        env["CLAUDE_MPM_DELEGATION_CAPTURE_FILE"] = str(self.capture_file)
        env["CLAUDE_MPM_DELEGATION_BLOCK"] = "true"

        # CI / telemetry
        env["CI"] = "true"
        env["DISABLE_TELEMETRY"] = "1"

        # CRITICAL: Remove CLAUDECODE to prevent nested-session errors
        env.pop("CLAUDECODE", None)

        # Limit turns so the session terminates quickly
        if max_turns:
            env["CLAUDE_CODE_MAX_TURNS"] = str(max_turns)

        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(self.workspace),
            env=env,
            check=False,
        )

    # ------------------------------------------------------------------
    # Capture retrieval
    # ------------------------------------------------------------------

    def get_captured_delegations(self) -> list[dict[str, Any]]:
        """Read all captured delegation records from the JSONL file.

        Returns
        -------
        list[dict]
            Each element is a parsed JSON object written by the interceptor.
        """
        if not self.capture_file.exists():
            return []

        records: list[dict[str, Any]] = []
        for line in self.capture_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return records

    def get_first_delegation(self) -> dict[str, Any] | None:
        """Return the first captured delegation, or *None*."""
        delegations = self.get_captured_delegations()
        return delegations[0] if delegations else None

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup(self) -> None:
        """Remove the workspace directory if we created it."""
        if self._owns_workspace and self.workspace.exists():
            shutil.rmtree(self.workspace, ignore_errors=True)

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> HookInterceptionHarness:
        self.setup()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.cleanup()


# ---------------------------------------------------------------------------
# Embedded fallback interceptor (used only if the source file is missing)
# ---------------------------------------------------------------------------

_EMBEDDED_INTERCEPTOR_FALLBACK = '''\
"""Minimal embedded delegation interceptor (fallback)."""
import json, os, sys, time
from pathlib import Path

def main():
    capture_file = Path(os.environ.get(
        "CLAUDE_MPM_DELEGATION_CAPTURE_FILE",
        "/tmp/delegation-captures.jsonl",
    ))
    try:
        event = json.loads(sys.stdin.read())
        tool_name = event.get("tool_name", "")
        if tool_name not in ("Task", "Agent"):
            print(json.dumps({"continue": True}))
            return
        tool_input = event.get("tool_input", {})
        record = {
            "timestamp": time.time(),
            "tool_name": tool_name,
            "session_id": event.get("session_id", ""),
            "cwd": event.get("cwd", ""),
            "delegation": {
                "agent_type": tool_input.get("subagent_type", ""),
                "prompt": tool_input.get("prompt", ""),
                "description": tool_input.get("description", ""),
                "mode": tool_input.get("mode", ""),
                "isolation": tool_input.get("isolation", ""),
                "run_in_background": tool_input.get("run_in_background", False),
            },
        }
        capture_file.parent.mkdir(parents=True, exist_ok=True)
        with open(capture_file, "a") as fh:
            fh.write(json.dumps(record) + "\\n")
        block = os.environ.get("CLAUDE_MPM_DELEGATION_BLOCK", "true").lower() == "true"
        if block:
            print(json.dumps({"continue": False,
                "stopReason": f"Delegation intercepted by test harness"}))
        else:
            print(json.dumps({"continue": True}))
    except Exception:
        print(json.dumps({"continue": True}))

if __name__ == "__main__":
    main()
'''
