# RQ4 Findings: Team Composition Patterns

**Date:** 2026-03-20
**Research Question:** What team compositions make sense, and what are the anti-patterns?
**Scope:** Narrowed per devil's advocate Concern 2 -- focus on the 2-3 compositions users actually need, not a full taxonomy.
**Dependencies:** Informed by RQ1 (worktree findings), Phase 1 parallel research design, devil's advocate analysis.

---

## 1. User Demand: The Three Original Use Cases

GitHub Issue #290 specified three use cases. These are the compositions users asked for. Everything in this document is evaluated against these three demands.

| # | Use Case | Roles Involved | Original Quote |
|---|----------|---------------|----------------|
| UC1 | Complex Features | Frontend Engineer + Backend Engineer + QA | "Frontend + backend + test coordinating simultaneously" |
| UC2 | Large Refactoring | Engineer + Engineer + ... | "Multiple engineers working on different subsystems" |
| UC3 | Security Audit | Research + Engineer + QA | "Research + implementation + verification in parallel" |

### Key Observation

UC1 and UC2 are **parallel Engineering** problems. UC3 is a **multi-phase pipeline** that LOOKS parallel but has sequential dependencies. This distinction drives the entire composition design.

---

## 2. Composition Analysis Per Use Case

### UC1: Complex Features (Frontend + Backend + QA)

**Roles:** Engineer (frontend) + Engineer (backend) + QA
**Dependency structure:** Semi-parallel with integration gate.

```
PM decomposes feature into frontend and backend tasks
    |
    +---> Engineer-Frontend (worktree A): Build UI components
    |         |
    +---> Engineer-Backend (worktree B): Build API endpoints
    |         |
    v         v
PM collects both results
    |
    v
PM merges worktrees (or delegates merge)
    |
    v
PM spawns QA: Test integrated feature
    |
    v
PM reports to user
```

**Analysis:**

- Engineers CAN run in parallel because frontend and backend typically operate on different files. File overlap is LOW if the PM decomposes cleanly (e.g., `src/frontend/` vs `src/api/`).
- QA CANNOT run in parallel with Engineers. QA must test the MERGED code. Testing code that has not been integrated is meaningless -- you would verify each half in isolation but miss integration failures.
- This is a **two-phase composition**: Phase A (parallel Engineering) followed by Phase B (sequential QA on merged result).

**Is this achievable with Agent Teams?**

Partially. Agent Teams can manage the parallel Engineering phase. The QA phase requires a SECOND team session (or a sequential delegation after the team completes). A single team session with all three teammates spawned simultaneously is an ANTI-PATTERN because QA would start testing before Engineers finish.

**Decision criteria for PM:**
- Feature naturally splits into 2+ subsystems with <20% file overlap
- Each subsystem has clear interface boundaries (API contract, shared types file)
- Test suite can exercise the integrated result

**Maximum practical team size:** 2 Engineers + 1 QA (across 2 phases). Adding a 3rd Engineer increases merge complexity superlinearly without proportional value gain.

---

### UC2: Large Refactoring (Multi-Engineer)

**Roles:** Engineer + Engineer + Engineer (all same role)
**Dependency structure:** Parallel with merge gate.

```
PM decomposes refactoring by subsystem
    |
    +---> Engineer-A (worktree A): Refactor subsystem X
    |
    +---> Engineer-B (worktree B): Refactor subsystem Y
    |
    +---> Engineer-C (worktree C): Refactor subsystem Z
    |
    v
PM collects all results
    |
    v
PM merges worktrees sequentially (A into main, then B, then C)
    |
    v
PM runs integration tests on merged result
    |
    v
PM reports to user (or spawns QA for deep verification)
```

**Analysis:**

- This is the cleanest parallel composition. Same-role teammates working on non-overlapping subsystems. No cross-role coordination needed.
- The CRITICAL constraint is file isolation. If subsystem X and Y share a dependency file (e.g., a shared types module, a database schema file, a configuration file), the refactoring creates merge conflicts. The PM MUST analyze overlap before spawning.
- Merge order matters. If Engineers A, B, C all succeed independently, merging A+B might conflict even if neither conflicts with the original main branch. The PM must merge sequentially and resolve conflicts at each step.

**Is this achievable with Agent Teams?**

Yes. This is the most natural Agent Teams composition for Engineering. All teammates share the same role, same model, same worktree isolation pattern. The PM orchestration is a direct extension of Phase 1's parallel Research pattern: decompose, spawn, collect, merge.

**Decision criteria for PM:**
- Refactoring scope spans 3+ subsystems
- Subsystems have clearly separable file sets (<20% file overlap)
- Each subsystem can be refactored independently (no cascading interface changes)
- Test suite covers integration points between subsystems

**Maximum practical team size:** 3 Engineers. Beyond 3:
- Merge complexity grows combinatorially (3 merges for 3 engineers, 6 for 4, 10 for 5)
- PM context accumulates 3 completion reports (~1500-6000 tokens), which is within budget
- Diminishing returns: Engineer #4 works on progressively smaller or more coupled subsystems

---

### UC3: Security Audit (Research + Implementation + Verification)

**Roles:** Research + Engineer + QA
**Dependency structure:** Sequential pipeline, NOT parallel.

```
Phase 1: Research
PM spawns Research team (2-3 researchers in parallel)
    |
    v
PM collects research findings
    |
    v
Phase 2: Implementation
PM decomposes fixes based on research findings
PM spawns Engineer team (1-2 engineers in parallel)
    |
    v
PM collects engineering results, merges worktrees
    |
    v
Phase 3: Verification
PM spawns QA to verify fixes against original vulnerabilities
    |
    v
PM reports to user
```

**Analysis:**

- This is NOT a parallel mixed-role team. It is a **three-phase sequential pipeline** where each phase can internally use parallel teammates of the same role.
- Research MUST complete before Engineering begins. Engineers need to know WHAT to fix. Spawning Research and Engineering simultaneously means Engineers are building without knowing the findings -- this is wasteful at best and counterproductive at worst.
- QA MUST run after Engineering merges. QA tests the FIXED code against the ORIGINAL vulnerabilities found by Research.
- The "parallel" aspect exists WITHIN each phase (2-3 researchers in parallel, 2 engineers in parallel), not ACROSS phases.

**Is this achievable with Agent Teams?**

Yes, but as 2-3 SEPARATE team sessions (one per phase), not a single mixed team. Each phase is an independent Agent Teams session:
- Phase 1 team: "security-research" with 2-3 Research teammates
- Phase 2 team: "security-implementation" with 1-2 Engineer teammates
- Phase 3 team: "security-verification" with 1 QA teammate (or standard delegation)

**Decision criteria for PM:**
- Task involves investigate-then-fix-then-verify workflow
- Findings from investigation directly determine implementation scope
- Verification requires both original findings AND implemented fixes

**Maximum practical team size per phase:** 2-3 per phase. Total across all phases: 5-7 teammates, but never more than 3 simultaneously.

---

## 3. Valid Compositions: Decision Table

This table is designed for direct inclusion in PM_INSTRUCTIONS.md Phase 2 changes.

| Composition | When to Use | Teammate Limit | Phases | Worktree Required? |
|-------------|------------|:--------------:|:------:|:------------------:|
| **All-Engineer Parallel** | Refactoring or feature work spanning 2-3 independent subsystems | 3 | 1 (parallel) + merge gate | YES |
| **Engineer-then-QA Pipeline** | Feature implementation requiring verification | 2-3 Engineers + 1 QA | 2 (Engineer parallel, then QA sequential) | YES (Engineers) |
| **Research-then-Engineer Pipeline** | Investigation-driven implementation (security audit, tech debt) | 2-3 Research + 2-3 Engineers | 2-3 (Research parallel, Engineer parallel, optionally QA) | YES (Engineers) |

### Composition Selection Flow for PM

```
User request arrives
    |
    v
Does the task involve WRITING code?
    |
    +-- No --> Phase 1 parallel Research pattern (existing)
    |
    +-- Yes --> Can the implementation be decomposed into
    |           2+ independent subsystems with <20% file overlap?
    |           |
    |           +-- No --> Standard sequential delegation
    |           |          (single Engineer, then single QA)
    |           |
    |           +-- Yes --> Does the task require investigation first?
    |                       |
    |                       +-- Yes --> Research-then-Engineer Pipeline
    |                       |          (Phase 1: parallel Research team)
    |                       |          (Phase 2: parallel Engineer team)
    |                       |          (Phase 3: QA on merged result)
    |                       |
    |                       +-- No --> Does the task require verification?
    |                                  |
    |                                  +-- Yes --> Engineer-then-QA Pipeline
    |                                  |          (Phase 1: parallel Engineer team)
    |                                  |          (Phase 2: QA on merged result)
    |                                  |
    |                                  +-- No --> All-Engineer Parallel
    |                                             (Single phase: parallel Engineers)
    |                                             (PM merges + runs tests)
```

---

## 4. Anti-Patterns: Compositions That MUST NOT Be Used

### Anti-Pattern 1: Two Engineers on Overlapping Files Without Worktree Isolation

**Scenario:** PM spawns Engineer-A and Engineer-B without `isolation: "worktree"`. Both modify `src/models/user.py`.

**What happens:** Race condition. Both Engineers read the same file, make different changes, and write back. The last write wins; the first Engineer's changes are silently lost. No conflict detection. No merge opportunity.

**Rule:** ALL parallel Engineer teams MUST use `isolation: "worktree"`. No exceptions.

**Detection:** PM must analyze file overlap BEFORE spawning. If the PM cannot guarantee <20% file overlap between tasks, use sequential delegation instead.

### Anti-Pattern 2: Mixed Research + Engineer Where Engineer Depends on Research Findings

**Scenario:** PM spawns a Research teammate and an Engineer teammate simultaneously. The Engineer is supposed to implement fixes based on what the Researcher finds.

**What happens:** The Engineer starts working immediately with no findings to act on. One of three outcomes:
1. Engineer guesses what to implement (wrong, wastes tokens)
2. Engineer waits idle for Research to complete via SendMessage (defeats the purpose of parallelism)
3. Engineer implements something unrelated to the findings (wasted work)

**Rule:** If Engineer work DEPENDS on Research output, these are sequential phases, not parallel teammates. Research team completes first. PM synthesizes findings. Then PM spawns Engineer team with findings as input.

**Detection:** PM asks: "Can the Engineer begin work WITHOUT knowing the Research results?" If no, sequential.

### Anti-Pattern 3: QA Testing Code That Has Not Been Merged

**Scenario:** PM spawns Engineer-A, Engineer-B, and QA-Agent simultaneously in a team. QA starts running tests while Engineers are still writing code.

**What happens:** QA tests against the ORIGINAL codebase (or a stale worktree), not the Engineers' changes. All tests pass (the original code hasn't broken), but QA has verified nothing about the new implementation. PM receives a false "all clear" signal.

**Rule:** QA MUST run AFTER Engineer worktrees are merged into a single integration branch. QA is ALWAYS a subsequent phase, never a parallel teammate with Engineers.

**Detection:** PM asks: "Is QA testing the NEW code or the OLD code?" If QA would be testing old code because Engineers haven't finished, QA must wait.

### Anti-Pattern 4: More Than 3 Engineers in a Single Parallel Phase

**Scenario:** PM spawns 5 Engineers simultaneously for a large refactoring.

**What happens:**
- PM must track 5 completion reports (~2500-10000 tokens of context consumed)
- PM must perform 5 sequential merges (merge complexity grows: Engineer 4 merges into a codebase already changed by 1+2+3)
- Integration failures compound: if merge #3 introduces a subtle bug, merges #4 and #5 build on top of it
- PM context quality degrades, leading to worse merge decisions

**Rule:** Maximum 3 parallel Engineers per phase. If the task requires more, decompose into 2 phases: Engineers A+B+C in phase 1, then Engineers D+E in phase 2 (after phase 1 merges).

**Detection:** PM counts the number of independent subsystems. If >3, split into sequential batches of 2-3.

### Anti-Pattern 5: Spawning a Team for a Small Task

**Scenario:** PM spawns 2 Engineers for a task that touches 3 files total.

**What happens:** The overhead of team orchestration (decomposition, spawn, collect, merge, verify) exceeds the time the Engineers actually spend coding. A single Engineer finishes faster because there is no merge step, no cross-validation, no synthesis.

**Rule:** Only use teams when the task is large enough that parallel execution saves more time than orchestration costs. Heuristic: if a single Engineer would take <15 minutes, do not use a team.

**Detection:** PM estimates single-Engineer effort. If <15 minutes, standard delegation.

---

## 5. Expected PM Orchestration Flow Per Composition

### All-Engineer Parallel

```
1. DECOMPOSE: PM identifies 2-3 independent subsystems
2. PRE-FLIGHT: PM verifies <20% file overlap between subsystems
3. SPAWN: PM creates Engineer team (all in single message)
   - Each Engineer: isolation="worktree", specific subsystem scope
4. WAIT: PM receives completion messages from each Engineer
5. VALIDATE: Per-Engineer QA gate (evidence, file manifest, diff summary)
6. MERGE: PM merges worktrees sequentially into integration branch
   - After each merge: check for git conflicts
   - If conflict: PM resolves simple conflicts or reports to user
7. TEST: PM runs integration tests on merged branch
   - If tests pass: report success
   - If tests fail: identify which Engineer's changes broke the build
8. REPORT: PM presents results with attribution
```

### Engineer-then-QA Pipeline

```
Phase A: Engineering (same as All-Engineer Parallel steps 1-7)

Phase B: QA
1. SPAWN: PM creates QA agent against merged integration branch
   - QA prompt includes: what was changed, where, and why
   - QA prompt includes: which tests to run, what to verify
2. WAIT: PM receives QA completion
3. VALIDATE: QA result has test output, coverage data, pass/fail
4. REPORT: PM presents integrated results (engineering + QA)
```

### Research-then-Engineer Pipeline

```
Phase A: Research (Phase 1 pattern, already implemented)
1. DECOMPOSE into independent research questions
2. SPAWN Research team
3. COLLECT and SYNTHESIZE findings

Phase B: Engineering
1. DECOMPOSE engineering tasks BASED ON research findings
2. PRE-FLIGHT: verify file overlap
3. SPAWN Engineer team with research findings as context
4. COLLECT, VALIDATE, MERGE (same as All-Engineer Parallel)

Phase C: Verification (optional)
1. SPAWN QA against merged result
2. QA verifies fixes against original research findings
```

---

## 6. Implications for PM_INSTRUCTIONS.md Changes

### New Content Required

1. **Composition decision table** (Section 3 of this document) -- approximately 15 lines
2. **Anti-patterns list** (Section 4) -- approximately 10 lines (condensed from the detailed versions above)
3. **Phase-based orchestration rules:**
   - "Parallel teammates must be same-role within a phase"
   - "QA is always a subsequent phase, never parallel with Engineers"
   - "Research findings must be synthesized before spawning Engineers"
4. **Worktree enforcement:** "All parallel Engineer teams MUST use `isolation: 'worktree'`"
5. **File overlap check:** PM MUST estimate file overlap before spawning parallel Engineers. If overlap >20%, fall back to sequential.

### Existing Content to Modify

1. **"Agent Teams: Parallel Research" section** (lines 1135-1184): Rename to "Agent Teams" and expand to cover Engineering compositions. Keep Research rules intact; add Engineering and Pipeline subsections.
2. **Anti-patterns list** (lines 1173-1178): Expand from Research-specific to cover Engineering anti-patterns.
3. **Delegation table:** Add rows for parallel Engineering and pipeline compositions.

### Estimated Line Count Impact

| Change | Lines Added |
|--------|:-----------:|
| Composition decision table | ~15 |
| Engineering anti-patterns | ~10 |
| Phase-based orchestration rules | ~15 |
| Worktree enforcement rule | ~3 |
| File overlap pre-flight | ~5 |
| **Total** | **~48** |

This is within the incremental budget established in Phase 1 (~41 lines for Research; ~48 more for Engineering; total ~89 lines for the full Agent Teams section).

---

## 7. Open Questions for Downstream RQs

1. **Merge strategy details** (RQ1/RQ2): How does the PM actually merge worktrees? Does it delegate to a Version Control agent? Use git commands directly? The composition design assumes merge is possible but does not specify the mechanism.

2. **Integration test duration** (RQ3): If integration tests take >5 minutes, the merge-then-test gate becomes a significant bottleneck. The composition design assumes tests are fast. If they are not, the PM may need to run tests in the background.

3. **PM context limits** (RQ5): The 3-Engineer cap is based on the devil's advocate analysis (Concern 8, lines 486-489) but has not been empirically validated. RQ5 should test whether 3 Engineer completion reports actually fit in PM context without degradation.

4. **Protocol extensions** (RQ6): Engineer teammates need different rules than Research teammates (scope declaration before starting, diff summary in completion). The composition design assumes these rules exist but does not define them.
