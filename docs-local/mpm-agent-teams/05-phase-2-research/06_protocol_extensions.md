# RQ6: TEAMMATE_PROTOCOL Extensions -- Role-Specific Rules

**Research Question:** Does the TEAMMATE_PROTOCOL need role-specific rules for Engineer and QA teammates?

**Date:** 2026-03-20
**Status:** Complete
**Conclusion:** Yes. Option C (base protocol + role-specific addendum) is recommended.

---

## 1. Current Protocol Analysis

### Source Files Examined

| File | Relevance |
|------|-----------|
| `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py` lines 29-55 | TEAMMATE_PROTOCOL constant (production code) |
| `docs-local/mpm-agent-teams/02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md` Section 3 | Canonical text and token budget |
| `src/claude_mpm/agents/BASE_AGENT.md` | Universal rules inherited by all agents |
| `docs-local/mpm-agent-teams/04-phase-1.5/investigation/01_wp2_parallel_research.md` Section 2 | Hook API limitations (inject/log only, cannot block) |

### Current Protocol Dimensions

| Metric | Value |
|--------|-------|
| Character count | 1,583 |
| Estimated tokens (chars/4) | ~396 |
| Token budget | 500 max |
| Budget remaining | ~104 tokens |
| Rules | 5 |
| Roles served | Research only (Phase 1) |

### Role-Applicability Matrix

| Rule | Research | Engineer | QA | Notes |
|------|:--------:|:--------:|:--:|-------|
| **Rule 1: Evidence-Based Completion** (CB#3) | Applies (cite files/lines) | Applies (commands + output) | Applies (test commands + output) | Universal but "evidence" means different things per role |
| **Rule 2: File Change Manifest** (CB#4) | Weak fit -- Research rarely modifies files | Critical -- Engineers always modify files | Weak fit -- QA may create test files but does not modify production code | Research could skip this rule; Engineers need a STRONGER version |
| **Rule 3: QA Scope Honesty** (CB#8) | Applies (Research is not QA) | Critical (Engineer must not claim QA verification) | Does not apply -- QA IS the verification role | QA teammates should never say "QA has not been performed" -- they are QA |
| **Rule 4: Self-Execution** (CB#9) | Universal | Universal | Universal | Already in BASE_AGENT.md; reinforced here for peer context |
| **Rule 5: No Peer Delegation** | Universal | Universal | Universal | Critical for all roles in Agent Teams |

### Key Finding: Three Mismatches

1. **Rule 2 is over-specified for Research, under-specified for Engineer.** Research agents write docs/research files but do not modify production code. Engineers need git diff summaries, scope declarations, and worktree awareness -- far beyond a simple file manifest.

2. **Rule 3 is nonsensical for QA.** Telling a QA teammate "state that QA has not been performed" contradicts their purpose. QA teammates should instead be told to declare WHICH engineer's work they are verifying and provide independent evidence.

3. **Rule 1's "evidence" is underspecified.** For Research, evidence means citations (file:line references). For Engineer, evidence means command output and git diffs. For QA, evidence means test commands with full output. The generic phrasing works but role-specific guidance would increase compliance.

---

## 2. Engineer-Specific Rules (Drafted)

### Rationale

Engineer teammates have the highest risk profile in Agent Teams:
- They modify production code (unlike Research)
- They can claim "tests pass" without QA (CB#8 bypass risk)
- They can scope-creep into files outside their assignment
- They operate in worktrees that must be merged back

The current protocol's Rule 2 (file manifest) is necessary but insufficient. Engineers need:
- Pre-declaration of intended file scope (prevents scope creep)
- Lint/format verification before completion (prevents broken commits)
- Git diff summary (more actionable than file list alone)
- Worktree boundary awareness (Phase 2 uses worktree isolation)

### Drafted Engineer Addendum

```markdown
### Engineer Rules
- Declare intended file scope BEFORE starting work. Do not modify files outside that scope.
- Run linting/formatting checks before reporting completion.
- Include git diff summary (files changed, insertions, deletions) in your completion report.
- You are working in an isolated worktree. Do not reference or modify files in the main working tree.
```

**Token cost:** ~92 tokens (366 characters)
**Combined with base:** ~487 tokens (WITHIN 500-token budget, 13 tokens margin)

### Rule-by-Rule Justification

| Engineer Rule | Problem It Prevents | Enforcement Tier |
|---------------|--------------------|--------------------|
| Declare file scope | Scope creep into unrelated files; merge conflicts with parallel engineers | T1: Teammate-enforced (pre-declaration is self-enforced) |
| Run lint/format | Broken formatting committed to branch; style violations that block CI | T1: Teammate-enforced (can verify independently) |
| Git diff summary | Vague "I updated the file" claims that fail CB#4 cross-reference | T3: Dual (teammate provides, PM cross-references) |
| Worktree isolation | Engineer modifies main tree and corrupts other teammates' state | T1: Teammate-enforced (worktree is their sandbox) |

---

## 3. QA-Specific Rules (Drafted)

### Rationale

QA teammates have a unique position: they are the verification layer that the entire circuit breaker system depends on (CB#8). The highest-rated residual risk in the protocol (Risk 2: Collective Unverified Completion, rated HIGH in TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 5) targets exactly the scenario where QA fails to provide independent evidence.

The current protocol's Rule 3 ("state that QA has not been performed") makes no sense for a QA teammate -- they ARE performing QA. QA needs:
- Clean test environment requirement (prevents false positives from leftover state)
- Full command + output reporting (not just "12 passed")
- Explicit declaration of which engineer's work they verify (traceability)
- Merged-code testing when multiple engineers contribute (prevents gap testing)

### Drafted QA Addendum

```markdown
### QA Rules
- Run tests in a clean state (no uncommitted changes from your own edits).
- Report the full test command AND its complete output, not just pass/fail counts.
- When verifying an Engineer's work, explicitly state which Engineer and which files you are verifying.
- Test against the MERGED code when verifying work from multiple Engineers.
```

**Token cost:** ~88 tokens (350 characters)
**Combined with base:** ~483 tokens (WITHIN 500-token budget, 17 tokens margin)

### Rule 3 Replacement for QA

The base protocol's Rule 3 ("QA Scope Honesty") should be **dropped** for QA teammates and **replaced** with QA-specific rules. This saves 66 tokens from the base and uses 88 for the QA addendum, netting +22 tokens but providing far more relevant guidance.

| QA Rule | Problem It Prevents | Enforcement Tier |
|---------|--------------------|--------------------|
| Clean test state | False positives from leftover files/config from QA's own exploration | T1: Teammate-enforced |
| Full command + output | Vague "tests pass" claims that could be fabricated (Risk 2 mitigation) | T3: Dual (QA provides, PM spot-checks) |
| Declare which engineer | Untraceable QA results when multiple engineers contribute | T1: Teammate-enforced |
| Test merged code | Gap testing when QA only tests one engineer's work in isolation | T1: Teammate-enforced |

---

## 4. Research-Specific Rules (Optional)

### Rationale

Research teammates have the lowest risk profile because they rarely modify production code. The current protocol was designed for them and works well. However, two clarifications would help:

1. Research should not modify source code files (they are investigators, not implementers).
2. Research should cite specific file paths and line numbers for every claim.

### Drafted Research Addendum (Optional)

```markdown
### Research Rules
- Do not modify source code files. Your deliverable is analysis, not implementation.
- Cite specific file paths and line numbers for every claim about the codebase.
```

**Token cost:** ~46 tokens (183 characters)
**Combined with base:** ~442 tokens (WITHIN 500-token budget, 58 tokens margin)

### Assessment

This addendum is lower priority than Engineer/QA because:
- Research is already the only supported role (Phase 1) and works without it
- BASE_AGENT.md already contains output format standards that cover citations
- The file modification prohibition is implicit in the research role definition

**Recommendation:** Include for completeness and consistency, but do not gate Phase 2 on it.

---

## 5. Token Budget Analysis (Measured)

### Base Protocol Breakdown (from source code)

| Component | Characters | Estimated Tokens |
|-----------|-----------|-----------------|
| Header + intro | 170 | ~42 |
| Rule 1 (CB#3 Evidence) | 373 | ~93 |
| Rule 2 (CB#4 File Manifest) | 265 | ~66 |
| Rule 3 (CB#8 QA Scope) | 263 | ~66 |
| Rule 4 (CB#9 Self-Execute) | 148 | ~37 |
| Rule 5 (Peer Delegation) | 324 | ~81 |
| **Base Total** | **1,583** | **~396** |

### Role-Specific Addendum Costs

| Addendum | Characters | Tokens | Base + Addendum | Within Budget? |
|----------|-----------|--------|-----------------|----------------|
| Engineer | 366 | ~92 | ~487 | Yes (13 margin) |
| QA | 350 | ~88 | ~483 | Yes (17 margin) |
| Research | 183 | ~46 | ~442 | Yes (58 margin) |

### Optimization: Drop Inapplicable Rules Per Role

If we drop rules that do not apply to a role, we gain additional budget:

| Variant | Dropped Rule | Token Savings | Addendum Cost | Net Total | Margin |
|---------|-------------|---------------|---------------|-----------|--------|
| Engineer | None dropped | 0 | +92 | ~487 | 13 |
| QA | Rule 3 (QA Scope) | -66 | +88 | ~418 | 82 |
| Research | Rule 2 (File Manifest) | -66 | +46 | ~375 | 125 |

**Key insight:** Dropping inapplicable rules is not just a token optimization -- it eliminates confusing or contradictory instructions. Telling QA to say "QA has not been performed" is actively harmful.

### Budget Verdict

All three role-specific variants fit within the 500-token budget, even without dropping inapplicable rules. With smart rule drops:
- Engineer: 487 tokens (tight but viable)
- QA: 418 tokens (comfortable)
- Research: 375 tokens (generous)

---

## 6. Injection Strategy Analysis

### Option A: Single Protocol with Role-Conditional Sections

```python
TEAMMATE_PROTOCOL = """## MPM Teammate Protocol
...base rules...

If you are an Engineer:
...engineer rules...

If you are a QA teammate:
...qa rules...
"""
```

| Criterion | Assessment |
|-----------|------------|
| Token cost | ~646 tokens -- **OVER 500-token budget** |
| Simplicity | One constant, no branching logic |
| Maintenance | All rules in one place, easy to review |
| Token efficiency | Poor -- every role pays for all roles' rules |
| Correctness | Risky -- LLM might apply wrong role's rules |

**Verdict: Rejected.** Exceeds budget. Injecting irrelevant role-specific rules wastes tokens and risks cross-role contamination.

### Option B: Separate Protocol Constants Per Role

```python
TEAMMATE_PROTOCOL_RESEARCH = """...(base rules tuned for research)..."""
TEAMMATE_PROTOCOL_ENGINEER = """...(base rules tuned for engineer)..."""
TEAMMATE_PROTOCOL_QA = """...(base rules tuned for QA)..."""
```

| Criterion | Assessment |
|-----------|------------|
| Token cost | 375-487 per role -- **WITHIN budget** |
| Simplicity | Three constants, selection logic needed |
| Maintenance | Three copies of base rules -- **DRY violation** |
| Token efficiency | Optimal -- each role gets exactly what it needs |
| Correctness | No cross-role contamination |

**Verdict: Viable but not recommended.** DRY violation means updating a base rule requires editing three constants. Sync bugs become likely over time.

### Option C: Base Protocol + Role-Specific Addendum (RECOMMENDED)

```python
TEAMMATE_PROTOCOL_BASE = """...(universal rules)..."""
TEAMMATE_PROTOCOL_ENGINEER = """### Engineer Rules\n..."""
TEAMMATE_PROTOCOL_QA = """### QA Rules\n..."""
TEAMMATE_PROTOCOL_RESEARCH = """### Research Rules\n..."""  # optional

# In inject_context():
protocol = TEAMMATE_PROTOCOL_BASE
role = tool_input.get("subagent_type", "unknown").lower()
if role in ("engineer",):
    protocol += "\n\n" + TEAMMATE_PROTOCOL_ENGINEER
elif role in ("qa", "qa-agent"):
    # Drop Rule 3 from base, add QA-specific rules
    protocol = TEAMMATE_PROTOCOL_BASE_WITHOUT_RULE3
    protocol += "\n\n" + TEAMMATE_PROTOCOL_QA
elif role in ("research", "research-agent"):
    protocol += "\n\n" + TEAMMATE_PROTOCOL_RESEARCH
```

| Criterion | Assessment |
|-----------|------------|
| Token cost | 375-487 per role -- **WITHIN budget** |
| Simplicity | Base + addendum constants, moderate branching |
| Maintenance | Base rules edited once, addenda edited per role -- **DRY compliant** |
| Token efficiency | Good -- each role pays only for base + its addendum |
| Correctness | No cross-role contamination; role-appropriate rules |

**Verdict: Recommended.** Best balance of DRY compliance, token efficiency, and correctness.

### Implementation Impact on `inject_context()`

Current code (lines 119-157 of `teammate_context_injector.py`):
- `should_inject()` checks: enabled + tool_name == "Agent" + "team_name" in tool_input
- `inject_context()` prepends TEAMMATE_PROTOCOL to prompt unconditionally
- `subagent_type` is already extracted (line 140) but only used for logging

Required changes for Option C:
1. Add `TEAMMATE_PROTOCOL_ENGINEER`, `TEAMMATE_PROTOCOL_QA` constants (and optionally `TEAMMATE_PROTOCOL_RESEARCH`)
2. Extract `subagent_type` BEFORE protocol assembly (already done at line 140)
3. Select base protocol variant (with or without Rule 3 depending on role)
4. Append role-specific addendum
5. No changes to `should_inject()` -- injection still fires for all team spawns

**Code change estimate:** ~30 lines added to `teammate_context_injector.py`. No changes to hook_handler.py or event_handlers.py.

---

## 7. The Rule 3 Problem: Detailed Analysis

Rule 3 deserves special attention because it is the one rule that is actively **wrong** for one role.

### Current Rule 3 Text

> If your role is implementation (not QA), you MUST state: "QA verification has not been performed" when reporting completion. Do NOT claim your work is fully verified unless you independently ran tests and included results per Rule 1.

### Problem

The rule says "if your role is implementation (not QA)". This conditional phrasing has three issues:

1. **QA teammates see it and must decide "am I QA?"** -- This burns attention on a self-classification question that the system should answer.
2. **The negation path ("not QA") is the active instruction.** QA teammates read the rule but have no affirmative instruction for what THEY should do.
3. **Research teammates are neither "implementation" nor "QA."** The rule's "implementation" framing is ambiguous for Research.

### Proposed Resolution

For Option C (base + addendum):
- **Base protocol (all roles):** Remove Rule 3 entirely from the base. It is role-specific by definition.
- **Engineer addendum:** Include: "You MUST state: 'QA verification has not been performed' when reporting completion."
- **QA addendum:** Include: "You ARE the QA verification layer. Provide independent evidence."
- **Research addendum:** Include nothing about QA scope (Research does not perform implementation or QA).

This moves the QA scope declaration from a confusing conditional in the base to a clear, direct statement in each role's addendum.

### Token Impact of Removing Rule 3 from Base

| Change | Tokens |
|--------|--------|
| Remove Rule 3 from base | -66 |
| Add QA-scope statement to Engineer addendum | +20 (one sentence) |
| Net savings | ~46 tokens |

This creates more room for role-specific rules while eliminating the confusing conditional.

---

## 8. Draft Protocol Texts

### 8a. Base Protocol (Role-Agnostic, Rule 3 Removed)

```markdown
## MPM Teammate Protocol

You are operating as a teammate in an MPM-managed Agent Teams session. The team lead (PM) assigned you this task. Follow these rules strictly.

### Rule 1: Evidence-Based Completion (CB#3)
When reporting task completion, you MUST include:
- Specific commands you executed and their actual output
- File paths and line numbers of all changes made
- Test results with pass/fail counts (if applicable)
FORBIDDEN phrases: "should work", "appears to be working", "looks correct", "I believe this fixes". Use only verified facts.

### Rule 2: File Change Manifest (CB#4)
Before reporting completion, list ALL files you created, modified, or deleted:
- File path
- Action: created / modified / deleted
- One-line summary of the change
Omit nothing. The team lead will cross-reference against git status.

### Rule 3: Self-Execution (CB#9)
Execute all work yourself using available tools. Never instruct the user or any teammate to run commands on your behalf.

### Rule 4: No Peer Delegation
Do NOT delegate your assigned task to another teammate via SendMessage. Do NOT orchestrate multi-step workflows with other teammates. If you cannot complete your task, report the blocker to the team lead -- do not ask a peer to do it. You have ONE task. Complete it and report results to the team lead.
```

**Estimated tokens:** ~330 (1,320 characters)

### 8b. Engineer Addendum

```markdown
### Engineer Rules
- You MUST state "QA verification has not been performed" when reporting completion. Do NOT claim your work is fully verified.
- Declare intended file scope BEFORE starting work. Do not modify files outside that scope.
- Run linting/formatting checks before reporting completion.
- Include git diff summary (files changed, insertions, deletions) in your completion report.
- You are working in an isolated worktree. Do not reference or modify files in the main working tree.
```

**Estimated tokens:** ~112 (450 characters)
**Combined total:** ~442 tokens (58 margin)

### 8c. QA Addendum

```markdown
### QA Rules
- You ARE the QA verification layer. Your evidence must be independent of the Engineer's claims.
- Run tests in a clean state (no uncommitted changes from your own edits).
- Report the full test command AND its complete output, not just pass/fail counts.
- When verifying an Engineer's work, explicitly state which Engineer and which files you are verifying.
- Test against the MERGED code when verifying work from multiple Engineers.
```

**Estimated tokens:** ~108 (430 characters)
**Combined total:** ~438 tokens (62 margin)

### 8d. Research Addendum (Optional)

```markdown
### Research Rules
- Do not modify source code files. Your deliverable is analysis, not implementation.
- Cite specific file paths and line numbers for every claim about the codebase.
```

**Estimated tokens:** ~46 (183 characters)
**Combined total:** ~376 tokens (124 margin)

---

## 9. Injection Strategy: Implementation Sketch

### Constants (in teammate_context_injector.py)

```python
# Base protocol (~330 tokens) - injected for ALL roles
TEAMMATE_PROTOCOL_BASE = """\
## MPM Teammate Protocol
...(Section 8a text above)..."""

# Role addenda - injected conditionally based on subagent_type
TEAMMATE_PROTOCOL_ENGINEER = """\
### Engineer Rules
...(Section 8b text above)..."""

TEAMMATE_PROTOCOL_QA = """\
### QA Rules
...(Section 8c text above)..."""

TEAMMATE_PROTOCOL_RESEARCH = """\
### Research Rules
...(Section 8d text above)..."""

# Mapping from subagent_type values to addenda
_ROLE_ADDENDA = {
    "engineer": TEAMMATE_PROTOCOL_ENGINEER,
    "qa": TEAMMATE_PROTOCOL_QA,
    "qa-agent": TEAMMATE_PROTOCOL_QA,
    "research": TEAMMATE_PROTOCOL_RESEARCH,
    "research-agent": TEAMMATE_PROTOCOL_RESEARCH,
}
```

### Modified inject_context()

```python
def inject_context(self, tool_input: dict) -> dict:
    modified = copy.copy(tool_input)

    team_name = tool_input.get("team_name", "")
    subagent_type = tool_input.get("subagent_type", "unknown")

    # Build role-appropriate protocol
    protocol = TEAMMATE_PROTOCOL_BASE
    addendum = _ROLE_ADDENDA.get(subagent_type.lower(), "")
    if addendum:
        protocol += "\n\n" + addendum

    # Log injection details
    _log(
        f"TeammateContextInjector: Injected protocol "
        f"(team_name={team_name}, subagent_type={subagent_type}, "
        f"addendum={'yes' if addendum else 'none'})"
    )

    original_prompt = tool_input.get("prompt") or ""
    modified["prompt"] = protocol + "\n\n---\n\n" + original_prompt
    return modified
```

### Backward Compatibility

- `TEAMMATE_PROTOCOL` constant is kept as an alias for `TEAMMATE_PROTOCOL_BASE` (or kept unchanged for Phase 1 compatibility)
- Unknown `subagent_type` values get base protocol only (same as current behavior)
- No changes to `should_inject()` logic
- No changes to hook_handler.py or event_handlers.py

---

## 10. Tradeoff Summary

| Dimension | Option A (All-in-One) | Option B (Separate) | Option C (Base + Addendum) |
|-----------|----------------------|--------------------|-----------------------------|
| Token budget | OVER (646) | WITHIN (375-487) | WITHIN (376-442) |
| DRY compliance | Yes (one block) | No (3 copies of base) | Yes (one base, N addenda) |
| Maintenance | Low (one file) | High (sync 3 files) | Medium (1 base + 3 addenda) |
| Role accuracy | Risky (cross-contamination) | Excellent | Excellent |
| Code complexity | None (no branching) | Low (select constant) | Medium (build from parts) |
| Backward compat | Breaking (new format) | Breaking (new constants) | Non-breaking (alias old name) |

---

## 11. Recommendation

**Implement Option C: Base Protocol + Role-Specific Addendum.**

### Immediate Actions (Phase 2)

1. Refactor TEAMMATE_PROTOCOL into TEAMMATE_PROTOCOL_BASE (remove Rule 3, renumber to 4 rules).
2. Add TEAMMATE_PROTOCOL_ENGINEER, TEAMMATE_PROTOCOL_QA, TEAMMATE_PROTOCOL_RESEARCH constants.
3. Add _ROLE_ADDENDA mapping dict.
4. Modify inject_context() to assemble protocol from base + addendum based on subagent_type.
5. Keep TEAMMATE_PROTOCOL as alias for backward compatibility during transition.
6. Add tests: one per role variant verifying correct assembly.

### Deferred (Phase 3+)

- Rule 2 (File Manifest) could be dropped for Research in a future optimization.
- Worktree isolation rule could be made conditional on `isolation` parameter.
- Engineer lint/format rule could specify project-specific linter commands.

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| LLM ignores role-specific rules | Low | Medium | Rules are short, direct, imperative -- high compliance expected |
| subagent_type not set correctly | Medium | Low | Fallback to base-only protocol (current behavior) |
| Token budget exceeded by future additions | Low | Medium | 58-124 token margin per role; monitor on each change |
| Backward compatibility break | Low | Low | TEAMMATE_PROTOCOL alias maintained |
