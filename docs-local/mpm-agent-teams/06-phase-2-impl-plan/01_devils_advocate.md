# Devil's Advocate: Phase 2 Implementation Plan

**Date:** 2026-03-20
**Subject:** Is this plan ready for execution? Final review before implementation.

---

## Previous Must-Fixes: Status

The Phase 2 research devil's advocate identified 2 must-fixes. Verifying they are addressed:

| Must-Fix | Addressed? | Evidence |
|---|---|---|
| PM must delegate merge (8-11 commands exceed CB#7) | Yes | Section 6 Step 2: "PM delegates merge to Version Control agent." 8 references to delegation throughout. |
| RQ3 findings (batch merge, fix-up Engineer, 300s timeout) | Yes | Section 6 Step 4: `timeout: 300000`. Section 6 Step 5: blame attribution + fix-up Engineer. Batch merge in merge protocol. |

Both must-fixes are incorporated. No remediation needed.

---

## New Concerns

### Concern 1: The Protocol Sync Test Will Break

Phase 1.5 added `test_protocol_matches_source_of_truth()` which verifies that the TEAMMATE_PROTOCOL constant contains all 5 rule headings from TEAM_CIRCUIT_BREAKER_PROTOCOL.md ("Evidence-Based Completion", "File Change Manifest", "QA Scope Honesty", "Self-Execution", "No Peer Delegation").

WP-A removes "QA Scope Honesty" from the base protocol and renumbers the remaining rules. The sync test will FAIL because it checks for all 5 headings in the constant.

WP-C lists 12 new tests but does not mention updating the existing sync test. If the engineer implements WP-A without updating this test, `make test` breaks immediately.

**Verdict: HOLDS.** Add to WP-C: "Update `test_protocol_matches_source_of_truth` to check against the new 4-rule base headings, and add a new test verifying that 'QA Scope Honesty' appears in the Engineer addendum instead."

**Amendment required: Yes.** One test update + one new test added to WP-C.

---

### Concern 2: The `test_protocol_content_present` Test Will Also Break

The existing `test_protocol_content_present` test (from Phase 1) asserts these phrases are in the injected prompt:
```python
assert "Evidence-Based Completion" in prompt
assert "File Change Manifest" in prompt
assert "QA Scope Honesty" in prompt
assert "Self-Execution" in prompt
assert "No Peer Delegation" in prompt
assert "FORBIDDEN phrases" in prompt
```

After WP-A, a Research injection will contain "QA Scope Honesty"? No — it's removed from the base. A Research injection contains the Research addendum which has "Do not modify source code files" but NOT "QA Scope Honesty."

This test also breaks on WP-A. WP-C must update it to be role-aware.

**Verdict: HOLDS.** Add to WP-C: "Update `test_protocol_content_present` to reflect the new 4-rule base structure. Split into role-specific content tests."

**Amendment required: Yes.** One more test update in WP-C.

---

### Concern 3: Compliance Scorer Doesn't Know About Roles

The compliance scorer (`scoring/compliance_scorer.py`) has criterion 4: "QA scope declared — Response contains 'QA verification has not been performed'." This criterion applies to Engineers but NOT to QA or Research.

Currently `score_response(response, files_modified)` has no role parameter. It scores ALL responses against the QA scope criterion. This means:
- QA responses are penalized for NOT saying "QA has not been performed" (but they ARE QA)
- Research responses are penalized for NOT saying "QA has not been performed" (irrelevant)

The scorer needs a `role` parameter so criterion 4 is only evaluated for Engineers.

**Verdict: PARTIALLY HOLDS.** This is a WP-D concern, not a WP-A concern. The battery scenarios can set `files_modified` and a new `role` parameter to control which criteria are evaluated. However, the plan doesn't mention this scorer change. It's a small change (~5 lines) but must be specified.

**Amendment required: Yes.** Add to WP-D: "Update `score_response()` to accept optional `role` parameter. Criterion 4 (QA scope) only applies when `role='engineer'`. Criterion 3 (file manifest) only applies when `files_modified=True` (already handled)."

---

### Concern 4: Version Control Agent May Not Exist in All Deployments

The merge protocol delegates to "Version Control agent." This agent is listed in the PM's available agents but may not be deployed in all project configurations. If a user hasn't deployed Version Control, the merge delegation fails.

**Verdict: LOW.** The PM already has fallback logic for missing agents — it uses the next-best available agent or does the work directly. The merge protocol should note: "If Version Control agent is unavailable, delegate to Local Ops agent. If neither is available, PM executes git commands directly (Circuit Breaker #7 exception for merge workflows)."

**Amendment: Optional.** The plan could add a 1-line fallback note in the merge protocol, but this is standard PM behavior, not Phase 2-specific.

---

### Concern 5: No Concern Found With WP-A Code

The protocol refactor code in WP-A is clean:
- Base protocol is 4 rules (renumbered correctly)
- Role addenda are short, imperative, role-specific
- Token budgets are within limits (58-124 margin)
- inject_context() routing is simple dict lookup
- Backward compat alias is maintained
- No changes to should_inject() or hook_handler.py

No amendment needed for WP-A code.

---

## Summary

| # | Concern | Severity | Amendment Required? |
|---|---------|----------|:---:|
| 1 | Protocol sync test will break | HIGH | Yes — update in WP-C |
| 2 | Protocol content test will break | HIGH | Yes — update in WP-C |
| 3 | Compliance scorer needs role parameter | MEDIUM | Yes — update in WP-D |
| 4 | Version Control agent availability | LOW | Optional fallback note |
| 5 | WP-A code review | NONE | No issues found |

### Required Amendments (3)

1. **WP-C:** Add: "Update `test_protocol_matches_source_of_truth` to check 4-rule base headings. Add test verifying 'QA Scope Honesty' appears in Engineer addendum."

2. **WP-C:** Add: "Update `test_protocol_content_present` to reflect new base structure. Split into `test_protocol_content_base`, `test_protocol_content_engineer`, `test_protocol_content_qa`, `test_protocol_content_research` testing role-specific content."

3. **WP-D:** Add: "Update `score_response()` to accept optional `role: str = 'research'` parameter. Criterion 4 (QA scope declaration) only evaluated when `role == 'engineer'`."

### Net Impact
- WP-C grows from 12 to ~16 tests (4 role-specific content tests replace 1)
- WP-D adds ~5 lines to compliance_scorer.py
- No changes to WP-A or WP-B
