# WP2 Investigation: Parallel Research Pattern

**Phase:** 1.5
**Status:** Investigation complete, ready for implementation
**Goal:** Remove teammate cap, add code-level observability, strengthen validation

---

## 1. Teammate Cap Removal

### Current Cap Locations

The 3-teammate cap exists in exactly 2 files, 3 text occurrences, zero code:

| Location | Current Text | Action |
|----------|-------------|--------|
| PM_INSTRUCTIONS.md ~line 1140 | "Spawn a Research team (2-3 teammates) when ALL conditions are met" | Change to "Spawn a Research team when ALL conditions are met" |
| PM_INSTRUCTIONS.md ~line 1174 | "**Never** spawn > 3 Research teammates (Phase 1 limit)" | Remove this anti-pattern entirely |
| 02_parallel_research_design.md Section 3 table | "Maximum teammates: 3 \| Phase 1 limit" | Change to "Maximum teammates: no ceiling \| constrained by decomposition quality" |

No code changes needed for cap removal. The TeammateContextInjector has no teammate count check.

### Replacement Guidance

Replace the hard cap with a decomposition-quality heuristic in PM_INSTRUCTIONS.md:

"Spawn one Research teammate per independent question. If you cannot articulate a distinct scope boundary (different files, different subsystem, non-overlapping deliverables) for each additional teammate, do not spawn them. Poor decomposition produces overlapping work and conflicting results."

---

## 2. Code vs. Instruction Enforcement Split

### What Code CAN Enforce (via PreToolUse hook)

| Behavior | Mechanism | Status |
|----------|-----------|--------|
| Protocol injection into teammate prompts | TeammateContextInjector.inject_context() | Done (Phase 1) |
| Logging team_name on every spawn | _log() in inject_context() | Done (Phase 1) |
| Detecting non-research subagent_type in teams | New: check in inject_context() | To implement |
| Logging role violations | New: warning log on non-research subagent_type | To implement |
| Compliance event recording | New: _compliance_log() on injection + completion | To implement (WP5) |

### What Code CANNOT Enforce (hook API limitation)

The PreToolUse hook can return a modified tool_input or None. It CANNOT return a "block this call" signal. Therefore:

| Behavior | Why Instruction-Only |
|----------|---------------------|
| Blocking spawns (e.g., blocking Engineer in a research team) | No "reject" return path in hook API |
| Sequential dependency detection | Requires PM semantic reasoning about task structure |
| Scope boundary enforcement (<20% file overlap) | Cannot evaluate overlap before spawn |
| Send-back count tracking | Requires PM to track after receiving results |
| Conflict detection between teammate results | Requires PM to compare result sets |
| Evidence quality verification | PM applies T3 circuit breaker on result content |

**Key insight:** Code does: inject, log, detect, surface. Instructions do: decide, evaluate, gate, escalate. Counting is derived post-hoc from the compliance log (see WP5).

---

## 3. Code Changes

### ~~3a. Teammate Count Tracking~~ REMOVED

> **Amendment (devil's advocate review):** In-memory teammate counting via
> `_team_counts: dict[str, int]` was originally planned here. This was removed because
> each Claude Code hook invocation is a **fresh Python process** — the module-level
> `_global_handler` singleton and all instance state (including `_team_counts`) reset on
> every event. The dict would always show 0 or 1, never accumulating across the 2-5
> teammate spawns in a team session.
>
> **Replacement:** Teammate counting is derived from the compliance log JSONL file
> (see WP5, Section 4). The audit script counts `injection` events per `team_name` —
> the file IS the persistent cross-invocation state. This is tested in
> `tests/hooks/test_audit_calculations.py` (3 counting tests).

### 3b. Role Violation Logging

In inject_context(), add role awareness (log-only, no blocking):

```python
subagent_type = tool_input.get("subagent_type", "unknown")
if subagent_type != "research":
    _log(
        f"[AGENT_TEAMS] WARNING: Non-research subagent_type '{subagent_type}' "
        f"in Agent Teams call (team_name={team_name}). "
        f"Phase 1 supports Research only. Injection proceeds."
    )
```

Note: Injection still proceeds. The hook cannot block. This is observability, not enforcement.

---

## 4. Unit Tests (Fast, in `make test`)

### New Tests for TeammateContextInjector

3 new tests to add to tests/hooks/test_teammate_context_injector.py:

> **Note:** Teammate counting tests were moved to WP5 (`test_audit_calculations.py`)
> where they test the audit script's count-from-JSONL logic. See the amendment note in
> Section 3a above.

**Role Violation Logging (2 tests):**

| Test | What it verifies |
|------|-----------------|
| `test_injection_logs_non_research_role_in_team` | Inject with subagent_type="engineer", verify warning logged |
| `test_injection_proceeds_despite_non_research_role` | Inject with subagent_type="engineer", verify TEAMMATE_PROTOCOL still in result |

**Protocol Sync (1 test):**

| Test | What it verifies |
|------|-----------------|
| `test_protocol_matches_source_of_truth` | Read TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 3, verify all 5 rule headings present in TEAMMATE_PROTOCOL constant |

All 3 tests are fast (no LLM, no network), deterministic, and run in `make test`.

---

## 5. Integration Tests (LLM-Required, in `make test-agent-teams`)

These require live Claude Code execution and are placed in tests/manual/agent_teams_battery/:

| Test | Input | Expected PM Behavior | Pass Criterion |
|------|-------|---------------------|----------------|
| Sequential dependency detection | "First find auth entry points, then find which lack rate limiting" | PM spawns ONE agent, not a team | No team_name in Agent calls |
| Scope boundary assignment | "Investigate auth, payments, notifications, and caching independently" | PM spawns 4 teammates with non-overlapping scopes | 4 Agent calls, each with explicit scope constraint |
| Trivial task rejection | "Check if package.json has a test script" | PM uses single agent, not a team | No team_name in Agent call |
| Fallback (env var absent) | Complex multi-question task with AGENT_TEAMS env var unset | PM spawns agents with run_in_background, no team_name | run_in_background=true, no team_name |
| Conflict handling | Synthesize conflicting results from 2 teammates | PM presents both findings, no adjudication | Both findings present in PM output |

---

## 6. Fallback Behavior

When CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS is absent:
1. TeammateContextInjector.is_enabled() returns False
2. should_inject() returns False (no team_name matters — injector is off)
3. PM falls back to Agent tool with run_in_background: true, no team_name
4. No TEAMMATE_PROTOCOL injection (correct — protocol references teammate semantics)
5. Research agent still has BASE_AGENT.md evidence requirements
6. PM still applies T2/T3 circuit breaker enforcement from PM_INSTRUCTIONS.md

The fallback works at the code level today. No code changes needed. The PM instructions already describe this behavior.

**Recommendation:** In fallback mode, PM should still set `name: "<topic>-researcher"` on Agent calls to maintain a correlation handle between spawned agents and research questions.
