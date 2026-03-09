#!/usr/bin/env python3
"""V1 Verification: Determine if the delegation tool name is "Task" or "Agent".

This script performs static analysis of the codebase AND checks existing hook logs
to determine the actual tool name used in Claude Code PreToolUse events.

Can be run from within a Claude session (no claude -p needed).
"""

import json
import os
import re
import sys
from pathlib import Path


def check_code_references(project_root: Path) -> dict:
    """Scan codebase for tool_name == 'Task' and tool_name == 'Agent' references."""
    src_dir = project_root / "src" / "claude_mpm"
    task_refs = []
    agent_refs = []

    for py_file in src_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            content = py_file.read_text()
            for i, line in enumerate(content.splitlines(), 1):
                if 'tool_name == "Task"' in line or "tool_name == 'Task'" in line:
                    task_refs.append(
                        f"{py_file.relative_to(project_root)}:{i}: {line.strip()}"
                    )
                if 'tool_name == "Agent"' in line or "tool_name == 'Agent'" in line:
                    agent_refs.append(
                        f"{py_file.relative_to(project_root)}:{i}: {line.strip()}"
                    )
        except Exception:
            continue

    return {"task_refs": task_refs, "agent_refs": agent_refs}


def check_hook_log(log_path: str = "/tmp/claude-mpm-hook.log") -> dict:  # nosec B108
    """Parse hook log for any tool_name values from PreToolUse events."""
    tool_names = set()
    delegation_evidence = []

    if not os.path.exists(log_path):
        return {"exists": False, "tool_names": [], "delegation_evidence": []}

    try:
        with open(log_path) as f:
            for line in f:
                # Look for JSON event data that contains tool_name
                # The hook handler logs "Received event with keys:" but not values
                # Check for delegation-related patterns
                if "is_delegation" in line and "True" in line:
                    delegation_evidence.append(line.strip()[:200])
                if "Task" in line and "tool" in line.lower():
                    # Look for lines referencing Task as a tool
                    if "delegation" in line.lower() or "subagent" in line.lower():
                        delegation_evidence.append(line.strip()[:200])
    except Exception as e:
        return {
            "exists": True,
            "error": str(e),
            "tool_names": [],
            "delegation_evidence": [],
        }

    return {
        "exists": True,
        "tool_names": sorted(tool_names),
        "delegation_evidence": delegation_evidence[:10],  # limit
    }


def check_settings_json(project_root: Path) -> dict:
    """Check settings.local.json for hook matcher patterns."""
    settings_path = project_root / ".claude" / "settings.local.json"
    if not settings_path.exists():
        return {"exists": False}

    try:
        settings = json.loads(settings_path.read_text())
        hooks = settings.get("hooks", {})
        pre_tool_use = hooks.get("PreToolUse", [])
        matchers = []
        for entry in pre_tool_use:
            if isinstance(entry, dict):
                matchers.append(entry.get("matcher", "N/A"))
        return {"exists": True, "matchers": matchers}
    except Exception as e:
        return {"exists": True, "error": str(e)}


def check_claude_code_tool_definitions(project_root: Path) -> dict:
    """Check if there are Agent or Task tool definitions in Claude Code integration."""
    # Check for any agent template files that reference tool names
    patterns = {
        "Agent tool in templates": [],
        "Task tool in templates": [],
    }

    for json_file in (project_root / "src" / "claude_mpm" / "agents").rglob("*.json"):
        try:
            content = json_file.read_text()
            if '"Agent"' in content:
                patterns["Agent tool in templates"].append(
                    str(json_file.relative_to(project_root))
                )
            if '"Task"' in content:
                patterns["Task tool in templates"].append(
                    str(json_file.relative_to(project_root))
                )
        except Exception:
            continue

    return patterns


def main():
    project_root = Path(__file__).parent.parent.resolve()
    print(f"Project root: {project_root}")
    print("=" * 60)
    print("V1 VERIFICATION: Tool Name Resolution")
    print("=" * 60)

    # 1. Code analysis
    print("\n## 1. Code Reference Analysis")
    refs = check_code_references(project_root)
    print(f'   tool_name == "Task" references: {len(refs["task_refs"])}')
    for ref in refs["task_refs"]:
        print(f"     - {ref}")
    print(f'   tool_name == "Agent" references: {len(refs["agent_refs"])}')
    for ref in refs["agent_refs"]:
        print(f"     - {ref}")

    # 2. Hook log analysis
    print("\n## 2. Hook Log Analysis")
    log_data = check_hook_log()
    if not log_data["exists"]:
        print("   No hook log found at /tmp/claude-mpm-hook.log")
    else:
        print(
            f"   Delegation evidence found: {len(log_data.get('delegation_evidence', []))}"
        )
        for ev in log_data.get("delegation_evidence", []):
            print(f"     - {ev}")

    # 3. Settings analysis
    print("\n## 3. Settings Configuration")
    settings = check_settings_json(project_root)
    if settings["exists"]:
        print(f"   PreToolUse matchers: {settings.get('matchers', 'N/A')}")
    else:
        print("   No settings.local.json found")

    # 4. Template analysis
    print("\n## 4. Agent Template Analysis")
    templates = check_claude_code_tool_definitions(project_root)
    for key, files in templates.items():
        print(f"   {key}: {len(files)} files")

    # 5. Conclusion
    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)

    task_count = len(refs["task_refs"])
    agent_count = len(refs["agent_refs"])

    if task_count > 0 and agent_count == 0:
        print(
            f'   RESULT: Tool name is "Task" ({task_count} code references, 0 "Agent" refs)'
        )
        print("   STATUS: VERIFIED (code analysis)")
        print(
            "   NOTE: Empirical verification via hook capture recommended (run verify-e2e-prerequisites.sh)"
        )
        return 0
    if agent_count > 0 and task_count == 0:
        print(f'   RESULT: Tool name is "Agent" ({agent_count} code references)')
        print("   STATUS: VERIFIED (code analysis)")
        return 0
    if task_count > 0 and agent_count > 0:
        print(
            f'   RESULT: MIXED - both "Task" ({task_count}) and "Agent" ({agent_count}) found'
        )
        print("   STATUS: NEEDS EMPIRICAL VERIFICATION")
        return 1
    print("   RESULT: INCONCLUSIVE - no references to either name found")
    print("   STATUS: NEEDS EMPIRICAL VERIFICATION")
    return 1


if __name__ == "__main__":
    sys.exit(main())
