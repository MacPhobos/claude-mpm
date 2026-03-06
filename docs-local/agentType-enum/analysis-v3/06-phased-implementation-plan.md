# Phased Implementation Plan: `type` -> `agent_type` Standardization

**Date**: 2026-03-03
**Author**: Synthesis Agent (Claude Opus 4.6), Team agenttype-enum-v3
**Branch**: `agenttype-enums`
**Task**: Task #5 — Phased implementation plan
**Companion document**: `05-holistic-report.md` (consolidated findings and recommendations)

---

## Overview

This plan implements the field name standardization from `type:` to `agent_type:` across the claude-mpm codebase. It is scoped to **Layer 1 only** (field naming), explicitly excluding Layer 2 (file naming convention cleanup) and Layer 3 (enum consolidation / value vocabulary).

### Phase Dependency Graph

```
Phase 0: Pre-work (Integration Tests, Backup, Document Current State)
    │
    ├──→ Phase 1: Archive Cleanup (INDEPENDENT — can run in parallel with Phase 2)
    │
    └──→ Phase 2: Fix Critical Bug (agent_management_service.py:444)
              │
              v
         Phase 3: Standardize Field Name (Root Cause + All 7 Translation Points + Normalization Layer)
              │
              v
         Phase 4: Deployed Frontmatter Migration (48 Agent Files)
              │
              v
         Phase 5: Full Verification and Regression Testing
```

**Critical ordering constraint**: Phase 3 (builder change + normalization) MUST be complete and verified before Phase 4 (frontmatter migration). Phase 2 (bug fix) MUST be complete before Phase 3. Phase 0 (tests) MUST be complete before any production changes.

---

## What NOT To Do

These constraints are derived from the devil's advocate analysis (Task #4) and apply across **ALL phases**:

| # | Prohibition | Rationale |
|---|---|---|
| 1 | **DO NOT remove `-agent` suffixed files** (`research-agent.md`, `qa-agent.md`, etc.) | 7+ production code paths hardcode these names. PM delegation matrix explicitly uses them. |
| 2 | **DO NOT remove underscore-named files** (`golang_engineer.md`, etc.) | Referenced by `agent_name_normalizer.py` for display/lookup. |
| 3 | **DO NOT conflate file naming with field naming** | This effort changes `type:` -> `agent_type:` in frontmatter content only. It does NOT rename any files. |
| 4 | **DO NOT remove the normalization fallback** after migration | The `preserve_user_agents` flag means some agents may retain `type:` indefinitely. Keep `get("agent_type", get("type", default))` **permanently**. |
| 5 | **DO NOT remove the archive directory** | Zero runtime impact from keeping it; contains valuable reference data. Add a README instead. |
| 6 | **DO NOT attempt enum consolidation** | The four misaligned enum systems (Enum 1, 2, 3, AgentCategory) are a separate, larger refactor for a future effort. |

### Clear Separation: File Naming Convention Cleanup is OUT OF SCOPE

The following are **explicitly excluded** from this effort and must be addressed separately:

- Removing or consolidating duplicate agent files (kebab-case + underscore + `-agent` suffix)
- Updating hardcoded agent filenames in `agent_check.py`, `git_source_sync_service.py`, `todo_task_tools.py`
- Updating `agent_name_normalizer.py` display/lookup mappings
- Deciding the canonical file naming convention (kebab-case vs underscore vs `-agent`)

---

## Phase 0: Pre-work — Integration Tests, Backup, Document Current State

### Objective
Establish a safety net before any production code changes. Create integration tests that verify the current state and will catch regressions in later phases.

### Specific Files to Modify

#### 0.1 Create Agent Deployment Verification Test

**New file**: `tests/integration/agents/test_agent_field_consistency.py`

This test must verify:
1. All hardcoded agent filenames across the codebase resolve to actual files in `.claude/agents/`
2. Every deployed agent has either `type:` or `agent_type:` in its frontmatter
3. The PM delegation matrix agent names (from `todo_task_tools.py`) match deployed file names
4. `agent_management_service.py` can load all deployed agents without `ValueError`

**Hardcoded agent names to verify** (from Task #4 devil's advocate):

| Source File | Line(s) | Agent Names |
|---|---|---|
| `agent_check.py` | 156-161 | `research-agent.md`, `engineer.md`, `qa-agent.md`, `documentation-agent.md` |
| `git_source_sync_service.py` | 759-771 | `research-agent.md`, `engineer.md`, `qa-agent.md`, `documentation-agent.md`, `web-qa-agent.md`, `security.md`, `ops.md`, `ticketing.md`, `product_owner.md`, `version_control.md`, `project_organizer.md` |
| `todo_task_tools.py` | 50-55 | `research-agent`, `qa-agent`, `documentation-agent`, `security-agent`, `ops-agent` |

#### 0.2 Document Current State Baseline

**New file**: `docs-local/agentType-enum/baseline-snapshot.md`

Capture:
- Count of files using `type:` vs `agent_type:` in frontmatter (expected: 48 vs 27)
- Complete list of deployed agent files with their field name
- Current `agent_management_service.py:444` crash behavior (document the bug)
- Snapshot of frontmatter fields: `grep -r "^type:\|^agent_type:" .claude/agents/*.md`

#### 0.3 Create Git Branch Strategy

```
agenttype-enums (current branch)
├── phase-0-tests        (merge first — tests only)
├── phase-1-archive      (independent of phases 2-5)
├── phase-2-bugfix       (after phase-0)
├── phase-3-standardize  (after phase-2 verified)
├── phase-4-frontmatter  (after phase-3 verified)
└── phase-5-verify       (after phase-4)
```

### Expected Behavior Changes
None — Phase 0 is observation and test creation only.

### Rollback Strategy
Delete test files and baseline document. No production changes to revert.

### Testing Criteria (must pass before proceeding to Phase 1/2)
- [ ] Verification test passes against current codebase state (proves the test itself is correct)
- [ ] Baseline document created with complete current-state snapshot
- [ ] Branch strategy documented

### Estimated Effort: **S** (Small — 2-4 hours)

---

## Phase 1: Archive Cleanup

### Objective
Clean up the archive directory's status without removing it. Document its purpose and fix the only data quality issue.

**Note**: This phase is INDEPENDENT of Phases 2-5 and can run in parallel.

### Specific Files to Modify

| File | Change | Line(s) |
|---|---|---|
| `src/claude_mpm/agents/templates/archive/README.md` | **CREATE** — Document archive as reference-only, not runtime data source | N/A (new file) |
| `src/claude_mpm/agents/templates/archive/javascript_engineer_agent.json` | Fix typo: `"engineering"` -> `"engineer"` | Line containing `"agent_type"` value |

#### README.md Content

```markdown
# Agent Templates Archive (Reference Only)

This directory contains 39 JSON agent definition files preserved as a
canonical reference for rich agent metadata. These files are NOT read
by any production code at runtime.

## Purpose
- Reference for agent capabilities, interactions, memory_routing, and skill mappings
- Source material for the delegation_matrix_poc.py script
- Historical record of the original JSON template schema

## NOT Used By
- AgentTemplateBuilder (reads from git cache, not archive)
- SkillManager (path bug: scans templates/*.json, not templates/archive/*.json)
- Any runtime production code path

## Field Convention
All 39 JSON files use "agent_type" as the field name (not "type").
```

### Expected Behavior Changes
- No runtime behavior change
- Archive purpose documented for future developers
- `javascript_engineer_agent.json` typo corrected

### Rollback Strategy
```bash
git revert <commit>  # Delete README.md and revert JSON typo fix
```

### Testing Criteria
- [ ] No test regressions
- [ ] `README.md` exists in archive directory
- [ ] `grep -r '"engineering"' src/claude_mpm/agents/templates/archive/` returns 0 results
- [ ] `grep -r '"engineer"' src/claude_mpm/agents/templates/archive/javascript_engineer_agent.json` returns 1 result

### Estimated Effort: **S** (Small — 30 minutes)

---

## Phase 2: Fix Critical Bug — `agent_management_service.py:444`

### Objective
Fix the `ValueError` crash that occurs when `AgentType(post.metadata.get("type", "core"))` encounters frontmatter values like `engineer`, `ops`, `qa` — which are not valid Enum 1 members.

### Specific Files to Modify

| File | Change | Line(s) |
|---|---|---|
| `src/claude_mpm/services/agents/management/agent_management_service.py` | Replace unsafe `AgentType()` construction with safe fallback | 444 |
| `src/claude_mpm/services/agents/management/agent_management_service.py` | Review and update consistency at other `AgentType` usage | 318, 625, 723 |

#### Line 444 — Before:
```python
type=AgentType(post.metadata.get("type", "core")),
```

#### Line 444 — After:
```python
type=_safe_parse_agent_type(post.metadata.get("type", post.metadata.get("agent_type", "core"))),
```

#### Add helper method to the class:
```python
@staticmethod
def _safe_parse_agent_type(value: str) -> AgentType:
    """Safely parse agent type, falling back to CUSTOM for unknown values."""
    try:
        return AgentType(value)
    except ValueError:
        return AgentType.CUSTOM
```

**Notes**:
- This also adds forward-compatible normalization (reads both `type` and `agent_type`)
- The fallback to `AgentType.CUSTOM` is the correct behavior — an agent with `type: engineer` is not "core", "project", "system", or "specialized", so `CUSTOM` is the most accurate Enum 1 classification

### Expected Behavior Changes
- Agents with frontmatter values like `engineer`, `ops`, `qa` will **NO LONGER crash** with `ValueError`
- Instead, they are classified as `AgentType.CUSTOM`
- This is a behavioral **improvement** — previously these agents were inaccessible through the management service

### Rollback Strategy
```bash
git revert <commit>  # Restores original line 444 + removes helper
```
Low-risk rollback because the current code is already broken for most agents.

### Testing Criteria (must pass before proceeding to Phase 3)
- [ ] New test: `test_safe_parse_agent_type()` — verify no `ValueError` for all frontmatter values: `engineer`, `ops`, `qa`, `research`, `documentation`, `security`, `product`, `specialized`, `system`, `analysis`, `refactoring`, `content`, `imagemagick`, `memory_manager`, `claude-mpm`
- [ ] New test: `test_agent_management_service_loads_all_agents()` — verify management service can load every deployed agent
- [ ] Existing tests pass
- [ ] Manual verification: `agent_management_service` processes agents with `type: engineer` without crash

### Estimated Effort: **S** (Small — 1-2 hours)

---

## Phase 3: Standardize Field Name — Root Cause + Translation Points + Normalization

### Objective
Fix the root cause (T1), add a permanent normalization layer, and update all downstream readers/writers to use `agent_type` consistently. After this phase, all code reads `agent_type` (with `type` fallback) and all new deployments write `agent_type:`.

### Specific Files to Modify (with line references)

#### 3.1 Create Normalization Utility

**New file**: `src/claude_mpm/utils/frontmatter_utils.py`

```python
"""Utility for reading agent type field from frontmatter/dicts.

Both 'agent_type' and 'type' may be present in agent frontmatter.
This module provides a single function to read the correct field,
preferring 'agent_type' and falling back to 'type'.

PERMANENT: This normalization must remain even after migration,
as a safety net for user-customized agents (preserve_user_agents flag).
"""

def read_agent_type(data: dict, default: str = "general") -> str:
    """Read agent type from dict, checking agent_type first, then type.

    Args:
        data: Frontmatter dict or agent data dict
        default: Fallback value if neither field exists

    Returns:
        The agent type string value
    """
    return data.get("agent_type", data.get("type", default))
```

#### 3.2 Fix Root Cause (T1)

| File | Line(s) | Before | After |
|---|---|---|---|
| `agent_template_builder.py` | 544 | `# type: agent type for categorization...` | `# agent_type: agent type for categorization...` |
| `agent_template_builder.py` | 567-568 | `frontmatter_lines.append(f"type: {agent_type}")` | `frontmatter_lines.append(f"agent_type: {agent_type}")` |

#### 3.3 Update Translation Points T2-T6

| T# | File | Line(s) | Current Output Key | New Output Key |
|---|---|---|---|---|
| **T2** | `agent_discovery_service.py` | 320 | `"type": frontmatter.get("agent_type", ...)` | `"agent_type": read_agent_type(frontmatter, ...)` |
| **T3** | `agent_registry.py` | 73, 105, 208, 321, 747, 801 | `"type": unified_metadata.agent_type.value` | `"agent_type": unified_metadata.agent_type.value` (all 6 locations) |
| **T4** | `system_agent_config.py` | 513 | `"type": agent.agent_type` | `"agent_type": agent.agent_type` |
| **T5** | `dynamic_skills_generator.py` | 110 | `agent_info.get("type", "general-purpose")` | `read_agent_type(agent_info, "general-purpose")` |
| **T6** | `agent_wizard.py` | 753 | `"type": agent_type` | `"agent_type": agent_type` |

**Note on T7**: `subagent_type` -> `agent_type` translation in `event_handlers.py` is **correct as-is** and should NOT be changed. It bridges Claude Code's API parameter to our internal field name.

#### 3.4 Update Remaining `"type"` Readers (Agent Context)

| File | Line(s) | Current Code | New Code |
|---|---|---|---|
| `agent_management_service.py` | 153 | `key in ["type", ...]` | `key in ["type", "agent_type", ...]` |
| `agent_management_service.py` | 318 | `"type": agent_def.metadata.type.value` | `"agent_type": agent_def.metadata.type.value` |
| `agent_management_service.py` | 625 | `"type": definition.metadata.type.value` | `"agent_type": definition.metadata.type.value` |
| `agent_management_service.py` | 723 | `"Agent Type": ...type.value` | Update display label |
| `agent_validator.py` | 329 | `"type": "agent"` | `"agent_type": "agent"` |
| `agent_validator.py` | 362-363 | `startswith("type:")` | Check for both `"type:"` and `"agent_type:"` |
| `deployment_wrapper.py` | 111 | `agent.get("type", "agent")` | `read_agent_type(agent, "agent")` |
| `deployed_agent_discovery.py` | 109 | `agent.get("type", ...)` | `read_agent_type(agent, ...)` |
| `deployed_agent_discovery.py` | 133 | `getattr(agent, "type", None)` | `getattr(agent, "agent_type", getattr(agent, "type", None))` |
| `deployed_agent_discovery.py` | 193 | Mixed reads | Use `read_agent_type()` |
| `agent_listing_service.py` | 214, 250, 296 | `agent_data.get("type", "agent")` | `read_agent_type(agent_data, "agent")` |
| `agent_listing_service.py` | 372 | `getattr(agent, "type", "agent")` | `getattr(agent, "agent_type", getattr(agent, "type", "agent"))` |
| `agent_lifecycle_manager.py` | 310 | `"type": agent_metadata.type` | `"agent_type": agent_metadata.type` |
| `agents_metadata.py` | 14+ (15 entries) | `"type": "core_agent"` | `"agent_type": "core_agent"` (all 15 entries) |
| `agent_registry.py` | 239 | `metadata["type"]` | `metadata.get("agent_type", metadata.get("type", "unknown"))` |
| `log_manager.py` | 553 | `f"type: {data.get('type', 'unknown')}"` | `f"agent_type: {read_agent_type(data, 'unknown')}"` |

### Expected Behavior Changes
- **New deployments**: Write `agent_type:` instead of `type:` in frontmatter
- **Existing agents**: Still readable via normalization fallback (reads `type:` if `agent_type:` missing)
- **Agent registry**: Dict key changes from `"type"` to `"agent_type"` in serialized output
- **CLI listing**: Key changes from `"type"` to `"agent_type"` in output dicts
- **No event/hook changes**: These already use `agent_type` — confirmed safe by Task #2
- **No skill system changes**: Confirmed safe by Task #3

### Rollback Strategy
```bash
git revert <commit>  # Restores all files to pre-Phase-3 state
```
The normalization utility ensures both old and new field names work, so **partial rollback within Phase 3 is also safe** — any file can be reverted independently.

### Testing Criteria (must pass before proceeding to Phase 4)
- [ ] All existing tests pass (with import/key updates where needed)
- [ ] New test: `test_read_agent_type()` covers: `agent_type` only, `type` only, both present (prefers `agent_type`), neither present (returns default)
- [ ] New test: `test_template_builder_writes_agent_type()` — verify new deployments use `agent_type:` in frontmatter
- [ ] Manual: Deploy one agent, verify frontmatter contains `agent_type:` (not `type:`)
- [ ] Grep verification: No remaining `get("type"` in agent-context code (except normalization fallback and validator that checks for both)
- [ ] `claude-mpm list agents` shows correct types for all agents
- [ ] Dashboard loads and displays all agents correctly

### Estimated Effort: **M** (Medium — 4-6 hours)

---

## Phase 4: Deployed Frontmatter Migration — 48 Agent Files

### Objective
Bulk-update all 48 deployed Gen 1 agent files from `type:` to `agent_type:` in their frontmatter. The 27 files already using `agent_type:` (Gen 2 + Gen 3) need no changes.

### Specific Files to Modify

All 48 files listed in Task #2, Section 2.1. The change is mechanical — in each file, line 4 (within frontmatter):

```
BEFORE:
type: engineer

AFTER:
agent_type: engineer
```

#### Migration Script

```bash
#!/usr/bin/env bash
# Migrate type: to agent_type: in deployed agent frontmatter
# Only changes lines within frontmatter (between --- markers)
# Does NOT change lines in the body of the file

for f in .claude/agents/*.md; do
    awk '
        /^---$/ { fm_count++; print; next }
        fm_count == 1 && /^type: / { sub(/^type: /, "agent_type: "); print; next }
        { print }
    ' "$f" > "${f}.tmp" && mv "${f}.tmp" "$f"
done
```

#### Complete File List (48 files to change)

```
agentic-coder-optimizer.md    imagemagick.md                refactoring-engineer.md
api-qa.md                     java-engineer.md              research.md
aws-ops.md                    javascript-engineer.md        ruby-engineer.md
clerk-ops.md                  local-ops.md                  rust-engineer.md
code-analyzer.md              memory-manager-agent.md       security.md
content-agent.md              mpm-agent-manager.md          svelte-engineer.md
dart-engineer.md              mpm-skills-manager.md         tauri-engineer.md
data-engineer.md              nestjs-engineer.md            ticketing.md
data-scientist.md             nextjs-engineer.md            tmux-agent.md
digitalocean-ops.md           ops.md                        typescript-engineer.md
documentation.md              php-engineer.md               vercel-ops.md
engineer.md                   phoenix-engineer.md           version-control.md
gcp-ops.md                    product-owner.md              visual-basic-engineer.md
golang-engineer.md            project-organizer.md          web-qa.md
                              prompt-engineer.md            web-ui.md
                              python-engineer.md
                              qa.md
                              react-engineer.md
                              real-user.md
```

#### Also Update Body Schema References

| File | Line | Current | New |
|---|---|---|---|
| `.claude/agents/mpm-agent-manager.md` | 1218 | `type: engineer\|ops\|research\|qa\|security\|docs` | `agent_type: engineer\|ops\|research\|qa\|security\|docs` |

**Note**: Lines 259 and 1569 of `mpm-agent-manager.md` already reference `agent_type:` and need no change.

### Expected Behavior Changes
- All deployed agents now consistently use `agent_type:` field
- The normalization fallback from Phase 3 means this is transparent to all readers
- `grep "^type:" .claude/agents/*.md` returns 0 results (frontmatter context)

### Rollback Strategy
```bash
# Reverse the migration (mechanical reversal)
for f in .claude/agents/*.md; do
    awk '
        /^---$/ { fm_count++; print; next }
        fm_count == 1 && /^agent_type: / { sub(/^agent_type: /, "type: "); print; next }
        { print }
    ' "$f" > "${f}.tmp" && mv "${f}.tmp" "$f"
done
```

Or simply: `git checkout -- .claude/agents/` (if no other `.claude/agents/` changes are staged)

**Rollback is safe**: Phase 3's normalization fallback reads both field names.

### Testing Criteria (must pass before proceeding to Phase 5)
- [ ] `grep -c "^type:" .claude/agents/*.md` returns 0 for all files (frontmatter context)
- [ ] `grep -c "^agent_type:" .claude/agents/*.md` returns ≥1 for every agent file
- [ ] Phase 0 verification test passes (all hardcoded names resolve, no crashes)
- [ ] `skills:` field unchanged in all agent files (spot-check 5 agents)
- [ ] Dashboard loads all agents correctly
- [ ] `claude-mpm doctor` passes (if applicable)
- [ ] `claude-mpm list agents` shows all agents with correct types

### Estimated Effort: **S** (Small — 1-2 hours including verification)

---

## Phase 5: Full Verification and Regression Testing

### Objective
Run comprehensive regression testing to confirm all changes from Phases 0-4 work together correctly. Document the final state.

### Verification Checklist

#### 5.1 Automated Tests
- [ ] Full test suite passes: `pytest tests/ -v`
- [ ] Phase 0 verification test passes
- [ ] No `ValueError` from `agent_management_service.py` for any deployed agent
- [ ] `test_read_agent_type()` passes
- [ ] `test_template_builder_writes_agent_type()` passes

#### 5.2 Field Consistency
- [ ] `grep -r "^type:" .claude/agents/*.md` returns 0 results (frontmatter context)
- [ ] `grep -r "^agent_type:" .claude/agents/*.md` returns result for EVERY agent file
- [ ] All 7 translation points verified:

| T# | Status | Verification Command |
|---|---|---|
| T1 | FIXED | Deploy one agent, verify `agent_type:` in output |
| T2 | FIXED | Verify `agent_discovery_service` outputs `"agent_type"` key |
| T3 | FIXED | Verify `agent_registry` serializes as `"agent_type"` |
| T4 | FIXED | Verify `system_agent_config` outputs `"agent_type"` |
| T5 | FIXED | Verify `dynamic_skills_generator` reads via normalizer |
| T6 | FIXED | Run agent wizard, verify output dict uses `"agent_type"` |
| T7 | UNCHANGED | Verify `subagent_type` → `agent_type` still works in events |

#### 5.3 Skill System Verification (Task #3 Confirmation)
- [ ] `skills:` field preserved in all deployed agents (compare before/after snapshots)
- [ ] Sample agent delegation works: PM delegates to `research-agent`, agent loads correctly
- [ ] Skills are loaded by Claude Code for delegated agents (spot-check 2-3 agents)

#### 5.4 Deployment Pipeline Verification
- [ ] Redeploy one agent via `AgentTemplateBuilder` — verify output uses `agent_type:`
- [ ] Agent discovery service finds all agents
- [ ] Agent listing service displays all agents with correct types

#### 5.5 Dashboard Verification
- [ ] Dashboard loads and displays all agents
- [ ] Agent type classification is correct in dashboard view

#### 5.6 Code Audit
- [ ] No remaining `get("type"` calls in agent-context Python code (except normalization utility and validator)
- [ ] No remaining `frontmatter_lines.append(f"type:` patterns
- [ ] `read_agent_type()` utility exists and is imported consistently
- [ ] All `agents_metadata.py` entries use `"agent_type"` key

#### 5.7 Documentation
- [ ] Archive `README.md` documents reference-only status (Phase 1)
- [ ] Baseline snapshot updated with post-migration state
- [ ] This implementation plan marked as completed
- [ ] Normalization utility docstring clearly states it is **PERMANENT**

### Rollback Strategy
If Phase 5 reveals issues, most likely rollback target is Phase 4 (frontmatter files) since Phase 3's normalization reads both fields. See Phase 4 rollback instructions.

### Testing Criteria (to declare DONE)
- [ ] ALL items in Sections 5.1-5.7 checked off
- [ ] No known regressions
- [ ] Post-migration baseline snapshot created
- [ ] Normalization fallback confirmed as permanent (not scheduled for removal)

### Estimated Effort: **S** (Small — 2-3 hours for thorough verification)

---

## Summary

| Phase | Objective | Files Modified | Effort | Key Risk |
|---|---|---|---|---|
| **0** | Integration tests + baseline | ~3 new files | **S** (2-4h) | None (observation only) |
| **1** | Archive cleanup | 2 files (README + typo fix) | **S** (30min) | None (independent) |
| **2** | Fix critical crash bug | 1 file (`agent_management_service.py`) | **S** (1-2h) | Low — current code already broken |
| **3** | Standardize field name | ~12-15 Python files + 1 new utility | **M** (4-6h) | Medium — must verify all 7 translation points |
| **4** | Migrate 48 frontmatter files | 48 `.md` files (mechanical) | **S** (1-2h) | Low — normalization provides safety net |
| **5** | Full verification | 0 files (testing only) | **S** (2-3h) | None (verification only) |

**Total estimated effort**: **M** (10-18 hours)

### Change Count Summary

| Category | Count | Notes |
|---|---|---|
| Python source files modified | ~15 | Normalization, bug fix, downstream readers |
| Python source files created | 2 | `frontmatter_utils.py` + verification test |
| Agent frontmatter files modified | 48 | Bulk rename `type:` -> `agent_type:` |
| Archive files modified | 2 | README.md (new) + typo fix |
| JSON template files | 0 | Already use `agent_type` |
| Remote agent files | 0 | Already use `agent_type` |
| Hook/event system files | 0 | Already use `agent_type` |
| Skill system files | 0 | Uses `agent_id` / `skills:`, not affected |

---

## Appendix A: Files Modified Per Phase

### Phase 0 (new files only)
- `tests/integration/agents/test_agent_field_consistency.py` (**NEW**)
- `docs-local/agentType-enum/baseline-snapshot.md` (**NEW**)
- `docs-local/agentType-enum/DECISION.md` (**NEW**)

### Phase 1 (archive only)
- `src/claude_mpm/agents/templates/archive/README.md` (**NEW**)
- `src/claude_mpm/agents/templates/archive/javascript_engineer_agent.json` (typo fix)

### Phase 2 (bug fix)
- `src/claude_mpm/services/agents/management/agent_management_service.py` (line 444 + helper method)

### Phase 3 (standardization — largest phase)
- `src/claude_mpm/utils/frontmatter_utils.py` (**NEW** — normalization utility)
- `src/claude_mpm/services/agents/deployment/agent_template_builder.py` (lines 544, 568)
- `src/claude_mpm/services/agents/deployment/agent_discovery_service.py` (line 320)
- `src/claude_mpm/core/agent_registry.py` (lines 73, 105, 208, 239, 321, 747, 801)
- `src/claude_mpm/agents/system_agent_config.py` (line 513)
- `src/claude_mpm/services/dynamic_skills_generator.py` (line 110)
- `src/claude_mpm/cli/interactive/agent_wizard.py` (line 753)
- `src/claude_mpm/services/agents/management/agent_management_service.py` (lines 153, 318, 625, 723)
- `src/claude_mpm/services/agents/deployment/agent_validator.py` (lines 329, 362-363)
- `src/claude_mpm/services/cli/agent_listing_service.py` (lines 214, 250, 296, 372)
- `src/claude_mpm/services/agents/registry/deployed_agent_discovery.py` (lines 109, 133, 193)
- `src/claude_mpm/services/agents/deployment/deployment_wrapper.py` (line 111)
- `src/claude_mpm/services/agents/deployment/agent_lifecycle_manager.py` (line 310)
- `src/claude_mpm/agents/agents_metadata.py` (15 entries)
- `src/claude_mpm/services/monitor/log_manager.py` (line 553)

### Phase 4 (frontmatter migration)
- 48 `.claude/agents/*.md` files (frontmatter field rename)
- `.claude/agents/mpm-agent-manager.md` (body schema doc, line 1218)

### Phase 5 (no file changes)
- Testing and verification only

---

## Appendix B: Rollback Strategy Per Phase

| Phase | Rollback Method | Risk | Time to Rollback |
|---|---|---|---|
| 0 | Delete new test/doc files | None | 2 minutes |
| 1 | Delete archive README, revert JSON typo | None | 2 minutes |
| 2 | Revert line 444 change + remove helper | Low (restores the existing crash) | 5 minutes |
| 3 | `git revert` all Phase 3 commits | None (normalization made this safe) | 15 minutes |
| 4 | `sed 's/^agent_type: /type: /' .claude/agents/*.md` | None (Phase 3 normalization reads both) | 5 minutes |
| 5 | N/A (no changes) | N/A | N/A |

**Key safety property**: At any point after Phase 3, the normalization layer ensures both `type:` and `agent_type:` are correctly read. This means partial completion is **always safe** — the system works regardless of which frontmatter field name is present.

---

## Appendix C: Systems Confirmed Safe (No Changes Needed)

| System | Why No Change | Confirmed By |
|---|---|---|
| Hook/event system (12 files, 80+ refs) | Already uses `agent_type` exclusively | Task #2 |
| Event data contract | Already uses `agent_type` | Task #2 |
| Serialization (unified_agent_registry) | Already uses `agent_type` | Task #2 |
| Skill system (3 mapping systems) | Uses `agent_id` / `skills:` field, not `type`/`agent_type` | Task #3 |
| Remote agent repository | Already uses `agent_type` | Task #1 |
| JSON archive templates | Already use `agent_type` | Task #1 |
| SKILL.md files (189) | No agent type references | Task #3 |
| Claude Code platform runtime | Ignores both fields | Task #4 |
| `subagent_type` translation (T7) | Necessary bridge to Claude Code API; correct as-is | Task #2 |
| Test files (71 using `agent_type`) | Already use correct field name | Task #2 |
