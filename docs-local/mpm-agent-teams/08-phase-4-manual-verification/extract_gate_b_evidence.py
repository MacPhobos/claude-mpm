#!/usr/bin/env python3
"""Extract Gate B evidence from Claude Code session JSONL logs.

After running a Gate B verification session, use this script to automatically
extract and evaluate the PM's Agent Teams behavior from the session log.

Usage:
    python extract_gate_b_evidence.py <session-id>
    python extract_gate_b_evidence.py <session-id> --verbose
    python extract_gate_b_evidence.py --latest
    python extract_gate_b_evidence.py --list

Session logs are stored at:
    ~/.claude/projects/-Users-mac-workspace-claude-mpm-fork/<session-id>.jsonl

Examples:
    python extract_gate_b_evidence.py 0faed01b-bb88-4584-9af5-1e16581566a1
    python extract_gate_b_evidence.py --latest --verbose
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Claude Code session log directory for this project
PROJECT_DIR = (
    Path.home() / ".claude" / "projects" / "-Users-mac-workspace-claude-mpm-fork"
)


def find_sessions() -> list[tuple[Path, float]]:
    """Find all session JSONL files, sorted by modification time (newest first)."""
    if not PROJECT_DIR.exists():
        return []
    sessions = []
    for f in PROJECT_DIR.glob("*.jsonl"):
        sessions.append((f, f.stat().st_mtime))
    return sorted(sessions, key=lambda x: x[1], reverse=True)


def extract_tool_calls(session_file: Path) -> list[dict]:
    """Extract all tool calls from a session JSONL file."""
    tool_calls = []
    with open(session_file) as f:
        for line_num, line in enumerate(f, 1):
            try:
                record = json.loads(line.strip())
            except json.JSONDecodeError:
                continue

            # Assistant messages contain tool_use blocks
            if record.get("type") == "assistant":
                content = record.get("message", {}).get("content", [])
                for block in content:
                    if block.get("type") == "tool_use":
                        tool_calls.append(
                            {
                                "line": line_num,
                                "tool": block.get("name", "?"),
                                "id": block.get("id", ""),
                                "input": block.get("input", {}),
                            }
                        )
    return tool_calls


def evaluate_gate_b(tool_calls: list[dict], verbose: bool = False) -> dict:
    """Evaluate Gate B checklist items from extracted tool calls."""

    results = {
        "B1": {
            "passed": False,
            "evidence": [],
            "desc": "Engineers spawned with isolation: worktree",
        },
        "B2": {
            "passed": False,
            "evidence": [],
            "desc": "Merge delegated to VC/Ops agent",
        },
        "B3": {
            "passed": False,
            "evidence": [],
            "desc": "PM ran make test directly (single command)",
        },
        "B4": {
            "passed": False,
            "evidence": [],
            "desc": "Research completed before engineering started",
        },
        "B5": {"passed": False, "evidence": [], "desc": "Worktree cleanup delegated"},
        "B6": {
            "passed": False,
            "evidence": [],
            "desc": "Team NOT spawned for trivial task",
        },
    }

    # Track sequencing for B4
    has_research_team = False
    research_complete = False
    engineer_after_research = False

    # Track whether ANY team was spawned (for B6 — absence of teams)
    team_agent_calls = []
    non_team_agent_calls = []

    for call in tool_calls:
        tool = call["tool"]
        inp = call["input"]

        if tool == "Agent":
            subagent_type = (inp.get("subagent_type") or "").lower()
            isolation = inp.get("isolation", "")
            team_name = inp.get("team_name", "")
            description = inp.get("description", "")[:80]
            prompt_preview = (inp.get("prompt") or "")[:120]

            if team_name:
                team_agent_calls.append(call)
            else:
                non_team_agent_calls.append(call)

            # B1: Engineer with worktree isolation
            if "engineer" in subagent_type and isolation == "worktree":
                results["B1"]["passed"] = True
                results["B1"]["evidence"].append(
                    f"Line {call['line']}: Agent(subagent_type={subagent_type}, "
                    f"isolation=worktree, team_name={team_name}, desc={description})"
                )

            # B2: Merge delegation to VC/Ops
            if subagent_type in ("version control", "local ops", "ops"):
                prompt_lower = (inp.get("prompt") or "").lower()
                if any(kw in prompt_lower for kw in ["merge", "git merge", "worktree"]):
                    results["B2"]["passed"] = True
                    results["B2"]["evidence"].append(
                        f"Line {call['line']}: Agent(subagent_type={subagent_type}, "
                        f"desc={description}) — merge delegation"
                    )

            # B4: Research before Engineer sequencing
            if "research" in subagent_type and team_name:
                has_research_team = True

            # B5: Cleanup delegation to VC/Ops
            if subagent_type in ("version control", "local ops", "ops"):
                prompt_lower = (inp.get("prompt") or "").lower()
                if any(
                    kw in prompt_lower
                    for kw in [
                        "cleanup",
                        "clean up",
                        "worktree remove",
                        "remove worktree",
                    ]
                ):
                    results["B5"]["passed"] = True
                    results["B5"]["evidence"].append(
                        f"Line {call['line']}: Agent(subagent_type={subagent_type}, "
                        f"desc={description}) — cleanup delegation"
                    )

        elif tool == "Bash":
            command = inp.get("command", "")

            # B3: PM runs make test directly
            if any(cmd in command for cmd in ["make test", "uv run pytest", "pytest"]):
                results["B3"]["passed"] = True
                results["B3"]["evidence"].append(
                    f"Line {call['line']}: Bash(command={command[:80]})"
                )

        elif tool == "SendMessage":
            # Track research completion for B4
            pass  # SendMessage from research teammates indicates completion

    # B4: Check if research teammates were spawned before engineers
    # (Simple heuristic: look at ordering of team Agent calls)
    research_lines = []
    engineer_lines = []
    for call in team_agent_calls:
        subagent_type = (call["input"].get("subagent_type") or "").lower()
        if "research" in subagent_type:
            research_lines.append(call["line"])
        elif "engineer" in subagent_type:
            engineer_lines.append(call["line"])

    if research_lines and engineer_lines:
        max_research = max(research_lines)
        min_engineer = min(engineer_lines)
        if max_research < min_engineer:
            results["B4"]["passed"] = True
            results["B4"]["evidence"].append(
                f"Research team calls (lines {research_lines}) all precede "
                f"engineer team calls (lines {engineer_lines})"
            )
        else:
            results["B4"]["evidence"].append(
                f"WARNING: Research (lines {research_lines}) and engineer "
                f"(lines {engineer_lines}) may overlap"
            )

    # B6: Detect absence of team spawning for trivial tasks
    # This is harder to detect automatically — we flag if there are non-team
    # agent calls (simple delegation) which COULD indicate B6 compliance
    if non_team_agent_calls and not team_agent_calls:
        results["B6"]["passed"] = True
        results["B6"]["evidence"].append(
            f"{len(non_team_agent_calls)} agent calls without team_name "
            f"(no Agent Teams used — correct for trivial tasks)"
        )
    elif non_team_agent_calls:
        results["B6"]["evidence"].append(
            f"{len(non_team_agent_calls)} non-team + {len(team_agent_calls)} team calls. "
            f"Check manually whether trivial tasks avoided teams."
        )

    return results


def print_report(
    session_file: Path, results: dict, tool_calls: list[dict], verbose: bool
):
    """Print the Gate B evidence report."""
    print("=" * 70)
    print("GATE B EVIDENCE EXTRACTION REPORT")
    print("=" * 70)
    print(f"Session: {session_file.stem}")
    print(f"Log file: {session_file}")
    print(f"Total tool calls: {len(tool_calls)}")

    agent_calls = [c for c in tool_calls if c["tool"] == "Agent"]
    bash_calls = [c for c in tool_calls if c["tool"] == "Bash"]
    team_calls = [c for c in agent_calls if c["input"].get("team_name")]
    print(f"Agent calls: {len(agent_calls)} ({len(team_calls)} with team_name)")
    print(f"Bash calls: {len(bash_calls)}")
    print()

    # Agent Teams summary
    if team_calls:
        print("--- Agent Teams Calls ---")
        for call in team_calls:
            inp = call["input"]
            print(
                f"  Line {call['line']}: {inp.get('subagent_type', '?')} "
                f"| team={inp.get('team_name')} "
                f"| isolation={inp.get('isolation', 'none')} "
                f"| {inp.get('description', '?')[:50]}"
            )
        print()

    # Gate B checklist
    print("--- Gate B Checklist ---")
    all_passed = True
    for item_id in ["B1", "B2", "B3", "B4", "B5", "B6"]:
        item = results[item_id]
        status = "PASS" if item["passed"] else "FAIL"
        icon = "✅" if item["passed"] else "❌"
        all_passed = all_passed and item["passed"]
        print(f"  {icon} {item_id}: {item['desc']} — {status}")
        if verbose or not item["passed"]:
            for ev in item["evidence"]:
                print(f"       {ev}")
    print()

    passed_count = sum(1 for r in results.values() if r["passed"])
    print(f"--- Result: {passed_count}/6 checklist items passed ---")
    if all_passed:
        print("🎉 GATE B: ALL ITEMS PASSED")
    else:
        missing = [k for k, v in results.items() if not v["passed"]]
        print(f"⚠️  Missing: {', '.join(missing)} — run additional sessions")
    print("=" * 70)

    # Verbose: dump all agent calls
    if verbose:
        print()
        print("--- All Agent Calls (verbose) ---")
        for call in agent_calls:
            inp = call["input"]
            print(
                f"  Line {call['line']}: {call['tool']}({inp.get('name', inp.get('description', '?'))[:60]})"
            )
            print(f"    subagent_type: {inp.get('subagent_type', 'none')}")
            print(f"    isolation: {inp.get('isolation', 'none')}")
            print(f"    team_name: {inp.get('team_name', 'none')}")
            print(f"    model: {inp.get('model', 'inherit')}")
            prompt = (inp.get("prompt") or "")[:200]
            if prompt:
                print(f"    prompt: {prompt}...")
            print()


def main():
    if "--list" in sys.argv:
        sessions = find_sessions()
        if not sessions:
            print(f"No sessions found in {PROJECT_DIR}")
            return 1
        print(f"Sessions in {PROJECT_DIR} (newest first):")
        for path, mtime in sessions[:20]:
            import datetime

            dt = datetime.datetime.fromtimestamp(mtime)
            size_mb = path.stat().st_size / 1024 / 1024
            print(f"  {path.stem}  {dt:%Y-%m-%d %H:%M}  {size_mb:.1f}MB")
        return 0

    verbose = "--verbose" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    if "--latest" in sys.argv:
        sessions = find_sessions()
        if not sessions:
            print(f"No sessions found in {PROJECT_DIR}")
            return 1
        session_file = sessions[0][0]
    elif args:
        session_id = args[0]
        session_file = PROJECT_DIR / f"{session_id}.jsonl"
        if not session_file.exists():
            print(f"Session file not found: {session_file}")
            return 1
    else:
        print(__doc__)
        return 1

    tool_calls = extract_tool_calls(session_file)
    results = evaluate_gate_b(tool_calls, verbose)
    print_report(session_file, results, tool_calls, verbose)
    return 0


if __name__ == "__main__":
    sys.exit(main())
