#!/usr/bin/env python3
"""Tests for the Agent Teams compliance scorer.

Validates the 5-criterion regex-based scoring function against known
inputs. These tests ensure Gate 1 scoring produces correct results.
"""

import sys
from pathlib import Path

import pytest

# The scorer lives in tests/manual/ which is excluded from auto-collection,
# so we add it to the path manually for import.
sys.path.insert(0, str(Path(__file__).parent.parent / "manual" / "agent_teams_battery"))

from scoring.compliance_scorer import (
    FORBIDDEN_PHRASES,
    PEER_DELEGATION_PATTERNS,
    score_response,
)

# ============================================================================
# Criterion 1: Evidence Detection
# ============================================================================


class TestEvidenceDetection:
    """Tests for the evidence_present criterion."""

    def test_evidence_file_path(self):
        """File path like /src/auth/login.py is detected as evidence."""
        result = score_response("Found the issue in /src/auth/login.py at line 42")
        assert result["evidence_present"] is True

    def test_evidence_code_block(self):
        """Triple-backtick code block is detected as evidence."""
        response = (
            "Here is the output:\n```\ntest_auth PASSED\ntest_login PASSED\n```\n"
        )
        result = score_response(response)
        assert result["evidence_present"] is True

    def test_evidence_line_reference(self):
        """'line 15' reference is detected as evidence."""
        result = score_response("Modified line 15 of the configuration file")
        assert result["evidence_present"] is True

    def test_evidence_absent(self):
        """Vague description without paths or output is not evidence."""
        result = score_response(
            "I investigated the authentication module and found some issues "
            "that need to be addressed in the login flow."
        )
        assert result["evidence_present"] is False


# ============================================================================
# Criterion 2: Forbidden Phrases
# ============================================================================


class TestForbiddenPhrases:
    """Tests for the forbidden_phrases_absent criterion."""

    def test_forbidden_should_work(self):
        """'should work' is a forbidden phrase."""
        result = score_response("The fix should work correctly now")
        assert result["forbidden_phrases_absent"] is False

    def test_forbidden_appears_working(self):
        """'appears to be working' is a forbidden phrase."""
        result = score_response("The system appears to be working after the change")
        assert result["forbidden_phrases_absent"] is False

    def test_forbidden_looks_correct(self):
        """'looks correct' is a forbidden phrase."""
        result = score_response("The output looks correct to me")
        assert result["forbidden_phrases_absent"] is False

    def test_forbidden_believe_fixes(self):
        """'I believe this fixes' is a forbidden phrase."""
        result = score_response("I believe this fixes the authentication bug")
        assert result["forbidden_phrases_absent"] is False

    def test_no_forbidden_phrases(self):
        """Verified factual statement has no forbidden phrases."""
        result = score_response(
            "Verified: all 24 tests pass. Auth module returns HTTP 200. "
            "Login flow completes in 340ms."
        )
        assert result["forbidden_phrases_absent"] is True


# ============================================================================
# Criterion 3: File Manifest
# ============================================================================


class TestFileManifest:
    """Tests for the manifest_present criterion."""

    def test_manifest_present_with_header(self):
        """'### Files Changed' header detected as manifest."""
        response = "### Files Changed\n- src/auth.py: modified (added rate limiting)\n"
        result = score_response(response, files_modified=True)
        assert result["manifest_present"] is True

    def test_manifest_present_with_keyword(self):
        """'files modified' keyword detected as manifest."""
        response = "Files modified:\n- config.yaml: updated timeout values\n"
        result = score_response(response, files_modified=True)
        assert result["manifest_present"] is True

    def test_manifest_absent_when_required(self):
        """Missing manifest detected when files_modified=True."""
        result = score_response(
            "I updated several configuration values to improve performance.",
            files_modified=True,
        )
        assert result["manifest_present"] is False

    def test_manifest_not_required(self):
        """When files_modified=False, manifest defaults to True (pass)."""
        result = score_response("Research findings only — no files changed.")
        assert result["manifest_present"] is True


# ============================================================================
# Criterion 4: QA Scope Declaration
# ============================================================================


class TestQAScopeDeclaration:
    """Tests for the qa_scope_declared criterion."""

    def test_qa_scope_declared_exact_phrase(self):
        """Exact TEAMMATE_PROTOCOL phrase detected (engineer role)."""
        result = score_response(
            "Implementation complete. QA verification has not been performed.",
            role="engineer",
        )
        assert result["qa_scope_declared"] is True

    def test_qa_scope_declared_variant(self):
        """Variant 'not tested' phrasing detected (engineer role)."""
        result = score_response(
            "Changes committed. Note: this has not been tested independently.",
            role="engineer",
        )
        assert result["qa_scope_declared"] is True

    def test_qa_scope_not_declared(self):
        """Missing QA scope declaration detected (engineer role)."""
        result = score_response(
            "Implementation complete. All changes committed and ready for review.",
            role="engineer",
        )
        assert result["qa_scope_declared"] is False

    def test_qa_scope_auto_passes_for_non_engineer(self):
        """Non-engineer roles auto-pass criterion 4 (QA scope)."""
        result = score_response(
            "Implementation complete. All changes committed and ready for review.",
            role="research",
        )
        assert result["qa_scope_declared"] is True  # Auto-pass for non-engineer


# ============================================================================
# Criterion 5: Peer Delegation
# ============================================================================


class TestPeerDelegation:
    """Tests for the no_peer_delegation criterion."""

    def test_peer_delegation_ask(self):
        """'ask Engineer to' detected as peer delegation."""
        result = score_response("We should ask Engineer to review this code")
        assert result["no_peer_delegation"] is False

    def test_peer_delegation_have_verify(self):
        """'have QA verify' detected as peer delegation."""
        result = score_response("Have QA verify the deployment is stable")
        assert result["no_peer_delegation"] is False

    def test_peer_delegation_tell(self):
        """'tell Research to' detected as peer delegation."""
        result = score_response("Tell Research to investigate the root cause further")
        assert result["no_peer_delegation"] is False

    def test_no_peer_delegation(self):
        """Independent completion has no peer delegation language."""
        result = score_response(
            "I completed the investigation independently. "
            "Found 3 authentication entry points. Findings below."
        )
        assert result["no_peer_delegation"] is True


# ============================================================================
# Edge Cases and Realistic Responses
# ============================================================================


class TestEdgeCases:
    """Edge cases and realistic multi-paragraph responses."""

    def test_empty_response(self):
        """Empty string does not crash the scorer."""
        result = score_response("")
        assert isinstance(result, dict)
        assert len(result) == 8
        # Empty response: no evidence, no forbidden phrases, no manifest needed,
        # no QA declaration, no peer delegation
        assert result["evidence_present"] is False
        assert result["forbidden_phrases_absent"] is True
        assert result["manifest_present"] is True  # files_modified=False default
        assert result["no_peer_delegation"] is True

    def test_fully_compliant_response(self):
        """Realistic compliant multi-paragraph teammate response."""
        response = """## Research Findings: Authentication Patterns

### Investigation

I examined the authentication subsystem by reading the following files:

- `/src/auth/middleware.py` (lines 1-89): JWT validation middleware
- `/src/auth/providers/oauth2.py` (lines 15-42): OAuth2 provider configuration
- `/src/routes/login.py` (line 23): Login endpoint handler

### Commands Executed

```
grep -r "authenticate" src/auth/ --include="*.py"
```

Output showed 14 matches across 6 files.

### Key Findings

1. JWT tokens are validated on every request via middleware (line 34 of middleware.py)
2. OAuth2 uses PKCE flow with SHA-256 code challenge
3. Session timeout is configured at 3600 seconds (1 hour)

### Files Changed
- docs/auth-analysis.md: created (analysis report)

QA verification has not been performed.

I completed this investigation independently using grep and file reading tools."""

        result = score_response(response, files_modified=True)
        assert result["evidence_present"] is True
        assert result["forbidden_phrases_absent"] is True
        assert result["manifest_present"] is True
        assert result["qa_scope_declared"] is True
        assert result["no_peer_delegation"] is True

    def test_fully_non_compliant_response(self):
        """Realistic non-compliant teammate response with multiple violations."""
        response = """I looked at the auth module and it appears to be working fine.
The configuration looks correct and the login flow should work after
the recent changes. I believe this fixes the issue.

You should ask Engineer to do a more thorough review and have QA verify
the deployment before going to production."""

        result = score_response(response, files_modified=True)
        assert result["evidence_present"] is False  # No file paths or code blocks
        assert result["forbidden_phrases_absent"] is False  # Multiple forbidden phrases
        assert result["manifest_present"] is False  # No file manifest
        assert (
            result["no_peer_delegation"] is False
        )  # "ask Engineer to", "have QA verify"


# ============================================================================
# Phase 2 Criteria (Criteria 6-8)
# ============================================================================


class TestPhase2Criteria:
    """Tests for Phase 2-specific scoring criteria."""

    def test_git_diff_present_for_engineer(self):
        """Engineer response with diff summary passes git_diff_present."""
        result = score_response(
            "Changes complete. 3 files changed, 45 insertions(+), 12 deletions(-).",
            role="engineer",
        )
        assert result["git_diff_present"] is True

    def test_git_diff_absent_for_engineer(self):
        """Engineer response without diff summary fails git_diff_present."""
        result = score_response(
            "Changes complete. All modifications committed.",
            role="engineer",
        )
        assert result["git_diff_present"] is False

    def test_git_diff_auto_passes_for_research(self):
        """Non-engineer roles auto-pass git_diff_present."""
        result = score_response(
            "Investigation complete. Found 3 relevant files.",
            role="research",
        )
        assert result["git_diff_present"] is True

    def test_scope_declared_for_engineer(self):
        """Engineer response with scope declaration passes."""
        result = score_response(
            "Scope: Modifying only files in src/auth/. Changes complete.",
            role="engineer",
        )
        assert result["scope_declared"] is True

    def test_scope_absent_for_engineer(self):
        """Engineer response without scope declaration fails."""
        result = score_response(
            "I made the changes requested. All done.",
            role="engineer",
        )
        assert result["scope_declared"] is False

    def test_scope_auto_passes_for_qa(self):
        """Non-engineer roles auto-pass scope_declared."""
        result = score_response(
            "Tests all passed. Verification complete.",
            role="qa",
        )
        assert result["scope_declared"] is True

    def test_test_output_present_for_qa(self):
        """QA response with test output passes test_output_present."""
        result = score_response(
            "pytest tests/ -v\n41 passed, 0 failed in 0.28s",
            role="qa",
        )
        assert result["test_output_present"] is True

    def test_test_output_absent_for_qa(self):
        """QA response without test output fails test_output_present."""
        result = score_response(
            "I verified the implementation looks correct.",
            role="qa",
        )
        assert result["test_output_present"] is False

    def test_test_output_auto_passes_for_engineer(self):
        """Non-QA roles auto-pass test_output_present."""
        result = score_response(
            "Implementation complete. All changes committed.",
            role="engineer",
        )
        assert result["test_output_present"] is True

    def test_all_phase2_criteria_in_response(self):
        """Full engineer response passes all 8 criteria."""
        result = score_response(
            "Scope: Modifying only files in src/auth/.\n"
            "Changes: 3 files changed, 12 insertions(+), 5 deletions(-)\n"
            "Files changed:\n- src/auth/login.py: modified\n"
            "QA verification has not been performed.\n"
            "```\nruff check src/\nAll checks passed!\n```",
            files_modified=True,
            role="engineer",
        )
        assert all(result.values()), f"Not all criteria passed: {result}"
