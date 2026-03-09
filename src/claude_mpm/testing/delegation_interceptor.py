"""PreToolUse hook interceptor for capturing and blocking Task/Agent delegations.

This script is designed to be invoked by Claude Code as a PreToolUse hook.
It reads a tool-use event from stdin (JSON), inspects whether it is a Task
or Agent tool call, and captures delegation metadata to a JSONL file for
test assertions.

Environment Variables
---------------------
CLAUDE_MPM_DELEGATION_CAPTURE_FILE : str
    Path to the JSONL file where captured delegations are appended.
    Default: /tmp/delegation-captures.jsonl

CLAUDE_MPM_DELEGATION_BLOCK : str
    When "true" (default), the hook outputs ``{"continue": false, ...}`` to
    stdout so that Claude Code does NOT actually spawn the sub-agent.
    Set to "false" to let the delegation proceed after capture.

Usage
-----
Intended to be referenced from ``.claude/settings.local.json``::

    {
      "hooks": {
        "PreToolUse": [
          {
            "matcher": "Task",
            "command": "python3 /path/to/delegation_interceptor.py"
          }
        ]
      }
    }

The script is fail-open: any unhandled exception results in
``{"continue": true}`` so that the outer Claude session is not disrupted.
Errors are logged to ``<capture_file>.errors``.
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any


def _capture_file_path() -> Path:
    """Return the path to the JSONL capture file."""
    return Path(
        os.environ.get(
            "CLAUDE_MPM_DELEGATION_CAPTURE_FILE",
            "/tmp/delegation-captures.jsonl",  # nosec B108
        )
    )


def _should_block() -> bool:
    """Return True if delegations should be blocked (default)."""
    return os.environ.get("CLAUDE_MPM_DELEGATION_BLOCK", "true").lower() == "true"


def _build_capture_record(event: dict[str, Any]) -> dict[str, Any]:
    """Extract delegation metadata from a PreToolUse event JSON.

    Args:
        event: The parsed JSON event from stdin.

    Returns:
        A dict with timestamp, tool_name, session_id, cwd, and nested
        delegation details.
    """
    tool_name: str = event.get("tool_name", "")
    tool_input: dict[str, Any] = event.get("tool_input", {})
    session_id: str = event.get("session_id", "")
    cwd: str = event.get("cwd", "")

    delegation: dict[str, Any] = {
        "agent_type": tool_input.get("subagent_type", ""),
        "prompt": tool_input.get("prompt", ""),
        "description": tool_input.get("description", ""),
        "mode": tool_input.get("mode", ""),
        "isolation": tool_input.get("isolation", ""),
        "run_in_background": tool_input.get("run_in_background", False),
    }

    return {
        "timestamp": time.time(),
        "tool_name": tool_name,
        "session_id": session_id,
        "cwd": cwd,
        "delegation": delegation,
    }


def _write_capture(record: dict[str, Any], capture_file: Path) -> None:
    """Append a capture record as a single JSONL line."""
    capture_file.parent.mkdir(parents=True, exist_ok=True)
    with open(capture_file, "a") as fh:
        fh.write(json.dumps(record) + "\n")


def _log_error(message: str, capture_file: Path) -> None:
    """Append an error message to the error log file."""
    error_file = Path(str(capture_file) + ".errors")
    error_file.parent.mkdir(parents=True, exist_ok=True)
    with open(error_file, "a") as fh:
        fh.write(f"{time.time()}: {message}\n")


def main() -> None:
    """Entry point: read stdin, capture delegation, emit continue/block."""
    capture_file = _capture_file_path()

    try:
        raw_input = sys.stdin.read()
        event: dict[str, Any] = json.loads(raw_input)

        tool_name: str = event.get("tool_name", "")

        # Only intercept Task / Agent tool calls
        if tool_name not in ("Task", "Agent"):
            # Pass through for non-delegation tools
            print(json.dumps({"continue": True}))
            return

        # Build and persist capture record
        record = _build_capture_record(event)
        _write_capture(record, capture_file)

        # Emit blocking or pass-through response
        if _should_block():
            stop_reason = (
                f"Delegation to '{record['delegation']['agent_type']}' "
                f"intercepted by test harness"
            )
            print(json.dumps({"continue": False, "stopReason": stop_reason}))
        else:
            print(json.dumps({"continue": True}))

    except Exception:
        # Fail-open: let the tool call proceed and log the error
        _log_error(traceback.format_exc(), capture_file)
        print(json.dumps({"continue": True}))


if __name__ == "__main__":
    main()
