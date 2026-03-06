# Executive Summary: Agent Naming & Deployment Unification

**Date**: 2026-03-06
**Scope**: 3-phase fix across agent naming, PM delegation, and deployment pipeline
**Total Effort**: ~8-11 hours across 3 independent PRs
**Research Base**: 4 specialist analysts, 5 research reports, 1 verification pass

---

## 1. Concise Summary

Claude MPM's agent delegation system has a fundamental identity mismatch: the PM tells Claude Code to find agents using names that don't match what's actually deployed. Claude Code resolves agents by exact, case-sensitive match on the `name:` frontmatter field in `.claude/agents/*.md` files — but PM prompts, system context, and internal normalizers all reference agents using filename stems, lowercase variants, or inconsistent formats that Claude Code cannot resolve.

Additionally, three separate deployment code paths produce inconsistently named files (mixing `_` and `-` separators), 39 dead archive templates create confusion, competing hardcoded agent lists have drifted out of sync, and the frontmatter field name for agent type (`type:` vs `agent_type:`) is used inconsistently across the codebase.

The fix is structured in three phases: an immediate Minimal Viable Fix (Phase 1, LOW risk) that resolves all active delegation failures, followed by two architectural cleanup PRs (Phases 2-3, MEDIUM risk) that prevent recurrence.

---

## 2. Problem Areas Being Fixed

### A. PM Delegation Failures (CRITICAL — Phase 1)

PM prompt files instruct Claude Code to delegate using wrong agent identifiers. Claude Code cannot resolve these, causing silent delegation failures or errors.

| What PM Says | What Claude Code Needs | File |
|-------------|----------------------|------|
| `"research"` | `"Research"` | system_context.py |
| `"local-ops"` | `"Local Ops"` | CLAUDE_MPM_OUTPUT_STYLE.md |
| `"Documentation"` | `"Documentation Agent"` | CLAUDE_MPM_OUTPUT_STYLE.md |
| `"version-control"` | `"Version Control"` | pr-workflow-examples.md |
| `"local-ops-agent"` | `"Local Ops"` | pm-examples.md |
| `"api-qa"` | `"API QA"` | WORKFLOW.md |

**10+ files affected, 40+ individual wrong references.**

### B. Broken CLI Command (CRITICAL — Phase 1)

The `claude-mpm agents deploy` command calls a method with wrong parameters and crashes. Users cannot deploy agents via CLI.

### C. Internal Name Map Drift (HIGH — Phase 1)

`CANONICAL_NAMES` (used for display/normalization) has diverged from actual deployed `name:` values for 10 agents. Any code path that uses this map for delegation-adjacent logic produces wrong names.

### D. Dead Archive Templates (MEDIUM — Phase 1)

39 JSON templates in `templates/archive/` are leftover from a one-time migration. They are not discovered by the modern deployment pipeline (which globs `*.md` only), but their presence creates confusion and has misled prior implementation attempts.

### E. Fragmented Type System (MEDIUM — Phase 2)

- `AgentType` enum covers only 5 of ~15 observed frontmatter values (87% fall to `CUSTOM`)
- Two separate `AgentType` enums exist in different files with different meanings
- 5+ separate `CORE_AGENTS` lists across the codebase with different formats and different agent sets
- Frontmatter field inconsistency: some code reads `"type"`, some reads `"agent_type"`

### F. Inconsistent Deployment Output (MEDIUM — Phase 3)

Three deployment paths produce differently-named output files:
- Path 1 (`deploy_agent_file`): Full normalization (lowercase, dash-separated, dedup)
- Path 2 (`SingleAgentDeployer`): No normalization (raw template filename)
- Path 3 (`configure.py`): No normalization (raw `shutil.copy2`)

This causes duplicate agent files (e.g., both `python-engineer.md` and `python_engineer.md`) and inconsistent frontmatter in `.claude/agents/`.

### G. Dead Module (LOW — Phase 3)

`templates/__init__.py` contains `AGENT_TEMPLATES` mapping 10 agent types to files that don't exist, `AGENT_NICKNAMES` (a 6th competing agent name list), and two functions that always return `None`. Zero production consumers.

---

## 3. Impact If Not Fixed

### Immediate User-Facing Impact

**PM delegation is unreliable.** When a user asks Claude MPM to perform work, the PM agent delegates to specialist agents (Research, Engineer, QA, etc.) using the `subagent_type` parameter. If the value doesn't exactly match the agent's `name:` frontmatter field, Claude Code either:
- Fails silently (no agent found, task dropped)
- Raises an error (delegation failure message to user)
- Picks a wrong agent (if a partial match occurs)

This affects the core value proposition of Claude MPM — orchestrating work across specialized agents. **Every delegation attempt that uses a wrong identifier is a user-visible failure.**

Specific scenarios:
- User says "start the app" → PM tries to delegate to `local-ops` → fails (correct: `Local Ops`)
- User says "update the docs" → PM tries to delegate to `Documentation` → fails (correct: `Documentation Agent`)
- User says "run tests" → PM tries to delegate to `qa` → fails (correct: `QA`)
- `claude-mpm agents deploy` → crashes with method signature error → user cannot deploy agents

### Progressive Degradation If Left Unfixed

1. **Name map drift accelerates**: Every new agent added to the upstream repository increases the gap between hardcoded lists and reality. Without drift-detection tests, nobody notices until users report failures.

2. **Duplicate agents multiply**: Without normalized filenames across all deployment paths, each deploy cycle may create both `agent_name.md` and `agent-name.md`. Users see duplicate agents in listings, and Claude Code may resolve to the wrong copy.

3. **New features built on broken foundations**: The archive templates and dead `templates/__init__.py` module have already misled developers (the `agenttype-enums` branch spent 15 commits and 3 correction commits partly due to incorrect assumptions about these). Future work will repeat these mistakes.

4. **Type system becomes meaningless**: With 87% of agents classified as `CUSTOM`, any filtering, categorization, or recommendation logic based on `AgentType` is effectively random. The agent recommendation service (`agent_recommendation_service.py`) and toolchain detector (`toolchain_detector.py`) both rely on `CORE_AGENTS` lists that don't agree with each other.

### Business Impact

Claude MPM's competitive differentiation is autonomous multi-agent orchestration. If the PM cannot reliably delegate to the right agent, users experience:
- Failed workflows requiring manual intervention
- Wasted tokens on retries and error recovery
- Loss of trust in the "autonomous team" promise
- Regression to single-agent usage (defeating the purpose of MPM)

**The Phase 1 MVF (~2-3 hours, LOW risk) eliminates all active delegation failures. Phases 2-3 prevent recurrence and reduce technical debt. The cost of NOT fixing is ongoing user-visible failures in the product's core workflow.**
