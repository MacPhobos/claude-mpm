# Phase 2 Implementation Plan: Parallel Engineering & Mixed Teams

**Issue:** #290
**Phase:** 2 (Implementation -- gated on Phase 1.5 success)
**Date:** 2026-03-20
**Branch:** mpm-teams
**Synthesized from:** RQ0+RQ1+RQ2 (worktree/merge), RQ4 (compositions), RQ5 (orchestration), RQ6 (protocol extensions), RQ7 (SendMessage), RQ8 (rollback/recovery)
**Devil's advocate amendments incorporated:** RQ0 baseline added, RQ1+RQ2 merged, RQ4 narrowed to user demand, RQ7 downgraded to brief note
**Pending:** RQ3 (build verification protocol) -- not yet written; will be folded in as addendum

---

## 1. Executive Summary

Phase 2 extends MPM Agent Teams from parallel Research (read-only, conflict-free) to parallel Engineering (file writes, merge conflicts, integration testing) and multi-phase pipelines (Research-then-Engineer, Engineer-then-QA). The key finding across all research questions is that **this is primarily an INSTRUCTION problem, not a CODE problem.** The underlying platform mechanics -- git worktrees, `isolation: "worktree"`, Claude Code Agent Teams lifecycle -- already work correctly. What is missing is PM behavioral guidance for merge-test-cleanup workflows, role-specific teammate protocol extensions, and composition decision rules. The estimated implementation effort is **3-5 days** of work, with approximately 70% instruction text and 30% Python code changes.

---

## 2. Go/No-Go Recommendation

### Recommendation: GO

Phase 2 should proceed, subject to these conditions:

| Condition | Status | Notes |
|-----------|--------|-------|
| Phase 1.5 Gate 1 (Compliance CI lower bound > 70%) | Required | If Research compliance is poor, Engineering compliance will be worse |
| Phase 1.5 Gate 3 (Auto-detection working) | Required | Phase 2 builds on the same activation mechanism |
| Phase 1.5 Gate 2 (Context reduction) | Optional | If context claim dropped, proceed but PM orchestration limits become binding constraint |

### Rationale

1. **Worktree merge is solved.** The RQ1+RQ2 experiment verified that git's `ort` strategy auto-merges same-file-different-section changes, and `git merge --no-commit` provides safe conflict pre-detection with clean abort. No unsolvable merge problems were found.

2. **Scope is manageable.** Phase 2 delivers ~100 lines of PM instruction changes, ~30 lines of Python code changes, and ~50 new test lines. This is a 3-5 day effort, not a multi-week project.

3. **User demand is clear.** Issue #290 specifies three use cases (complex features, large refactoring, security audit) that all require parallel Engineering. Phase 1 Research-only teams were explicitly a stepping stone.

4. **Risk mitigations exist.** Sequential fallback is always available. The 3-failure abort threshold prevents runaway team sessions. PM-mediated coordination (Rule 5 maintained) keeps the audit trail clean.

### Conditions That Would Block Go

- Phase 1.5 Gate 1 fails with CI lower bound < 70%: Fix compliance first
- A Claude Code platform change breaks worktree isolation semantics
- `isolation: "worktree"` is deprecated or removed from the Agent tool API

---

## 3. Scope: What Phase 2 Delivers

### Supported Team Compositions

Source: RQ4, narrowed to the three user-demanded patterns from Issue #290.

| Composition | Use Case (Issue #290) | Roles | Phases | Max Team Size |
|-------------|----------------------|-------|:------:|:-------------:|
| **All-Engineer Parallel** | Large Refactoring: "Multiple engineers on different subsystems" | 2-3 Engineers | 1 parallel + merge gate | 3 |
| **Engineer-then-QA Pipeline** | Complex Features: "Frontend + backend + test coordinating" | 2-3 Engineers + 1 QA | 2 (Engineer parallel, then QA sequential) | 4 |
| **Research-then-Engineer Pipeline** | Security Audit: "Research + implementation + verification" | 2-3 Research + 2-3 Engineers (+ optional QA) | 2-3 sequential | 7 total (max 3 simultaneous) |

### What Phase 2 Explicitly Does NOT Support

| Anti-Pattern | Why Excluded |
|---|---|
| Mixed Research + Engineer in a single parallel phase | Engineer depends on Research findings; must be sequential phases (RQ4 Section 4, Anti-Pattern 2) |
| QA running parallel with Engineers | QA must test MERGED code, not in-flight code (RQ4 Section 4, Anti-Pattern 3) |
| More than 3 Engineers in a single parallel phase | Merge complexity grows combinatorially; PM context degrades (RQ4 Section 4, Anti-Pattern 4; RQ5 Section 3) |
| Peer-to-peer coordination via SendMessage | Rule 5 maintained; SendMessage not hookable; deferred to Phase 3 (RQ7) |
| Automated merge conflict resolution | PM presents conflicts to user; automated merge agent deferred to Phase 3 (RQ1+RQ2 Section 5) |
| Teams for tasks a single Engineer completes in <15 minutes | Orchestration overhead exceeds parallelism benefit (RQ4 Section 4, Anti-Pattern 5) |

---

## 4. Implementation Work Packages

### WP-A: TEAMMATE_PROTOCOL Role Extensions

**Description:** Refactor the monolithic `TEAMMATE_PROTOCOL` constant into a base protocol plus role-specific addenda (Option C from RQ6). Remove Rule 3 from base (it is role-specific), add Engineer, QA, and Research addendum constants, add role-routing logic to `inject_context()`.

**Source:** RQ6 Sections 6-9

**Files to modify/create:**

| File | Change | Lines |
|------|--------|:-----:|
| `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py` | Refactor `TEAMMATE_PROTOCOL` into `TEAMMATE_PROTOCOL_BASE` + `TEAMMATE_PROTOCOL_ENGINEER` + `TEAMMATE_PROTOCOL_QA` + `TEAMMATE_PROTOCOL_RESEARCH`. Add `_ROLE_ADDENDA` mapping dict. Modify `inject_context()` to assemble protocol from base + addendum based on `subagent_type`. Keep `TEAMMATE_PROTOCOL` as backward-compatibility alias. Remove Phase 1 warning for non-research subagent_type (it is now expected). | ~40 added, ~15 modified |

**Detailed code changes:**

1. **New constants** (insert after current line 55):
   - `TEAMMATE_PROTOCOL_BASE` -- RQ6 Section 8a text (4 rules, ~330 tokens, Rule 3 removed and renumbered)
   - `TEAMMATE_PROTOCOL_ENGINEER` -- RQ6 Section 8b text (~112 tokens: QA-not-performed declaration, scope declaration, lint check, diff summary, worktree awareness)
   - `TEAMMATE_PROTOCOL_QA` -- RQ6 Section 8c text (~108 tokens: independent evidence, clean state, full output, engineer attribution, merged code testing)
   - `TEAMMATE_PROTOCOL_RESEARCH` -- RQ6 Section 8d text (~46 tokens: no source code modification, cite file:line)
   - `_ROLE_ADDENDA` -- dict mapping `subagent_type` strings to addendum constants
   - `TEAMMATE_PROTOCOL` -- kept as alias for `TEAMMATE_PROTOCOL_BASE` (backward compat)

2. **Modified `inject_context()`** (lines 119-157):
   - Replace unconditional `TEAMMATE_PROTOCOL` usage with: `protocol = TEAMMATE_PROTOCOL_BASE` then `addendum = _ROLE_ADDENDA.get(subagent_type.lower(), "")` then `if addendum: protocol += "\n\n" + addendum`
   - Remove the Phase 1 "non-research WARNING" log (lines 141-146) since non-research roles are now expected
   - Update the logging line to include `addendum={'yes' if addendum else 'none'}`

**Token budget verification:**

| Role | Base | Addendum | Total | Within 500? | Margin |
|------|:----:|:--------:|:-----:|:-----------:|:------:|
| Engineer | 330 | 112 | 442 | Yes | 58 |
| QA | 330 | 108 | 438 | Yes | 62 |
| Research | 330 | 46 | 376 | Yes | 124 |

**Effort:** 0.5 days
**Dependencies:** None (can start immediately)

---

### WP-B: PM_INSTRUCTIONS.md Phase 2 Section

**Description:** Expand the "Agent Teams: Parallel Research" section into a comprehensive "Agent Teams" section covering compositions, orchestration flows, merge protocol, and failure handling. Keep existing Research rules intact; add Engineering and Pipeline subsections.

**Source:** RQ4 Sections 3+5, RQ5 Sections 2+4+5, RQ8 Section 6

**Files to modify:**

| File | Change | Lines |
|------|--------|:-----:|
| `src/claude_mpm/agents/PM_INSTRUCTIONS.md` | Rename section header. Add composition decision table, phase-based orchestration model, merge protocol, recovery protocol, worktree cleanup, team size limits, engineering anti-patterns. | ~50 lines added |

**Section structure (within PM_INSTRUCTIONS.md):**

Current section occupies lines 1135-1184 (~50 lines). Phase 2 expands this to ~100 lines total. The structure:

```
## Agent Teams                                              (renamed from "Agent Teams: Parallel Research")

### When to Use Teams                                       (existing, expanded with Engineering criteria)
  - Research criteria (existing, unchanged)
  - Engineering criteria (NEW: >=2 independent subsystems, <20% file overlap)
  - Pipeline criteria (NEW: investigation-then-implementation workflow)

### Compositions                                            (NEW: ~15 lines)
  Decision table: All-Engineer / Eng-then-QA / Research-then-Eng
  Composition selection flow (condensed from RQ4 Section 3)

### Spawning Protocol                                       (existing, expanded)
  - Research spawning (existing, unchanged)
  - Engineering spawning (NEW: isolation="worktree" required, scope declaration in prompt)
  - Pipeline spawning (NEW: phase-by-phase, transition summaries)

### Merge Protocol                                          (NEW: ~15 lines)
  - Sequential merge order (merge A, test-merge B with --no-commit)
  - Conflict classification (trivial: PM resolves; non-trivial: escalate to user)
  - Integration test after all merges

### Recovery Protocol                                       (NEW: ~10 lines)
  - Teammate failure: assess worktree, retry or proceed
  - Merge conflict: resolve/delegate/abort
  - 3-failure abort threshold -> fall back to sequential

### Worktree Cleanup                                        (NEW: ~5 lines)
  - git worktree list after every team session
  - Remove merged worktrees, force-remove failed worktrees
  - Verify only main worktree remains

### Anti-Patterns                                           (existing, expanded: ~10 lines added)
  - Existing Research anti-patterns (unchanged)
  - NEW: Two Engineers on overlapping files without worktree isolation
  - NEW: QA parallel with Engineers (QA must test merged code)
  - NEW: Mixed Research + Engineer in same parallel phase
  - NEW: >3 Engineers in single phase
  - NEW: Teams for <15-minute tasks

### Fallback                                                (existing, unchanged)
```

**Estimated line count:**

| Sub-section | New Lines |
|---|:---:|
| Composition decision table | 15 |
| Engineering anti-patterns | 10 |
| Phase-based orchestration + spawning rules | 10 |
| Merge protocol | 15 |
| Recovery protocol + abort threshold | 10 |
| Worktree cleanup | 5 |
| Team size limits | 3 |
| **Total new lines** | **~68** |
| Existing lines modified/removed | ~5 (header rename, anti-pattern line update) |
| **Net section size** | **~113 lines** (current ~50 + ~68 new - ~5 modified) |

**Effort:** 1 day
**Dependencies:** WP-A (protocol extensions define what "Engineer" and "QA" teammates are)

---

### WP-C: Worktree Merge Protocol

**Description:** This is the instructional content embedded in WP-B (PM_INSTRUCTIONS.md merge protocol subsection), plus the operational knowledge the PM needs. No code changes -- this is entirely PM behavioral guidance.

**Source:** RQ1+RQ2 Sections 3-5

**What the PM must be instructed to do:**

```
Post-Completion Merge Lifecycle:

1. COLLECT: Wait for all Engineer completion messages
2. MERGE SEQUENTIALLY:
   a. git merge <branch-A>           (first merge: fast-forward)
   b. git merge <branch-B> --no-commit   (subsequent merges: dry-run)
      - If clean: git commit
      - If conflict: git merge --abort -> escalate to user
   c. Repeat for branch-C
3. TEST: Run integration tests (make test / uv run pytest)
   - Pass: proceed to report (or QA phase)
   - Fail: identify responsible branch, revert, delegate fix
4. CLEAN UP: git worktree remove <path> + git branch -d <branch>
5. VERIFY: git worktree list shows only main worktree
```

**Files affected:** Only `PM_INSTRUCTIONS.md` (captured in WP-B line counts)

**Effort:** Included in WP-B (0 additional)
**Dependencies:** RQ1+RQ2 findings (complete)

---

### WP-D: Recovery Protocol

**Description:** Instructional content defining PM behavior when teammates fail, merges conflict, or integration tests break. Embedded in WP-B (PM_INSTRUCTIONS.md recovery protocol subsection).

**Source:** RQ8 Sections 2, 4, 5

**Key decision rules for PM:**

| Failure | PM Action |
|---------|-----------|
| 1 of N Engineers fails, others succeed | Proceed without; note gap; user can request follow-up |
| Multiple Engineers fail (>=50% of team) | Abort team; fall back to sequential |
| Merge conflict (trivial: whitespace, imports) | PM resolves automatically |
| Merge conflict (non-trivial: logic overlap) | Present both versions to user for decision |
| Integration tests fail (attributable to one branch) | Revert that branch; delegate fix sequentially |
| Integration tests fail (interaction between branches) | Revert both; delegate unified fix to single Engineer |
| 3 total failures in session | Abort team; fall back to sequential; report to user |
| Stale worktrees after session | PM cleans up per worktree cleanup protocol |

**Abort threshold:** 3 failures per team session (aligned with existing CB#10 delegation failure limit, extended to team-wide scope).

**Files affected:** Only `PM_INSTRUCTIONS.md` (captured in WP-B line counts)

**Effort:** Included in WP-B (0 additional)
**Dependencies:** RQ8 findings (complete)

---

### WP-E: Unit Tests

**Description:** Add fast, deterministic tests for the protocol extension code changes (WP-A). These run in `make test` with `-n auto`.

**Source:** RQ6 Section 11 (recommended actions)

**Files to create/modify:**

| File | Change | Lines |
|------|--------|:-----:|
| `tests/hooks/test_teammate_context_injector.py` | Add tests for role-based protocol assembly | ~60 added |

**New test cases:**

| Test | What It Verifies |
|------|-----------------|
| `test_engineer_protocol_includes_base_plus_engineer_addendum` | Engineer subagent_type gets base + engineer rules |
| `test_qa_protocol_includes_base_plus_qa_addendum` | QA subagent_type gets base + QA rules |
| `test_research_protocol_includes_base_plus_research_addendum` | Research subagent_type gets base + research rules |
| `test_unknown_role_gets_base_only` | Unknown/missing subagent_type gets base protocol only |
| `test_engineer_protocol_contains_scope_declaration_rule` | Engineer addendum includes "Declare intended file scope" |
| `test_engineer_protocol_contains_qa_not_performed` | Engineer addendum includes QA-not-performed statement |
| `test_qa_protocol_contains_merged_code_rule` | QA addendum includes "Test against the MERGED code" |
| `test_qa_protocol_does_not_contain_old_rule3` | QA protocol does NOT contain "QA verification has not been performed" |
| `test_base_protocol_does_not_contain_old_rule3` | Base protocol does not contain the conditional Rule 3 |
| `test_all_role_variants_within_token_budget` | All role variants produce protocol text < 2000 characters (~500 tokens) |
| `test_backward_compat_teammate_protocol_alias` | `TEAMMATE_PROTOCOL` constant still exists and is usable |
| `test_inject_context_logs_addendum_status` | Log message includes addendum presence for each role |

**Effort:** 0.5 days
**Dependencies:** WP-A (code changes must exist before tests)

---

### WP-F: Documentation

**Description:** Update design documents to reflect Phase 2 decisions. Create a Phase 2 results document after implementation.

**Source:** All RQ findings

**Files to create/modify:**

| File | Change | Lines |
|------|--------|:-----:|
| `docs-local/mpm-agent-teams/05-phase-2-research/03_build_verification.md` | Create: build verification protocol addendum (deferred during research; write during implementation) | ~80 |
| `docs-local/mpm-agent-teams/06-phase-2/phase2_implementation_results.md` | Create: what was built, test evidence, compliance data | ~150 (post-implementation) |

**Effort:** 0.5 days (split: 0.25 days during implementation for RQ3 addendum, 0.25 days post-implementation for results)
**Dependencies:** All other WPs complete

---

## 5. Code Changes (Specific)

### File-by-File Change Summary

| # | File Path | Type | What Changes | Est. Lines | Instruction or Code? |
|:-:|-----------|------|-------------|:----------:|:--------------------:|
| 1 | `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py` | Python | Refactor TEAMMATE_PROTOCOL into base + 3 role addenda. Add `_ROLE_ADDENDA` dict. Modify `inject_context()` for role routing. Remove Phase 1 non-research warning. Keep backward-compat alias. | +40 / ~15 modified | Code |
| 2 | `src/claude_mpm/agents/PM_INSTRUCTIONS.md` | Markdown | Expand "Agent Teams" section: compositions, merge protocol, recovery protocol, worktree cleanup, engineering anti-patterns, team size limits | +68 / ~5 modified | Instruction text |
| 3 | `tests/hooks/test_teammate_context_injector.py` | Python | Add 12 tests for role-based protocol assembly, token budget, backward compat | +60 | Code (test) |
| 4 | `docs-local/mpm-agent-teams/05-phase-2-research/03_build_verification.md` | Markdown | RQ3 addendum: build verification protocol design | +80 | Documentation |
| 5 | `docs-local/mpm-agent-teams/06-phase-2/phase2_implementation_results.md` | Markdown | Implementation results, test evidence, gate status | +150 | Documentation |

**Totals:**

| Category | Lines Added | Lines Modified |
|----------|:----------:|:--------------:|
| Python code (production) | ~40 | ~15 |
| Python code (test) | ~60 | 0 |
| Instruction text (PM_INSTRUCTIONS.md) | ~68 | ~5 |
| Documentation | ~230 | 0 |
| **Grand total** | **~398** | **~20** |

**Ratio:** ~73% instruction/documentation, ~27% code. This confirms the core finding: Phase 2 is an INSTRUCTION problem.

---

## 6. Testing Strategy

### Fast Tests (in `make test`)

| Test File | New Tests | What They Cover |
|-----------|:---------:|-----------------|
| `tests/hooks/test_teammate_context_injector.py` | 12 | Role-based protocol assembly (Engineer, QA, Research, unknown), token budget per role, backward compatibility, Rule 3 removal verification, addendum logging |

All 12 tests are fast, deterministic, no LLM, no network. They exercise the `TeammateContextInjector` class directly with mocked inputs.

**Verification command:** `cd /Users/mac/workspace/claude-mpm-fork && uv run pytest tests/hooks/test_teammate_context_injector.py -v`

### Battery Extension (in `make test-agent-teams`)

The Phase 1.5 compliance battery (35 tasks) should be extended with Phase 2 scenarios:

| Scenario Category | Tasks | What They Test |
|-------------------|:-----:|----------------|
| Engineer teammate protocol compliance | 5 | Do Engineer teammates declare scope, include diff summary, state QA-not-performed? |
| QA teammate protocol compliance | 3 | Does QA provide independent evidence, full command output, engineer attribution? |
| All-Engineer parallel merge | 3 | Does PM merge worktrees, detect conflicts, run integration tests? |
| Engineer-then-QA pipeline | 2 | Does PM correctly sequence Engineering phase -> QA phase? |
| Failure/recovery scenarios | 2 | Does PM handle teammate timeout, abort after 3 failures? |
| **Total Phase 2 additions** | **15** | |

**Combined battery size:** 35 (Phase 1) + 15 (Phase 2) = 50 tasks.

**Note:** Battery execution requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` and cannot run in CI.

### Integration Validation (Merge Workflow)

The merge workflow is instruction-driven (PM follows PM_INSTRUCTIONS.md), not code-driven. Validation is through battery scenarios, not unit tests. The three merge battery scenarios test:

1. **Clean merge (2 Engineers, non-overlapping files):** PM merges both worktrees, runs tests, reports success.
2. **Conflict merge (2 Engineers, overlapping file):** PM detects conflict via `git merge --no-commit`, aborts, reports to user.
3. **Semantic conflict (2 Engineers, clean merge, test failure):** PM merges successfully, tests fail, PM identifies responsible branch.

---

## 7. PM_INSTRUCTIONS.md Change Budget

### Current State

| Metric | Value |
|--------|:-----:|
| Current "Agent Teams" section | Lines 1135-1184 (~50 lines) |
| Current content | Research-only: when to use, spawning protocol, anti-patterns, fallback |

### Phase 2 Additions

| Topic | Lines Added | Source RQ |
|-------|:----------:|:---------:|
| Composition decision table | 15 | RQ4 |
| Engineering anti-patterns | 10 | RQ4 |
| Phase-based orchestration + spawning rules | 10 | RQ5 |
| Merge protocol | 15 | RQ1+RQ2 |
| Recovery protocol + abort threshold | 10 | RQ8 |
| Worktree cleanup | 5 | RQ8 |
| Team size limits | 3 | RQ5 |
| **Total additions** | **~68** | |

### Projected Section Size

| Metric | Value |
|--------|:-----:|
| Current section | ~50 lines |
| Phase 2 additions | ~68 lines |
| Lines removed/modified | ~5 |
| **Projected total** | **~113 lines** |

### Context Window Constraint

The PM_INSTRUCTIONS.md file is loaded into PM context at session start. Adding ~68 lines (~2000 characters, ~500 tokens) is within acceptable limits. For reference:
- The entire PM_INSTRUCTIONS.md is ~1190 lines currently
- Adding 68 lines is a 5.7% increase
- The Agent Teams section growing from 50 to 113 lines keeps it comparable to other major sections (e.g., the delegation rules section)

**Conciseness guideline:** Each instruction should be a single imperative sentence. No flowcharts, no detailed tables, no theory. The detailed orchestration flows documented in RQ5 are for engineering reference, NOT for inclusion in PM_INSTRUCTIONS.md. The PM instructions contain actionable rules; the research docs contain the reasoning.

---

## 8. Checkpoint Gate

### Compliance Data Collection Model

Phase 2 uses the **passive compliance collection model** established in Phase 1.5. Compliance data accumulates automatically during implementation and testing:

1. **During implementation:** Every `make test` run exercises the injection code paths and produces structured compliance log entries via `_compliance_log()`.

2. **During battery runs:** Every `make test-agent-teams` scenario produces JSONL entries recording:
   - `injection_event`: protocol variant injected (base + which addendum)
   - `completion_event`: teammate response, evidence presence, role match

3. **At gate evaluation:** Run `python scripts/audit_agent_teams_compliance.py --gate` to compute Clopper-Pearson CI on accumulated data.

### When to Run `--gate` Evaluation

Run gate evaluation after:
- All WPs (A through F) are complete
- At least 15 Phase 2 battery scenarios have been executed
- Combined battery has >= 30 data points per stratum (Research, Engineer, QA)

### What Blocks Final Merge

| Gate | Criterion | Blocks Merge? |
|------|-----------|:-------------:|
| All fast tests pass | `make test` exits 0 | YES |
| Protocol token budget | All role variants < 500 tokens | YES |
| Engineer injection routing | Engineer subagent_type receives engineer addendum | YES |
| QA injection routing | QA subagent_type receives QA addendum | YES |
| Backward compatibility | `TEAMMATE_PROTOCOL` alias still works | YES |
| Compliance CI (if battery run) | 95% CI lower bound > 70% per stratum | YES (if battery data exists) |
| PM_INSTRUCTIONS.md section size | Agent Teams section < 120 lines | Advisory (not blocking) |

---

## 9. Timeline

### Day-by-Day Execution Plan

| Day | Work Package | Deliverable | Parallelizable? |
|:---:|:---:|---|:---:|
| 1 | **WP-A** | `teammate_context_injector.py` refactored: base + 3 role addenda + routing logic. Backward-compat alias in place. | No (foundation for everything else) |
| 1 | **WP-E** (partial) | 6 of 12 tests written and passing (role assembly tests) | Yes (with WP-A, write tests as code lands) |
| 2 | **WP-B** | PM_INSTRUCTIONS.md expanded: compositions, merge protocol, recovery, cleanup, anti-patterns | No (depends on WP-A for role definitions) |
| 2 | **WP-E** (complete) | Remaining 6 tests written and passing (budget, compat, logging tests) | Yes (with WP-B) |
| 3 | **WP-F** (partial) | `03_build_verification.md` written (RQ3 addendum) | Yes (independent) |
| 3 | Battery extension | 15 Phase 2 scenarios added to battery | Yes (with WP-F) |
| 4 | Battery execution | Run `make test-agent-teams` with Phase 2 scenarios | No (requires all code/instruction changes) |
| 4 | Gate evaluation | `audit_agent_teams_compliance.py --gate` on combined data | No (requires battery data) |
| 5 | **WP-F** (complete) | `phase2_implementation_results.md` written | No (requires gate results) |
| 5 | Final review | Code review, documentation review, merge PR | No |

### Parallelization Opportunities

```
Day 1:  WP-A (code) -----+------> WP-E partial (tests, 6 of 12)
                          |
Day 2:  WP-B (instructions) ----> WP-E complete (tests, 6 of 12)
                          |
Day 3:  WP-F partial ----+------> Battery extension
        (RQ3 addendum)   |
                          |
Day 4:  Battery execution -------> Gate evaluation
                          |
Day 5:  WP-F complete -----------> Final review + merge
```

**Critical path:** WP-A -> WP-B -> Battery execution -> Gate evaluation
**Total estimated effort:** 3-5 days (3 days if battery runs smoothly, 5 days if retries needed)

---

## 10. Risks and Mitigations

### Synthesized from All RQ Findings

| # | Risk | Source | Severity | Likelihood | Mitigation |
|:-:|------|--------|:--------:|:----------:|------------|
| 1 | PM context degrades with 5+ teammate results | RQ5 Section 3 | MEDIUM | Medium | Hard limit: 3 teammates per phase, 7 total per pipeline. Progressive summarization at phase transitions. |
| 2 | Merge conflicts in parallel Engineering | RQ1+RQ2 Section 4 | MEDIUM | Medium | Pre-flight file overlap check (<20%). `git merge --no-commit` for safe detection. PM escalates non-trivial conflicts to user. |
| 3 | Semantic conflicts (tests pass individually, fail together) | RQ1+RQ2 Section 3 (Scenario 4) | MEDIUM | Medium | Mandatory integration test after every merge sequence. PM runs `make test` on merged branch before reporting success. |
| 4 | Stale worktrees accumulate on disk | RQ8 Section 3 | LOW | High | PM cleanup obligation in PM_INSTRUCTIONS.md. `git worktree list` + remove after every team session. |
| 5 | Engineer teammates ignore scope declaration rule | RQ6 Section 11 | LOW | Medium | Rule is short and imperative (high compliance expected). PM cross-references diff summary against declared scope. Fallback: merge conflict reveals scope violation. |
| 6 | QA teammate produces false pass (tests pass but wrong assertions) | RQ8 Section 1.1 | MEDIUM | Low | QA rules require full command + output (not just counts). PM spot-checks test output. Battery adversarial scenarios test this. |
| 7 | PM cannot translate Research findings into Engineering tasks (pipeline) | RQ5 Section 2.3 | MEDIUM | Medium | PM instructions include phase transition summary template. If translation fails, PM falls back to sequential delegation (no pipeline). |
| 8 | Claude Code platform changes break Agent Teams API | Research Plan Section "Risks" | HIGH | Low | 6-month sunset clause from Phase 1. Agent Teams is experimental; if deprecated, fall back to `run_in_background` + `isolation: "worktree"` (RQ0 baseline). |
| 9 | Token budget exceeded by future protocol additions | RQ6 Section 5 | LOW | Low | Current margin: 58-124 tokens per role. Monitor on each change. Drop Rule 2 for Research (saves 66 tokens) if needed. |
| 10 | SendMessage peer coordination emerges despite Rule 5 | RQ7 Section 1 | MEDIUM | Low | Rule 5 maintained in protocol. PostToolUse logging can detect SendMessage events post-hoc. Phase 3 addresses if needed. |

---

## 11. Open Questions

These require decisions during implementation, not before.

| # | Question | Decision Owner | When to Decide | Default If No Decision |
|:-:|----------|:-------------:|:---:|---|
| 1 | **Should PM merge worktrees directly or delegate to a Version Control agent?** PM_INSTRUCTIONS.md currently allows PM to run single documented commands. Is `git merge` a "single command"? | Implementer | WP-B (Day 2) | PM merges directly. `git merge` is a single documented command. |
| 2 | **Should PM run `make test` directly or delegate to QA?** | Implementer | WP-B (Day 2) | PM runs directly for All-Engineer composition. Delegates to QA in pipeline compositions (QA already spawned). |
| 3 | **Should RQ3 (build verification) be a separate document or folded into the merge protocol?** | Implementer | WP-F (Day 3) | Separate document (03_build_verification.md) for traceability, referenced from PM_INSTRUCTIONS.md merge protocol. |
| 4 | **Phase transition summary: PM writes to conversation or to a file?** PM could write a summary file (persistent) or just state the summary in the next message (ephemeral, subject to auto-compression). | Implementer | WP-B (Day 2) | PM states summary in conversation (not a file). Simpler, keeps it in context naturally. |
| 5 | **Merge conflict resolution: should PM attempt simple resolutions (whitespace, imports) or always escalate?** | Implementer | WP-B (Day 2) | PM escalates all conflicts to user in Phase 2 (simplest). PM auto-resolving trivial conflicts is a Phase 3 optimization. |
| 6 | **Should the `_ROLE_ADDENDA` dict be exposed for external configuration, or hardcoded?** | Implementer | WP-A (Day 1) | Hardcoded. External configuration adds complexity without clear user demand. |
| 7 | **Backward compatibility: keep `TEAMMATE_PROTOCOL` as exact Phase 1 text or as alias for `TEAMMATE_PROTOCOL_BASE`?** The base has Rule 3 removed, so it is NOT identical to Phase 1 text. | Implementer | WP-A (Day 1) | Keep as alias for `TEAMMATE_PROTOCOL_BASE` (new format). Phase 1 exact text is not used outside of tests, and tests should be updated to test the new base. |

---

## Appendix A: Devil's Advocate Amendments Incorporated

| Concern | Amendment | Where Applied |
|---------|-----------|---------------|
| Concern 1: RQ1 worktree investigation partially redundant | RQ0 baseline added; RQ1 narrowed to merge path delta | `01_worktree_and_merge.md` covers RQ0+RQ1+RQ2 as single integrated document |
| Concern 2: RQ4 team compositions is premature design | RQ4 narrowed to 3 user-demanded compositions from Issue #290 | `04_team_compositions.md` Section 1 starts with user demand, Section 4 constrains to 3 patterns |
| Concern 3: RQ7 SendMessage is a non-problem | RQ7 downgraded to brief note; Rule 5 maintained | `07_sendmessage_coordination.md` is 70 lines (decision brief), not a full investigation |
| Concern 4: Dependency chain overfit | RQ1+RQ2 merged into single investigation | `01_worktree_and_merge.md` covers both as single experiment |
| Concern 5: Missing baseline analysis | RQ0 added | `01_worktree_and_merge.md` Section 1 covers RQ0 |
| Concern 6: 4-5 days research is expensive | Research compressed to spike-and-plan (~2 days actual research) | All RQs completed in compressed timeline; this plan is the synthesized output |

---

## Appendix B: Research Question Traceability

| RQ | Document | Key Finding | Where It Appears in This Plan |
|----|----------|------------|-------------------------------|
| RQ0 | `01_worktree_and_merge.md` S1 | PM already supports parallel Engineering via `run_in_background` + `isolation: "worktree"`. Agent Teams adds orchestration, not new mechanics. | Section 2 (Go rationale), Section 3 (scope) |
| RQ1 | `01_worktree_and_merge.md` S2 | Worktrees work correctly. Each `isolation: "worktree"` creates independent workspace. No auto-merge, no auto-cleanup. ~42MB per worktree. | WP-C (merge protocol), Section 10 Risk 4 |
| RQ2 | `01_worktree_and_merge.md` S3-4 | Git auto-merges same-file-different-section. `--no-commit` enables safe conflict pre-detection. PM must own merge workflow. | WP-B (PM instructions), WP-C (merge protocol), Section 10 Risk 2 |
| RQ3 | NOT YET WRITTEN | Build verification protocol pending. Integration test after merge is mandatory. | WP-F addendum (Day 3), Open Question 3 |
| RQ4 | `04_team_compositions.md` | 3 valid compositions (All-Engineer, Eng-then-QA, Research-then-Eng). 5 anti-patterns. Max 3 Engineers per phase. | Section 3 (scope), WP-B (compositions) |
| RQ5 | `05_pm_orchestration.md` | Phase-based model with blocking gates. Context: 4K-12K tokens depending on composition. Max 3 teammates/phase, 7 total/pipeline. | WP-B (orchestration), Section 7 (change budget), Section 10 Risk 1 |
| RQ6 | `06_protocol_extensions.md` | Option C (base + addendum). Rule 3 removed from base. Engineer: +112 tokens. QA: +108 tokens. All within 500-token budget. | WP-A (code changes), WP-E (tests), Section 5 (code detail) |
| RQ7 | `07_sendmessage_coordination.md` | Rule 5 maintained. SendMessage not hookable. Peer coordination deferred to Phase 3. | Section 3 (not supported), Section 10 Risk 10 |
| RQ8 | `08_rollback_recovery.md` | Worktrees persist after crash. 3-failure abort threshold. Sequential fallback always available. PM cleanup obligation. | WP-D (recovery), WP-B (cleanup), Section 10 Risks 4+6 |
