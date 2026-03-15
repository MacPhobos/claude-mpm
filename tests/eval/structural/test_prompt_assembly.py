"""Tier 1 Structural Tests: PM Prompt Assembly Validation.

Zero-cost, deterministic tests that verify the assembled PM prompt
contains all required sections, agent definitions, and critical instructions.

Phase 1 of E2E delegation testing.
"""

import hashlib
import re

import pytest

# ============================================================================
# Section Presence Tests
# ============================================================================


class TestPromptSectionPresence:
    """Verify all critical sections exist in assembled prompt."""

    REQUIRED_SECTIONS = [
        "DELEGATION-BY-DEFAULT PRINCIPLE",
        "ABSOLUTE PROHIBITIONS",
        "Circuit Breaker",
        "QA VERIFICATION GATE PROTOCOL",
        "Research Gate Protocol",
        "Agent Deployment Architecture",
        "Model Selection Protocol",
        "Available Agent Capabilities",
        "Workflow Pipeline",
        "Git File Tracking",
        "Common Delegation Patterns",
        "Verification Requirements",
    ]

    @pytest.mark.eval
    @pytest.mark.structural
    @pytest.mark.parametrize("section", REQUIRED_SECTIONS)
    def test_section_present(self, assembled_prompt, section):
        assert section in assembled_prompt, (
            f"Critical section '{section}' missing from assembled prompt"
        )

    REQUIRED_AGENTS = [
        "Research",
        "Engineer",
        "Local Ops",
        "QA",
        "Web QA",
        "Documentation",
        "Version Control",
        "Security",
    ]

    @pytest.mark.eval
    @pytest.mark.structural
    @pytest.mark.parametrize("agent", REQUIRED_AGENTS)
    def test_agent_referenced(self, assembled_prompt, agent):
        assert agent.lower() in assembled_prompt.lower(), (
            f"Agent '{agent}' not found in assembled prompt"
        )

    @pytest.mark.eval
    @pytest.mark.structural
    def test_no_unresolved_templates(self, assembled_prompt):
        """No {{variable}} template placeholders left unresolved."""
        matches = re.findall(r"\{\{[^}]+\}\}", assembled_prompt)
        assert not matches, f"Unresolved template variables: {matches}"

    @pytest.mark.eval
    @pytest.mark.structural
    def test_minimum_prompt_length(self, assembled_prompt):
        """Prompt should be at least 40KB (current is ~68KB)."""
        assert len(assembled_prompt) >= 40_000, (
            f"Assembled prompt too short: {len(assembled_prompt)} bytes "
            f"(expected >= 40,000). Assembly pipeline may be broken."
        )

    @pytest.mark.eval
    @pytest.mark.structural
    def test_maximum_prompt_length(self, assembled_prompt):
        """Prompt should not exceed 120KB (runaway assembly)."""
        assert len(assembled_prompt) <= 120_000, (
            f"Assembled prompt too large: {len(assembled_prompt)} bytes "
            f"(expected <= 120,000). Possible duplicate section assembly."
        )


# ============================================================================
# Semantic Checksum Tests
# ============================================================================


class TestPromptSemanticChecksums:
    """Hash critical sections to detect unauthorized modifications.

    When a critical section changes, the hash changes, and the test fails.
    The developer must update the expected hash -- forcing explicit review
    of delegation-critical content changes.
    """

    # These hashes are updated when sections intentionally change.
    # Format: (section_start_marker, expected_hash_prefix)
    # Hash is first 16 chars of SHA-256 of section content.
    CRITICAL_SECTIONS = {
        "delegation_principle": {
            "start": "DELEGATION-BY-DEFAULT PRINCIPLE",
            "hash": "75e180a6fc60c8c7",  # pragma: allowlist secret
            "description": "Core delegation-first behavior",
        },
        "absolute_prohibitions": {
            "start": "ABSOLUTE PROHIBITIONS",
            "hash": "13267ae7a81c88d2",  # pragma: allowlist secret
            "description": "PM forbidden actions list",
        },
        "circuit_breakers": {
            "start": "Circuit Breakers (Enforcement)",
            "hash": "e9b4a28e04250391",  # pragma: allowlist secret
            "description": "Circuit breaker enforcement rules",
        },
        "qa_verification_gate": {
            "start": "QA VERIFICATION GATE PROTOCOL",
            "hash": "40a25adc7d1c711a",  # pragma: allowlist secret
            "description": "Mandatory QA verification gate",
        },
    }

    def _extract_section(self, prompt, start_marker):
        """Extract section content from start marker to next ## heading."""
        idx = prompt.find(start_marker)
        if idx == -1:
            return None
        # Find next section heading at same or higher level
        next_section = prompt.find("\n## ", idx + len(start_marker))
        if next_section == -1:
            return prompt[idx:]
        return prompt[idx:next_section]

    @pytest.mark.eval
    @pytest.mark.structural
    @pytest.mark.parametrize("section_name", list(CRITICAL_SECTIONS.keys()))
    def test_critical_section_unchanged(self, assembled_prompt, section_name):
        config = self.CRITICAL_SECTIONS[section_name]
        if config["hash"] is None:
            pytest.skip(
                f"Hash not yet baselined for '{section_name}' "
                f"-- run baseline script first"
            )

        section = self._extract_section(assembled_prompt, config["start"])
        assert section is not None, f"Section '{section_name}' not found in prompt"

        current_hash = hashlib.sha256(section.encode()).hexdigest()[:16]
        assert current_hash == config["hash"], (
            f"Critical section '{section_name}' ({config['description']}) "
            f"has been modified.\n"
            f"Expected hash: {config['hash']}\n"
            f"Current hash:  {current_hash}\n"
            f"If this change is intentional, update the expected hash in "
            f"test_prompt_assembly.py and re-run Tier 2 canary tests."
            f"New hashes can be generated using: uv run pytest tests/eval/structural/test_prompt_assembly.py::TestPromptSemanticChecksums::test_baseline_hash_helper -xvs"
        )

    @pytest.mark.eval
    @pytest.mark.structural
    def test_baseline_hash_helper(self, assembled_prompt):
        """Helper test that prints current hashes for baselining.

        Run with: uv run pytest tests/eval/structural/test_prompt_assembly.py::TestPromptSemanticChecksums::test_baseline_hash_helper -xvs

        Then copy the printed hashes into CRITICAL_SECTIONS above.
        """
        print("\n\n=== SEMANTIC CHECKSUM BASELINES ===")
        for name, config in self.CRITICAL_SECTIONS.items():
            section = self._extract_section(assembled_prompt, config["start"])
            if section:
                h = hashlib.sha256(section.encode()).hexdigest()[:16]
                print(f'  "{name}": "{h}",  # {config["description"]}')
            else:
                print(f'  "{name}": NOT FOUND -- marker "{config["start"]}" missing')
        print("=== END BASELINES ===\n")


# ============================================================================
# Assembly Component Tests
# ============================================================================


class TestPromptAssemblyComponents:
    """Verify individual assembly pipeline components are present."""

    @pytest.mark.eval
    @pytest.mark.structural
    def test_contains_agent_definitions(self, assembled_prompt):
        """Prompt includes the Available Agent Capabilities section."""
        assert "Available Agent Capabilities" in assembled_prompt
        # Should contain actual agent entries
        assert "Engineer" in assembled_prompt
        assert "Research" in assembled_prompt

    @pytest.mark.eval
    @pytest.mark.structural
    def test_contains_workflow_instructions(self, assembled_prompt):
        """Prompt includes workflow instruction content."""
        assert "Workflow" in assembled_prompt
        # Should contain phase references
        assert "Phase" in assembled_prompt or "phase" in assembled_prompt

    @pytest.mark.eval
    @pytest.mark.structural
    def test_contains_memory_content(self, assembled_prompt):
        """Prompt includes memory section."""
        assert "Memory" in assembled_prompt or "memory" in assembled_prompt

    @pytest.mark.eval
    @pytest.mark.structural
    def test_contains_skills_references(self, assembled_prompt):
        """Prompt references the skills system."""
        assert "skill" in assembled_prompt.lower()

    @pytest.mark.eval
    @pytest.mark.structural
    def test_contains_temporal_context(self, assembled_prompt):
        """Prompt includes temporal/user context section."""
        assert (
            "Temporal" in assembled_prompt
            or "Current DateTime" in assembled_prompt
            or "DateTime" in assembled_prompt
        )

    @pytest.mark.eval
    @pytest.mark.structural
    def test_framework_loader_idempotent(self):
        """FrameworkLoader returns identical content on consecutive calls."""
        from claude_mpm.core.framework_loader import FrameworkLoader

        loader = FrameworkLoader(config={"validate_api_keys": False})
        content1 = loader.get_framework_instructions()
        content2 = loader.get_framework_instructions()
        assert content1 == content2, (
            f"Content differs between calls: {len(content1)} vs {len(content2)} bytes"
        )

    @pytest.mark.eval
    @pytest.mark.structural
    def test_no_duplicate_sections(self, assembled_prompt):
        """Critical sections should not appear more than once."""
        # Check that major headings appear exactly once
        unique_headings = [
            "## 🔴 DELEGATION-BY-DEFAULT PRINCIPLE",
            "## 🔴 ABSOLUTE PROHIBITIONS",
            "## Agent Deployment Architecture",
            "## Model Selection Protocol",
        ]
        for heading in unique_headings:
            count = assembled_prompt.count(heading)
            if count > 0:  # Only assert if heading exists (format may vary)
                assert count == 1, (
                    f"Heading '{heading}' appears {count} times "
                    f"(expected 1). "
                    f"Possible duplicate section assembly."
                )
