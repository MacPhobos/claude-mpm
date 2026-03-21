"""Deterministic compliance scorer for teammate responses.

Scores responses against 5 binary criteria using regex/string matching.
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

# Peer delegation patterns from TEAMMATE_PROTOCOL Rule 5
PEER_DELEGATION_PATTERNS = [
    r"ask\s+\w+\s+to\b",
    r"have\s+\w+\s+verify\b",
    r"tell\s+\w+\s+to\b",
    r"coordinate\s+with\b",
]


def score_response(response: str, files_modified: bool = False) -> dict[str, bool]:
    """Score a teammate response against 5 compliance criteria.

    Args:
        response: The teammate's completion response text.
        files_modified: Whether the task involved file modifications.

    Returns:
        Dict with 5 boolean criteria scores.
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

    # Criterion 4: QA scope declared (for implementation roles)
    qa_declared = bool(
        re.search(r"qa\s+verification\s+has\s+not\s+been\s+performed", response_lower)
    ) or bool(re.search(r"not\s+.*(?:tested|verified|validated)", response_lower))

    # Criterion 5: No peer delegation language
    peer_delegation_found = any(
        re.search(pattern, response_lower) for pattern in PEER_DELEGATION_PATTERNS
    )

    return {
        "evidence_present": evidence_present,
        "forbidden_phrases_absent": not forbidden_found,
        "manifest_present": manifest_present,
        "qa_scope_declared": qa_declared,
        "no_peer_delegation": not peer_delegation_found,
    }
