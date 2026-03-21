# RQ7: SendMessage Coordination — Decision Brief

**Phase:** 2 Research
**Date:** 2026-03-20
**Status:** Resolved (deferred to Phase 3)
**Severity:** Downgraded per devil's advocate review (Concern 3)

---

## Decision

**Rule 5 (No Peer Delegation) is maintained in Phase 2. All coordination flows through the PM.**

Phase 2's goal is to prove that parallel Engineering works with worktree isolation and PM-mediated orchestration. Relaxing the peer coordination model introduces a second experimental variable alongside the already-complex merge/conflict problem. The coordination model change is deferred to Phase 3, contingent on Phase 2 success.

---

## Why Peer Coordination Is Deferred

### 1. Four Risks from the Peer-to-Peer Risk Matrix

The TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 5 catalogs four risks that apply directly to peer SendMessage coordination:

| Risk | Description | Residual Rating | Why It Blocks Phase 2 |
|------|-------------|:-:|---|
| **Unauthorized Delegation** (Risk 1) | Teammate A asks B to implement work, then claims credit. Violates CB#5 (Delegation Chain) and CB#3 (Unverified Assertions). | MEDIUM | Git diff can detect who modified files, but if Engineer A fabricates matching evidence and Engineer B cooperates, detection is difficult. Adding this ambiguity to Phase 2's already-complex merge coordination is unacceptable. |
| **Collective Unverified Completion** (Risk 2) | Engineer tells QA "it works" via SendMessage. QA parrots the claim without running tests. Rated the HIGHEST risk — hardest to mitigate with prompts alone. | HIGH | This risk is already the single most dangerous failure mode in the protocol. Allowing SendMessage between Engineers and QA creates the exact collusion channel this risk describes. |
| **File Tracking Omission** (Risk 3) | Teammates modify files during peer-coordinated work but omit changes from their manifest. | LOW | Low residual because git provides ground truth, but peer coordination increases the surface area of unreported changes. |
| **Shadow Workflow** (Risk 4) | Multiple teammates self-organize into an undisclosed Research-Implement-Test pipeline, bypassing PM's phase-by-phase verification. Violates CB#5, CB#8, and CB#3. | MEDIUM | The entire value of PM-mediated orchestration is phase-by-phase verification. Peer SendMessage is the mechanism by which shadow workflows form. |

### 2. SendMessage Is Not Hookable

TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 6 explicitly identifies SendMessage as a platform built-in that MPM cannot intercept:

> "SendMessage content compliance. The Teammate Protocol Block tells teammates not to delegate via SendMessage. But there is no mechanism to block or inspect SendMessage content in real time."

The hooks API has no "reject" return path (confirmed in Phase 1.5 investigation WP2). MPM can log SendMessage events via PostToolUse, but cannot prevent a teammate from sending a delegation request. Detection is post-hoc only.

Until Claude Code provides a mechanism to inspect or gate SendMessage content, peer coordination cannot be enforced programmatically — only instructed via prompts.

### 3. Phase 2 Already Introduces Sufficient Complexity

Phase 2 introduces three major new variables simultaneously:

1. **Parallel file writes** — Engineers modifying code in separate worktrees
2. **Merge conflicts** — Git conflict detection, resolution, and integration testing
3. **Mixed-role teams** — Research + Engineer + QA in coordinated sessions

Adding peer-to-peer coordination as a fourth variable would make failure attribution impossible. If a Phase 2 team fails, was it the merge strategy? The coordination model? The conflict resolution? The peer delegation? Isolating variables requires keeping the coordination model stable (PM-mediated) while testing the new engineering variables.

---

## What Phase 3 Might Explore

If Phase 2 demonstrates that parallel Engineering works reliably with PM-mediated coordination, Phase 3 could investigate controlled peer communication:

- **Interface contract sharing:** Engineer A finishes an API endpoint and sends the interface spec to Engineer B via SendMessage, with PM copied. This avoids full PM round-trips for mechanical information sharing.
- **Early termination signals:** In parallel Research, if one researcher finds the complete answer, it could signal peers to stop via SendMessage rather than waiting for the PM to notice and relay.
- **QA failure notifications:** QA teammate discovers a test failure and notifies the responsible Engineer directly, reducing PM context churn for simple fix-retry cycles.

All of these would require either (a) a SendMessage inspection hook from Claude Code, or (b) a structured messaging protocol where teammates include metadata that PostToolUse logging can validate. Neither exists today.

---

## References

- `02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md` Section 5 (Peer-to-Peer Risk Matrix)
- `02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md` Section 6 (Residual Risk Summary)
- `04-phase-1.5/investigation/01_wp2_parallel_research.md` Section 2 (Hook API limitations)
- `05-phase-2-research/devils_advocate.md` Concern 3 (RQ7 downgrade rationale)
