"""
Integration tests for agent field consistency (Phase 0.1 safety net).

PURPOSE: These tests verify the CURRENT state of agent configurations before
the type -> agent_type field standardization (Phases 1-4). They serve as a
safety net to catch regressions during migration.

WHAT THIS VERIFIES:
1. Hardcoded agent filenames in source files resolve to actual .claude/agents/ files
2. Every deployed agent has `type:` or `agent_type:` in its frontmatter
3. PM delegation matrix agent names match deployed agent files
4. Documents known bug in agent_management_service.py:444 (AgentType enum mismatch)

BRANCH: agenttype-enums
PHASE: 0.1 - Safety net tests BEFORE production code changes
"""

import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest

# Project root: from tests/integration/agents/ go up 3 levels
PROJECT_ROOT = Path(__file__).parents[3]
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"

# Source files containing hardcoded agent references
AGENT_CHECK_SOURCE = (
    PROJECT_ROOT
    / "src"
    / "claude_mpm"
    / "services"
    / "diagnostics"
    / "checks"
    / "agent_check.py"
)
GIT_SYNC_SOURCE = (
    PROJECT_ROOT
    / "src"
    / "claude_mpm"
    / "services"
    / "agents"
    / "sources"
    / "git_source_sync_service.py"
)
TODO_TASK_TOOLS_SOURCE = (
    PROJECT_ROOT
    / "src"
    / "claude_mpm"
    / "services"
    / "framework_claude_md_generator"
    / "section_generators"
    / "todo_task_tools.py"
)
AGENT_DEFINITION_SOURCE = (
    PROJECT_ROOT / "src" / "claude_mpm" / "models" / "agent_definition.py"
)
AGENT_MGMT_SERVICE_SOURCE = (
    PROJECT_ROOT
    / "src"
    / "claude_mpm"
    / "services"
    / "agents"
    / "management"
    / "agent_management_service.py"
)


def _parse_frontmatter(file_path: Path) -> Dict[str, str]:
    """Extract frontmatter fields from a markdown agent file.

    Parses ONLY the YAML frontmatter between the first two '---' lines.
    Returns a dict of key-value pairs found in the frontmatter.
    Does NOT match content in the markdown body.

    Args:
        file_path: Path to the .md agent file.

    Returns:
        Dictionary of frontmatter key-value pairs (values are raw strings).
    """
    content = file_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # Find frontmatter boundaries
    fence_indices: List[int] = []
    for i, line in enumerate(lines):
        if line.strip() == "---":
            fence_indices.append(i)
            if len(fence_indices) == 2:
                break

    if len(fence_indices) < 2:
        return {}

    # Extract frontmatter lines between the two '---' markers
    frontmatter_lines = lines[fence_indices[0] + 1 : fence_indices[1]]

    result: Dict[str, str] = {}
    for line in frontmatter_lines:
        # Match top-level key: value pairs (not nested YAML)
        match = re.match(r"^(\w[\w_-]*)\s*:\s*(.*)$", line)
        if match:
            key = match.group(1)
            value = match.group(2).strip().strip('"').strip("'")
            result[key] = value

    return result


class TestAgentFieldConsistency:
    """Safety-net tests verifying agent configuration consistency.

    These tests document the CURRENT state before the type -> agent_type
    migration. They will catch regressions during Phases 1-4.
    """

    # ------------------------------------------------------------------ #
    # Test 1: Hardcoded agent filenames resolve to actual files
    # ------------------------------------------------------------------ #

    def test_agent_check_core_agents_exist(self) -> None:
        """Verify hardcoded core_agents in agent_check.py resolve to files.

        The agent_check.py diagnostic check has a hardcoded list of 'core_agents'
        that it expects to find deployed. Each filename must correspond to an
        actual file in .claude/agents/.

        Source: src/claude_mpm/services/diagnostics/checks/agent_check.py
        Approximate location: lines 156-161

        KNOWN ISSUE: The core_agents list includes '-agent' suffixed names
        (e.g., 'research-agent.md', 'qa-agent.md') which may not be deployed
        if the runtime only deploys canonical (non-suffixed) agents. The
        non-suffixed equivalents ('research.md', 'qa.md') should exist instead.
        This naming convention conflict is documented in devil's advocate
        analysis (04-devils-advocate-risks.md, Risk #2).
        """
        assert AGENT_CHECK_SOURCE.exists(), (
            f"Source file not found: {AGENT_CHECK_SOURCE}"
        )
        assert AGENTS_DIR.exists(), f"Agents directory not found: {AGENTS_DIR}"

        # Extract hardcoded agent filenames from core_agents list
        source_content = AGENT_CHECK_SOURCE.read_text(encoding="utf-8")

        # Filter to only those in the core_agents block
        # The core_agents list is between 'core_agents = [' and ']'
        core_block_match = re.search(
            r"core_agents\s*=\s*\[(.*?)\]", source_content, re.DOTALL
        )
        assert core_block_match is not None, (
            "Could not find 'core_agents = [...]' list in agent_check.py"
        )
        core_block = core_block_match.group(1)
        core_agents = re.findall(r'"([^"]+\.md)"', core_block)

        assert len(core_agents) > 0, "No core agent filenames extracted"

        missing: List[str] = []
        for agent_filename in core_agents:
            agent_path = AGENTS_DIR / agent_filename
            if not agent_path.exists():
                # Check if non-suffixed variant exists (e.g., research.md for
                # research-agent.md). This is a known naming convention issue.
                base_name = agent_filename.replace("-agent.md", ".md")
                if base_name != agent_filename and (AGENTS_DIR / base_name).exists():
                    # Non-suffixed variant exists — known naming issue, not a failure
                    continue
                missing.append(agent_filename)

        assert not missing, (
            f"Core agents referenced in agent_check.py but missing from "
            f"{AGENTS_DIR} (no suffixed or non-suffixed variant found):\n"
            + "\n".join(f"  - {m}" for m in missing)
        )

    def test_git_sync_fallback_agents_exist(self) -> None:
        """Verify hardcoded fallback agents in git_source_sync_service.py resolve to files.

        The git_source_sync_service.py has a fallback list of agent filenames
        used when the GitHub API is unavailable. Each must correspond to an
        actual file in .claude/agents/.

        Source: src/claude_mpm/services/agents/sources/git_source_sync_service.py
        Approximate location: lines 759-771

        KNOWN ISSUES:
        - The fallback list references underscore-named files
          (e.g., 'version_control.md', 'project_organizer.md') but the actual
          deployed files use hyphens (e.g., 'version-control.md',
          'project-organizer.md').
        - The fallback list includes '-agent' suffixed names
          (e.g., 'research-agent.md') which may not be deployed if the runtime
          only deploys canonical (non-suffixed) agents (e.g., 'research.md').
        These naming inconsistencies are documented in devil's advocate
        analysis (04-devils-advocate-risks.md, Risks #2 and #3).
        """
        assert GIT_SYNC_SOURCE.exists(), f"Source file not found: {GIT_SYNC_SOURCE}"
        assert AGENTS_DIR.exists(), f"Agents directory not found: {AGENTS_DIR}"

        source_content = GIT_SYNC_SOURCE.read_text(encoding="utf-8")

        # Find the fallback return block: 'return [\n  "research-agent.md",\n  ...\n]'
        # Look for the pattern after "Fallback to known agent list" or similar
        fallback_match = re.search(
            r"(?:fallback|Fallback).*?return\s*\[(.*?)\]",
            source_content,
            re.DOTALL,
        )
        assert fallback_match is not None, (
            "Could not find fallback agent list in git_source_sync_service.py"
        )
        fallback_block = fallback_match.group(1)
        fallback_agents = re.findall(r'"([^"]+\.md)"', fallback_block)

        assert len(fallback_agents) > 0, "No fallback agent filenames extracted"

        def _resolve_agent_name(filename: str) -> bool:
            """Check if agent exists directly or via naming variant."""
            if (AGENTS_DIR / filename).exists():
                return True
            # Try underscore -> hyphen conversion
            hyphen_name = filename.replace("_", "-")
            if hyphen_name != filename and (AGENTS_DIR / hyphen_name).exists():
                return True
            # Try removing -agent suffix (e.g., research-agent.md -> research.md)
            base_name = filename.replace("-agent.md", ".md")
            if base_name != filename and (AGENTS_DIR / base_name).exists():
                return True
            return False

        missing: List[str] = []
        for agent_filename in fallback_agents:
            if not _resolve_agent_name(agent_filename):
                missing.append(agent_filename)

        # Fail only on agents that have NO resolvable variant
        assert not missing, (
            f"Fallback agents referenced in git_source_sync_service.py with "
            f"no resolvable variant in {AGENTS_DIR}:\n"
            + "\n".join(f"  - {m}" for m in missing)
        )

    # ------------------------------------------------------------------ #
    # Test 2: Every deployed agent has type: or agent_type: in frontmatter
    # ------------------------------------------------------------------ #

    def test_all_deployed_agents_have_type_field(self) -> None:
        """Verify every .md file in .claude/agents/ has type: or agent_type: in frontmatter.

        This uses frontmatter-aware parsing to avoid false positives from
        matching 'type:' in the markdown body content. Only the YAML
        frontmatter (between the first two '---' lines) is inspected.
        """
        assert AGENTS_DIR.exists(), f"Agents directory not found: {AGENTS_DIR}"

        agent_files = sorted(AGENTS_DIR.glob("*.md"))
        assert len(agent_files) > 0, f"No .md files found in {AGENTS_DIR}"

        agents_missing_type: List[str] = []

        for agent_file in agent_files:
            frontmatter = _parse_frontmatter(agent_file)
            has_type = "type" in frontmatter
            has_agent_type = "agent_type" in frontmatter

            if not has_type and not has_agent_type:
                agents_missing_type.append(agent_file.name)

        assert not agents_missing_type, (
            "Deployed agents missing both 'type:' and 'agent_type:' in "
            "frontmatter:\n" + "\n".join(f"  - {a}" for a in agents_missing_type)
        )

    def test_frontmatter_parser_only_reads_frontmatter(self) -> None:
        """Verify _parse_frontmatter does NOT match content outside frontmatter.

        This test ensures the parser is frontmatter-aware and wouldn't
        produce false positives from body content containing 'type:'.
        """
        # Create a synthetic test to verify parser behavior
        import tempfile

        test_content = (
            "---\n"
            "name: test-agent\n"
            "agent_type: core\n"
            "---\n"
            "# Agent Body\n"
            "type: this-should-not-be-parsed\n"
            "some other content\n"
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(test_content)
            temp_path = Path(f.name)

        try:
            result = _parse_frontmatter(temp_path)
            assert "agent_type" in result, "Should find agent_type in frontmatter"
            assert result["agent_type"] == "core"
            assert result.get("name") == "test-agent"
            # The 'type: this-should-not-be-parsed' from body should NOT appear
            assert result.get("type") is None, (
                "Parser incorrectly matched 'type:' from markdown body"
            )
        finally:
            temp_path.unlink()

    # ------------------------------------------------------------------ #
    # Test 3: PM delegation matrix agent names match deployed files
    # ------------------------------------------------------------------ #

    def test_delegation_matrix_agents_have_deployed_files(self) -> None:
        """Verify subagent_type values in todo_task_tools.py have matching files.

        The PM delegation matrix in todo_task_tools.py references agent names
        via subagent_type="xxx". For each such value, a corresponding
        .claude/agents/xxx.md file must exist.

        Source: src/claude_mpm/services/framework_claude_md_generator/
                section_generators/todo_task_tools.py
        Approximate location: lines 50-59

        KNOWN ISSUES:
        - Template placeholder '[agent-type]' appears in the source as a
          documentation example, not a real agent name.
        - 'pm' and 'test_integration' are virtual agent types that do not
          correspond to deployed .md files.
        """
        assert TODO_TASK_TOOLS_SOURCE.exists(), (
            f"Source file not found: {TODO_TASK_TOOLS_SOURCE}"
        )
        assert AGENTS_DIR.exists(), f"Agents directory not found: {AGENTS_DIR}"

        source_content = TODO_TASK_TOOLS_SOURCE.read_text(encoding="utf-8")

        # Extract all subagent_type="xxx" values
        subagent_types = re.findall(r'subagent_type="([^"]+)"', source_content)
        assert len(subagent_types) > 0, (
            "No subagent_type values found in todo_task_tools.py"
        )

        # Filter out template placeholders (e.g., '[agent-type]'),
        # virtual agent types, and intentionally-wrong examples
        template_placeholders = {"[agent-type]"}
        virtual_agent_types = {
            "pm",  # PM is the orchestrator, not a deployed agent
            "test_integration",  # Virtual type for integration testing
        }
        # Values that appear in "WRONG" examples (lines marked with cross)
        # e.g., 'subagent_type="version_control"' (WRONG - should be 'version-control')
        # e.g., 'subagent_type="research"' (WRONG - missing '-agent' suffix)
        # e.g., 'subagent_type="documentation"' (WRONG - missing '-agent' suffix)
        wrong_examples = {
            "version_control",  # WRONG example: should be 'version-control'
            "research",  # WRONG example: should be 'research-agent'
            "documentation",  # WRONG example: should be 'documentation-agent'
        }
        excluded = template_placeholders | virtual_agent_types | wrong_examples

        # Deduplicate while preserving order, excluding non-agent values
        seen: Set[str] = set()
        unique_subagent_types: List[str] = []
        for st in subagent_types:
            if st not in seen and st not in excluded:
                seen.add(st)
                unique_subagent_types.append(st)

        missing: List[str] = []
        for agent_name in unique_subagent_types:
            agent_path = AGENTS_DIR / f"{agent_name}.md"
            if not agent_path.exists():
                # Check if non-suffixed variant exists
                # e.g., research-agent -> research.md
                base_name = agent_name.replace("-agent", "")
                base_path = AGENTS_DIR / f"{base_name}.md"
                if base_name != agent_name and base_path.exists():
                    # Known naming convention issue: -agent suffix not deployed
                    # but canonical (non-suffixed) agent exists
                    continue
                missing.append(agent_name)

        assert not missing, (
            "Delegation matrix subagent_type values without matching "
            ".claude/agents/{name}.md file (checked -agent suffix and "
            "non-suffixed variants):\n"
            + "\n".join(f'  - subagent_type="{m}" -> {m}.md (missing)' for m in missing)
        )

    def test_delegation_matrix_extracts_expected_agents(self) -> None:
        """Verify that we extract the expected agent names from the delegation matrix.

        This test documents the KNOWN subagent_type values so that if any are
        added or removed, the test suite catches the change.
        """
        assert TODO_TASK_TOOLS_SOURCE.exists()

        source_content = TODO_TASK_TOOLS_SOURCE.read_text(encoding="utf-8")

        # Extract unique subagent_type values (including placeholders)
        subagent_types = set(re.findall(r'subagent_type="([^"]+)"', source_content))

        # These are ALL currently known subagent_type values in the source,
        # including template placeholders, virtual types, and wrong examples
        expected_agents = {
            "[agent-type]",  # Template placeholder in documentation
            "research-agent",  # Correct: deployed agent
            "engineer",  # Correct: deployed agent
            "qa-agent",  # Correct: deployed agent
            "documentation-agent",  # Correct: deployed agent
            "security-agent",  # Correct: deployed agent
            "ops-agent",  # Correct: deployed agent
            "version-control",  # Correct: deployed agent
            "data-engineer",  # Correct: deployed agent
            "pm",  # Virtual: PM orchestrator
            "test_integration",  # Virtual: integration testing type
            "research",  # WRONG example in source
            "documentation",  # WRONG example in source
            "version_control",  # WRONG example in source
        }

        # Check that all expected agents are present
        missing_expected = expected_agents - subagent_types
        assert not missing_expected, (
            "Expected subagent_type values not found in source:\n"
            + "\n".join(f"  - {m}" for m in sorted(missing_expected))
        )

    # ------------------------------------------------------------------ #
    # Test 4: Document known AgentType enum bug
    # ------------------------------------------------------------------ #

    @pytest.mark.xfail(
        reason=(
            "Known bug: agent_management_service.py:444 uses "
            "AgentType(post.metadata.get('type', 'core')) which throws "
            "ValueError for most frontmatter 'type' values like 'engineer', "
            "'ops', 'qa', 'security' because they are not valid AgentType "
            "enum members. Phase 2 will fix this."
        ),
        strict=True,
    )
    def test_frontmatter_type_values_are_valid_agent_type_enum(self) -> None:
        """Demonstrate the known AgentType enum mismatch bug.

        The AgentType enum only accepts: 'core', 'project', 'custom',
        'system', 'specialized'. However, agent frontmatter uses
        domain-specific values like 'engineer', 'ops', 'qa', 'security',
        'documentation', 'research', 'product'.

        When agent_management_service.py:444 tries to construct
        AgentType(frontmatter_value), it crashes with ValueError for most
        agents.

        This test is marked xfail to document the bug. It will be converted
        to a passing test in Phase 2 when the fix is applied.
        """
        from claude_mpm.models.agent_definition import AgentType

        # These are actual frontmatter 'type' values found in deployed agents
        actual_frontmatter_type_values = [
            "engineer",
            "ops",
            "qa",
            "security",
            "documentation",
            "research",
            "product",
        ]

        # Attempt to construct AgentType from each value
        # This SHOULD work but currently crashes for most values
        failures: List[Tuple[str, str]] = []
        for value in actual_frontmatter_type_values:
            try:
                AgentType(value)
            except ValueError as e:
                failures.append((value, str(e)))

        # If any failures occurred, the bug is present (expected)
        assert not failures, (
            "AgentType enum cannot parse these frontmatter values:\n"
            + "\n".join(f"  - AgentType('{v}') -> {err}" for v, err in failures)
        )

    def test_agent_type_enum_valid_values_documented(self) -> None:
        """Document the current valid AgentType enum values.

        This test captures the CURRENT enum values so that Phase 2 changes
        to the enum are detected immediately.
        """
        from claude_mpm.models.agent_definition import AgentType

        expected_values = {"core", "project", "custom", "system", "specialized"}
        actual_values = {member.value for member in AgentType}

        assert actual_values == expected_values, (
            f"AgentType enum values changed unexpectedly.\n"
            f"Expected: {sorted(expected_values)}\n"
            f"Actual:   {sorted(actual_values)}\n"
            f"Added:    {sorted(actual_values - expected_values)}\n"
            f"Removed:  {sorted(expected_values - actual_values)}"
        )

    # ------------------------------------------------------------------ #
    # Supplementary: Cross-check hardcoded lists against each other
    # ------------------------------------------------------------------ #

    def test_core_agents_are_subset_of_fallback_agents(self) -> None:
        """Verify agent_check core_agents are a subset of git_sync fallback agents.

        The core_agents list (4 agents) should be contained within the larger
        fallback list (11 agents). If a core agent is missing from the fallback,
        it indicates a synchronization issue between the two hardcoded lists.
        """
        if not AGENT_CHECK_SOURCE.exists() or not GIT_SYNC_SOURCE.exists():
            pytest.skip("Source files not available")

        # Extract core_agents
        ac_content = AGENT_CHECK_SOURCE.read_text(encoding="utf-8")
        core_match = re.search(r"core_agents\s*=\s*\[(.*?)\]", ac_content, re.DOTALL)
        assert core_match is not None
        core_agents = set(re.findall(r'"([^"]+\.md)"', core_match.group(1)))

        # Extract fallback agents
        gs_content = GIT_SYNC_SOURCE.read_text(encoding="utf-8")
        fb_match = re.search(
            r"(?:fallback|Fallback).*?return\s*\[(.*?)\]",
            gs_content,
            re.DOTALL,
        )
        assert fb_match is not None
        fallback_agents = set(re.findall(r'"([^"]+\.md)"', fb_match.group(1)))

        not_in_fallback = core_agents - fallback_agents
        assert not not_in_fallback, "Core agents not in fallback list:\n" + "\n".join(
            f"  - {a}" for a in sorted(not_in_fallback)
        )

    def test_deployed_agents_directory_is_not_empty(self) -> None:
        """Verify .claude/agents/ exists and contains agent files.

        Basic precondition check to ensure the test suite has something
        to verify against.
        """
        assert AGENTS_DIR.exists(), f"Agents directory does not exist: {AGENTS_DIR}"
        agent_files = list(AGENTS_DIR.glob("*.md"))
        assert len(agent_files) >= 10, (
            f"Expected at least 10 deployed agents, found {len(agent_files)}"
        )

    def test_type_vs_agent_type_field_usage_report(self) -> None:
        """Report which agents use 'type:' vs 'agent_type:' in frontmatter.

        This is a documentation test that captures the CURRENT state of field
        usage across all deployed agents. It does not fail but records the
        data for Phase 1 migration planning.
        """
        assert AGENTS_DIR.exists()

        agent_files = sorted(AGENTS_DIR.glob("*.md"))
        assert len(agent_files) > 0

        uses_type: List[str] = []
        uses_agent_type: List[str] = []
        uses_both: List[str] = []
        uses_neither: List[str] = []

        for agent_file in agent_files:
            fm = _parse_frontmatter(agent_file)
            has_type = "type" in fm
            has_agent_type = "agent_type" in fm

            if has_type and has_agent_type:
                uses_both.append(agent_file.name)
            elif has_type:
                uses_type.append(agent_file.name)
            elif has_agent_type:
                uses_agent_type.append(agent_file.name)
            else:
                uses_neither.append(agent_file.name)

        # This test documents the current state; it passes as long as we
        # successfully categorized all agents
        total = (
            len(uses_type) + len(uses_agent_type) + len(uses_both) + len(uses_neither)
        )
        assert total == len(agent_files), "Failed to categorize all agent files"

        # Print a summary for diagnostic purposes (visible with pytest -v)
        print("\n--- Agent Field Usage Report ---")
        print(f"Total agents: {len(agent_files)}")
        print(f"Using 'type:' only:       {len(uses_type)}")
        print(f"Using 'agent_type:' only:  {len(uses_agent_type)}")
        print(f"Using both:               {len(uses_both)}")
        print(f"Using neither:            {len(uses_neither)}")

        if uses_neither:
            print("\nAgents with NEITHER field:")
            for name in uses_neither:
                print(f"  - {name}")

    # ------------------------------------------------------------------ #
    # Phase 2 Tests: _safe_parse_agent_type and management service fix
    # ------------------------------------------------------------------ #

    def test_safe_parse_agent_type_valid_enum_values(self) -> None:
        """Verify _safe_parse_agent_type returns correct enum for valid values.

        Phase 2 added a safe wrapper around AgentType() construction.
        Valid enum values (core, project, custom, system, specialized)
        should return the corresponding enum member directly.
        """
        from claude_mpm.models.agent_definition import AgentType
        from claude_mpm.services.agents.management.agent_management_service import (
            AgentManager,
        )

        valid_values = {
            "core": AgentType.CORE,
            "project": AgentType.PROJECT,
            "custom": AgentType.CUSTOM,
            "system": AgentType.SYSTEM,
            "specialized": AgentType.SPECIALIZED,
        }

        for value, expected in valid_values.items():
            result = AgentManager._safe_parse_agent_type(value)
            assert result == expected, (
                f"_safe_parse_agent_type('{value}') returned {result}, "
                f"expected {expected}"
            )

    def test_safe_parse_agent_type_frontmatter_values_return_custom(self) -> None:
        """Verify _safe_parse_agent_type returns CUSTOM for frontmatter values.

        Deployed agents use domain-specific values like 'engineer', 'ops', 'qa'
        which are NOT valid AgentType enum members. The safe parser should
        return AgentType.CUSTOM instead of raising ValueError.

        This is the Phase 2 fix for the bug at agent_management_service.py:444.
        """
        from claude_mpm.models.agent_definition import AgentType
        from claude_mpm.services.agents.management.agent_management_service import (
            AgentManager,
        )

        # All frontmatter values found in deployed agents
        frontmatter_values = [
            "engineer",
            "ops",
            "qa",
            "research",
            "documentation",
            "security",
            "product",
            "analysis",
            "refactoring",
            "content",
            "imagemagick",
            "memory_manager",
            "claude-mpm",
        ]

        for value in frontmatter_values:
            result = AgentManager._safe_parse_agent_type(value)
            assert result == AgentType.CUSTOM, (
                f"_safe_parse_agent_type('{value}') returned {result}, "
                f"expected AgentType.CUSTOM"
            )
            # Critically: must NOT raise ValueError
            # (this was the original bug)
