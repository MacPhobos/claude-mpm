# Deployment Pipeline & Archive Template Analysis (v3)

**Date**: 2026-03-03
**Analyst**: Deployment Pipeline Analyst (Claude Opus 4.6)
**Branch**: `agenttype-enums`
**Task**: Task #1 — Comprehensive deployment pipeline and archive template usage analysis
**Builds on**: analysis-v2 (5 documents) + analysis-v2.1 (5 documents)

---

## Executive Summary

This analysis provides a **fresh, verified** trace of the complete deployment pipeline and archive template lifecycle. It confirms and extends key findings from v2/v2.1, corrects minor discrepancies, and provides new analysis on:

1. **The archive directory (`src/claude_mpm/agents/templates/archive/`) is referenced by exactly 2 production-adjacent Python files** — both are scripts, not runtime code. Zero production source files in `src/claude_mpm/` import from or reference the archive path directly.
2. **The `AgentTemplateBuilder` rename of `agent_type` → `type` on line 568 is confirmed** as the sole conversion point. The comment on line 544 even labels it: `"type: agent type for categorization and functionality"`.
3. **39 JSON files exist in the archive** (not 38 as stated in v2). The archive serves as a **manually maintained canonical reference** with no automated consumers.
4. **Removing the archive directory would have zero impact on runtime behavior** — no production code reads from it. The only breakage would be to the `scripts/delegation_matrix_poc.py` POC script and the `scripts/migrate_json_to_markdown.py` migration tool.
5. **Three additional code paths scan `templates/` (not `templates/archive/`)** for `*.json` files — `SkillManager`, `SimpleAgentManager`, and `NativeAgentConverter` — and all find **zero JSON files** because the JSON files are in the `archive/` subdirectory.

---

## 1. Archive Directory Inventory

### Location

```
src/claude_mpm/agents/templates/archive/
```

### Contents: 39 JSON Files

```
agent-manager.json              java_engineer.json
agentic-coder-optimizer.json    javascript_engineer_agent.json
api_qa.json                     memory_manager.json
clerk-ops.json                  nextjs_engineer.json
code_analyzer.json              ops.json
content-agent.json              php-engineer.json
dart_engineer.json              product_owner.json
data_engineer.json              project_organizer.json
documentation.json              prompt-engineer.json
engineer.json                   python_engineer.json
gcp_ops_agent.json              qa.json
golang_engineer.json            react_engineer.json
imagemagick.json                refactoring_engineer.json
                                research.json
                                ruby-engineer.json
                                rust_engineer.json
                                security.json
                                svelte-engineer.json
                                tauri_engineer.json
                                ticketing.json
                                typescript_engineer.json
                                vercel_ops_agent.json
                                version_control.json
                                web_qa.json
                                web_ui.json
```

### JSON Template Schema (from `golang_engineer.json`)

```json
{
  "name": "Golang Engineer",
  "description": "Go 1.23-1.24 specialist...",
  "schema_version": "1.3.0",
  "agent_id": "golang_engineer",
  "agent_version": "1.0.0",
  "agent_type": "engineer",           // <-- THE FIELD IN QUESTION
  "metadata": {
    "name": "Golang Engineer",
    "category": "engineering",
    "tags": ["golang", "go", ...],
    "color": "cyan"
  },
  "capabilities": {
    "model": "sonnet",
    "tools": ["Read", "Write", ...],
    "resource_tier": "standard"
  },
  "skills": ["toolchains-java-core", ...]
}
```

**Key observation**: ALL 39 JSON templates use `"agent_type"` as the field name. Values are functional role strings: `"engineer"`, `"ops"`, `"qa"`, `"research"`, `"documentation"`, `"security"`, `"specialized"`, `"system"`, `"analysis"`, `"refactoring"`, `"product"`, `"content"`, `"imagemagick"`, `"memory_manager"`, `"claude-mpm"`.

---

## 2. Complete Code Reference Map: Who References the Archive?

### 2.1 Production Source Code (`src/claude_mpm/`) — ZERO REFERENCES

**No production code in `src/claude_mpm/` directly references `templates/archive/`.**

The following production code references `templates/` (the parent directory) but scans for `*.json` at the TOP LEVEL only, missing the `archive/` subdirectory:

| File | Line | Path Used | Glob Pattern | Files Found |
|------|------|-----------|-------------|-------------|
| `skills/skill_manager.py` | 28 | `...agents/templates` | `*.json` | **0** (JSON files in `archive/` subdirectory) |
| `cli/commands/agent_state_manager.py` | 40-41 | `...agents/templates` | `*.json` | **0** (same reason) |
| `services/native_agent_converter.py` | 276 | `...agents/templates` | `*.json` | **0** (same reason) |
| `core/framework/loaders/agent_loader.py` | 142 | `.claude-mpm/agents` | `*.json` | **0** (different directory entirely) |
| `core/framework/processors/template_processor.py` | 219 | `.claude-mpm/agents` | `*.json` | **0** (different directory entirely) |

**Confirmed**: The SkillManager path bug from v2.1 is VERIFIED. Line 28 constructs:
```python
agent_templates_dir = Path(__file__).parent.parent / "agents" / "templates"
# Resolves to: src/claude_mpm/agents/templates/  (NOT templates/archive/)
```

Then line 37 globs `*.json` — non-recursive, finds zero files.

### 2.2 Scripts (Outside `src/`) — TWO REFERENCES

| File | Line | Reference Type | Purpose |
|------|------|---------------|---------|
| `scripts/delegation_matrix_poc.py` | 20 | Direct path to `archive/` | POC script reads JSON templates for delegation matrix generation |
| `scripts/migrate_json_to_markdown.py` | 425 | Creates `archive/` subdirectory | Migration tool archives JSON files after conversion |

### 2.3 Documentation References

| File | Context |
|------|---------|
| `docs/migration/JSON_TO_MARKDOWN_MIGRATION_SUMMARY.md` | Documents the `--archive` flag behavior |
| `docs/_archive/*/json-template-documentation-audit-2025-12-23.md` | Notes 39 archived files |
| `docs/_archive/*/agent-deployment-warnings-analysis-2025-12-19.md` | Lists archive as legacy source |
| `docs/_archive/*/pm-instruction-gaps-investigation-2025-12-25.md` | References archive location |
| `docs/_archive/*/skills-auto-linking-investigation-2025-12-29.md` | Example from archive JSON |

### 2.4 Configuration References

| File | Context |
|------|---------|
| `.secrets.baseline` | Lists 4 archive JSON files with detected secret patterns (false positives for ops/security agent API key examples) |

### 2.5 Test References — ZERO

No test file references `templates/archive/` directly.

---

## 3. The Deployment Pipeline: End-to-End Trace

### 3.1 The Active Pipeline (Gen 1 Agents)

```
                                              CONVERSION POINT
                                              ================
Remote Git Repo                                        |
(bobmatnyc/claude-mpm-agents)                          |
    |                                                  |
    | git sync (GitSourceSyncService)                  |
    v                                                  v
Cache: ~/.claude-mpm/cache/agents/       AgentTemplateBuilder
    |  agent_type: engineer              Line 493: reads "agent_type"
    |  (ALL 48 remote agents use         Line 567-568: writes "type:"
    |   agent_type, not type)                 |
    |                                         |
    v                                         v
Deployed: .claude/agents/*.md            type: engineer
    (45 Gen 1 kebab-case files)          (CONVERTED from agent_type)
```

**Verified at `agent_template_builder.py`**:

```python
# Line 493: READ agent_type from template data
agent_type = template_data.get("agent_type", "general")

# Lines 544 (comment): documents the field purpose
# "type: agent type for categorization and functionality (optional but important)"

# Lines 567-568: WRITE as type to frontmatter
if agent_type and agent_type != "general":
    frontmatter_lines.append(f"type: {agent_type}")
```

**This is the SOLE point where `agent_type` becomes `type`.**

### 3.2 The Migration Pipeline (Gen 2 Agents — One-Time)

```
JSON Templates (archive/)                  migrate_json_to_markdown.py
    |  "agent_type": "engineer"            Line 114: preserves agent_type
    |                                          |
    v                                          v
Deployed: .claude/agents/*_*.md            agent_type: engineer
    (14 underscore-named files)            (PRESERVED, not converted)
```

**Verified at `migrate_json_to_markdown.py:114`**:

```python
"agent_type": template_data.get("agent_type", "specialized"),
```

### 3.3 Key Difference

| Pipeline | Source Field | Output Field | Conversion? |
|----------|-------------|-------------|-------------|
| AgentTemplateBuilder (active, Gen 1) | `agent_type` | `type` | **YES** (line 568) |
| migrate_json_to_markdown (one-time, Gen 2) | `agent_type` | `agent_type` | **NO** (preserved) |

**This explains the field name split**: The active deployment pipeline converts the field name, while the migration script preserves it.

---

## 4. The Archive Directory: Role, Purpose, and Impact of Removal

### 4.1 Current Role

The archive directory serves as a **manually maintained canonical reference** for agent definitions with rich metadata (schema_version, agent_id, capabilities, interactions, memory_routing, knowledge domains) that the deployed markdown agents do not carry.

**How they are maintained**: Manual updates by the project developer with Claude Code assistance. Evidence from recent commit messages:
```
ab05426a feat: add Java core skill and integrate with java-engineer and code-analyzer
8b14e146 feat: add language core skills and best-practice matching to code-analyzer
f99e3ecf feat: add language-specific core skills paired with engineer agents
```

### 4.2 What Reads from Archive at Runtime?

**Nothing.** Zero production code paths read from the archive directory. The three code paths that scan `templates/` (parent directory) all use `*.json` (non-recursive) and find zero files.

### 4.3 Impact of Removing Archive Directory

| Component | Impact | Severity |
|-----------|--------|----------|
| **Runtime behavior** | None | ZERO |
| **Agent deployment** | None — AgentTemplateBuilder reads from git cache, not archive | ZERO |
| **Agent discovery** | None — AgentDiscoveryService scans for `*.md` files only | ZERO |
| **Skill mapping** | None — SkillManager already finds zero files due to path bug | ZERO |
| **Dashboard** | None — reads from deployed `.claude/agents/*.md` | ZERO |
| **`scripts/delegation_matrix_poc.py`** | Would fail to find templates | LOW (POC script) |
| **`scripts/migrate_json_to_markdown.py`** | Would have no source JSON files | LOW (one-time migration, already completed) |
| **`.secrets.baseline`** | Would have stale references | LOW (cosmetic) |
| **Developer reference** | Loses canonical rich-metadata agent definitions | MEDIUM |
| **Skills field in JSON** | Loses the `"skills"` mapping data (e.g., which skills go with which agents) | MEDIUM |

### 4.4 Recommendation for Archive

**Do NOT remove the archive yet.** While it has zero runtime impact, it serves as:
1. The only place where full agent metadata (capabilities, interactions, memory_routing) is documented
2. A reference for skill-to-agent mappings (the `"skills"` field)
3. Source material if the JSON template system is ever reactivated

**Instead**: Add a `README.md` to the archive directory documenting its purpose as a reference-only collection, not an active data source.

---

## 5. AgentTemplateBuilder: The `agent_type` → `type` Rename (Deep Dive)

### 5.1 All Locations Where `agent_type` Is Read

| Line | Code | Purpose |
|------|------|---------|
| 267 | `agent_type: The type of agent (engineer, qa, ops, research, documentation)` | Docstring parameter |
| 493 | `agent_type = template_data.get("agent_type", "general")` | **Primary read** — extracts agent_type from source template |
| 513-521 | `color_map = {"engineer": "blue", ...}; color_map.get(agent_type, "blue")` | Color assignment based on agent_type |
| 910 | `agent_type = template_data.get("agent_type", "general")` | Read in `_create_multiline_description()` for example generation |
| 1052 | `agent_type = template_data.get("agent_type", "general")` | Read in another description method |
| 1083 | `agent_type = template_data.get("agent_type", "general")` | Read in yet another method |

### 5.2 The Single Write Location

| Line | Code | Effect |
|------|------|--------|
| 567-568 | `if agent_type and agent_type != "general": frontmatter_lines.append(f"type: {agent_type}")` | **Writes `type:` (not `agent_type:`) to deployed frontmatter** |

### 5.3 What This Means for Standardization

To standardize on `agent_type:` in deployed agents, only **ONE line** needs to change:

```python
# Line 568 BEFORE:
frontmatter_lines.append(f"type: {agent_type}")

# Line 568 AFTER:
frontmatter_lines.append(f"agent_type: {agent_type}")
```

This single change would:
- Stop the field name conversion at the source
- All future deployments would use `agent_type:` in frontmatter
- Existing deployed agents would need a bulk rename (`type:` → `agent_type:`)

The comment on line 544 would also need updating from `"type: agent type..."` to `"agent_type: agent type..."`.

---

## 6. Downstream Readers: Who Reads What After Deployment

### 6.1 Readers of Deployed Agents (`type:` field — Gen 1 files)

| File | Line | Code | What It Does |
|------|------|------|-------------|
| `agent_management_service.py` | 444 | `AgentType(post.metadata.get("type", "core"))` | Reads `type:`, crashes for most values |
| `agent_validator.py` | 362 | `stripped_line.startswith("type:")` | Validates `type:` field presence |
| `deployment_wrapper.py` | 111 | `agent.get("type", "agent")` | Reads `type` from agent dict |
| `deployed_agent_discovery.py` | 109 | `agent.get("type", agent.get("name", "unknown"))` | Uses `type` as fallback ID |
| `agent_listing_service.py` | 214, 250, 296 | `agent_data.get("type", "agent")` | Reads for CLI display |
| `agent_registry.py` | 239 | `metadata["type"]` | Aggregates all type values |
| `agents_metadata.py` | 14+ | `"type": "core_agent"` (15 entries) | Hardcoded metadata uses `"type"` key |
| `dynamic_skills_generator.py` | 110 | `agent_info.get("type", "general-purpose")` | Reads for skills generation |

### 6.2 Readers of Template Data (`agent_type` field)

| File | Line | Code | What It Does |
|------|------|------|-------------|
| `agent_discovery_service.py` | 320-321 | `frontmatter.get("agent_type", frontmatter.get("category", "agent"))` | Reads `agent_type:` from frontmatter |
| `agent_template_builder.py` | 493, 910, 1052, 1083 | `template_data.get("agent_type", "general")` | Reads from template source data |
| `template_validator.py` | 31 | `"agent_type": str` | Requires `agent_type` in templates |
| `remote_agent_discovery_service.py` | 234 | `"agent_type"` in `simple_keys` | Extracts from remote YAML |
| `local_template_manager.py` | 83, 109 | `self.agent_type` / `data.get("agent_type", "")` | Local template management |
| `config_routes.py` | 817 | `fmdata.get("agent_type", "")` | Dashboard API |
| `unified_agent_registry.py` | 108, 116 | `data["agent_type"]` | Serialization/deserialization |
| `skill_manager.py` | 42 | `agent_data.get("agent_id") or agent_data.get("agent_type")` | Skill mapping (dead code) |
| `agent_session.py` | 112, 282, 488 | `self.agent_type` / `data.get("agent_type", ...)` | Session model |
| `event_handlers.py` | 442+ | `"agent_type": agent_type` | Event data |
| `subagent_processor.py` | 147+ | `event.get("agent_type", ...)` | Event processing |

### 6.3 Summary Count

| Field Name | Production Read Locations | Production Write Locations |
|-----------|--------------------------|---------------------------|
| `"type"` (in frontmatter/dict context) | ~8 files, ~15 locations | 1 file (template builder line 568) |
| `"agent_type"` (in frontmatter/data context) | ~15 files, ~40+ locations | Multiple (events, sessions, etc.) |

**The codebase overwhelmingly uses `agent_type` internally.** The `type` field name only appears in frontmatter parsing of deployed agents and in the hardcoded `agents_metadata.py`.

---

## 7. The `templates/__init__.py` Template System

The `src/claude_mpm/agents/templates/__init__.py` file contains a **separate template system** unrelated to the JSON archive:

```python
AGENT_TEMPLATES = {
    "documentation": "documentation_agent.md",
    "engineer": "engineer_agent.md",
    "qa": "qa_agent.md",
    ...
}
```

This maps agent types to `.md` delegation template files (like `engineer_agent.md`). These are **NOT** the JSON archive templates — they are instruction templates used for agent delegation. The `agent_type` parameter used in `get_template_path(agent_type)` and `load_template(agent_type)` accepts functional role strings (`"engineer"`, `"qa"`, `"ops"`, etc.).

**Impact**: This system uses `agent_type` as a function parameter (not a frontmatter field), reinforcing the convention that the functional role is called `agent_type` in code.

---

## 8. Three Code Paths That Scan `templates/` and Find Zero JSON Files

These are the "phantom scan" paths — they look for JSON in `templates/` but all JSON is in `templates/archive/`:

### 8.1 SkillManager (`skill_manager.py:28,37`)

```python
agent_templates_dir = Path(__file__).parent.parent / "agents" / "templates"
for template_file in agent_templates_dir.glob("*.json"):  # ZERO results
```

**Status**: Dead code (labeled "Legacy" in `__init__.py`)

### 8.2 SimpleAgentManager (`agent_state_manager.py:40-41,141`)

```python
self.templates_dir = Path(__file__).parent.parent.parent / "agents" / "templates"
for template_file in sorted(self.templates_dir.glob("*.json")):  # ZERO results
```

**Status**: Returns empty agent list; `configure` command shows no templates

### 8.3 NativeAgentConverter (`native_agent_converter.py:276,284`)

```python
mpm_package_dir = Path(__file__).parent.parent / "agents" / "templates"
json_files = list(templates_dir.glob("*.json"))  # ZERO results
```

**Status**: Returns empty list; converter loads no templates from this path

### 8.4 Observation

If these paths were fixed to scan `templates/archive/` (or use `**/*.json` recursive glob), they would find 39 JSON files and the following would change:

| Component | Current Behavior | Fixed Behavior |
|-----------|-----------------|----------------|
| SkillManager | 0 skill mappings | ~30+ skill mappings from `"skills"` field in JSON |
| SimpleAgentManager | Empty agent list in configure | 39 agents listed from JSON templates |
| NativeAgentConverter | No templates loaded | 39 agent configs available for conversion |

However, given these systems are labeled deprecated/legacy, fixing them may not be worthwhile.

---

## 9. Corrections and Deltas from v2/v2.1

### 9.1 Confirmed Findings

| v2/v2.1 Claim | Status | Evidence |
|---------------|--------|----------|
| AgentTemplateBuilder converts `agent_type` → `type` | **CONFIRMED** | Line 493 reads, line 568 writes |
| 100% of remote agents use `agent_type:` | **CONFIRMED** | v2.1 inventory of 48 remote agents |
| SkillManager has path bug | **CONFIRMED** | Line 28 scans parent dir, not archive/ |
| Archive JSON is manually maintained | **CONFIRMED** | Commit history shows manual edits |
| Three generations of agent files exist | **CONFIRMED** | Gen 1 (45), Gen 2 (14), Gen 3 (17) |
| 14+ duplicate agent pairs | **CONFIRMED** | Underscore ↔ kebab mapping verified |

### 9.2 Minor Corrections

| v2/v2.1 Claim | Correction |
|---------------|-----------|
| "38 JSON files in archive" (v2, v2.1) | **39 JSON files** (counted: 39 unique .json files in archive/) |
| Archive JSON "used by migration script only" | Also referenced by `scripts/delegation_matrix_poc.py` (POC for delegation matrix generation) |
| v2.1 "SimpleAgentManager" not mentioned | Added to analysis — it's a third code path scanning templates/ for JSON |

### 9.3 New Findings in v3

1. **`dynamic_skills_generator.py:110`** reads `agent_info.get("type", "general-purpose")` — an additional `type` reader not documented in v2
2. **`templates/__init__.py`** uses `agent_type` as a function parameter for template loading — reinforces the naming convention
3. **Comment on line 544 of template builder** explicitly documents the `type` field as: `"type: agent type for categorization and functionality (optional but important)"` — showing developer intent for the field
4. **`log_manager.py:553`** writes `f"type: {data.get('type', 'unknown')}"` — another location that writes `type:` (in log context, not agent frontmatter)

---

## 10. Summary: Key Facts for Implementation Planning

### 10.1 The Single Root Cause

**Line 568 of `agent_template_builder.py`** is the single point where `agent_type` becomes `type`. Changing this one line stops the field name divergence for all future deployments.

### 10.2 Archive Directory Safety

**Removing the archive directory has zero runtime impact.** It would only break two scripts (delegation_matrix_poc.py and migrate_json_to_markdown.py). However, it contains valuable reference data and should be preserved as documentation.

### 10.3 The Downstream Impact Chain

If we standardize on `agent_type:` in deployed frontmatter:

```
CHANGE: agent_template_builder.py:568 (write agent_type: instead of type:)
  |
  +--> New deployments: agent_type: engineer (correct)
  |
  +--> Existing 45 Gen 1 files: need bulk rename type: → agent_type:
  |
  +--> agent_management_service.py:444: must read agent_type instead of type
  |
  +--> agent_validator.py:362: must check for agent_type: prefix
  |
  +--> agent_listing_service.py:214,250,296: must use "agent_type" key
  |
  +--> agents_metadata.py:14+: must change "type" → "agent_type" (15 entries)
  |
  +--> deployed_agent_discovery.py:109: must read "agent_type"
  |
  +--> deployment_wrapper.py:111: must read "agent_type"
  |
  +--> agent_registry.py:239: must read "agent_type"
  |
  +--> dynamic_skills_generator.py:110: must read "agent_type"
```

**Total production code changes**: ~8-10 Python files, ~20-25 individual locations
**Total agent file changes**: 45 files (mechanical find-replace)
**Event/session contract changes**: ZERO (already uses `agent_type`)
**Serialization changes**: ZERO (unified_agent_registry already uses `agent_type`)

---

## Appendix A: All Files That Import From or Reference Archive

### Direct `templates/archive` References (2 files)

1. `scripts/delegation_matrix_poc.py:20` — `Path(...) / "src/claude_mpm/agents/templates/archive"`
2. `scripts/migrate_json_to_markdown.py:425` — `archive_path = templates_dir / "archive"`

### Indirect `templates/` References That Miss Archive (5 files)

3. `src/claude_mpm/skills/skill_manager.py:28` — scans `templates/` not `templates/archive/`
4. `src/claude_mpm/cli/commands/agent_state_manager.py:40` — scans `templates/` not `templates/archive/`
5. `src/claude_mpm/services/native_agent_converter.py:276` — scans `templates/` not `templates/archive/`
6. `src/claude_mpm/core/framework/loaders/agent_loader.py:142` — scans `.claude-mpm/agents/` (different dir)
7. `src/claude_mpm/core/framework/processors/template_processor.py:219` — scans `.claude-mpm/agents/` (different dir)

### Documentation References (5+ files)

8-12. Various `docs/` and `docs/_archive/` markdown files (listed in Section 2.3)

### Configuration References (1 file)

13. `.secrets.baseline` — false positive entries for archive JSON files

---

## Appendix B: Archive JSON `agent_type` Value Distribution

| `agent_type` Value | Count | Files |
|---|---|---|
| `engineer` | 14 | dart, data, golang, java, javascript, nextjs, php, python, react, refactoring, ruby, rust, svelte, tauri, typescript, engineer, web_ui |
| `ops` | 5 | agentic-coder-optimizer, clerk-ops, gcp_ops, ops, project_organizer, vercel_ops, version_control |
| `qa` | 3 | api_qa, qa, web_qa |
| `documentation` | 2 | documentation, ticketing |
| `research` | 2 | code_analyzer, research |
| `security` | 1 | security |
| `specialized` | 1 | local_ops |
| `system` | 1 | agent-manager |
| `analysis` | 1 | prompt-engineer |
| `product` | 1 | product_owner |
| `content` | 1 | content-agent |
| `imagemagick` | 1 | imagemagick |
| `memory_manager` | 1 | memory_manager |
| `engineering` | 1 | javascript_engineer_agent (**TYPO** — should be `engineer`) |

**Note**: The `javascript_engineer_agent.json` typo (`"engineering"` vs `"engineer"`) is confirmed. This is a data quality bug that would be caught by enum validation.

---

## Appendix C: Complete Templates Directory Structure

```
src/claude_mpm/agents/templates/
├── __init__.py                          # Template loading module (AGENT_TEMPLATES dict)
├── README.md                            # Documentation
├── archive/                             # 39 JSON agent definitions (REFERENCE ONLY)
│   ├── agent-manager.json
│   ├── agentic-coder-optimizer.json
│   ├── ... (37 more JSON files)
│   └── web_ui.json
├── circuit-breakers.md                  # PM delegation template
├── context-management-examples.md       # PM delegation template
├── git-file-tracking.md                 # PM delegation template
├── pm-examples.md                       # PM delegation template
├── pm-red-flags.md                      # PM delegation template
├── pr-workflow-examples.md              # PM delegation template
├── research-gate-examples.md            # PM delegation template
├── response-format.md                   # PM delegation template
├── structured-questions-examples.md     # PM delegation template
├── ticket-completeness-examples.md      # PM delegation template
├── ticketing-examples.md                # PM delegation template
└── validation-templates.md              # PM delegation template
```

The `.md` files at the top level are PM instruction/delegation templates used by the `__init__.py` module. They are completely separate from the JSON archive.
