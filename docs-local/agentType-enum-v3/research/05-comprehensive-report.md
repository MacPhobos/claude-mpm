# Comprehensive Report: Agent Naming & Deployment Unification v3

**Date**: 2026-03-06
**Status**: Final synthesis of 4-analyst team findings
**Target**: Fresh branch off `main` (no dependencies on `agenttype-enums` branch)

---

## Executive Summary

After extensive analysis by four specialists (Branch Historian, Baseline Auditor, Solution Architect, Devil's Advocate), we recommend a **two-tier approach**:

1. **Tier 1 — Minimal Viable Fix (MVF)**: 7 targeted changes that fix ALL active delegation failures and critical latent bugs. Deliverable in a single PR, ~2-3 hours effort, LOW risk.

2. **Tier 2 — Architectural Improvement**: Deeper structural changes (unified registry, enum consolidation, deployment path cleanup). Deliverable as 2-3 follow-up PRs, each independently shippable.

This approach is the OPPOSITE of the failed `agenttype-enums` branch pattern, which attempted all changes in one 15-commit sequence and required 3 correction commits.

---

## The Problems (Ranked by Severity)

### CRITICAL — Active Delegation Failures

| # | Problem | Impact | Evidence |
|---|---------|--------|----------|
| C1 | `CLAUDE_MPM_OUTPUT_STYLE.md:23` references `local-ops` (should be `Local Ops`) | PM delegation fails for local-ops when triggered by output style | v2 PM Prompt Auditor |
| C2 | `CLAUDE_MPM_OUTPUT_STYLE.md:75` references `Documentation` (should be `Documentation Agent`) | PM delegation fails for docs agent | v2 PM Prompt Auditor |
| C3 | `system_context.py` tells PM lowercase works (`"research"`, `"version-control"`) | PM sends wrong `subagent_type` format | v2 Devil's Advocate |
| C4 | 6+ PM prompt/template files use filename stems instead of `name:` values | `pm-examples.md` has 10x `local-ops-agent`, `pr-workflow-examples.md` has 8x `version-control`, `WORKFLOW.md` still has `api-qa`/`web-qa`/`local-ops` after cherry-pick | v3 Verification Pass |

### HIGH — Latent Bugs (Will Cause Failures Under Certain Code Paths)

| # | Problem | Impact | Evidence |
|---|---------|--------|----------|
| H1 | `CANONICAL_NAMES` diverges from actual `name:` values for 10 agents | Any code using `AgentNameNormalizer` for delegation-adjacent logic produces wrong names | v2 Devil's Advocate |
| H2 | `agents deploy` command calls non-existent `sync_repository()` method | The CLI deploy command literally doesn't work | Branch commit #11 |
| H3 | PM_INSTRUCTIONS.md references agents by filename stems in some places | Delegation may fail if PM uses these references | v8 correction plan |

### MEDIUM — Architectural Debt (Doesn't Cause User-Facing Failures)

| # | Problem | Impact | Evidence |
|---|---------|--------|----------|
| M1 | 39 dead JSON templates in `templates/archive/` | Dead code, potential confusion, test complexity | All analysts agree |
| M2 | `AgentType` enum gap — 87% of frontmatter values not in any enum | Type filtering returns CUSTOM/None for most agents (informational only) | v2 Naming Analyst |
| M3 | 5+ competing agent name lists with different formats | `CORE_AGENTS` in 5 files + `AGENT_TEMPLATES` in `templates/__init__.py` + `AGENT_NICKNAMES` — all divergent | v2 PM Prompt Auditor, v3 Verification |
| M4 | 5+ normalization functions with subtle differences | Edge-case divergence risk | v2 Code Archaeologist |
| M5 | 3 deployment paths with different normalization | Inconsistent frontmatter in deployed agents | v2 Code Archaeologist |
| M6 | `agent_frontmatter_schema.json` requires lowercase `name` pattern but agents use Title Case | Schema enforcement would break all agents | v3 Devil's Advocate |
| M7 | Frontmatter field `type:` vs `agent_type:` inconsistency | Some code reads `type`, some reads `agent_type` — no standard | v3 Verification Pass |
| M8 | `templates/__init__.py` is 100% dead module | `AGENT_TEMPLATES` references 10 nonexistent files, zero production consumers | v3 Verification Pass |

### LOW — Cosmetic / Metadata

| # | Problem | Impact | Evidence |
|---|---------|--------|----------|
| L1 | `agent_id` mismatches (54% don't match filename stem) | Internal confusion only | v2 Naming Analyst |
| L2 | `WORKFLOW.md:39` uses `qa` instead of `QA` | May fail delegation (case-sensitive) | v2 PM Prompt Auditor |
| L3 | 6 non-conforming upstream `name:` values | Requires ugly names in PM delegation | All analysts |

---

## Approach: Hybrid Implementation

Based on the devil's advocate's analysis, we adopt a **hybrid approach**:

### What We Cherry-Pick (3 clean commits from the branch)
- **Commit `e2c9e59c`** — `agents deploy` fix (standalone bug fix, no dependencies)
- **Commit `6ff9727c`** — `agent_name_registry.py` creation (standalone new file)
- **Commit `f392f54e`** — PM_INSTRUCTIONS.md + WORKFLOW.md reference fixes (standalone text changes)

These commits have NO correction chains and represent verified, hard-won work.

### What We Implement Fresh
Everything else, informed by all research findings and the architect's design.

### What We Drop
- Archive README creation (was created then deleted)
- `templates/__init__.py` partial deprecation (just delete it fully)
- `bump_agent_versions` rewrite (possibly dead code)

---

## Key Design Decisions (Resolving Team Disagreements)

### 1. AgentType: Extend, Don't Rename
- **Architect proposed**: Rename `AgentType` → `AgentCategory` (25+ files)
- **Devil's advocate argued**: Extend existing enum with missing values (2-3 files)
- **Decision**: **Extend**. Add the 10 missing category values to `agent_definition.py:AgentType`. Keep `unified_agent_registry.py:AgentType` separate (different purpose). Zero consumer changes needed for existing code.

### 2. Registry: Hardcoded with Dynamic Refresh
- **Architect proposed**: Hardcoded `AGENT_REGISTRY` + CI drift detection
- **Devil's advocate argued**: Hardcoded maps go stale (proven by `CANONICAL_NAMES`)
- **Decision**: **Hybrid**. Hardcoded `AGENT_NAME_MAP` as baseline, with lazy `_refresh_from_deployed()` that reads `.claude/agents/` when available. Hardcoded entries serve as fallback for testing/CI.

### 3. Deployment Paths: Normalize Filenames, Don't Merge Paths
- **Architect proposed**: Route all 3 paths through `deploy_agent_file()`
- **Devil's advocate argued**: `SingleAgentDeployer` builds content (different use case), `configure.py` preserves upstream exactly
- **Decision**: **Keep separate paths**. Add `normalize_deployment_filename()` call to `SingleAgentDeployer` for target filename. Add `ensure_agent_id_in_frontmatter()` call after `configure.py` copy. Don't force all content through one function.

### 4. Phase Count: 3 Phases, Not 5
- **Architect proposed**: 5 phases
- **Devil's advocate argued**: Fewer boundaries = fewer failure points
- **Decision**: **3 phases** (MVF → Registry+Enum → Cleanup+Tests). The MVF is a single PR. Remaining work is 2 optional follow-up PRs.

### 5. Fresh vs Cherry-Pick: Hybrid
- **Historian recommended**: Full fresh start
- **Devil's advocate argued**: 3 commits are clean and reusable
- **Decision**: **Hybrid**. Cherry-pick 3 proven commits, fresh-implement everything else.

### 6. Deployment Paths: Normalize, Not Consolidate (Reinterpretation of Goal)
- **User requested**: Consolidation of 3 deployment paths into one
- **Our recommendation**: Keep separate paths, normalize behavior across all three
- **Rationale**: The 3 paths serve genuinely different use cases:
  - Path 1 (`deploy_agent_file`): Builds from scratch with full normalization
  - Path 2 (`SingleAgentDeployer`): Builds from JSON templates via template_builder
  - Path 3 (`configure.py`): Copies pre-built .md from cache (preserves upstream exactly)
  Forcing all through one function would require Path 2 to stop building content
  and Path 3 to stop preserving upstream exactly. Both would introduce regressions.
- **What we DO deliver**: All 3 paths produce identical output filenames and
  consistent frontmatter, achieving the user's underlying goal (no duplicates,
  consistent naming) without the risk of merging different content-building strategies.

### 7. Frontmatter Field Standardization: `agent_type` Not `type`
- **User requested**: Standardize on `agent_type:` as the frontmatter field name
- **Finding**: Code is split — some reads `"type"`, some reads `"agent_type"`
- **Decision**: Standardize all code to read `agent_type` with fallback to `type` for backward compatibility. Add to Phase 2 as Change 6.

---

## Implementation Phases

### Phase 1: Minimal Viable Fix (MVF) — Single PR
**Goal**: Fix ALL active delegation failures and critical latent bugs.
**Effort**: ~2-3 hours
**Risk**: LOW
**Plan file**: `plans/phase-1-minimal-viable-fix.md`

Changes:
1. Cherry-pick `agents deploy` fix
2. Cherry-pick `agent_name_registry.py`
3. Cherry-pick PM_INSTRUCTIONS.md + WORKFLOW.md fixes
4. Fix CLAUDE_MPM_OUTPUT_STYLE.md (2 broken references)
5. Fix system_context.py incorrect lowercase guidance
6. Reconcile CANONICAL_NAMES with actual name: values (10 entries)
7. Delete `templates/archive/` (39 JSON files) + clean up references
8. Add drift-detection test
9. Fix `agent_frontmatter_schema.json` name pattern
10. **[ADDED]** Full PM prompt audit — fix 6+ additional files with wrong agent references (WORKFLOW.md residuals, pm-examples.md, pr-workflow-examples.md, circuit-breakers.md, BASE_AGENT.md)

### Phase 2: Registry & Enum Consolidation — Follow-up PR
**Goal**: Unify the identity and type systems.
**Effort**: ~3-4 hours
**Risk**: MEDIUM
**Plan file**: `plans/phase-2-registry-enum-consolidation.md`

Changes:
1. Extend `AgentType` enum with 10 missing category values
2. Update `_safe_parse_agent_type()` to handle all frontmatter values
3. Consolidate CORE_AGENTS into single canonical constant
4. Add dynamic refresh to agent name registry
5. Merge `agents_metadata.py` type system alignment
6. **[ADDED]** Standardize frontmatter field: `type:` → `agent_type:` across all code that parses agent frontmatter

### Phase 3: Deployment & Normalization Cleanup — Follow-up PR
**Goal**: Reduce technical debt in deployment pipeline and normalization.
**Effort**: ~3-4 hours
**Risk**: MEDIUM
**Plan file**: `plans/phase-3-deployment-normalization-cleanup.md`

Changes:
1. Add `normalize_deployment_filename()` to `SingleAgentDeployer`
2. Add `ensure_agent_id_in_frontmatter()` to `configure.py` deploy
3. Consolidate normalization functions (5+ → 2)
4. **[UPGRADED]** Gut dead `templates/__init__.py` module (AGENT_TEMPLATES, AGENT_NICKNAMES, 2 dead functions — all reference nonexistent files)
5. Add comprehensive integration tests

---

## Guard Rails (All Phases)

1. **Grep before EVERY commit**: Search for ALL reference patterns being changed
2. **Run full test suite**: `make test` after every commit
3. **Never split rename + reference fix**: Same commit always
4. **Verify local_template_manager.py** before deleting templates code
5. **Never change a `name:` field value** without verifying delegation still works
6. **Update agent_frontmatter_schema.json** if touching agent name validation
7. **Test PM delegation manually** for at least 3 agents after PM prompt changes

---

## Preconditions (Must Be True)

1. `name:` field IS the sole resolution key for Claude Code (confirmed empirically v6)
2. `CANONICAL_NAMES` is NOT used for delegation (verify with grep)
3. Archive directory has no runtime consumers (verify `local_template_manager.py`)
4. `ensure_agent_id_in_frontmatter` only touches `agent_id:`, never `name:`
5. The 6 non-conforming upstream `name:` values are stable

---

## Analyst Attribution

| Finding | Discoverer | Report |
|---------|------------|--------|
| Branch correction chains | Branch Historian | 01-branch-history |
| .claude/agents/ empty on main | Baseline Auditor | 02-baseline |
| 8-component architecture | Solution Architect | 03-architecture |
| MVF recommendation | Devil's Advocate | 04-devils-advocate |
| Hybrid cherry-pick approach | Devil's Advocate | 04-devils-advocate |
| AgentCategory rename blast radius | Devil's Advocate | 04-devils-advocate |
| Schema validation bomb | Devil's Advocate | 04-devils-advocate |
| Deployment path separation | Devil's Advocate | 04-devils-advocate |
| KEEP/REDO/DROP/NEW classification | Branch Historian | 01-branch-history |
| Archive exists on main (v2 team error) | Devil's Advocate | 04-devils-advocate |
