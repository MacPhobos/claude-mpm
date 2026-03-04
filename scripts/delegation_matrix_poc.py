#!/usr/bin/env python3
"""
Proof of concept: Generate delegation matrix from agent descriptions using headless claude.
"""

import json
import subprocess  # nosec B404 - intentional subprocess for CLI execution
import sys
import tempfile
from pathlib import Path

import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Files to skip when scanning agent .md files
SKIP_FILES = {"BASE-AGENT.md", "README.md", "CHANGELOG.md"}


def _parse_yaml_frontmatter(md_path: Path) -> dict | None:
    """Parse YAML frontmatter from a markdown file.

    Returns the frontmatter dict or None if parsing fails.
    """
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Warning: Could not read {md_path}: {e}")
        return None

    if not text.startswith("---"):
        return None

    # Find the closing --- delimiter
    end_idx = text.find("---", 3)
    if end_idx == -1:
        return None

    yaml_block = text[3:end_idx]
    try:
        return yaml.safe_load(yaml_block)
    except yaml.YAMLError as e:
        print(f"Warning: Could not parse YAML in {md_path}: {e}")
        return None


def load_agent_descriptions() -> list[dict]:
    """Load agent descriptions from git-cached markdown files with YAML frontmatter."""
    # Primary: git-cached agents directory
    agents_dir = (
        Path.home()
        / ".claude-mpm"
        / "cache"
        / "agents"
        / "bobmatnyc"
        / "claude-mpm-agents"
        / "agents"
    )
    agents = []

    if not agents_dir.exists():
        print(f"Warning: Git-cached agents directory not found at {agents_dir}")
        # Fallback to examples directory
        agents_dir = (
            Path(__file__).parent.parent
            / "examples/project_agents/.claude-mpm/agents/templates"
        )

    if not agents_dir.exists():
        print("Error: No agents directory found")
        return agents

    for md_file in sorted(agents_dir.rglob("*.md")):
        # Skip non-agent files
        if md_file.name in SKIP_FILES:
            continue

        data = _parse_yaml_frontmatter(md_file)
        if data is None:
            continue

        try:
            # Extract routing-relevant fields from YAML frontmatter
            skills = data.get("skills", [])
            memory_routing = data.get("memory_routing", {})
            capabilities = data.get("capabilities", {})

            agent_info = {
                "id": data.get("agent_id", md_file.stem),
                "name": data.get("name", ""),
                "description": data.get("description", ""),
                "type": data.get("agent_type", ""),
                "model": data.get("model", "sonnet"),
                "skills": skills[:10] if isinstance(skills, list) else [],
                "routing_keywords": (
                    memory_routing.get("keywords", [])[:10]
                    if isinstance(memory_routing, dict)
                    else []
                ),
                "memory_routing": memory_routing,
                "capabilities": capabilities,
            }
            agents.append(agent_info)
        except Exception as e:
            print(f"Warning: Could not process {md_file}: {e}")

    return agents


def generate_delegation_matrix(agents: list[dict]) -> str:
    """Call headless claude-mpm to generate delegation matrix."""
    # Build the prompt
    agent_summary = json.dumps(agents, indent=2)

    prompt = f"""You are helping build a Project Manager (PM) agent's delegation instructions.

Given these deployed agents with their capabilities:

{agent_summary}

Generate a concise delegation matrix that the PM can use to route tasks. Format as markdown with:

1. **Quick Reference Table**: Agent ID, Best For (2-3 words), Key Triggers
2. **Routing Decision Tree**: When user says X -> delegate to Y
3. **Handoff Chains**: Common sequences (e.g., Research -> Engineer -> QA)
4. **Model Tier Guidance**: When to use opus vs sonnet vs haiku agents

Keep it concise and actionable. The PM will use this to make instant delegation decisions.

IMPORTANT: Output ONLY the markdown. No preamble, no explanation. Just the delegation matrix."""

    print("Calling claude-mpm headless mode...")

    # Write prompt to temp file for piping
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        # Run headless claude-mpm
        result = subprocess.run(  # nosec B603 B607 - trusted claude CLI call
            ["claude", "--print", "-p", prompt],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return f"Error generating matrix: {result.stderr}"

        return result.stdout
    except subprocess.TimeoutExpired:
        return "Error: Timeout waiting for Claude response"
    except FileNotFoundError:
        return "Error: claude CLI not found. Make sure Claude Code is installed."
    finally:
        Path(prompt_file).unlink(missing_ok=True)


def main():
    print("=" * 60)
    print("Delegation Matrix Generator - Proof of Concept")
    print("=" * 60)

    # Load agents
    print("\n1. Loading agent descriptions...")
    agents = load_agent_descriptions()
    print(f"   Found {len(agents)} agents")

    if not agents:
        print("ERROR: No agents found to process")
        sys.exit(1)

    for agent in agents[:5]:
        desc = agent.get("description", "No description")[:50]
        print(f"   - {agent['id']}: {desc}...")
    if len(agents) > 5:
        print(f"   ... and {len(agents) - 5} more")

    # Generate matrix using headless claude
    print("\n2. Generating delegation matrix via headless claude...")
    matrix = generate_delegation_matrix(agents)

    # Output
    print("\n3. Generated Delegation Matrix:")
    print("=" * 60)
    print(matrix)
    print("=" * 60)

    # Save to file
    output_file = (
        Path(__file__).parent.parent / "docs/research/generated-delegation-matrix.md"
    )
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        f.write("# Generated Delegation Matrix\n\n")
        f.write(f"Generated: {__import__('datetime').datetime.now().isoformat()}\n\n")
        f.write(f"Source: {len(agents)} agent templates\n\n")
        f.write(matrix)
    print(f"\nSaved to: {output_file}")


if __name__ == "__main__":
    main()
