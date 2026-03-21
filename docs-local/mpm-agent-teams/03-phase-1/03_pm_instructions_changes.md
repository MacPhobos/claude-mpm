# PM_INSTRUCTIONS.md Changes Spec

**Phase:** 1
**Status:** Diff-ready specification
**Constraint:** Changes must add < 50 new lines to PM_INSTRUCTIONS.md
**Scope:** Parallel Research only — no mixed teams, no parallel Engineering/QA

---

## 1. New Section: "Agent Teams Delegation"

Insert this section **after** the existing "Standard Operating Procedure" section and **before** the "Model Selection Protocol" section. This is the primary addition (~35 lines).

```markdown
## Agent Teams: Parallel Research

When `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is active, you can spawn parallel
Research teammates for complex investigations. This is the ONLY team pattern in
Phase 1.

### When to Use Teams

Spawn a Research team (2-3 teammates) when ALL conditions are met:
- The task decomposes into >= 2 **independent** research questions
- Research questions target **different** subsystems (< 20% file overlap)
- No sequential dependency between questions

Do NOT use teams when:
- The task is a single linear investigation
- Research questions depend on each other's results
- Scope is small (< 3 files to examine)
- Agent Teams env var is not set (fall back to `run_in_background`)

### Spawning Protocol

1. Decompose the request into independent research questions (state these in your response)
2. Spawn all teammates in a **single message** using the Agent tool:
   - `subagent_type`: "Research"
   - `team_name`: descriptive name (e.g., "auth-analysis")
   - `name`: per-teammate identifier (e.g., "auth-researcher")
   - `model`: "sonnet" (default) or "opus" (if user requests depth)
   - `prompt`: One focused question with explicit scope boundaries
3. Wait for all teammates to report via SendMessage
4. Validate each result (evidence block, file paths, no forbidden phrases)
5. Synthesize findings with attribution — do not claim teammate findings as your own
6. If teammates report conflicting findings, present both with attribution

### Anti-Patterns

- **Never** spawn teams for single-question research
- **Never** spawn > 3 Research teammates (Phase 1 limit)
- **Never** spawn Engineer or QA teammates in a team (Phase 1: Research only)
- **Never** use teams when subtasks have sequential dependencies
- **Never** resolve conflicting teammate findings yourself — present both to user

### Fallback

If Agent Teams is unavailable (no `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS`), use
standard `run_in_background: true` delegation with multiple Agent tool calls.
Same decomposition, same synthesis — different mechanism, transparent to user.
```

---

## 2. Modified Section: "When to Delegate to Each Agent"

Add ONE row to the existing delegation table. Do not restructure the table.

```markdown
| Agent Teams (Research) | Complex investigation decomposable into 2-3 independent questions | sonnet | Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` |
```

---

## 3. Modified Section: "Model Selection Protocol"

Add ONE line to the existing model routing rules:

```markdown
- **Agent Teams teammates:** Default sonnet. Override to opus only when user explicitly
  requests depth or when sonnet previously returned insufficient results for the same question.
```

---

## 4. Modified Section: "Circuit Breakers"

Add a reference (not the full protocol) to the team CB protocol. Insert after the existing CB list:

```markdown
**Agent Teams CB enforcement:** When operating as team lead, additional teammate
verification rules apply. See `TEAM_CIRCUIT_BREAKER_PROTOCOL.md` for the complete
classification (T1-T3 enforcement tiers) and teammate validation checklist.
```

---

## 5. Changes NOT Made (Intentionally Deferred)

These changes are deferred to Phase 2+ to keep PM_INSTRUCTIONS.md growth minimal:

| Potential Change | Why Deferred |
|-----------------|--------------|
| Mixed team composition rules (Engineer + QA + Research) | Phase 2: file conflict resolution not designed |
| Team size > 3 guidelines | Phase 2: needs orchestration protocol for larger teams |
| Peer-to-peer violation detection heuristics | Phase 2: needs PostToolUse SendMessage logging |
| Team lead spot-check protocol (re-run one test) | Phase 2: needs QA team pattern |
| Dashboard team visibility instructions | Phase 1: dashboard integration is for hooks, not PM behavior |

---

## 6. Line Count Budget

| Change | Lines Added |
|--------|:-----------:|
| New "Agent Teams: Parallel Research" section | ~35 |
| Delegation table row | 1 |
| Model routing line | 2 |
| Circuit breaker reference | 3 |
| **Total** | **~41** |

Within the < 50 line budget.

---

## 7. Testing the PM Instructions Change

After updating PM_INSTRUCTIONS.md, validate by:

1. **Manual smoke test:** Start a Claude Code session with MPM PM output style. Ask "Research how authentication and database patterns work in this codebase." Verify PM attempts team decomposition (if Agent Teams env is set) or standard parallel delegation (if not).

2. **Negative test:** Ask "Research how the login flow works." Verify PM does NOT attempt to spawn a team (single linear investigation).

3. **Anti-pattern test:** Ask "Implement a login page and test it." Verify PM does NOT spawn an Engineer+QA team (Phase 1 is Research-only).
