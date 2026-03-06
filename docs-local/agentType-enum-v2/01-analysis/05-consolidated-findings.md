# Consolidated Analysis: Agent Naming, Deployment, and Resolution

**Date**: 2026-03-06
**Branch**: `agenttype-enums`
**Team**: Code Archaeologist, PM Prompt Auditor, Naming Standards Analyst, Devil's Advocate
**Status**: All four analysis streams complete; this document synthesizes findings.

---

## Executive Summary

A four-analyst team investigated agent naming, deployment pipeline, PM delegation resolution, and frontmatter consistency from independent angles. The analysis reveals that **several originally-proposed problems are already resolved** (filename separators, `type:` → `agent_type:` rename, archive removal), while **deeper systemic issues were discovered** that were NOT identified in prior research (v2-v8).

### The Three Root Problems

1. **Dual normalization divergence** — `AgentNameNormalizer.CANONICAL_NAMES` and `AGENT_NAME_MAP` produce different names for 10 agents, creating latent delegation bugs.
2. **AgentType enum gap** — 87% of frontmatter `agent_type:` values don't match any Python enum, making type-based filtering effectively broken.
3. **Three competing identity systems** — Upstream `name:` fields, `AGENT_NAME_MAP`, and `CANONICAL_NAMES` all provide different answers for the same agent.

---

## Section 1: What's Already Resolved (No Action Needed)

All four analysts independently confirmed these are non-issues:

### 1.1 Archive Templates — DOES NOT EXIST
- **Archaeologist**: `src/claude_mpm/agents/templates/archive/` directory does not exist. `rglob` searches return nothing.
- **Devil's Advocate**: Confirmed. No tests reference archive templates. No migration code depends on them.
- **Verdict**: ✅ No action needed. Remove this from the proposal scope.

### 1.2 Filename Separator Standardization — ALREADY COMPLETE
- **Naming Analyst**: All 48 deployed agents use kebab-case filenames. Zero underscore filenames exist.
- **Archaeologist**: `normalize_deployment_filename()` converts `_` → `-` during deployment.
- **Devil's Advocate**: Confirmed via independent grep. v8 Phases 1-4 already addressed this.
- **Verdict**: ✅ Complete. No further filename changes needed.

### 1.3 `type:` → `agent_type:` Field Rename — ALREADY COMPLETE
- **Naming Analyst**: All 48 agents use `agent_type:` in frontmatter. Zero use bare `type:`.
- **Devil's Advocate**: Confirmed. `agent_type:` is a claude-mpm extension, not a Claude Code standard field. No risk.
- **Verdict**: ✅ Complete. Only cosmetic cleanup needed (one example in `mpm-agent-manager.md` shows old `type:` format).

### 1.4 File-Level Duplication — ALREADY RESOLVED
- **Naming Analyst**: MD5 checksums show 100% match between deployed and cached agents. No duplicate files.
- **Devil's Advocate**: v8 Phase 4 already cleaned up legacy duplicates.
- **Verdict**: ✅ No duplicate agent files exist. Legacy `-agent` suffixed entries remain only in `AGENT_NAME_MAP` as backward compatibility.

---

## Section 2: Confirmed Active Problems

### 2.1 CRITICAL: Dual Normalization Divergence (NEW FINDING)

**Discovered by**: Devil's Advocate
**Confirmed by**: Naming Analyst, Code Archaeologist

Two separate name resolution systems produce DIFFERENT output for 10 agents:

| Agent Stem | Actual `name:` Field | `AGENT_NAME_MAP` (registry) | `CANONICAL_NAMES` (normalizer) | Divergent? |
|---|---|---|---|---|
| ticketing | `ticketing_agent` | `ticketing_agent` ✅ | `Ticketing` ❌ | **YES** |
| code-analyzer | `Code Analysis` | `Code Analysis` ✅ | `Code Analyzer` ❌ | **YES** |
| gcp-ops | `Google Cloud Ops` | `Google Cloud Ops` ✅ | `GCP Ops` ❌ | **YES** |
| clerk-ops | `Clerk Operations` | `Clerk Operations` ✅ | `Clerk Ops` ❌ | **YES** |
| real-user | `real-user` | `real-user` ✅ | `Real User` ❌ | **YES** |
| mpm-agent-manager | `mpm_agent_manager` | `mpm_agent_manager` ✅ | `MPM Agent Manager` ❌ | **YES** |
| mpm-skills-manager | `mpm_skills_manager` | `mpm_skills_manager` ✅ | `MPM Skills Manager` ❌ | **YES** |
| javascript-engineer | `Javascript Engineer` | `Javascript Engineer` ✅ | `JavaScript Engineer` ❌ | **YES** |
| typescript-engineer | `Typescript Engineer` | `Typescript Engineer` ✅ | `TypeScript Engineer` ❌ | **YES** |
| nestjs-engineer | `nestjs-engineer` | `nestjs-engineer` ✅ | `NestJS Engineer` ❌ | **YES** |

**Impact**: Any code path using `AgentNameNormalizer` for delegation produces WRONG `subagent_type` values for 10 agents, causing silent delegation failures. `AGENT_NAME_MAP` is correct; `CANONICAL_NAMES` has "prettier" but WRONG values.

**Location**:
- `src/claude_mpm/core/agent_name_normalizer.py` (CANONICAL_NAMES, lines 21-75)
- `src/claude_mpm/core/agent_name_registry.py` (AGENT_NAME_MAP, lines 43-116)

### 2.2 CRITICAL: AgentType Enum Gap (NEW FINDING)

**Discovered by**: Naming Standards Analyst
**Confirmed by**: Code Archaeologist

15 distinct `agent_type:` values exist in agent frontmatter. Only 2 (13%) match any Python AgentType enum value:

| Frontmatter Value | Count | In Enum 1 (`models/`)? | In Enum 2 (`core/`)? |
|---|---|---|---|
| `engineer` | 21 | NO | NO |
| `ops` | 10 | NO | NO |
| `qa` | 4 | NO | NO |
| `documentation` | 2 | NO | NO |
| `research` | 2 | NO | NO |
| `security` | 1 | NO | NO |
| `system` | 1 | YES | NO |
| `specialized` | 1 | YES | YES |
| `claude-mpm` | 1 | NO | NO |
| `analysis` | 1 | NO | NO |
| `refactoring` | 1 | NO | NO |
| `imagemagick` | 1 | NO | NO |
| `product` | 1 | NO | NO |
| `content` | 1 | NO | NO |
| `memory_manager` | 1 | NO | NO |

**Two competing enums**:
- `models/agent_definition.py:25`: `core, project, custom, system, specialized`
- `core/unified_agent_registry.py:52`: `core, specialized, user_defined, project, memory_aware`

**Third type system**: `agents_metadata.py` uses `core_agent`, `optimization_agent`, `system_agent` — matching neither enum nor frontmatter.

**Impact**: `_safe_parse_agent_type()` silently converts 87% of agents to `AgentType.CUSTOM` or `None`, making type-based filtering/routing non-functional.

### 2.3 HIGH: Three Broken PM Prompt References

**Discovered by**: PM Prompt Auditor

| Issue | Location | Current | Should Be | Impact |
|---|---|---|---|---|
| Wrong agent name | `CLAUDE_MPM_OUTPUT_STYLE.md:23` | `local-ops` | `Local Ops` | Delegation failure |
| Truncated name | `CLAUDE_MPM_OUTPUT_STYLE.md:75` | `Documentation` | `Documentation Agent` | Delegation failure |
| Wrong case | `WORKFLOW.md:39` | `qa` | `QA` | May fail delegation |

### 2.4 HIGH: Five Competing CORE_AGENTS Lists

**Discovered by**: PM Prompt Auditor
**Confirmed by**: Code Archaeologist

| Location | Format | Count | Unique Agents |
|---|---|---|---|
| `framework_agent_loader.py:35` | filename stems | 6 | engineer, research, qa, documentation, ops, ticketing |
| `toolchain_detector.py:162` | mixed stems+agent_ids | 7 | +memory-manager, local-ops, security; -ticketing, -ops |
| `agent_presets.py:29` | path format | 9 | +mpm-agent-manager, mpm-skills-manager, web-qa |
| `agent_recommendation_service.py:36` | filename stems (set) | 6 | Same as framework_agent_loader |
| `agent_deployment_handler.py:26` | filename stems | 7 | +web-qa |

12 distinct agents referenced across the 5 lists, with no list containing all of them.

### 2.5 HIGH: Five+ Normalization Functions with Subtle Differences

**Discovered by**: Code Archaeologist

| Function | Location | Strips `-agent`? | Handles spaces? | Handles `_`? |
|---|---|---|---|---|
| `normalize_deployment_filename` | deployment_utils.py | Yes | No | `_` → `-` |
| `_normalize_agent_name` | multi_source_deployment_service.py | No | space → `-` | `_` → `-` |
| `AgentNameNormalizer.normalize` | agent_name_normalizer.py | Yes (+ `-agent-agent`) | space → `-` | `_` → `-` |
| `normalize_agent_id_for_comparison` | agent_filters.py | Yes | No | `_` → `-` |
| `DynamicAgentRegistry.normalize_agent_id` | agent_registry.py | Yes | space → `-` | `_` → `-` |
| `SingleAgentDeployer` (inline) | single_agent_deployer.py:68 | Yes | No | `_` → `-` |

Most agree for common cases but diverge on edge cases (space handling, `-agent` suffix logic).

### 2.6 HIGH: `system_context.py` Provides Incorrect Guidance

**Discovered by**: Devil's Advocate

`src/claude_mpm/core/system_context.py:31-36` tells PM that lowercase format works:
```
"Lowercase format: 'research', 'engineer', 'qa', 'version-control', 'data-engineer'"
```

This is WRONG — `Agent(subagent_type="golang-engineer")` **fails** while `Agent(subagent_type="Golang Engineer")` succeeds. Only single-word agents (`research`, `engineer`, `qa`) work in lowercase because they happen to match.

### 2.7 MEDIUM: `agent_id` Mismatches (54% of agents)

**Discovered by**: Naming Analyst, Code Archaeologist

26 of 48 deployed agents have `agent_id:` values that don't match their filename stem:
- **14 agents**: underscore in `agent_id`, hyphen in filename (e.g., `golang_engineer` vs `golang-engineer.md`)
- **11 agents**: `-agent` suffix in `agent_id` not in filename (e.g., `research-agent` vs `research.md`)
- **1 agent**: `-engineer` suffix mismatch (`web-ui-engineer` vs `web-ui.md`)

Root cause: `ensure_agent_id_in_frontmatter()` uses `update_existing=False` — original `agent_id` values from git source are never overwritten.

### 2.8 MEDIUM: Dual Deployer Code Paths

**Discovered by**: Code Archaeologist

Two active deployment paths exist:
1. **`deploy_agent_file()`** (deployment_utils.py) — unified path with full normalization
2. **`SingleAgentDeployer.deploy_single_agent()`** (single_agent_deployer.py) — legacy path that does NOT call `deploy_agent_file()`, skips underscore cleanup and frontmatter injection

Evidence: 3 agents still deployed with `-agent` suffix in filename (`content-agent.md`, `memory-manager-agent.md`, `tmux-agent.md`) — these were deployed by a non-normalizing code path.

### 2.9 LOW: Bonus Bug — `ticketing.md` Has Wrong `agent_type`

**Discovered by**: Devil's Advocate

`ticketing.md` has `agent_type: documentation` — should be `ticketing` or `documentation` (if intentional for the documentation category). The ticketing agent is categorized under documentation in the cache hierarchy, but `agent_type: documentation` seems incorrect for a ticketing agent.

---

## Section 3: Disputed Findings and Resolutions

### 3.1 Dispute: Should `name:` Field Inconsistencies Be Fixed?

**Naming Analyst**: YES — standardize all 6 outliers to Title Case.
**Devil's Advocate**: AGREES it's the root cause, but notes these values come from upstream repo declared OUT OF SCOPE.

**Resolution**: The 6 non-conforming `name:` values (`ticketing_agent`, `aws_ops_agent`, `mpm_agent_manager`, `mpm_skills_manager`, `nestjs-engineer`, `real-user`) are the PRIMARY source of naming chaos. Declaring them "out of scope" is a process decision, not a technical one. **RECOMMENDATION**: Fix upstream. The effort is minimal (6 file edits) and the downstream simplification is massive.

### 3.2 Dispute: Should Legacy `-agent` Entries in AGENT_NAME_MAP Be Removed?

**Devil's Advocate**: NEEDS MORE DATA — check if any code still references legacy names.
**PM Prompt Auditor**: `toolchain_detector.py` previously used them but was fixed in v8 Phase 4.

**Resolution**: Grep the codebase for each legacy name. If no references remain, remove them to reduce confusion. If references exist, fix the references first.

### 3.3 Dispute: Should We Add More Normalization or Consolidate?

**Devil's Advocate**: DO NOT add more normalization layers. The problem is too many maps.
**All Analysts**: Agree — consolidation, not addition.

**Resolution**: Merge `AgentNameNormalizer.CANONICAL_NAMES` into alignment with `AGENT_NAME_MAP`. Long-term, consider merging both modules.

---

## Section 4: Prioritized Action Items

### Priority 1 — CRITICAL (Latent Bugs / Silent Failures)

| # | Action | Files Affected | Risk | Effort |
|---|---|---|---|---|
| **C1** | Reconcile `CANONICAL_NAMES` with `AGENT_NAME_MAP` — fix 10 divergent entries | `agent_name_normalizer.py` | Latent delegation bugs | Small (update dict) |
| **C2** | Fix `system_context.py` — remove incorrect claim that lowercase works | `system_context.py` | PM sends wrong `subagent_type` | Trivial (edit text) |
| **C3** | Create unified `AgentType` enum covering all 15 frontmatter values | `models/agent_definition.py`, `unified_agent_registry.py` | Type filtering broken for 87% of agents | Medium |

### Priority 2 — HIGH (Broken References / Fragmentation)

| # | Action | Files Affected | Risk | Effort |
|---|---|---|---|---|
| **H1** | Fix 3 broken PM prompt references | `CLAUDE_MPM_OUTPUT_STYLE.md`, `WORKFLOW.md` | Active delegation failures | Trivial (3 edits) |
| **H2** | Consolidate 5 CORE_AGENTS lists into one canonical registry | 5 files importing CORE_AGENTS | Fragmented agent set definitions | Medium |
| **H3** | Fix upstream `name:` field values for 6 non-conforming agents | Upstream `claude-mpm-agents` repo | Root cause of naming chaos | Small (6 edits + downstream) |
| **H4** | Eliminate `SingleAgentDeployer` or route through `deploy_agent_file()` | `single_agent_deployer.py` | Dual deployer creates inconsistencies | Medium |

### Priority 3 — MEDIUM (Consistency / Tech Debt)

| # | Action | Files Affected | Risk | Effort |
|---|---|---|---|---|
| **M1** | Fix `agent_id` mismatches — set `update_existing=True` or standardize source | `deployment_utils.py` or upstream | 54% mismatch | Medium |
| **M2** | Consolidate 5+ normalization functions into single canonical normalizer | 6 files | Subtle edge-case divergences | Large |
| **M3** | Eliminate `agents_metadata.py` third type system | `agents_metadata.py` | Disconnected type taxonomy | Medium |
| **M4** | Fix `ticketing.md` `agent_type: documentation` | Upstream | Wrong categorization | Trivial |
| **M5** | Normalize 3 remaining `-agent` suffixed filenames | `content-agent.md`, `memory-manager-agent.md`, `tmux-agent.md` | Inconsistent with normalization rules | Small |

### Priority 4 — LOW (Metadata Quality)

| # | Action | Files Affected | Risk | Effort |
|---|---|---|---|---|
| **L1** | Add `author:` field to 30 agents missing it | 30 upstream agent files | Incomplete metadata | Tedious |
| **L2** | Add `schema_version:` to 2 agents missing it | `nestjs-engineer.md`, `real-user.md` | Validation may fail | Trivial |
| **L3** | Add CI test asserting `CANONICAL_NAMES` == `AGENT_NAME_MAP` | New test file | Prevent future drift | Small |

---

## Section 5: Phased Implementation Plan

### Phase A: Stop the Bleeding (This PR)
**Goal**: Fix active bugs and latent failures. No architectural changes.

1. **C1**: Update `CANONICAL_NAMES` in `agent_name_normalizer.py` to match `AGENT_NAME_MAP` values
2. **C2**: Fix `system_context.py` incorrect lowercase guidance
3. **H1**: Fix 3 broken PM prompt references (`CLAUDE_MPM_OUTPUT_STYLE.md:23,75`, `WORKFLOW.md:39`)
4. **M4**: Fix `ticketing.md` `agent_type: documentation` → correct value
5. **L3**: Add drift-detection test

### Phase B: Unify Type System (Next PR)
**Goal**: Create one authoritative AgentType enum covering actual frontmatter values.

1. **C3**: Design unified enum with all 15 values (or consolidate outliers into fewer categories)
2. Merge `models/agent_definition.py` and `core/unified_agent_registry.py` enums
3. **M3**: Eliminate `agents_metadata.py` third type system
4. Update `_safe_parse_agent_type()` to use new comprehensive enum

### Phase C: Consolidate Registries (Follow-up)
**Goal**: Single source of truth for agent identity.

1. **H2**: Create one canonical `CORE_AGENTS` constant imported by all 5 modules
2. **M2**: Consolidate normalization functions (keep 1-2 with clear purposes)
3. **H4**: Route `SingleAgentDeployer` through `deploy_agent_file()` or remove

### Phase D: Fix Upstream (Separate PR to claude-mpm-agents)
**Goal**: Standardize the actual source of truth.

1. **H3**: Fix 6 non-conforming `name:` values to Title Case
2. **M1**: Fix `agent_id` values to match filename stems (kebab-case, no suffixes)
3. **L1**, **L2**: Add missing metadata fields
4. **M5**: Rename 3 `-agent` suffixed files in source repo

### Phase E: Validation (CI)
**Goal**: Prevent regression.

1. CI test: All PM prompt agent references match deployed `name:` fields
2. CI test: `CANONICAL_NAMES` ⊆ `AGENT_NAME_MAP` (no divergence)
3. CI test: All frontmatter `agent_type:` values exist in unified enum
4. CI test: All `agent_id:` values match filename stems

---

## Section 6: Key Metrics

| Metric | Before Analysis | Current State |
|---|---|---|
| Filename separator consistency | Was mixed `_`/`-` | ✅ 100% kebab-case |
| `type:` vs `agent_type:` field | Was mixed | ✅ 100% `agent_type:` |
| Archive contamination risk | Was a concern | ✅ Directory doesn't exist |
| `name:` field Title Case compliance | — | 87.5% (6 outliers) |
| `agent_id` matches filename stem | — | 46% (26 mismatches) |
| AgentType enum coverage | — | 13% (87% uncovered) |
| CANONICAL_NAMES accuracy | — | 79% (10 divergent) |
| PM prompt reference accuracy | — | 93% (3 broken) |
| CORE_AGENTS list consistency | — | 0% (5 different lists) |
| Normalization function consistency | — | ~80% (edge cases diverge) |

---

## Section 7: Analyst Attribution

| Finding | Primary Discoverer | Confirmed By |
|---|---|---|
| Archive doesn't exist | Code Archaeologist | Devil's Advocate |
| Filename standardization complete | Naming Analyst | Devil's Advocate |
| `agent_type:` rename complete | Naming Analyst | Devil's Advocate |
| 3 broken PM references | PM Prompt Auditor | — |
| 5 CORE_AGENTS lists | PM Prompt Auditor | — |
| Dual normalization divergence (10 agents) | Devil's Advocate | Naming Analyst |
| AgentType enum gap (87%) | Naming Analyst | Code Archaeologist |
| 5+ normalization functions | Code Archaeologist | — |
| `system_context.py` incorrect guidance | Devil's Advocate | — |
| `ticketing.md` wrong agent_type | Devil's Advocate | — |
| Dual deployer code paths | Code Archaeologist | — |
| `agent_id` 54% mismatch | Naming Analyst | Code Archaeologist |
| 3 remaining `-agent` suffixed filenames | Code Archaeologist | — |
| `ensure_agent_id_in_frontmatter` doesn't overwrite | Code Archaeologist | — |
| `agents_metadata.py` third type system | Naming Analyst | — |

---

## Appendix A: Files Referenced Across All Reports

### Pipeline Code
- `src/claude_mpm/services/agents/deployment_utils.py` — single source of truth for deployment
- `src/claude_mpm/services/agents/deployment/single_agent_deployer.py` — legacy deployer (DIVERGENT)
- `src/claude_mpm/services/agents/sources/git_source_sync_service.py` — git sync
- `src/claude_mpm/services/agents/single_tier_deployment_service.py` — orchestrator
- `src/claude_mpm/services/agents/deployment/agent_discovery_service.py` — template discovery

### Registries & Normalizers
- `src/claude_mpm/core/agent_name_registry.py` — `AGENT_NAME_MAP` (CORRECT for delegation)
- `src/claude_mpm/core/agent_name_normalizer.py` — `CANONICAL_NAMES` (WRONG for 10 agents)
- `src/claude_mpm/core/unified_agent_registry.py` — AgentType enum #2
- `src/claude_mpm/models/agent_definition.py` — AgentType enum #1
- `src/claude_mpm/agents/agents_metadata.py` — third type system
- `src/claude_mpm/utils/agent_filters.py` — normalize_agent_id_for_comparison

### PM Prompts
- `src/claude_mpm/agents/PM_INSTRUCTIONS.md` — main PM instructions (mostly correct)
- `src/claude_mpm/agents/CLAUDE_MPM_OUTPUT_STYLE.md` — 2 broken references
- `src/claude_mpm/agents/WORKFLOW.md` — 1 broken reference
- `src/claude_mpm/core/system_context.py` — incorrect lowercase guidance

### CORE_AGENTS Lists
- `src/claude_mpm/agents/framework_agent_loader.py:35` — 6 agents
- `src/claude_mpm/services/agents/toolchain_detector.py:162` — 7 agents (mixed format)
- `src/claude_mpm/services/agents/agent_presets.py:29` — 9 agents (path format)
- `src/claude_mpm/services/agents/agent_recommendation_service.py:36` — 6 agents
- `src/claude_mpm/services/agents/deployment/agent_deployment_handler.py:26` — 7 agents
