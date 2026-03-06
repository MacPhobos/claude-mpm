# Consolidated Analysis v6: Agent Filename Standardization

**Date**: 2026-03-04
**Branch**: `agenttype-enums`
**Sources**: v5 deployment analysis + 3 parallel investigations (prompt-tracer, reference-mapper, devils-advocate)

---

## Executive Summary

The plan at `~/.claude/plans/wise-kindling-sutherland.md` proposes standardizing agent filenames from underscores to hyphens. After comprehensive analysis from 4 independent investigations, the plan is **fundamentally sound in direction but dangerously incomplete in scope**.

### Key Numbers

| Metric | Plan Says | Actual |
|--------|-----------|--------|
| Files needing rename in `.claude/agents/` | ~15 | **29** (14 underscore + 15 `-agent` suffix) |
| Filename collision pairs | 0 | **5** (BLOCKING) |
| Code locations needing changes | 4 | **10+** |
| Normalization systems in conflict | 0 | **2** (normalizer vs registry) |
| Hardcoded agent name files at risk | 0 | **10+** (literal equality checks) |
| Agent identity systems | 1 | **3** (filename, `name` field, `agent_type`) |

### Verdict

**DO NOT EXECUTE the plan as-is.** It must be revised to address:
1. The 5 filename collision pairs (BLOCKING)
2. The PM prompting layer's multi-identity agent system
3. The normalizer-vs-registry conflict
4. 6+ missed code locations
5. The frontmatter `agent_id` update gap

---

## Part 1: Original Deployment Path Issues (from v5)

### What v5 Found

The original plan correctly identifies that `normalize_deployment_filename()` exists in `deployment_utils.py` and that 4 deployment paths bypass it. Line numbers are accurate.

### What v5 Missed (that v6 confirms)

v5 identified 3 additional deployment paths not in the plan. v6 confirms and expands:

| # | Code Location | In Plan? | Status |
|---|---------------|----------|--------|
| 1 | `single_agent_deployer.py:68` | YES | Confirmed raw stem |
| 2 | `single_agent_deployer.py:217` | YES | Confirmed raw parameter |
| 3 | `async_agent_deployment.py:481` | YES | Confirmed raw `_agent_name` |
| 4 | `local_template_deployment.py:113` | YES | Confirmed raw `template.agent_id` |
| 5 | `agent_deployment_context.py:73` | **NO** | Raw `template_file.stem` — pipeline path |
| 6 | `agent_processing_step.py:54` | **NO** | Raw stem before calling context factory |
| 7 | `agent_deployment.py:478` | **NO** | Orchestrator raw stem |
| 8 | `agent_management_service.py:97` | **NO** | User-facing `create_agent()` raw name |
| 9 | `deployment_utils.py` ensure_agent_id | **NO** | Skips existing `agent_id:` fields |
| 10 | `agent_name_normalizer.py` | **NO** | Underscore-canonical conflicts with plan direction |

---

## Part 2: The Three-Identity Problem (NEW — from prompt-tracer)

### Discovery

Each agent has **three distinct identities** used by different subsystems:

| Identity | Example (Research) | Source | Used By |
|----------|-------------------|--------|---------|
| **Filename stem** | `research-agent` | `.claude/agents/research-agent.md` | Claude Code file resolution, `AgentLoader` |
| **`name` field** | `Research` | YAML frontmatter `name:` | PM prompt capabilities section, `subagent_type` resolution |
| **`agent_type` field** | `research` | YAML frontmatter `agent_type:` | MPM internal: skills, hooks, event tracking |

### Why This Matters for the Rename

1. **The `name` field is the PM-facing delegation identifier.** When PM calls `Agent(subagent_type="Research")`, Claude Code matches this against the `name:` field in frontmatter. **Renaming filenames does NOT change the `name` field, so PM delegation routing is SAFE.**

2. **The `agent_type` field is NOT in the PM prompt.** Standardizing `agent_type` values is safe from a PM perspective.

3. **The filename stem is used as a fallback identifier.** When no `name:` field exists, the filename stem becomes the agent ID shown to PM. The fallback capabilities in `ContentFormatter` use a MIX of `name`-style and filename-style IDs — this is already broken.

### PM Prompt Assembly Chain

```
SystemInstructionsService
  → FrameworkLoader._generate_agent_capabilities_section()
    → CapabilityGenerator.parse_agent_metadata()
      → agent_data["id"] = metadata["name"]  // "Research", "Engineer", etc.
    → generate_capabilities_section()
      → "### Research (`Research`)"  // PM sees name field
  → ContentFormatter.format_full_framework()
    → Assembles: PM_INSTRUCTIONS + WORKFLOW + MEMORY + capabilities + context
```

### Hardcoded Agent References in PM Prompt Files

| File | References | Convention |
|------|-----------|------------|
| `PM_INSTRUCTIONS.md` | `local-ops`, `web-qa-agent`, `api-qa-agent` | Hyphen + sometimes `-agent` suffix |
| `WORKFLOW.md` | `api_qa`, `web_qa`, `qa` | Python-style identifiers (underscore) |
| `ContentFormatter` fallback | `engineer`, `research-agent`, `qa-agent` | MIXED (some bare, some with `-agent`) |
| `todo_task_tools.py` | `research-agent`, `engineer`, `qa-agent` | MIXED (engineer bare, others with suffix) |

**Impact**: PM_INSTRUCTIONS.md and WORKFLOW.md contain hardcoded agent names that won't auto-update when files are renamed. These are "soft" breaks (PM interprets them contextually) but contribute to confusion.

---

## Part 3: Agent Name Reference Map (NEW — from reference-mapper)

### Scale of Hardcoding

**11 categories** of agent name references found across the codebase, spanning:
- Core Python code (equality checks)
- Agent templates and metadata
- Services (deployment, memory, capabilities)
- Hooks (event handlers, tool analysis)
- CLI commands
- Skills files
- PM instructions
- YAML configs
- Agent registry/catalog
- Test files (139 files with hardcoded agent names)

### The 5 Critical Inconsistencies

| # | Inconsistency | Impact |
|---|---------------|--------|
| 1 | **Normalizer vs Registry conflict**: `agent_name_normalizer.py` → `python_engineer` (underscore); `agent_registry.py` → `python-engineer` (hyphen) | Code paths through different modules produce different canonical IDs |
| 2 | **PM instructions mixed conventions**: `PM_INSTRUCTIONS.md` says `local-ops`, `pm-examples.md` says `local-ops-agent`, `circuit-breakers.md` uses both | PM gets contradictory guidance |
| 3 | **Engineer has no `-agent` suffix but research/qa do** in `todo_task_tools.py`: `subagent_type="engineer"` vs `subagent_type="research-agent"` | PM taught inconsistent naming rules |
| 4 | **`agent_capabilities.yaml` mixed within entries**: `php_engineer` key → `agent_id: "php-engineer"` | YAML key ≠ value convention |
| 5 | **`skill_to_agent_mapping.yaml`** uses hyphens; Python code uses underscores | Skill routing uses different IDs than Python model |

### 10 Highest-Risk Files (Literal Equality Checks)

These files do exact string matching on agent names — any rename without updating them causes silent failures:

1. `tool_access_control.py` — `agent_type == "pm"`, `== "engineer"`, etc.
2. `tool_analysis.py` — `subagent_type == "research"`, `== "engineer"`
3. `event_handlers.py` — `agent_type in ["research", "engineer", "qa", ...]`
4. `subagent_processor.py` — hardcoded list `["research", "engineer", "pm", ...]`
5. `templates/__init__.py` — `AGENT_TEMPLATES` dict keys
6. `agents_metadata.py` — metadata registry dict keys
7. `agent_session_manager.py` — session prompt dict keys
8. `system_agent_config.py` — `SystemAgentConfig(agent_type="engineer", ...)`
9. `agent_deployment_handler.py` — allowlist `["engineer", "research", "qa", "web-qa"]`
10. `slack commands.py` — default `"engineer"` fallback

### All Agent Name Variants (Reference Table)

| Agent | Bare | Underscore | Hyphen | +suffix | Display |
|-------|------|-----------|--------|---------|---------|
| Engineer | `engineer` | — | — | — | `Engineer` |
| Research | `research` | — | — | `research-agent` | `Research` |
| QA | `qa` | — | — | `qa-agent` | `QA` |
| Web QA | — | `web_qa` | `web-qa` | `web-qa-agent` | `Web QA` |
| Local Ops | — | `local_ops` | `local-ops` | `local-ops-agent` | `Local Ops` |
| Python Eng | — | `python_engineer` | `python-engineer` | — | `Python Engineer` |
| Golang Eng | — | `golang_engineer` | `golang-engineer` | — | `Golang Engineer` |
| Ops | `ops` | — | — | `ops-agent` | `Ops` |
| PM | `pm` | `project_manager` | — | — | `PM` |

---

## Part 4: Confirmed and Likely Breaks (NEW — from devils-advocate)

### CONFIRMED BREAKS (will crash or silently fail)

| # | Location | Failure Mode |
|---|----------|-------------|
| 1 | `scripts/bump_agent_versions.py:10-42` | `FileNotFoundError` — hardcoded underscore filenames like `"golang_engineer"` |
| 2 | `agent_capabilities_service.py:224` | Silent lookup miss — `agent_id = agent_file.stem` (no normalization), YAML keys are underscore |
| 3 | `agent_capabilities.yaml` | Already internally inconsistent: `php_engineer` key → `agent_id: "php-engineer"`. Rename amplifies. |
| 4 | `agent_capabilities.yaml` `local_ops_agent` entry | Template reference already hyphen, key is underscore, `bump_agent_versions.py` expects underscore |

### LIKELY BREAKS (high probability of silent failure)

| # | Location | Failure Mode |
|---|----------|-------------|
| 5 | `tool_analysis.py:84-86` | Exact `== "research"` / `== "engineer"` checks on subagent_type — dashboard misclassification |
| 6 | `subagent_processor.py:351` | Hardcoded agent type list for `is_delegation_related` — events misclassified |
| 7 | Duplicate files in `.claude/agents/` | Rename source templates but deployed files stay old until redeploy — both versions coexist |

### META-FINDING

The deployed `.claude/agents/` directory is **already a mixed mess**: `golang_engineer.md` AND `python-engineer.md` coexist right now. The rename doesn't solve inconsistency — it moves the line. A comprehensive solution requires updating ALL references atomically.

---

## Part 5: Risk Assessment (Consolidated)

### BLOCKING Risks (must resolve before execution)

| Risk | Description | Resolution |
|------|-------------|------------|
| **R1: Filename collisions** | 5 collision pairs where `-agent` suffix stripping produces a name that already exists (`documentation-agent.md` → `documentation.md` which exists) | Human decision per pair: which file wins? |
| **R3: Pipeline path regression** | `AgentDeploymentContext.from_template_file()` not in plan — will re-create underscore files on next pipeline run | Add to fix list |

### HIGH Risks (should resolve before execution)

| Risk | Description | Resolution |
|------|-------------|------------|
| **R2: Frontmatter `agent_id` mismatch** | `ensure_agent_id_in_frontmatter()` skips files that already have `agent_id:` — won't update from underscore to hyphen | Extend function with `update_existing` parameter |
| **R4: Conflicting normalizers** | `agent_name_normalizer.py` (underscore-canonical) vs `agent_registry.py` (hyphen-canonical) | Pick one canonical form, update both |
| **Hardcoded references** | 10+ files with literal equality checks on agent names | Audit and update all, or centralize behind normalizer |

### MEDIUM Risks (should address in same release)

| Risk | Description |
|------|-------------|
| **R5**: Async `_agent_name` stays underscore in logs | Normalize at load time |
| **R7**: No user migration strategy | Add `claude-mpm agents normalize` command |
| **R8**: Management service creates non-normalized files | Add normalization to `create_agent()` |
| **PM prompt hardcoding**: PM_INSTRUCTIONS.md, WORKFLOW.md, todo_task_tools.py | Update references or accept as soft references |

### LOW Risks (can defer)

| Risk | Description |
|------|-------------|
| **R6**: Race condition during delete-then-write | Standard file-replace problem, sub-millisecond window |
| **Test files**: 139 files with hardcoded expectations | Update as tests fail |

---

## Part 6: Critical Unanswered Question

**Does Claude Code resolve `subagent_type` from filename stem OR from frontmatter `name:` field?**

- If **filename stem** → ALL existing Task tool calls with old names break after redeploy
- If **`name` field** → Core PM delegation routing is safe, but MPM internal code still breaks

Evidence from prompt-tracer suggests it's the **`name` field** (Claude Code scans `.claude/agents/*.md` and matches `subagent_type` to the `name:` in YAML frontmatter). This means:

**PM delegation is SAFE** — the `name:` field doesn't change when filenames change.
**MPM internal code is NOT SAFE** — it uses filename stems, `agent_type`, and hardcoded strings.

---

## Part 7: Recommended Plan Revisions

### Before Any Code Changes

1. **Resolve the 5 collision pairs** — human decision required for each:
   - `documentation-agent.md` vs `documentation.md`
   - `ops-agent.md` vs `ops.md`
   - `qa-agent.md` vs `qa.md`
   - `research-agent.md` vs `research.md`
   - `web-qa-agent.md` vs `web-qa.md`

2. **Choose one canonical form** — hyphen (aligned with plan direction and `agent_registry.py`)

3. **Decide scope**: Filenames only? Or also reconcile `agent_name_normalizer.py`, `agent_capabilities.yaml` keys, and all hardcoded references?

### Expanded Fix List (10 locations, not 4)

| # | File | Change |
|---|------|--------|
| 1 | `single_agent_deployer.py:68` | Normalize `template_file.stem` |
| 2 | `single_agent_deployer.py:217` | Normalize `agent_name` parameter |
| 3 | `async_agent_deployment.py:264,481` | Normalize `_agent_name` at load AND use |
| 4 | `local_template_deployment.py:113` | Normalize `template.agent_id` |
| 5 | `agent_deployment_context.py:73` | Normalize in `from_template_file()` |
| 6 | `agent_processing_step.py:54` | Remove raw stem extraction |
| 7 | `agent_deployment.py:478` | Normalize before passing to deployer |
| 8 | `agent_management_service.py:97` | Normalize `name` in `create_agent()` |
| 9 | `deployment_utils.py` | Extend `ensure_agent_id_in_frontmatter()` to update existing |
| 10 | `agent_name_normalizer.py` | Flip canonical form from underscore to hyphen |

### Additional Files to Update

- `scripts/bump_agent_versions.py` — rewrite to derive filenames dynamically
- `agent_capabilities.yaml` — standardize all keys and `agent_id` values
- `agent_capabilities_service.py:224` — normalize raw stem
- PM_INSTRUCTIONS.md, WORKFLOW.md, todo_task_tools.py — update hardcoded references (or accept as soft)

### Migration Strategy

Add `claude-mpm agents normalize` command that:
1. Scans `.claude/agents/` for underscore-named files
2. Renames to hyphen equivalents
3. Updates `agent_id:` in frontmatter
4. Removes old files
5. Reports changes

---

## Appendix: Source Documents

| Document | Location | Author |
|----------|----------|--------|
| PM Prompt Assembly Analysis | `analysis-v6/pm-prompt-assembly.md` | prompt-tracer |
| Agent Name Reference Map | `analysis-v6/agent-name-references.md` | reference-mapper |
| Devil's Advocate Breaks | `analysis-v6/devils-advocate.md` | devils-advocate |
| v5 Devil's Advocate | `analysis-v5/devils-advocate-findings.md` | v5 research |
| v5 Risk Assessment | `analysis-v5/risk-assessment.md` | v5 research |
| v5 Code Evidence | `analysis-v5/code-evidence.md` | v5 research |
| Original Plan | `~/.claude/plans/wise-kindling-sutherland.md` | — |
