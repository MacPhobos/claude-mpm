"""V1 Verification Test: Delegation tool name resolution.

Verifies that the codebase consistently uses the correct tool name
for delegation detection in hook handlers.

Part of Phase 0 pre-implementation verification (V1).
"""

import re
from pathlib import Path

import pytest


@pytest.mark.eval
@pytest.mark.structural
class TestToolNameResolution:
    """Verify tool name consistency for delegation detection (V1)."""

    @pytest.fixture
    def src_dir(self) -> Path:
        """Get the source directory path."""
        # Walk up from test file to find project root
        current = Path(__file__).resolve()
        for parent in current.parents:
            if (parent / "src" / "claude_mpm").is_dir():
                return parent / "src" / "claude_mpm"
        pytest.fail("Could not find src/claude_mpm directory")

    def _find_tool_name_checks(self, src_dir: Path, tool_name: str) -> list[str]:
        """Find all code locations checking for a specific tool_name."""
        pattern = re.compile(rf'tool_name\s*==\s*["\']{re.escape(tool_name)}["\']')
        matches = []
        for py_file in src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text()
                for i, line in enumerate(content.splitlines(), 1):
                    if pattern.search(line):
                        rel = py_file.relative_to(src_dir.parent.parent)
                        matches.append(f"{rel}:{i}")
            except Exception:
                continue
        return matches

    def test_task_tool_name_exists_in_codebase(self, src_dir):
        """At least one code location checks for tool_name == 'Task'."""
        refs = self._find_tool_name_checks(src_dir, "Task")
        assert len(refs) > 0, (
            'No references to tool_name == "Task" found in codebase. '
            "Has the tool been renamed?"
        )

    def test_no_agent_tool_name_in_hooks(self, src_dir):
        """No hook code checks for tool_name == 'Agent' (wrong name)."""
        # Only check hook-related files, not general code
        hooks_dir = src_dir / "hooks"
        if not hooks_dir.exists():
            pytest.skip("No hooks directory found")

        pattern = re.compile(r'tool_name\s*==\s*["\']Agent["\']')
        violations = []
        for py_file in hooks_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            try:
                content = py_file.read_text()
                for i, line in enumerate(content.splitlines(), 1):
                    if pattern.search(line):
                        rel = py_file.relative_to(src_dir.parent.parent)
                        violations.append(f"{rel}:{i}: {line.strip()}")
            except Exception:
                continue

        assert len(violations) == 0, (
            f'Found {len(violations)} references to tool_name == "Agent" '
            f'in hooks code (should be "Task"):\n' + "\n".join(violations)
        )

    def test_tool_name_consistency(self, src_dir):
        """All delegation-related tool_name checks use the same name."""
        task_refs = self._find_tool_name_checks(src_dir, "Task")
        agent_refs = self._find_tool_name_checks(src_dir, "Agent")

        if task_refs and agent_refs:
            pytest.fail(
                f"INCONSISTENT tool names found!\n"
                f'"Task" references ({len(task_refs)}): {task_refs}\n'
                f'"Agent" references ({len(agent_refs)}): {agent_refs}\n'
                f"All references should use the same name."
            )

        # At least one reference should exist
        total = len(task_refs) + len(agent_refs)
        assert total > 0, "No tool_name references found at all"

    def test_delegation_detection_code_exists(self, src_dir):
        """Key delegation detection files exist with expected patterns."""
        expected_files = [
            "hooks/claude_hooks/event_handlers.py",
            "hooks/claude_hooks/tool_analysis.py",
        ]

        for rel_path in expected_files:
            full_path = src_dir / rel_path
            assert full_path.exists(), f"Expected file not found: {rel_path}"

            content = full_path.read_text()
            assert "delegation" in content.lower(), (
                f"{rel_path} does not contain 'delegation' - "
                "file may have been refactored"
            )

    def test_known_tool_name_locations(self, src_dir):
        """Specific critical code locations check for the right tool name."""
        critical_checks = {
            "hooks/claude_hooks/event_handlers.py": [
                "is_delegation",  # Must exist for delegation classification
            ],
            "hooks/claude_hooks/tool_analysis.py": [
                "delegation",  # Must classify Task tool as delegation
            ],
        }

        for rel_path, expected_patterns in critical_checks.items():
            full_path = src_dir / rel_path
            if not full_path.exists():
                pytest.skip(f"{rel_path} not found")
                continue

            content = full_path.read_text()
            for pattern in expected_patterns:
                assert pattern in content, (
                    f"{rel_path} missing expected pattern '{pattern}'"
                )
