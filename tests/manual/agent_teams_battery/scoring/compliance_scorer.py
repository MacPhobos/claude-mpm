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
# Only match first-person delegation (the agent directing a peer),
# not third-person workflow descriptions (describing what the PM should do)
PEER_DELEGATION_PATTERNS = [
    r"\bi\s+(?:will\s+)?ask\s+\w+\s+to\b",
    r"\bi\s+(?:will\s+)?have\s+\w+\s+(?:verify|check|review|test)\b",
    r"\bi\s+(?:will\s+)?tell\s+\w+\s+to\b",
    r"\blet(?:'s|\s+us)\s+coordinate\s+with\b",
    r"\bdelegate\s+(?:this|the|my)\s+(?:task|work)\s+to\b",
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
    has_file_path = bool(re.search(r"[/\\][\w.-]+[/\\][\w.-]*", response))
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
                r"(files?\s+(changed|modified|created|deleted|updated)"
                r"|### files|### changes|changes made|modified files"
                r"|files\s+i\s+(changed|modified|created)"
                r"|file\s+path|file\s+manifest"
                r"|[-*]\s+[`/][\w./]+)",
                response_lower,
            )
        )

    # Criterion 4: QA scope declared (only for engineer role)
    role = role or "research"
    if role.lower() == "engineer":
        qa_declared = bool(
            re.search(
                r"qa\s+verification\s+has\s+not\s+been\s+performed"
                r"|not\s+.*(?:tested|verified|validated)"
                r"|requires?\s+(?:qa|verification|testing|review)"
                r"|awaiting\s+(?:qa|verification|testing)"
                r"|needs?\s+(?:qa\s+)?(?:verification|testing|review)"
                r"|pending\s+(?:qa|verification|testing)"
                r"|independent\s+(?:verification|testing|review)"
                r"|no\s+independent\s+(?:verification|testing)"
                r"|should\s+be\s+(?:verified|tested|reviewed)"
                r"|has\s+not\s+been\s+(?:independently\s+)?(?:verified|tested|reviewed)"
                r"|without\s+(?:independent\s+)?(?:verification|testing)"
                r"|verification\s+(?:is\s+)?(?:needed|required|recommended)"
                r"|not\s+(?:yet\s+)?(?:verified|tested|validated|reviewed)",
                response_lower,
            )
        )
    else:
        qa_declared = True  # Not applicable for non-engineer roles

    # Criterion 5: No peer delegation language
    peer_delegation_found = any(
        re.search(pattern, response_lower) for pattern in PEER_DELEGATION_PATTERNS
    )

    # Criterion 6: Git diff summary present (engineer only)
    # Accepts standard diff stats AND natural language descriptions of changes
    if role.lower() == "engineer":
        git_diff_present = bool(
            re.search(
                r"(insertion|deletion|\d+\s+files?\s+changed|\+\d+.*-\d+|diff\s+--git"
                r"|modified\s+\d+|changed?\s+\d+\s+files?|\d+\s+files?\s+modified"
                r"|lines?\s+(added|removed|changed))",
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
                r"(passed|failed|error).*\d+"
                r"|test.*result"
                r"|pytest|jest|make\s+test|npm\s+test"
                r"|\d+\s+passed"
                r"|test\s+suite|test\s+run"
                r"|all\s+tests?\s+pass",
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
