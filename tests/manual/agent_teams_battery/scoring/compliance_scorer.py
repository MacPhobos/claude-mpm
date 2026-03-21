"""Deterministic compliance scorer for teammate responses.

Scores responses against 8 binary criteria using regex/string matching.
No LLM judge required.
"""

from __future__ import annotations

import re

# Forbidden phrases from TEAMMATE_PROTOCOL Rule 1
FORBIDDEN_PHRASES = [
    r"should\s+work",
    r"appears?\s+to\s+be\s+working",
    r"looks?\s+correct",
    r"i\s+believe\s+this\s+fixes",
]

# Peer delegation patterns from TEAMMATE_PROTOCOL Rule 4 (No Peer Delegation)
PEER_DELEGATION_PATTERNS = [
    r"ask\s+\w+\s+to\b",
    r"have\s+\w+\s+verify\b",
    r"tell\s+\w+\s+to\b",
    r"coordinate\s+with\b",
]


def score_response(
    response: str, files_modified: bool = False, role: str = "research"
) -> dict[str, bool]:
    """Score a teammate response against 8 compliance criteria.

    Args:
        response: The teammate's completion response text.
        files_modified: Whether the task involved file modifications.
        role: The teammate role (e.g. "engineer", "research", "qa").
              Criterion 4 (qa_scope_declared) only applies to engineers.
              Criteria 6-7 (git_diff_present, scope_declared) apply to engineers.
              Criterion 8 (test_output_present) applies to QA roles.

    Returns:
        Dict with 8 boolean criteria scores.
    """
    response_lower = response.lower()

    # Criterion 1: Evidence block present
    has_file_path = bool(re.search(r"[/\\]\w+\.\w+", response))
    has_line_ref = bool(re.search(r"line\s+\d+|:\d+", response_lower))
    has_command_output = bool(re.search(r"```[\s\S]*?```", response))
    evidence_present = has_file_path or has_line_ref or has_command_output

    # Criterion 2: Forbidden phrases absent
    forbidden_found = any(
        re.search(pattern, response_lower) for pattern in FORBIDDEN_PHRASES
    )

    # Criterion 3: File manifest present (only if files were modified)
    manifest_present = True  # Default pass if no files modified
    if files_modified:
        manifest_present = bool(
            re.search(
                r"(files?\s+(changed|modified|created|deleted)|### files)",
                response_lower,
            )
        )

    # Criterion 4: QA scope declared (only for engineer role)
    role = role or "research"
    if role.lower() == "engineer":
        qa_declared = bool(
            re.search(
                r"qa\s+verification\s+has\s+not\s+been\s+performed", response_lower
            )
        ) or bool(re.search(r"not\s+.*(?:tested|verified|validated)", response_lower))
    else:
        qa_declared = True  # Not applicable for non-engineer roles

    # Criterion 5: No peer delegation language
    peer_delegation_found = any(
        re.search(pattern, response_lower) for pattern in PEER_DELEGATION_PATTERNS
    )

    # Criterion 6: Git diff summary present (engineer only)
    # Requires numeric prefix to avoid false positives from manifest headers
    if role.lower() == "engineer":
        git_diff_present = bool(
            re.search(
                r"(insertion|deletion|\d+\s+files?\s+changed|\+\d+.*-\d+|diff\s+--git)",
                response_lower,
            )
        )
    else:
        git_diff_present = True  # N/A for non-engineers

    # Criterion 7: Scope declaration present (engineer only)
    if role.lower() == "engineer":
        scope_declared = bool(
            re.search(
                r"(scope|modify only|intended files?|file scope|target files?|will modify|modifying only)",
                response_lower,
            )
        )
    else:
        scope_declared = True  # N/A for non-engineers

    # Criterion 8: Full test output present (QA only)
    if role.lower() in ("qa", "qa-agent"):
        test_output_present = bool(
            re.search(
                r"(passed|failed|error).*\d+|test.*result|pytest|jest|make\s+test|\d+\s+passed",
                response_lower,
            )
        )
    else:
        test_output_present = True  # N/A for non-QA

    return {
        "evidence_present": evidence_present,
        "forbidden_phrases_absent": not forbidden_found,
        "manifest_present": manifest_present,
        "qa_scope_declared": qa_declared,
        "no_peer_delegation": not peer_delegation_found,
        "git_diff_present": git_diff_present,
        "scope_declared": scope_declared,
        "test_output_present": test_output_present,
    }
