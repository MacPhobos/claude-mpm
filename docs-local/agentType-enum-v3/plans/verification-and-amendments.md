# Verification Report & Critical Amendments

**Date**: 2026-03-06
**Purpose**: Devil's advocate verification of research and plans against original instructions
**Verdict**: 5 gaps found — 2 CRITICAL (blocking), 3 MEDIUM (should fix)

---

## Methodology

Each requirement from the original instructions was checked against:
1. The comprehensive report (`05-comprehensive-report.md`)
2. All three phase plans
3. Actual code on `main` (verified via `git show main:`)

---

## Requirements Compliance Matrix

| # | Requirement | Addressed? | Where | Verdict |
|---|-------------|-----------|-------|---------|
| 1a | Standardize `-` separator in filenames | YES | Phase 1 (normalization), Phase 3 (all paths) | PASS |
| 1b | Standardize `agent_type` not `type` as frontmatter field | **NO** | **NOWHERE** | **CRITICAL GAP** |
| 1c | `name:` field as stable identifier for PM delegation | YES | Phase 1 Changes 3-5, comprehensive report | PASS |
| 2 | Single source of truth from git repos | YES | Phase 2 (registry), Phase 3 (normalization) | PASS |
| 3 | No duplicate deployed agents | YES | Phase 3 Changes 1-2 (dedup logic) | PASS |
| 4a | Remove archive + code that discovers/deploys them | **PARTIAL** | Phase 1 Change 7 deletes archive, but see GAP 2 | **MEDIUM GAP** |
| 4b | Archive was one-time migration | YES | Comprehensive report acknowledges this | PASS |
| 4c | Code hinting at archive must be researched/adjusted | **PARTIAL** | Phase 3 Change 4 mentions `templates/__init__.py` but underestimates scope | **MEDIUM GAP** |
| 5 | Three deployment paths require consolidation | **REINTERPRETED** | Plans normalize, don't consolidate — see GAP 4 | **MEDIUM GAP** |
| Ob1 | `subagent_type` matches `name:` exactly | YES | Core finding throughout all research | PASS |
| Ob2 | Cached agents may have inconsistent naming | YES | Noted in comprehensive report (6 non-conforming) | PASS |
| C1 | PM delegation relies on `name:` field | YES | Foundational to all plans | PASS |
| C2 | Audit ALL PM prompts for correct `name:` references | **PARTIAL** | Fixes 4 files, misses 6+ more | **CRITICAL GAP** |
| C3 | Standardize `agent_type` field in frontmatter | **NO** | **NOWHERE** | **CRITICAL GAP** (same as 1b) |
| G1 | Understand research evolution | YES | Branch historian report | PASS |
| G2 | Consistent `-` filenames, no duplicates | YES | Phases 1+3 | PASS |
| G3 | PM delegation uses `name:` field correctly | PARTIAL | See GAP 5 for incomplete audit | PARTIAL |

---

## GAP 1 (CRITICAL): `type:` vs `agent_type:` Frontmatter Standardization — COMPLETELY MISSING

### What the instructions say

> **Motivation 1b**: "agent definition files have frontmatter which specifies 'type' or 'agent_type' fields. We should standardize on 'agent_type' and not 'type' as the field name"
>
> **Critical #3**: "standardizing on 'agent_type' as the field name in the frontmatter for agent type is important to ensure consistency across all agent definition files. The codebase should be adjusted to use 'agent_type' consistently"

### What the plans say

Nothing. Zero mention of standardizing `type:` → `agent_type:` anywhere.

### Evidence of the problem on main

Code that reads `type` (not `agent_type`) from agent data:
- `deployed_agent_discovery.py:109` — `agent.get("type", agent.get("name", "unknown"))`
- `deployed_agent_discovery.py:133` — `agent_type = getattr(agent, "type", None)`
- `deployed_agent_discovery.py:143` — `getattr(agent, "agent_id", agent_type or "unknown")`
- `deployment_wrapper.py:111` — `"type": agent.get("type", "agent")`

Code that reads `agent_type` correctly:
- `local_template_manager.py:109` — `agent_type=data.get("agent_type", "")`
- Archive JSON files all use `"agent_type"` key

### Required Amendment

**Add to Phase 2 as new Change 6** (or new Phase 2.5):

**Audit and standardize all frontmatter field readers:**
1. Grep for all code that reads `"type"` from agent frontmatter/data dicts
2. Change to read `"agent_type"` with fallback: `data.get("agent_type", data.get("type", ""))`
3. Add deprecation warning when `type` is used without `agent_type`
4. Update `agent_frontmatter_schema.json` (if it exists) to use `agent_type` as the required field
5. Note in Ob2 documentation: upstream agents should use `agent_type:` in frontmatter

**Files to modify** (at minimum):
- `src/claude_mpm/services/agents/registry/deployed_agent_discovery.py`
- `src/claude_mpm/services/agents/deployment/deployment_wrapper.py`
- Any other files found by:
  ```bash
  grep -rn '\.get.*"type"' src/claude_mpm/services/agents/ --include="*.py" | grep -v __pycache__ | grep -v agent_type
  ```

---

## GAP 2 (CRITICAL): Incomplete PM Prompt Audit — 6+ Files Missed

### What the instructions say

> **Critical #2**: "PM prompts must be audited to ensure that ALL references to agents use the 'name' field from the agent frontmatter"

### What the plans fix

Only 4 files:
1. `PM_INSTRUCTIONS.md` (cherry-pick)
2. `WORKFLOW.md` (cherry-pick)
3. `CLAUDE_MPM_OUTPUT_STYLE.md` (Phase 1 Change 4)
4. `system_context.py` (Phase 1 Change 5)

### Files with WRONG agent references still unfixed on main

**A. `WORKFLOW.md` — STILL HAS PROBLEMS after cherry-pick**

Line 38: `api-qa (APIs), web-qa (UI), qa (general)` — These are filename stems, NOT `name:` values.
- Correct: `API QA`, `Web QA`, `QA`

Lines 43-45: `use api_qa` / `use web_qa` / `use qa` — wrong format.
- Correct: `use "API QA"` / `use "Web QA"` / `use "QA"`

Lines 111-115: `local-ops` used 3 times — should be `Local Ops`

**B. `templates/pm-examples.md`** (loaded into PM context)

Line 39: `local-ops-agent` — should be `Local Ops`
Lines 245-306: 10+ references to `local-ops-agent` — ALL should be `Local Ops`

**C. `templates/pr-workflow-examples.md`** (loaded into PM context)

Lines 5, 29, 30, 36, 37, 87, 88, 99, 100, 112: `version-control` — should be `Version Control`

**D. `templates/circuit-breakers.md`** (loaded into PM context)

Line 58: `Research agent` — should be `Research`
Line 63: `Research agent` — should be `Research`

**E. `BASE_AGENT.md`** (inherited by ALL agents)

Lines 76-80: `Engineer`, `QA`, `Security`, `Documentation`, `Research` — Some of these may be wrong:
- `Documentation` should be `Documentation Agent`

**F. `MEMORY.md`**

Line 27: `engineer, qa, research, security` — These are filename stems, not `name:` values. However, this refers to memory file naming (not delegation), so it may be intentional.

### Required Amendment

**Expand Phase 1 Change 3** (or add Phase 1 Change 3b):

After cherry-picking the PM_INSTRUCTIONS.md + WORKFLOW.md fixes, perform a FULL audit:
```bash
# Find ALL agent references in PM prompt files
grep -rn "local-ops\|version-control\|api-qa\|web-qa\|local.ops.agent\|documentation\b" \
  src/claude_mpm/agents/ --include="*.md" | grep -v archive
```

Fix every file where an agent is referenced by filename stem instead of `name:` field value. Priority:
1. Files that are directly injected into PM context (WORKFLOW.md, OUTPUT_STYLE, templates/*.md)
2. Files inherited by agents (BASE_AGENT.md)
3. Documentation files (MEMORY.md — may be intentional)

**Complete list of fixes needed**:

| File | Wrong Reference | Correct `name:` Value |
|------|----------------|----------------------|
| WORKFLOW.md:38 | `api-qa` | `API QA` |
| WORKFLOW.md:38 | `web-qa` | `Web QA` |
| WORKFLOW.md:38 | `qa` | `QA` |
| WORKFLOW.md:43-45 | `api_qa`, `web_qa`, `qa` | `API QA`, `Web QA`, `QA` |
| WORKFLOW.md:111-115 | `local-ops` (3x) | `Local Ops` |
| pm-examples.md:39+ | `local-ops-agent` (10x) | `Local Ops` |
| pr-workflow-examples.md | `version-control` (8x) | `Version Control` |
| circuit-breakers.md:58,63 | `Research agent` | `Research` |
| BASE_AGENT.md:78 | `Documentation` | `Documentation Agent` |

---

## GAP 3 (MEDIUM): `templates/__init__.py` Is a Fully Dead Module

### What the plan says

Phase 3 Change 4 says: "If the file contains archive references → Remove them. If empty or just comments → Leave as-is."

### What it actually is

`templates/__init__.py` is a **100% dead module** containing:
- `AGENT_TEMPLATES` dict mapping 10 agent types to files that **DON'T EXIST** (all `*_agent.md` files — none exist in templates/)
- `AGENT_NICKNAMES` dict — yet ANOTHER competing agent name list (missed in the "4+ competing CORE_AGENTS lists" audit)
- `get_template_path()` and `load_template()` — functions that can NEVER return valid data (target files don't exist)
- **Zero production consumers** — no code imports `AGENT_TEMPLATES`, `AGENT_NICKNAMES`, `get_template_path`, or `load_template` (verified by grep)

### Required Amendment

**Upgrade Phase 3 Change 4 from "maybe cleanup" to "gut the module":**

Replace the entire file contents with just the Python package marker:
```python
"""Agent templates module."""
```

This eliminates:
- The dead `AGENT_TEMPLATES` dict (a 6th competing agent list the report missed)
- The dead `AGENT_NICKNAMES` dict
- Two dead functions that reference nonexistent files

**Also update the comprehensive report** to change M3 from "4+ competing CORE_AGENTS lists" to "5+ competing agent lists" — `templates/__init__.py:AGENT_TEMPLATES` was missed.

---

## GAP 4 (MEDIUM): Deployment Path "Consolidation" vs "Normalization" — Silent Reinterpretation

### What the instructions say

> **Motivation 5**: "three different agent deployment code paths that **require consolidation** and standardization of callers"

### What the plans do

The plans explicitly decide to keep all 3 paths separate and just normalize filenames across them. The devil's advocate research justified this (different use cases), but the comprehensive report and plans never explicitly acknowledge this diverges from the user's stated goal.

### Required Amendment

**Add to the comprehensive report** a new section under "Key Design Decisions":

```markdown
### 6. Deployment Paths: Normalize, Not Consolidate (Reinterpretation of Goal)
- **User requested**: Consolidation of 3 deployment paths
- **Our recommendation**: Keep separate, normalize behavior
- **Rationale**: The 3 paths serve genuinely different use cases:
  - Path 1 (deploy_agent_file): Builds from scratch with full normalization
  - Path 2 (SingleAgentDeployer): Builds from JSON templates via template_builder
  - Path 3 (configure.py): Copies pre-built .md from cache
  Forcing all through one function would require Path 2 to stop building content
  and Path 3 to stop preserving upstream exactly. Both would introduce regressions.
- **What we DO deliver**: All 3 paths produce identical output filenames and
  consistent frontmatter, achieving the user's underlying goal (no duplicates,
  consistent naming) without the risk of merging different content-building strategies.
```

---

## GAP 5 (MEDIUM): Archive Deletion Verification Is Insufficient

### What the plan says

Phase 1 Change 7 verifies: `grep -rn "templates/archive" src/claude_mpm/` — checking for direct path references.

### What the user specifically worried about

> **Motivation 4a**: "by using rglob to find json templates in the archive/ directory and deploying them to .claude/agents/"

### What I found

The modern discovery path (`AgentDiscoveryService`) uses `*.md` glob (NOT `*.json`, NOT recursive), so archive `.json` files are NOT discovered. BUT the plan doesn't explain this — it just says "verify no runtime consumers" without proving WHY they aren't consumers.

### Required Amendment

**Add to Phase 1 Change 7, after pre-deletion verification:**

```markdown
**WHY archive is safe to delete (proven by code analysis)**:
1. `AgentDiscoveryService.list_available_agents()` uses `self.templates_dir.glob("*.md")`
   — flat glob, `.md` only. Archive contains `.json` files → NOT discovered.
2. `AgentDiscoveryService.get_filtered_templates()` delegates to `list_available_agents()`
   — same `.md` glob constraint.
3. `multi_source_deployment_service.py` uses `AgentDiscoveryService` for all 4 tiers
   — same `.md` glob constraint.
4. `SingleAgentDeployer` receives `template_file` from the discovery service
   — it never discovers files itself.
5. `agent_template_builder.py` CAN read `.json` files (line 365), but it receives
   paths from the deployer, which receives paths from discovery (`.md` only).
6. No code uses `rglob` or `**/*.json` patterns on the templates directory.

Conclusion: archive `.json` files have zero discovery path. Deletion is safe.
```

---

## Summary of Required Amendments

### CRITICAL (must fix before implementation)

| # | Gap | Fix | Where |
|---|-----|-----|-------|
| 1 | `type:` → `agent_type:` standardization missing | Add new change to Phase 2 | Phase 2 + comprehensive report |
| 2 | PM prompt audit incomplete (6+ files missed) | Expand Phase 1 Change 3 scope | Phase 1 plan |

### MEDIUM (should fix before implementation)

| # | Gap | Fix | Where |
|---|-----|-----|-------|
| 3 | `templates/__init__.py` is fully dead module | Upgrade Phase 3 Change 4 | Phase 3 plan |
| 4 | Silent reinterpretation of "consolidation" goal | Add design decision #6 | Comprehensive report |
| 5 | Archive deletion rationale insufficient | Add code analysis proof | Phase 1 Change 7 |

---

## Files Requiring Amendment

1. `docs-local/agentType-enum-v3/research/05-comprehensive-report.md` — Add design decision #6, update M3 count
2. `docs-local/agentType-enum-v3/plans/phase-1-minimal-viable-fix.md` — Expand Change 3, enhance Change 7
3. `docs-local/agentType-enum-v3/plans/phase-2-registry-enum-consolidation.md` — Add Change 6 for type→agent_type
4. `docs-local/agentType-enum-v3/plans/phase-3-deployment-normalization-cleanup.md` — Upgrade Change 4
