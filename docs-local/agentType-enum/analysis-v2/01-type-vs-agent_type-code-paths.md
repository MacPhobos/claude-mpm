# Code Path Analysis: "type" vs "agent_type" Frontmatter Fields

**Date**: 2026-03-03
**Investigator**: Research Agent (Claude Opus 4.6)
**Branch**: `agenttype-enums`
**Task**: Trace complete code paths for "type" vs "agent_type" frontmatter field parsing

---

## 1. Executive Summary

The codebase has a **dual naming problem**: agent markdown files in `.claude/agents/` use **two different frontmatter field names** to express the same concept (functional role of the agent), and different code paths read different field names with no normalization layer between them. This creates a situation where:

- **Files using `type:`** are correctly parsed by `AgentManager` (the CRUD/API path) but **invisible** to `AgentDiscoveryService` (the deployment/discovery path).
- **Files using `agent_type:`** are correctly parsed by `AgentDiscoveryService` but **default to "core"** in `AgentManager`.
- **No file uses both fields simultaneously**.
- The `AgentTemplateBuilder` reads `agent_type` from JSON templates but **writes `type`** to frontmatter, creating an asymmetry between template source and deployed output.

---

## 2. Field Distribution in Agent Markdown Files

### Summary Counts

| Field Used | File Count | File Name Pattern |
|-----------|-----------|-------------------|
| `type:` | 48 files | Kebab-case names (e.g., `engineer.md`, `golang-engineer.md`) |
| `agent_type:` | 27 files | Underscore names (e.g., `golang_engineer.md`) or `-agent` suffix (e.g., `research-agent.md`) |
| **Both fields** | **0 files** | None |
| **Neither field** | 0 files | N/A |

### Correlation with File Naming Convention

The two field names correlate strongly with two distinct file naming conventions:

**Files using `type:`** (48 files): These follow the kebab-case Claude Code convention (e.g., `engineer.md`, `golang-engineer.md`, `rust-engineer.md`). These appear to be the "deployed" format produced by `AgentTemplateBuilder`.

**Files using `agent_type:`** (27 files): These follow either underscore naming (e.g., `golang_engineer.md`, `react_engineer.md`) or include an `-agent` suffix (e.g., `research-agent.md`, `qa-agent.md`). These appear to be a newer schema format with additional fields like `schema_version`, `agent_id`, `resource_tier`, `category`, `color`, `author`, `temperature`, `max_tokens`, `timeout`, `capabilities`, and `dependencies`.

**Implication**: There appear to be two **generations** of agent files coexisting in `.claude/agents/`. The older generation uses `type:` with minimal frontmatter; the newer generation uses `agent_type:` with rich metadata in a `schema_version: 1.3.0` format.

### Example: Old-style file (`engineer.md`) using `type:`

```yaml
---
name: engineer
description: "Use this agent when..."
type: engineer
version: "3.9.1"
skills:
- brainstorming
- dispatching-parallel-agents
---
```

### Example: New-style file (`golang_engineer.md`) using `agent_type:`

```yaml
---
name: Golang Engineer
description: 'Go 1.23-1.24 specialist...'
version: 1.0.0
schema_version: 1.3.0
agent_id: golang_engineer
agent_type: engineer
resource_tier: standard
tags:
- golang
- go
category: engineering
color: cyan
author: Claude MPM Team
temperature: 0.2
max_tokens: 4096
timeout: 900
capabilities:
  memory_limit: 2048
  cpu_limit: 50
  network_access: true
---
```

---

## 3. Code Path #1: AgentManager (CRUD/API Path) -- Reads `type:`

### Entry Point

**File**: `src/claude_mpm/services/agents/management/agent_management_service.py`
**Method**: `_parse_agent_markdown()` (line 435)
**Import**: `from claude_mpm.models.agent_definition import AgentType` (Enum 1)

### Parsing Logic (line 444)

```python
metadata = AgentMetadata(
    type=AgentType(post.metadata.get("type", "core")),
    ...
)
```

### What This Does

1. Uses `python-frontmatter` library to parse the YAML frontmatter
2. Reads the `"type"` key from frontmatter metadata
3. Falls back to `"core"` if `type:` is not present
4. Passes the string to `AgentType()` constructor (Enum 1: `models.agent_definition.AgentType`)

### Behavior Matrix

| File Has | Frontmatter Value | `post.metadata.get("type", "core")` Returns | `AgentType()` Result |
|----------|------------------|----------------------------------------------|---------------------|
| `type: engineer` | "engineer" | "engineer" | **ValueError** -- "engineer" not in Enum 1 |
| `type: ops` | "ops" | "ops" | **ValueError** -- "ops" not in Enum 1 |
| `type: core` | "core" | "core" | `AgentType.CORE` (success) |
| `type: system` | "system" | "system" | `AgentType.SYSTEM` (success) |
| `type: specialized` | "specialized" | "specialized" | `AgentType.SPECIALIZED` (success) |
| `agent_type: engineer` | N/A | **"core"** (default) | `AgentType.CORE` (wrong type!) |
| Neither field | N/A | "core" | `AgentType.CORE` |

**Critical Issues**:
1. For files with `type: engineer` (the majority), `AgentType("engineer")` raises `ValueError` because Enum 1 only contains `{core, project, custom, system, specialized}`.
2. For files with `agent_type: engineer`, the `type:` field is absent, so the default `"core"` is used -- the agent's functional role is **completely lost**.
3. The previous `_safe_parse_agent_type()` fallback (commit `854fb8f0`) appears to have been **reverted** -- the current code at line 444 does a direct `AgentType()` call with no error handling.

### Downstream Impact

This `AgentMetadata.type` flows to:
- **`AgentDefinition.to_dict()`** (line 177): Serializes as `metadata.type.value` -> appears in API responses
- **`_definition_to_markdown()`** (line 625): Writes `type: {definition.metadata.type.value}` back to frontmatter on save
- **`list_agents()`** (line 318): Returns `agent_def.metadata.type.value` as `"type"` in the agent listing
- **`update_agent()`** (line 153): Can set `agent_def.metadata.type` via updates dict

### Complete Call Chain

```
User/API request
    -> AgentManager.read_agent(name)
        -> AgentManager._find_agent_file(name) -> Path
        -> AgentManager._parse_agent_markdown(content, name, file_path)
            -> frontmatter.loads(content) -> post
            -> post.metadata.get("type", "core") -> type_str
            -> AgentType(type_str) -> ValueError if "engineer", "ops", etc.
            -> AgentMetadata(type=agent_type, ...) -> metadata
            -> AgentDefinition(..., metadata=metadata) -> definition
    -> return definition
        -> .to_dict() -> {"metadata": {"type": "core"}} for API responses
```

---

## 4. Code Path #2: AgentDiscoveryService (Deployment/Discovery Path) -- Reads `agent_type:`

### Entry Point

**File**: `src/claude_mpm/services/agents/deployment/agent_discovery_service.py`
**Method**: `_extract_metadata_from_template()` (line ~300)
**No AgentType enum import** -- stores as raw string

### Parsing Logic (lines 320-322)

```python
agent_info = {
    "type": frontmatter.get(
        "agent_type", frontmatter.get("category", "agent")
    ),
    ...
}
```

### What This Does

1. Manually extracts YAML frontmatter (not using `python-frontmatter` library)
2. Reads `"agent_type"` key first
3. Falls back to `"category"` key
4. Falls back to `"agent"` string as final default
5. Stores the value as a plain string in `agent_info["type"]` -- **no enum conversion**

### Behavior Matrix

| File Has | `frontmatter.get("agent_type", ...)` Returns |
|----------|---------------------------------------------|
| `agent_type: engineer` | "engineer" (correct) |
| `agent_type: ops` | "ops" (correct) |
| `type: engineer` (no `agent_type`) | Falls to `category` or "agent" (**wrong!**) |
| `type: core` (no `agent_type`) | Falls to `category` or "agent" (**wrong!**) |
| Both `type:` and `agent_type:` | N/A (never happens in practice) |

**Critical Issue**: This path only reads `agent_type:`, never `type:`. For the 48 files using `type:`, the functional role is lost and replaced with `category` (if present) or the default string `"agent"`.

### Downstream Impact

The `agent_info["type"]` flows to:
- Discovery service agent listings
- Deployment comparison logic
- Template matching and update detection

---

## 5. Code Path #3: AgentTemplateBuilder (JSON -> Markdown Conversion) -- Reads `agent_type`, Writes `type`

### Entry Point

**File**: `src/claude_mpm/services/agents/deployment/agent_template_builder.py`
**Multiple methods** use `template_data.get("agent_type", "general")`

### Key Conversion Points

**Line 493** (main build method):
```python
agent_type = template_data.get("agent_type", "general")
```

**Lines 566-568** (frontmatter output):
```python
# Add type field (important for agent categorization)
if agent_type and agent_type != "general":
    frontmatter_lines.append(f"type: {agent_type}")
```

**Line 910** (description creation):
```python
agent_type = template_data.get("agent_type", "general")
```

### What This Does

1. Reads `"agent_type"` from the JSON template source data
2. Uses the value for color mapping, description generation, and example creation
3. **Writes the value as `type:` in the output markdown frontmatter** (line 568)

### The Asymmetry

This creates a crucial **naming asymmetry**:

```
JSON template source:   "agent_type": "engineer"
                           |
                           v (AgentTemplateBuilder reads "agent_type")
                           |
Deployed MD frontmatter: type: engineer
                           |
                           v (AgentManager reads "type")
                           |
                        AgentType("engineer") -> ValueError!
```

So the template builder converts `agent_type` -> `type` during deployment, but the downstream `AgentManager` cannot parse the resulting `type: engineer` because Enum 1 doesn't include "engineer".

---

## 6. Code Path #4: UnifiedAgentRegistry (Discovery-Time Classification) -- NEVER reads frontmatter type

### Entry Point

**File**: `src/claude_mpm/core/unified_agent_registry.py`
**Method**: `_determine_agent_type()` (line 431)
**Import**: Uses its own `AgentType` (Enum 2)

### Classification Logic

```python
def _determine_agent_type(self, file_path: Path, tier: AgentTier) -> AgentType:
    if tier == AgentTier.PROJECT:
        return AgentType.PROJECT
    if tier == AgentTier.USER:
        return AgentType.USER_DEFINED
    if "templates" in path_str or "core" in path_str:
        return AgentType.CORE
    return AgentType.SPECIALIZED
```

### What This Does

This code path **completely ignores frontmatter**. It classifies agents based on:
- File system location (project dir vs user dir vs system dir)
- Path string matching ("templates", "core")
- Default to SPECIALIZED

Neither `type:` nor `agent_type:` from frontmatter is ever read by this system.

---

## 7. Code Path #5: Config Routes (Dashboard API) -- Reads `agent_type:` from frontmatter

### Entry Point

**File**: `src/claude_mpm/services/monitor/config_routes.py`
**Line 817**

### Parsing Logic

```python
"agent_type": fmdata.get("agent_type", ""),
```

### What This Does

Reads `agent_type:` directly from frontmatter for the dashboard detail API. Returns empty string for files that use `type:` instead.

**Impact**: Dashboard agent detail view shows `agent_type` field as empty for all 48 old-style files that use `type:`.

---

## 8. Code Path #6: DeployedAgentDiscovery (JSON Agent Loading) -- Reads `agent_type` from JSON

### Entry Point

**File**: `src/claude_mpm/services/agents/registry/deployed_agent_discovery.py`
**Line 193**

### Parsing Logic

```python
"id": json_data.get("agent_type", registry_info.get("type", "unknown")),
```

### What This Does

For JSON agent files, reads `agent_type` field, falling back to `type` from registry info. This path handles the local JSON template format, not markdown frontmatter.

---

## 9. Code Path #7: SkillManager -- Reads `agent_type` from agent data

### Entry Point

**File**: `src/claude_mpm/skills/skill_manager.py`
**Line 42**

### Parsing Logic

```python
agent_id = agent_data.get("agent_id") or agent_data.get("agent_type")
```

### What This Does

Uses `agent_type` as a fallback identifier for agents when `agent_id` is not present. This is used for skill-to-agent mapping.

---

## 10. Summary of All Code Paths

| Code Path | File | Reads | Expected Frontmatter Key | Enum Used | Handles Missing? |
|-----------|------|-------|------------------------|-----------|-----------------|
| AgentManager (CRUD) | `agent_management_service.py:444` | `type:` | `type` | Enum 1 (str, Enum) | Default "core" |
| AgentDiscoveryService | `agent_discovery_service.py:320` | `agent_type:` | `agent_type` | None (raw string) | Fallback to `category` then "agent" |
| AgentTemplateBuilder | `agent_template_builder.py:493,568` | JSON `agent_type` -> writes `type:` | N/A (writes) | None | Default "general" |
| UnifiedAgentRegistry | `unified_agent_registry.py:431` | **Nothing** (path-based) | N/A | Enum 2 (plain Enum) | N/A |
| Config Routes (Dashboard) | `config_routes.py:817` | `agent_type:` | `agent_type` | None (raw string) | Default "" |
| DeployedAgentDiscovery | `deployed_agent_discovery.py:193` | `agent_type` from JSON | `agent_type` (JSON) | None | Fallback to `type` |
| SkillManager | `skill_manager.py:42` | `agent_type` from data | `agent_type` (data) | None | Fallback to `agent_id` |
| _definition_to_markdown | `agent_management_service.py:625` | N/A (writes) | Writes `type:` | Enum 1 value | N/A |

---

## 11. The Critical Mismatch Diagram

```
                         JSON Templates
                    (.claude-mpm/cache/agents/)
                    Field: "agent_type": "engineer"
                              |
                              v
                    AgentTemplateBuilder
                    (reads "agent_type", writes "type:")
                              |
                              v
              Deployed Markdown (.claude/agents/)
              +-----------------+-------------------+
              |                 |                   |
              v                 v                   v
         AgentManager      AgentDiscovery      Config Routes
         reads: "type"     reads: "agent_type"  reads: "agent_type"
              |                 |                   |
              v                 v                   v
         "engineer" found   "agent_type" missing   "agent_type" missing
         -> ValueError!     -> fallback "agent"    -> returns ""
              |                 |                   |
              v                 v                   v
         BREAKS             WRONG TYPE            EMPTY TYPE
```

For new-style files (using `agent_type:`), the reverse happens:

```
              New-style Markdown (.claude/agents/)
              Field: "agent_type: engineer"
              +-----------------+-------------------+
              |                 |                   |
              v                 v                   v
         AgentManager      AgentDiscovery      Config Routes
         reads: "type"     reads: "agent_type"  reads: "agent_type"
              |                 |                   |
              v                 v                   v
         "type" missing     "engineer" found     "engineer" found
         -> default "core"  -> correct!          -> correct!
              |                 |                   |
              v                 v                   v
         WRONG TYPE (core)  CORRECT              CORRECT
```

---

## 12. Key Findings

### Finding 1: Two field names, zero overlap
No agent file uses both `type:` and `agent_type:` simultaneously. The two naming conventions are mutually exclusive and correlate with two distinct file generations.

### Finding 2: No normalization layer exists
There is no code that normalizes `type:` and `agent_type:` into a single field before consumption. Each code path independently decides which field to read.

### Finding 3: The template builder creates the mismatch
`AgentTemplateBuilder` reads `agent_type` from JSON but writes `type:` to markdown. Since `AgentDiscoveryService` then reads `agent_type:` (not `type:`) from the deployed markdown, the template builder's output is invisible to the discovery service.

### Finding 4: AgentManager's Enum 1 is broken for 46/48 agents
Line 444's `AgentType(post.metadata.get("type", "core"))` will raise `ValueError` for any agent with `type: engineer`, `type: ops`, etc. The safe fallback appears to have been reverted.

### Finding 5: Claude Code (the platform) does not read either field
Based on analysis of the `FrontmatterValidator` (which validates `name`, `description`, `tools`, and `model` only), Claude Code the platform does not use `type:` or `agent_type:` for any platform-level functionality. These fields are purely for claude-mpm's internal use. Claude Code's required frontmatter fields are: `name`, `description`, and `tools` (per `REQUIRED_FIELDS` in `frontmatter_validator.py`).

### Finding 6: Semantic equivalence
Both `type:` and `agent_type:` carry the same semantic meaning: the functional role of the agent (engineer, ops, qa, etc.). There is no intentional distinction between them -- the divergence is accidental, arising from two different code paths (template builder output vs newer schema format).

---

## 13. Recommendations

### Immediate (Pre-Consolidation)

1. **Add normalization to all read paths**: Every code path that reads frontmatter should check BOTH fields:
   ```python
   agent_type = frontmatter.get("type") or frontmatter.get("agent_type") or "core"
   ```

2. **Restore safe parsing in AgentManager**: Line 444 needs error handling for unknown AgentType values to prevent ValueError crashes.

### For Enum Consolidation

3. **Standardize on one field name**: Choose either `type` or `agent_type` and migrate all files to use it consistently. `type` is the shorter, more natural choice and is what Claude Code's frontmatter convention uses for other purpose-specific fields.

4. **The consolidated enum must include frontmatter values**: Whichever enum design is chosen (Option A, B, C, or D from the problem analysis), it must accept values like "engineer", "ops", "qa" that actually appear in frontmatter.

---

## Appendix: Files Referenced

| File | Key Lines | Role |
|------|-----------|------|
| `src/claude_mpm/services/agents/management/agent_management_service.py` | 444, 625, 318 | Reads `type:`, writes `type:`, lists agents |
| `src/claude_mpm/services/agents/deployment/agent_discovery_service.py` | 320-322 | Reads `agent_type:`, falls back to `category` |
| `src/claude_mpm/services/agents/deployment/agent_template_builder.py` | 493, 566-568, 910 | Reads JSON `agent_type`, writes `type:` |
| `src/claude_mpm/core/unified_agent_registry.py` | 431-448 | Path-based classification, ignores frontmatter |
| `src/claude_mpm/services/monitor/config_routes.py` | 817 | Reads `agent_type:` for dashboard |
| `src/claude_mpm/services/agents/registry/deployed_agent_discovery.py` | 193 | Reads `agent_type` from JSON |
| `src/claude_mpm/skills/skill_manager.py` | 42 | Reads `agent_type` as fallback ID |
| `src/claude_mpm/models/agent_definition.py` | 25-36, 99, 177 | Enum 1 definition, AgentMetadata.type field |
| `src/claude_mpm/core/unified_agent_registry.py` | 52-59, 75, 108, 116 | Enum 2 definition, AgentMetadata.agent_type field |
| `src/claude_mpm/validation/frontmatter_validator.py` | 47 | REQUIRED_FIELDS = {name, description, tools} |
| `.claude/agents/*.md` | frontmatter | 48 files use `type:`, 27 files use `agent_type:` |
| `src/claude_mpm/agents/templates/archive/*.json` | top-level | JSON templates use `agent_type` |
