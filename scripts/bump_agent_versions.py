#!/usr/bin/env python3
"""Bump agent versions for skills integration."""

import json
from pathlib import Path

AGENTS_DIR = (
    Path(__file__).parent.parent / "src" / "claude_mpm" / "agents" / "templates"
)


def discover_agents(agents_dir: Path) -> list[str]:
    """Discover agent template files dynamically.

    Args:
        agents_dir: Path to the agents templates directory.

    Returns:
        List of agent names (file stems) found in the directory.
    """
    return [f.stem for f in agents_dir.glob("*.json") if f.is_file()]


def bump_patch_version(version_str):
    """Bump patch version (3.0.0 -> 3.0.1)."""
    parts = version_str.split(".")
    if len(parts) == 3:
        major, minor, patch = parts
        new_patch = str(int(patch) + 1)
        return f"{major}.{minor}.{new_patch}"
    return version_str


def bump_agent_version(agent_file):
    """Bump version in agent JSON file."""
    with open(agent_file) as f:
        data = json.load(f)

    old_version = data.get("version", "1.0.0")
    new_version = bump_patch_version(old_version)
    data["version"] = new_version

    with open(agent_file, "w") as f:
        json.dump(data, f, indent=2)

    return old_version, new_version


def main():
    """Main execution function."""
    print("Bumping agent versions for skills integration...")
    print("=" * 60)

    if not AGENTS_DIR.exists():
        print(f"ERROR: Agents directory not found: {AGENTS_DIR}")
        return [], [("agents_dir", "directory not found")]

    agents = discover_agents(AGENTS_DIR)
    if not agents:
        print("No agent JSON files found in templates directory.")
        return [], []

    print(f"Discovered {len(agents)} agent template(s).\n")

    bumped = []
    failed = []

    for agent_name in sorted(agents):
        agent_file = AGENTS_DIR / f"{agent_name}.json"
        try:
            old, new = bump_agent_version(agent_file)
            bumped.append((agent_name, old, new))
            print(f"  {agent_name}: {old} -> {new}")
        except Exception as e:
            failed.append((agent_name, str(e)))
            print(f"  {agent_name}: ERROR - {e}")

    print("\n" + "=" * 60)
    print(f"Summary: {len(bumped)} bumped, {len(failed)} failed")

    if failed:
        print("\nFailed agents:")
        for agent, reason in failed:
            print(f"  - {agent}: {reason}")

    return bumped, failed


if __name__ == "__main__":
    bumped, failed = main()
