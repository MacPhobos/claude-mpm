# Branch History Analysis: `agenttype-enums`

**Date**: 2026-03-06
**Analyst**: Branch Historian (Research Agent)
**Branch**: `agenttype-enums` (15 commits ahead of `main`)
**Purpose**: Comprehensive record for planning a fresh reimplementation

---

## 1. Research Evolution Timeline

The research went through 8+ versions over 5 days, with key pivot points where understanding fundamentally changed.

### Timeline

| Version | Date | Key Focus | Key Insight |
|---------|------|-----------|-------------|
| **v1 (problem-analysis)** | Mar 2 | Three incompatible `AgentType` enums | Identified 3 separate Python enums named `AgentType` with different members; 46/48 agents silently mapped to `CUSTOM` |
| **v2** | Mar 3 | Code paths for `type:` vs `agent_type:` | Mapped 5 code paths reading the field; identified enum values vs frontmatter values mismatch |
| **v2.1** | Mar 3 | Corrections to v2 | **PIVOT**: Discovered THREE deployment generations (not two); found SkillManager is dead code; identified 26 duplicate files |
| **v3** | Mar 3 | Deployment pipeline + archive analysis | Traced full pipeline; recommended archive removal |
| **v4** | Mar 3 | Cache system analysis | Deeper pipeline trace; confirmed cache structure |
| **v5** | Mar 4 | Devil's advocate on filename plan | **PIVOT**: Found 7 deployment paths (plan only covered 4); identified 5 filename collision pairs; discovered `agent_id` frontmatter mismatch problem |
| **v6** | Mar 4 | Empirical testing + unified analysis | **MAJOR PIVOT**: Empirical proof that Claude Code resolves `subagent_type` from `name:` field ONLY, not filename stems. PM delegation is safe under rename; internal MPM services are the real risk |
| **v7** | Mar 4 | Implementation plan based on v6 | 5-phase plan (pre-existing bugs, normalization, rename, code paths, verification) |
| **v7 Phase 5** | Mar 5 | Verification findings | Found 12 additional files with stale underscore references missed by phases 1-4 |
| **v8** | Mar 5 | Correction plan for remaining issues | Focused on PM prompt references using wrong format; 8 agents cached but not deployed; CORE_AGENTS list inconsistencies |

### Key Pivot Points

**Pivot 1 (v2.1)**: The system had THREE deployment generations, not two. This tripled the scope of file cleanup and revealed that duplicate files and dead code (SkillManager) existed.

**Pivot 2 (v5)**: The filename standardization plan was far more complex than originally scoped. The plan identified 4 code locations; devil's advocate found 7. Five filename collision pairs were discovered that would cause data loss during normalization.

**Pivot 3 (v6)**: The single most important discovery. Empirical testing proved `subagent_type` resolves exclusively from the `name:` frontmatter field. This:
- **Eliminated** the biggest feared risk (PM delegation breakage)
- **Revealed** the real risk surface (MPM internal services using filename stems)
- **Changed** the priority order of fixes (PM prompts are about cosmetic correctness, not functional routing)

**Pivot 4 (v8)**: After all filename/normalization work was done, discovered that PM_INSTRUCTIONS.md was referencing agents using filename stems (e.g., `local-ops`) instead of `name:` field values (e.g., `Local Ops`). Also found 8 agents existed in cache but weren't deployed.

### Findings Consistent Across All Versions

These conclusions remained stable from first discovery through all subsequent analysis:

1. The three AgentType enums are genuinely separate concepts that should not share a name
2. 87% of frontmatter `agent_type:` values don't match any Python enum
3. Multiple normalization systems produce conflicting canonical forms
4. The `name:` field is the only thing that matters for PM delegation (confirmed empirically in v6)
5. Hardcoded agent lists are fragmented across 5+ files with no single source of truth

---

## 2. Commit-by-Commit Analysis

### Implementation Phase Map

| Phase | Commits | Research Driver | Purpose |
|-------|---------|----------------|---------|
| **A: Initial standardization** | 5bdbaa57, e62212b9 | v2-v4 | `type:` -> `agent_type:` field rename + safety net tests |
| **B: Archive removal** | b0a7f9c7, bb9923cb | v3 | Remove 39 dead JSON templates |
| **C: Startup fix** | 0172d732 | Observation | Clarify "cached" -> "unused in cache" wording |
| **D: Naming standardization** | 1d6568ce, d7cbf33b, 7292de91, 4e070800, 37df5cb5 | v7 | Fix bugs, unify normalization, rename files, fix missed refs |
| **E: PM reference alignment** | e2c9e59c, 6ff9727c, 8164f1cf, f392f54e, 663bdaaf | v8 | Fix deploy command, create name registry, fix PM refs, fix hardcoded lists |

### Commit Detail Table

| # | Hash | Phase | Message | Files | Net Effect | Correcting Prior? |
|---|------|-------|---------|-------|------------|-------------------|
| 1 | 5bdbaa57 | A | Phases 0-2: safety tests + archive README + safe_parse | 4 (+725) | Added 13 integration tests; fixed `_safe_parse_agent_type()` fallback; added archive README | No (new) |
| 2 | e62212b9 | A | Phase 3: standardize `agent_type` field name | 19 (+115-47) | Created `read_agent_type()` utility; updated template builder to write `agent_type:`; updated 14 metadata entries | No (new) |
| 3 | b0a7f9c7 | B | Remove references to templates/archive | 4 (+75-125) | Updated delegation_matrix_poc.py to use .md agents; removed --archive flag from migration script | No (cleanup) |
| 4 | bb9923cb | B | Delete templates/archive directory | 41 (+81-11637) | Removed 39 JSON templates + archive README; updated tests to use mocks | No (cleanup) |
| 5 | 0172d732 | C | Clarify startup wording | 1 (+2-2) | "0 cached" -> "0 unused in cache" | No (UX fix) |
| 6 | 1d6568ce | D | Fix pre-existing naming bugs (v7 Phase 1) | 6 (+202-144) | Fixed `subagent_type` values in todo_task_tools, content_formatter, capability_generator; rewrote bump_agent_versions; deprecated templates/__init__.py | No (bug fixes) |
| 7 | d7cbf33b | D | Unify normalization to hyphen-canonical (v7 Phase 2) | 6 (+186-186) | Changed AgentNameNormalizer, ToolAccessControl, AgentSessionManager to produce hyphens; updated tests | No (new direction) |
| 8 | 7292de91 | D | Rename files + fix deployment paths (v7 Phase 3+4) | 14 (+113-56) | Renamed 14 agent files; updated agent_capabilities.yaml keys; fixed 8 deployment code paths | No (new) |
| 9 | 4e070800 | D | Phase 5 verification + fix remaining refs | 13 (+41-41) | **CORRECTION**: Found 12 files with stale underscore refs missed by phases 1-4 | YES - correcting #7/#8 |
| 10 | 37df5cb5 | D | Re-add "archive" as no-recurse dir | 1 (+1-1) | **CORRECTION**: Archive removal in commit #3 accidentally removed pytest norecursedirs | YES - correcting #3 |
| 11 | e2c9e59c | E | Fix `agents deploy` command (v8 Phase 1) | 3 (+76-40) | **BUG DISCOVERY**: `agents deploy` called non-existent `sync_repository()` — never actually deployed anything | Bug fix |
| 12 | 6ff9727c | E | Add agent name registry (v8 Phase 2) | 2 (+205) | Created `agent_name_registry.py` with 62-entry AGENT_NAME_MAP + extraction script | No (new) |
| 13 | 8164f1cf | E | Normalize agent IDs in configure (v8 Phase 2.5) | 4 (+160-17) | Fixed configure showing only 21/48 agents as "Installed" due to ID format mismatch | Bug fix |
| 14 | f392f54e | E | Fix PM references (v8 Phase 3) | 2 (+69-69) | Replaced 47 filename-stem references in PM_INSTRUCTIONS.md + WORKFLOW.md with `name:` field values | No (new) |
| 15 | 663bdaaf | E | Align hardcoded agent lists (v8 Phase 4) | 6 (+72-48) | Fixed git_source_sync fallback to use repo paths; fixed enums.py VERSION_CONTROL; SKIPPED toolchain_detector changes (devil's advocate proved plan was wrong) | Partially corrects plan |

### Correction Chain Analysis

The incremental nature of the work led to a correction-upon-correction pattern:

```
Commit #3 (remove archive refs)
  -> Commit #10 (re-add norecursedirs accidentally removed)

Commits #7-#8 (rename + fix deployment)
  -> Commit #9 (found 12 MORE files missed by the rename)

v8 plan Phase 4 (fix toolchain_detector)
  -> Commit #15 (skipped that fix — devil's advocate proved it would BREAK things)
```

---

## 3. Classification Matrix

### KEEP: Clearly correct, reimplement the same way

| Change | Commit(s) | Rationale |
|--------|-----------|-----------|
| `_safe_parse_agent_type()` fallback | 5bdbaa57 | Prevents ValueError crash for 87% of agents. Critical safety net. |
| `read_agent_type()` utility with dual fallback | e62212b9 | Reads both `agent_type:` and `type:` frontmatter fields. Permanent compatibility. |
| Archive directory deletion | bb9923cb | 39 dead JSON files consuming space. Confirmed no runtime dependencies. |
| Agent name registry (`agent_name_registry.py`) | 6ff9727c | Single source of truth for stem-to-name mapping. Essential for PM delegation correctness. |
| PM_INSTRUCTIONS.md using `name:` field values | f392f54e | Empirically proven: `subagent_type` resolves against `name:` only. |
| Fix `agents deploy` sync method call | e2c9e59c | Was calling non-existent method — deploy command was completely broken. |
| Fix `ensure_agent_id_in_frontmatter` with `update_existing` param | 7292de91 | Fixes stale `agent_id` values not being updated during deployment. |
| `git_source_sync_service.py` fallback using repo paths | 663bdaaf | Old fallback used flat filenames that didn't match nested repo structure. |

### REDO: Right idea, implementation needs adjustment

| Change | Commit(s) | Issue | Recommendation |
|--------|-----------|-------|----------------|
| Hyphen-canonical normalization | d7cbf33b | Correct direction, but didn't update ALL locations (12 files missed, caught in commit #9). | Do in one pass with comprehensive grep verification BEFORE committing. |
| File rename (14 underscore files) | 7292de91 | Correct, but 12 downstream references were missed. | Use automated verification: grep for ALL underscore patterns after rename. |
| `CANONICAL_NAMES` dict update | d7cbf33b | Updated to hyphens but values still diverge from `AGENT_NAME_MAP` for 10 agents (per v2 consolidated). | Align CANONICAL_NAMES values with actual `name:` fields, not "prettier" versions. |
| Integration tests for agent field consistency | 5bdbaa57 | Good idea but tests were modified multiple times as understanding evolved. | Write tests AFTER implementation is stable, not before. |
| `configure` installed detection normalization | 8164f1cf | Fixed the symptom (21/48 shown) but added yet another normalization function. | Use a single normalization utility shared across all sites. |
| `toolchain_detector.py` CORE_AGENTS handling | 663bdaaf | Correctly SKIPPED the v8 plan's proposed fix (devil's advocate proved it wrong), but the list still has issues. | Needs deeper analysis of what format `recommended` set expects downstream. |

### DROP: Addressing non-issues or introduced problems

| Change | Commit(s) | Why Drop |
|--------|-----------|----------|
| Archive README addition | 5bdbaa57 | Created a README for archive, then deleted the entire archive 2 commits later. Wasted effort. |
| `templates/__init__.py` deprecation warnings | 1d6568ce | Added deprecation to dead code but didn't remove it. v8 Phase 5 (removal) was never implemented. Should just delete. |
| `bump_agent_versions.py` rewrite | 1d6568ce | Rewrote script to use dynamic discovery, but the script itself may be entirely dead code (no JSON templates exist). Should investigate if script is used at all. |

### NEW: Needed but not yet implemented

| Need | Source | Priority |
|------|--------|----------|
| **Unified AgentType enum** covering all 15 frontmatter values | v2 consolidated Section 2.2 | CRITICAL — 87% of agents have uncovered types |
| **Reconcile CANONICAL_NAMES with AGENT_NAME_MAP** | v2 consolidated Section 2.1 | CRITICAL — 10 agents have divergent names causing latent bugs |
| **Fix `system_context.py`** incorrect lowercase guidance | v2 consolidated Section 2.6 | HIGH — tells PM that lowercase format works (it doesn't for multi-word agents) |
| **Fix CLAUDE_MPM_OUTPUT_STYLE.md** broken refs | v2 consolidated Section 2.3 | HIGH — 2 broken delegation references |
| **Consolidate 5+ normalization functions** | v2 consolidated Section 2.5 | MEDIUM — edge cases diverge across 6 implementations |
| **Consolidate 5 CORE_AGENTS lists** | v2 consolidated Section 2.4 | HIGH — 12 agents across 5 lists, no list has all of them |
| **Fix `SingleAgentDeployer`** dual deployer path | v2 consolidated Section 2.8 | MEDIUM — doesn't call `deploy_agent_file()`, skips normalization |
| **Fix `agent_id` mismatches** (54% of agents) | v2 consolidated Section 2.7 | MEDIUM — filename stems don't match frontmatter `agent_id` |
| **Remove dead `templates/__init__.py`** | v8 Phase 5 (never done) | LOW — dead code referencing non-existent files |
| **Fix upstream `name:` field outliers** (6 agents) | v2 consolidated Section 3.1 | HIGH but out of scope — requires upstream repo changes |
| **CI tests for drift detection** | v2 consolidated L3 | MEDIUM — prevent `CANONICAL_NAMES` vs `AGENT_NAME_MAP` divergence |

---

## 4. Key Lessons for Fresh Implementation

### Lesson 1: Verify scope BEFORE implementing
The v7 plan said "4 code locations need fixing." Reality was 7+ deployment paths and 12+ files with stale references. Every phase discovered more scope. **Fix**: Run comprehensive grep patterns FIRST, get the FULL list, then implement.

### Lesson 2: The `name:` field is sacred
Empirically proven in v6: Claude Code resolves `subagent_type` exclusively from YAML frontmatter `name:` fields. Changing a `name:` value breaks PM delegation with ZERO fallback. All PM-facing references must use exact `name:` values.

### Lesson 3: Two normalization systems are worse than none
`AgentNameNormalizer.CANONICAL_NAMES` and `agent_name_registry.AGENT_NAME_MAP` produce different output for 10 agents. Adding more normalization layers (e.g., `normalize_agent_id_for_comparison()` in commit #13) compounds the problem. **Fix**: ONE canonical mapping, used everywhere.

### Lesson 4: Don't add to dead code — remove it
Commit #1 added a README to the archive directory. Commit #4 deleted the archive. Commit #6 added deprecation warnings to dead template code. v8 planned to remove it but never did. **Fix**: Delete dead code immediately. Don't annotate it.

### Lesson 5: Test AFTER the dust settles
Integration tests were written in commit #1, then modified in commits #6, #8, #9, and #15 as understanding evolved. Tests written too early encode premature assumptions. **Fix**: Write tests after the design is stable, or use test-last for exploratory work.

### Lesson 6: Devil's advocate catches real bugs
Three times the devil's advocate analysis prevented or caught errors:
- v5: Found 5 filename collision pairs the plan ignored
- v7 Phase 5: Found 12 stale references missed by phases 1-4
- v8 Phase 4: Proved the `toolchain_detector` fix would BREAK auto-configure

### Lesson 7: The `agents deploy` command was broken the whole time
Commit #11 revealed that `agents deploy` called a non-existent method (`sync_repository()`) and silently failed. The 40 agents in `.claude/agents/` were deployed through OTHER code paths. This means all verification steps that relied on "run deploy and check" were testing nothing.

### Lesson 8: Upstream name: values are messy and out of scope
Six agents have non-standard `name:` values (`aws_ops_agent`, `ticketing_agent`, `mpm_agent_manager`, `mpm_skills_manager`, `nestjs-engineer`, `real-user`). These come from the external Git repo. PM must use these exact values. Any "normalization" that produces "prettier" versions (like `CANONICAL_NAMES` does) creates bugs.

---

## 5. Risks of Reimplementing vs Cherry-Picking

### Option A: Fresh Implementation on New Branch

**Pros:**
- Clean commit history without correction-upon-correction chains
- Can incorporate ALL lessons learned into a comprehensive plan
- Can batch-verify all changes before any commits
- Can address the NEW items (Section 3) that the current branch never reached
- No risk of carrying forward subtle bugs from partial implementations

**Cons:**
- Risk of re-introducing bugs that were already found and fixed
- Time investment to redo work that's already correct (KEEP items)
- Must carefully port the agent_name_registry and PM_INSTRUCTIONS fixes

**Risk level: MEDIUM** — The main risk is forgetting a hard-won lesson. This document mitigates that.

### Option B: Cherry-Pick from Current Branch

**Pros:**
- Preserves working code without rewriting
- Faster for the KEEP items
- Git blame history shows original reasoning

**Cons:**
- Some commits contain both good changes and later-corrected changes (e.g., commit #7 and #8 needed commit #9 to fix misses)
- Cherry-picking correction chains is fragile (commit #9 patches files changed in #7 and #8)
- Cannot easily split commits that mix KEEP and REDO changes
- Carries forward the "correction layer" approach rather than a clean implementation

**Risk level: HIGH** — Cherry-picking interdependent commits is error-prone.

### Option C: Squash-and-Rebase Selected Ranges

**Pros:**
- Can collapse correction chains (e.g., commits #7-#10 into one clean commit)
- Preserves the actual code changes
- Cleaner history than full cherry-pick

**Cons:**
- Merge conflicts likely when squashing across 15 commits
- Still carries forward code that should be REDO'd, not just replayed
- Hard to incorporate NEW items into squashed ranges

**Risk level: MEDIUM-HIGH**

### Recommendation

**Option A (Fresh Implementation)** with this document as the specification. The KEEP items are well-documented and straightforward to reimplement. The REDO items need different approaches. The NEW items are critical and can only be addressed with a fresh design. The correction chains on this branch make cherry-picking unreliable.

**Critical items to port from this branch:**
1. `agent_name_registry.py` (commit #12) — copy as-is or regenerate from extract script
2. PM_INSTRUCTIONS.md changes (commit #14) — the 47 replacements are correct
3. `agents deploy` fix (commit #11) — simple method name fix
4. `ensure_agent_id_in_frontmatter` `update_existing` parameter (commit #8)
5. The 12 stale-reference fixes from commit #9 (but apply as part of comprehensive rename)

---

## Appendix A: Research Document Inventory

| Directory | Docs | Key Content |
|-----------|------|-------------|
| `agentType-enum/` | problem-analysis.md, baseline-snapshot.md | Original problem: 3 enums, 46/48 agents mapped to CUSTOM |
| `agentType-enum/analysis-v2/` | 5 docs | Code path mapping, enum relationships, standardization impact |
| `agentType-enum/analysis-v2.1/` | 5 docs | Corrections: 3 generations, dead SkillManager, 26 duplicates |
| `agentType-enum/analysis-v3/` | 6 docs | Deployment + archive analysis, phased plan |
| `agentType-enum/analysis-v4/` | 6 docs | Cache system deep-dive, refined skill mapping |
| `agentType-enum/analysis-v5/` | 3 docs | Devil's advocate: 7 paths not 4, collision pairs, agent_id mismatch |
| `agentType-enum/analysis-v6/` | 9 docs | **Empirical proof**: name: field is exclusive for subagent_type |
| `agentType-enum/analysis-plan-v7/` | 2 docs | Implementation plan + Phase 5 verification (12 more files found) |
| `agentType-enum/correction-plan-v8/` | 2 docs | PM reference alignment, missing agents, CORE_AGENTS |
| `agentType-enum-v2/01-analysis/` | 5 docs | Team analysis: what's resolved, what's still broken, prioritized actions |

## Appendix B: Files Changed on Branch (Aggregate)

Total unique source files modified: ~55
Total test files modified: ~15
Total agent/config files modified: ~60 (including 39 deleted archive + 14 renamed)

### Most-Modified Source Files (touched in 3+ commits)
- `agents_metadata.py` — 3 commits
- `agent_management_service.py` — 3 commits
- `git_source_sync_service.py` — 3 commits
- `agent_name_normalizer.py` — 2 commits
- `agent_registry.py` — 2 commits
- `PM_INSTRUCTIONS.md` — 2 commits (Phase 5 + v8 Phase 3)
- `WORKFLOW.md` — 3 commits

### New Files Created
- `src/claude_mpm/core/agent_name_registry.py`
- `src/claude_mpm/utils/frontmatter_utils.py`
- `src/claude_mpm/utils/agent_filters.py`
- `scripts/extract_agent_names.sh`
- `tests/unit/utils/test_frontmatter_utils.py`
- Various test files
