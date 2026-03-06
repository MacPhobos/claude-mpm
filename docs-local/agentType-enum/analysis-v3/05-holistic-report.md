# Holistic Report: Agent Type Field Standardization (v3)

**Date**: 2026-03-03
**Author**: Synthesis Agent (Claude Opus 4.6), Team agenttype-enum-v3
**Branch**: `agenttype-enums`
**Task**: Task #5 — Synthesize findings from Tasks #1-#4 into comprehensive report
**Builds on**: analysis-v2 (5 docs), analysis-v2.1 (5 docs), analysis-v3 Tasks #1-#4

---

## 1. Executive Summary

The `claude-mpm` project suffers from a systematic field-naming split where agent type information is stored as `type:` in 48 deployed frontmatter files but as `agent_type` in ~170+ Python source locations, 39 JSON templates, 71 test files, and the entire hook/event system (80+ references). The root cause is a **single line of code** (`agent_template_builder.py:568`) that converts `agent_type` to `type` during deployment.

This report synthesizes findings from four specialized agents covering deployment pipelines, field usage mapping, skill-to-agent mapping, and adversarial risk assessment. It recommends standardizing on `agent_type` as the canonical field name, confirms the archive directory has zero runtime consumers, identifies a critical crash bug in `agent_management_service.py:444`, and warns that `-agent` suffixed agent files are NOT safe to remove without extensive code updates. File naming cleanup must be treated as a **separate effort**.

**Key numbers**:
- Python source code: `agent_type` dominates **4:1** (~170+ vs ~42 locations)
- Deployed frontmatter: `type:` dominates **2:1** (48 vs 27 files) — artificial, caused by the root-cause line
- Hook/event system: **100%** `agent_type` (80+ references, 12 files)
- JSON templates / Remote agents: **100%** `agent_type` (39 + 48 files)
- Test files: `agent_type` dominates **7:1** (71 vs ~10 files)
- Translation points: **7** locations where field names silently convert
- Root cause: **1** line of code

---

## 2. Scope of Analysis

### What Was Investigated

| Agent Role | Task # | Focus Area | Document |
|---|---|---|---|
| **deployment-analyst** | #1 | Deployment pipeline end-to-end trace, archive template lifecycle, code reference map | `01-deployment-and-archive-analysis.md` |
| **field-mapper** | #2 | Complete line-level inventory of all `type`/`agent_type` usage across 57 Python files, 76 agent files, 39 JSON templates, 71 test files | `02-type-field-usage-map.md` |
| **skill-analyst** | #3 | Three skill mapping systems, runtime skill flow, field name impact on skill matching | `03-skill-agent-mapping-analysis.md` |
| **devils-advocate** | #4 | Adversarial challenge of proposed changes, hardcoded filename risks, integration test gaps, naming convention conflicts | `04-devils-advocate-risks.md` |

### Prior Research

- **v2** (5 documents): Initial code-path tracing, enum relationships, impact quantification, first devil's advocate, holistic recommendation
- **v2.1** (5 documents): Deployment pipeline deep dive, three deployment generations, dead code/skill mapping, remote agent sources, corrections

### Methodology

Each v3 agent conducted independent investigation using grep, glob, and file reading across the full codebase. Findings were cross-referenced against v2/v2.1 claims, with corrections documented where prior analysis was inaccurate.

---

## 3. Consolidated Findings

### 3.1 Archive Template Status

**Source**: Task #1 (deployment-analyst)

The archive directory (`src/claude_mpm/agents/templates/archive/`) contains **39 JSON** agent definition files (corrected from 38 in v2).

| Aspect | Finding |
|---|---|
| Runtime consumers | **ZERO** — no production code in `src/claude_mpm/` reads from `templates/archive/` |
| Script consumers | **TWO** — `scripts/delegation_matrix_poc.py` (POC) and `scripts/migrate_json_to_markdown.py` (one-time migration) |
| Test consumers | **ZERO** |
| Path bug | Three code paths (SkillManager, SimpleAgentManager, NativeAgentConverter) scan `templates/` for `*.json` but all JSON files are in `archive/` subdirectory — they find **ZERO** files |
| Purpose | Manually maintained canonical reference for rich agent metadata (capabilities, interactions, memory_routing, skill mappings) |
| Field consistency | ALL 39 JSON templates use `"agent_type"` — no exceptions |
| Data quality bug | `javascript_engineer_agent.json` uses `"engineering"` instead of `"engineer"` |

**Verdict**: Removing the archive would have zero runtime impact but would destroy the only comprehensive agent metadata reference.

### 3.2 Field Name Usage Map (with 7 Translation Points)

**Source**: Task #2 (field-mapper)

#### Grand Totals

| Dimension | `"type"` | `"agent_type"` | Ratio |
|---|:---:|:---:|:---:|
| Python src locations (agent context) | ~42 | ~170+ | **1:4** |
| Deployed frontmatter files | 48 | 27 | 2:1 |
| JSON templates | 0 | 39 | 0:39 |
| Remote agents | 0 | 48 | 0:48 |
| Test files | ~10 | ~71 | **1:7** |
| Hook/event system | 0 | 80+ | **0:80+** |
| Event data contract | 0 | Yes (primary) | 0:1 |
| Serialization format | 0 | Yes (primary) | 0:1 |

Python code overwhelmingly uses `agent_type` (4:1). The `type` field only dominates in deployed frontmatter — an artifact of the single-line root cause.

#### The 7 Translation Points (T1-T7)

| # | File | Line(s) | Direction | Description |
|---|---|---|---|---|
| **T1** | `agent_template_builder.py` | 493 / 568 | `agent_type` -> `type:` | **ROOT CAUSE**: Reads `agent_type` from source, writes `type:` to deployed frontmatter |
| **T2** | `agent_discovery_service.py` | 320 | `agent_type:` -> `"type"` key | Reads `agent_type` from frontmatter, stores under `"type"` dict key |
| **T3** | `agent_registry.py` | 73, 105, 208, 321, 747, 801 | `.agent_type` -> `"type"` key | Compatibility layer: reads `.agent_type` from Enum 2, serializes as `"type"` (6 locations) |
| **T4** | `system_agent_config.py` | 513 | `.agent_type` -> `"type"` key | Config serialization |
| **T5** | `dynamic_skills_generator.py` | 110 | `"type"` -> `agent_type` var | Reverse translation |
| **T6** | `agent_wizard.py` | 753 | `agent_type` var -> `"type"` key | Interactive agent creation |
| **T7** | `event_handlers.py` | 420 / 442 | `subagent_type` -> `agent_type` | Claude Code API parameter to internal event field |

#### Third Variant: `subagent_type`

Claude Code's API uses `subagent_type` as the parameter name. This is translated to `agent_type` in T7. Six source files handle this. **Neither `type` nor `agent_type` is recognized by Claude Code itself — both are MPM-internal fields.**

### 3.3 Skill-to-Agent Mapping

**Source**: Task #3 (skill-analyst)

**Critical finding**: Changing deployed agent frontmatter from `type:` to `agent_type:` will **NOT break skill matching**.

| Skill System | Status | Uses `type`/`agent_type`? | Impact of Change |
|---|---|---|---|
| SkillManager (legacy) | Dead code (path bug) | Would read `agent_type` if path fixed | **None** |
| AgentSkillsInjector (new) | Unwired (never imported) | Uses `agent_id` only | **None** |
| SkillsService / SkillsRegistryHelper | Active but bypassed at runtime | Uses `agent_id` for lookup | **None** |
| Runtime skill flow | **Active** | Reads `skills:` field, NOT `type`/`agent_type` | **None** |
| SKILL.md files (189) | Active | Zero references to agent type | **None** |

The actual runtime skill chain is: source template `skills:` field -> AgentTemplateBuilder -> deployed markdown `skills:` field -> Claude Code reads `skills:` and loads matching `.claude/skills/` files. **All three internal mapping systems are bypassed.**

### 3.4 Critical Risks

**Source**: Task #4 (devils-advocate)

#### RISK: `-agent` Suffixed Files Are NOT Simple Duplicates

The v2/v2.1 analysis classified 12 `-agent` suffixed files as "Gen 3 duplicates" safe to remove. **This is dangerously incorrect.** At least **7 production code paths** hardcode these filenames:

| Code Path | File | `-agent` Names Referenced |
|---|---|---|
| Diagnostics | `agent_check.py:156-161` | `research-agent.md`, `qa-agent.md`, `documentation-agent.md` |
| Git sync fallback | `git_source_sync_service.py:759-771` | `research-agent.md`, `qa-agent.md`, `documentation-agent.md`, `web-qa-agent.md` |
| PM delegation matrix | `todo_task_tools.py:50-55` | `research-agent`, `qa-agent`, `documentation-agent`, `security-agent`, `ops-agent` |
| Agent recommendations | `agent_recommendation_service.py:12-13` | `-agent` names in docstring |
| Template processor | `template_processor.py:115-126` | Bidirectional `-agent` resolution |
| Agent name normalizer | `agent_name_normalizer.py` | Underscore variants for display/lookup |
| Memory router | `memory/router.py` | `-agent` suffix stripping logic |

**The PM delegation matrix explicitly instructs Claude to use `-agent` names and marks non-suffixed versions as WRONG.** Removing these files without updating all references breaks diagnostics, deployment fallbacks, and PM delegation.

#### RISK: No Integration Tests for Deployment Pipeline

No end-to-end test exists that verifies: (a) all expected agent files exist after deployment, (b) all hardcoded agent names resolve to actual files, (c) PM delegation matrix matches deployed agents, or (d) `claude-mpm doctor` passes after deployment.

#### RISK: Partial Deployment Creates Inconsistent State

If the builder change (Phase 3) is merged before the normalization layer (Phase 1) is verified complete, neither code path correctly reads all agents. **Phase ordering is critical.**

#### RISK: Phase 1 Normalization Must Be Permanent

The `preserve_user_agents` deployment flag (default: `True`) means user-customized agents may retain `type:` indefinitely. The fallback reading layer must remain **permanently**, not be removed after migration.

### 3.5 Critical Bug Discovery

**Source**: Task #2 (field-mapper), confirmed across v2 and v3

**File**: `services/agents/management/agent_management_service.py`
**Line**: 444

```python
type=AgentType(post.metadata.get("type", "core")),
```

`AgentType` (Enum 1 from `models/agent_definition.py`) has only 5 members: `CORE`, `PROJECT`, `CUSTOM`, `SYSTEM`, `SPECIALIZED`. Frontmatter values like `engineer`, `ops`, `qa`, `research`, `documentation` are NOT valid members. This line **throws `ValueError` for the vast majority of deployed agents**.

**Severity**: CRITICAL — affects the agent management CRUD path.

### 3.6 Enum Alignment Issues

**Source**: Task #2, Task #4, v2 analysis

Four separate classification systems with incompatible member sets:

| Enum | Location | Base Class | Members | Matches Frontmatter? |
|---|---|---|---|---|
| **Enum 1** | `models/agent_definition.py` | `str, Enum` | `CORE`, `PROJECT`, `CUSTOM`, `SYSTEM`, `SPECIALIZED` | **NO** |
| **Enum 2** | `core/unified_agent_registry.py` | `Enum` | `CORE`, `SPECIALIZED`, `USER_DEFINED`, `PROJECT`, `MEMORY_AWARE` | **NO** |
| **Enum 3** | `tests/eval/.../agent_response_parser.py` | `str, Enum` | `BASE`, `RESEARCH`, `ENGINEER`, `QA`, `OPS`, `DOCUMENTATION`, `PROMPT_ENGINEER`, `PM` | **YES** (only one!) |
| **AgentCategory** | `core/enums.py` | `StrEnum` | 17+ members (different naming: `ENGINEERING` vs `engineer`, `OPERATIONS` vs `ops`) | **Partial** |

Additionally, `agents_metadata.py` uses `"type": "core_agent"` / `"optimization_agent"` / `"system_agent"` — values matching none of the above.

---

## 4. Recommendations — Clear YES/NO

### 4.1 Should we remove the archive directory?

### **NO** (annotate instead)

| Factor | Assessment |
|---|---|
| Runtime impact of removal | Zero |
| Loss of reference data | Significant — only source of rich agent metadata |
| Script breakage | Two scripts affected |
| Cost of keeping | Negligible |

**Action**: Add a `README.md` to `templates/archive/` documenting its purpose as reference-only. Do NOT remove.

### 4.2 Should we standardize on `agent_type`?

### **YES**

| Factor | Assessment |
|---|---|
| Python code dominance | 4:1 favoring `agent_type` |
| Upstream sources | 100% `agent_type` (remote + JSON + migration) |
| Event/serialization contract | Uses `agent_type` exclusively |
| Future-proofing | `agent_type` is namespaced, less collision risk |
| Change footprint | ~42 `type` locations vs ~170+ if reversing |
| Root cause fix | 1 line change at `agent_template_builder.py:568` |

### 4.3 Should we clean up `-agent` suffixed file duplication?

### **NO — not in this effort**

| Factor | Assessment |
|---|---|
| Hardcoded references | 7+ production code paths |
| PM delegation | Explicitly uses `-agent` names |
| Integration tests | None exist to verify removal safety |
| Relationship to field naming | Orthogonal problem |

**Action**: Defer to a separate, dedicated effort with its own analysis, code audit, and migration plan.

### 4.4 Should we fix the enum alignment?

### **YES, but later** (out of scope for this effort)

| Factor | Assessment |
|---|---|
| Severity | Medium — 4 enums, all misaligned |
| Dependency | Benefits from field name standardization first |
| Scope | Large refactor affecting many files |
| v2 recommendation | Create consolidated `AgentRole` enum (still valid) |

**Action**: Track as follow-on effort. Phase 1 normalization provides stable foundation.

### 4.5 Should we fix the `agent_management_service.py` bug?

### **YES, immediately**

| Factor | Assessment |
|---|---|
| Severity | CRITICAL — crashes for most agents |
| Independence | Can fix before or concurrent with standardization |
| Fix complexity | Low — replace `AgentType(value)` with safe fallback |

---

## 5. Risk Matrix

| Risk | Likelihood | Impact | Combined Severity | Phase Affected | Mitigation |
|---|---|---|---|---|---|
| Removing `-agent` files breaks 7+ code paths | **CERTAIN** (if attempted) | **HIGH** | **CRITICAL** | All | Do NOT remove in this effort |
| No integration tests miss regressions | **HIGH** | **HIGH** | **CRITICAL** | All | Create verification tests in Phase 0 |
| `agent_management_service.py:444` crash | **CERTAIN** (already happening) | **MEDIUM** | **HIGH** | Phase 2 | Safe fallback enum construction |
| Phase 3 before Phase 1 = inconsistent state | **POSSIBLE** | **MEDIUM** | **MEDIUM** | Phase 1-3 | Strict phase ordering; CI gates |
| `preserve_user_agents` prevents 100% migration | **POSSIBLE** | **LOW** | **LOW-MEDIUM** | Phase 4 | Keep normalization fallback permanently |
| Underscore names in normalizer break lookup | **LIKELY** (if files removed) | **MEDIUM** | **MEDIUM** | N/A (out of scope) | Do NOT remove underscore files |
| Claude Code adds conflicting `type` field | **SPECULATIVE** | **MEDIUM** | **LOW** | Future | `agent_type` mitigates (namespaced) |
| Archive removal breaks POC scripts | **CERTAIN** (if attempted) | **LOW** | **LOW** | N/A (not removing) | Keep archive |
| `"engineering"` typo and value inconsistencies | **CERTAIN** (present) | **LOW** | **LOW** | Future | Value audit in separate effort |

---

## 6. Out of Scope

The following items were discovered during analysis but should **NOT** be addressed in this effort:

| # | Item | Why Deferred |
|---|---|---|
| 1 | **File naming convention cleanup** (kebab-case vs underscore vs `-agent` suffix) | 7+ hardcoded reference locations; requires its own analysis |
| 2 | **Enum consolidation** (create `AgentRole` / `AgentScope`) | Larger refactor; field name fix provides stable foundation |
| 3 | **AgentCategory cleanup** (17 members with different naming) | Superseded by eventual `AgentRole` enum |
| 4 | **SkillManager path bug** (scans wrong directory) | Dead code, not causing issues |
| 5 | **AgentSkillsInjector wiring** (never connected to pipeline) | Tech debt, not blocking |
| 6 | **Agent name normalizer overhaul** | Depends on file naming convention decision |
| 7 | **`agents_metadata.py` value vocabulary** (`core_agent`, etc.) | Separate classification system |
| 8 | **Three `AgentTier` enum consolidation** | Related but separate concern |
| 9 | **`subagent_type` -> `agent_type` translation** (T7) | Necessary bridge to Claude Code API; must remain |
| 10 | **Remote repository updates** (`bobmatnyc/claude-mpm-agents`) | Already uses `agent_type`; no changes needed |
| 11 | **`agent_type` VALUE standardization** (is `analysis` same as `research`?) | Semantic alignment needed but orthogonal to field naming |

---

## 7. The Three-Layer Problem

The analysis reveals three nested problems:

### Layer 1: Field Name (`type` vs `agent_type`) — THIS EFFORT

- **Problem**: Two names for the same field
- **Solution**: Standardize on `agent_type`
- **Difficulty**: Low — 1 root cause line, ~20-25 downstream changes, 48 frontmatter files
- **Status**: Ready for implementation

### Layer 2: File Naming (kebab-case vs underscore vs `-agent` suffix) — FUTURE

- **Problem**: Three naming conventions for the same agents
- **Solution**: Pick one convention, update all references
- **Difficulty**: Medium — 7+ files with hardcoded names, needs integration tests
- **Depends on**: Layer 1 complete

### Layer 3: Value Vocabulary (enum members vs frontmatter values) — FUTURE

- **Problem**: Four enum systems with incompatible member sets
- **Solution**: Design unified `AgentRole` classification
- **Difficulty**: High — architectural decision, many interfaces affected
- **Depends on**: Layers 1 and 2 complete

---

## Appendix A: Cross-Reference Matrix

| Finding | Task #1 | Task #2 | Task #3 | Task #4 |
|---------|:-------:|:-------:|:-------:|:-------:|
| Root cause at line 568 | Confirmed | Confirmed | — | — |
| `agent_type` dominates Python code 4:1 | — | Confirmed | — | — |
| 7 translation points (T1-T7) | — | Identified | — | — |
| Skill system unaffected | — | — | Confirmed | — |
| `-agent` files hardcoded in 7+ paths | — | — | — | **CRITICAL** |
| Archive has zero runtime consumers | Confirmed | — | — | Confirmed |
| No integration tests exist | — | — | — | **CRITICAL** |
| 4 enum systems misaligned | — | Documented | — | — |
| Dead skill mapping systems | Confirmed | — | Confirmed | — |
| `agent_management_service.py:444` crash | — | **CRITICAL** | — | — |
| Claude Code ignores `type`/`agent_type` | — | — | Confirmed | Confirmed |
| `preserve_user_agents` prevents full migration | — | — | — | Identified |
| `"engineering"` typo in JSON template | Confirmed | Confirmed | — | — |

## Appendix B: Corrections to v2/v2.1

| v2/v2.1 Claim | v3 Correction |
|---|---|
| "38 JSON files in archive" | **39** JSON files (verified count) |
| "-agent suffixed files are Gen 3 duplicates safe to remove" | **WRONG** — 7+ production code paths hardcode these names |
| "Phase 3.4: Remove Phase 1 compatibility layer" | **DO NOT** — keep normalization permanently due to `preserve_user_agents` |
| "Deduplicate 14+ agent file pairs in Phase 1" | **Defer** to separate effort — naming cleanup is orthogonal to field name fix |
| "Archive used by migration script only" | Also referenced by `scripts/delegation_matrix_poc.py` |
| "`SimpleAgentManager` not mentioned" | Added to analysis — third code path scanning templates/ for JSON |

## Appendix C: Documents Synthesized

### v3 Team Output (Primary Input)
1. `docs-local/agentType-enum/analysis-v3/01-deployment-and-archive-analysis.md` (Task #1)
2. `docs-local/agentType-enum/analysis-v3/02-type-field-usage-map.md` (Task #2)
3. `docs-local/agentType-enum/analysis-v3/03-skill-agent-mapping-analysis.md` (Task #3)
4. `docs-local/agentType-enum/analysis-v3/04-devils-advocate-risks.md` (Task #4)

### Previous Research (Background Context)
5. `docs-local/agentType-enum/analysis-v2/` (5 documents)
6. `docs-local/agentType-enum/analysis-v2.1/` (5 documents)
