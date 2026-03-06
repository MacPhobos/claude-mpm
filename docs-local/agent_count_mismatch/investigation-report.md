# Dashboard Agent Count Mismatch - Investigation Report

**Date**: 2026-03-02
**Investigator**: Research Agent (Claude Opus 4.6)
**Branch**: `dashboard-v2-agent-scope`
**Status**: Root cause identified

---

## Executive Summary

The dashboard Config tab shows 2 deployed agents instead of the expected 48. The root cause is a **strict `AgentType` enum validation** in `AgentManager._parse_agent_markdown()` that silently rejects 46 out of 48 agent files because they have non-standard `type` frontmatter values (e.g., "engineer", "ops", "qa") that are not members of the `AgentType` enum (which only accepts "core", "project", "custom", "system", "specialized").

This is NOT caused by the `DeploymentContext` refactor in commit `bc9418c4`. The bug is a **pre-existing mismatch** between the agent frontmatter schema used by the deployment pipeline and the `AgentType` enum used by `AgentManager`.

---

## 1. HAR File Analysis

### Endpoints Called

The HAR file (`/Users/mac/Downloads/localhost.har`) captured 13 requests from the dashboard UI at `http://localhost:5173`:

| # | Endpoint | Status | Size | Notes |
|---|----------|--------|------|-------|
| 0 | `/api/config/validate` | 200 | 76KB | 207 validation issues |
| 1 | `/api/config/project/summary` | 200 | 221B | Shows deployed: 2, available: 48 |
| 2 | `/api/config/agents/deployed` | 200 | 2KB | **Returns only 2 agents** |
| 3 | `/api/config/sources` | 200 | 491B | 3 sources (1 agent, 2 skill) |
| 7 | `/api/config/agents/available` | 200 | 95KB | Returns all 48 agents correctly |
| 8 | `/api/config/skills/deployed` | 200 | 93KB | Skills working correctly |

### Key Response: `/api/config/agents/deployed`

```json
{
  "success": true,
  "scope": "project",
  "agents": [
    {
      "name": "mpm-agent-manager",
      "type": "system",
      "is_core": true
    },
    {
      "name": "local-ops",
      "type": "specialized",
      "is_core": false
    }
  ],
  "total": 2
}
```

Only `mpm-agent-manager` (type: "system") and `local-ops` (type: "specialized") are returned.

### Key Response: `/api/config/project/summary`

```json
{
  "data": {
    "deployment_mode": "selective",
    "agents": { "deployed": 2, "available": 48 }
  }
}
```

### Cascading Effect on Validation

The `/api/config/validate` endpoint returns 205 agent-related issues, all stating skills are "not referenced by any agent" -- because the validation service only sees 2 agents instead of 48. This is a secondary symptom of the same root cause.

---

## 2. Actual Agent Count

The `.claude/agents/` directory contains **48 markdown files**:

```
$ ls /Users/mac/workspace/claude-mpm-fork/.claude/agents/*.md | wc -l
48
```

The `.mpm_deployment_state` file correctly records:
```json
{ "agent_count": 48 }
```

All files were last modified on **March 1, 2026** (deployed around the same time as commit `bc9418c4`).

### Agent Type Distribution (from frontmatter)

| Frontmatter Type | Count | Valid `AgentType` Enum? |
|-----------------|-------|------------------------|
| engineer | 20 | NO |
| ops | 10 | NO |
| qa | 4 | NO |
| documentation | 2 | NO |
| research | 2 | NO |
| analysis | 1 | NO |
| claude-mpm | 1 | NO |
| content | 1 | NO |
| imagemagick | 1 | NO |
| memory_manager | 1 | NO |
| product | 1 | NO |
| refactoring | 1 | NO |
| security | 1 | NO |
| **specialized** | **1** | **YES** (local-ops) |
| **system** | **1** | **YES** (mpm-agent-manager) |
| **TOTAL** | **48** | **2 valid** |

---

## 3. Commit Analysis

### Commit `da5e7c28` (Feb 28) - Dashboard UI Introduction

Introduced the Config tab with 6 GET endpoints including `/api/config/agents/deployed`.
The `handle_agents_deployed` handler calls `AgentManager.list_agents(location="project")`.

### Commit `bc9418c4` (Mar 1) - DeploymentContext Refactor

Changed `_get_agent_manager()` from:
```python
# Old (da5e7c28)
def _get_agent_manager(project_dir=None):
    agents_dir = project_dir or (Path.cwd() / ".claude" / "agents")
    _agent_manager = AgentManager(project_dir=agents_dir)
```

To:
```python
# New (bc9418c4)
def _get_agent_manager(scope="project"):
    ctx = DeploymentContext.from_project()
    _agent_managers[scope] = AgentManager(project_dir=ctx.agents_dir)
```

**Both resolve to the same path**: `Path.cwd() / ".claude" / "agents"`. The `DeploymentContext.from_project()` uses `Path.cwd()` as the project path, and `resolve_agents_dir(PROJECT, path)` returns `path / ".claude" / "agents"`.

**The `AgentManager` code was NOT changed** in `bc9418c4` -- no diff in `agent_management_service.py`.

### Commits After `da5e7c28` (none relevant to this bug)

```
a48f2369 style: fix ruff formatting issues pre-publish
4ea3111a style: fix import ordering in startup_display.py
a08353a0 chore: update uv.lock for v5.9.43
dbc89c19 bump: version 5.9.42 -> 5.9.43
8765edaa chore: update uv.lock
db4ead41 test: follow-up hardening from PR #325 review
77bc423b fix: test case stability corrections (PR #325)
57558f69 bump: version 5.9.41 -> 5.9.42
92f00c51 chore: ignore ENHANCED_*.md planning artifacts
a88a23cc fix: critical cwd bug - stale CLAUDE_MPM_USER_PWD
f0eae187 chore: ignore docs-local/ AI planning artifacts
bc9418c4 feat: DeploymentContext scope-aware abstraction (#322)
0e32a361 fix: clean stale hook paths from all settings files (#324)
ffdbf9a8 fix: add quotes around package extras for zsh
```

None of these commits modify `AgentManager._parse_agent_markdown()` or the `AgentType` enum.

---

## 4. Root Cause: Strict `AgentType` Enum Validation

### The Failure Chain

```
handle_agents_deployed()
  -> _get_agent_manager("project")
    -> AgentManager(project_dir=".claude/agents")
  -> agent_mgr.list_agents(location="project")
    -> for each .md file:
      -> _build_agent_entry(file, name, "project")
        -> self.read_agent(name)
          -> self._parse_agent_markdown(content, name, path)
            -> AgentType(post.metadata.get("type", "core"))
               ^^ RAISES ValueError for "engineer", "ops", etc.
          -> CAUGHT by except block, returns None
        -> returns None (agent silently skipped)
```

### Specific Code Locations

**File**: `src/claude_mpm/models/agent_definition.py`, line 25-36
```python
class AgentType(str, Enum):
    CORE = "core"
    PROJECT = "project"
    CUSTOM = "custom"
    SYSTEM = "system"
    SPECIALIZED = "specialized"
```

**File**: `src/claude_mpm/services/agents/management/agent_management_service.py`, line 444
```python
metadata = AgentMetadata(
    type=AgentType(post.metadata.get("type", "core")),  # <-- FAILS HERE
    ...
)
```

**File**: `src/claude_mpm/services/agents/management/agent_management_service.py`, lines 122-128
```python
try:
    content = agent_path.read_text(encoding="utf-8")
    return self._parse_agent_markdown(content, name, str(agent_path))
except Exception as e:
    logger.error(f"Error reading agent '{name}': {e}")
    return None  # <-- SILENTLY RETURNS NONE
```

### Verification

```python
>>> from enum import Enum
>>> class AgentType(str, Enum):
...     CORE = "core"
...     SYSTEM = "system"
...     SPECIALIZED = "specialized"
...
>>> AgentType("engineer")
ValueError: 'engineer' is not a valid AgentType
```

Only 2 of 48 agents have valid type values:
- `mpm-agent-manager.md`: type = "system" (VALID)
- `local-ops.md`: type = "specialized" (VALID)

---

## 5. Why the Available Agents Endpoint Returns 48

The `/api/config/agents/available` endpoint uses a completely different code path:

```python
async def handle_agents_available(request):
    git_mgr = _get_git_source_manager()
    agents = git_mgr.list_cached_agents()  # Reads from git cache
```

`GitSourceManager.list_cached_agents()` reads agent metadata from cached git repository files without going through `AgentType` enum validation. It extracts metadata differently and does not attempt to construct `AgentMetadata` objects.

Similarly, `AgentManager.list_agent_names()` (line 265) just globs `*.md` files and returns stems -- it does NOT parse frontmatter at all. This method would correctly return 48 names.

---

## 6. Devil's Advocate Analysis

### Alternative Explanation 1: CWD / Path Resolution Issue

**Hypothesis**: The dashboard daemon's `Path.cwd()` points to the wrong directory, so `AgentManager` looks in the wrong `.claude/agents/` folder.

**Evidence Against**: The HAR response includes full file paths for the 2 returned agents:
```json
"path": "/Users/mac/workspace/claude-mpm-fork/.claude/agents/mpm-agent-manager.md"
```
This confirms the correct project directory is being used. If CWD were wrong, zero agents would be found.

**Verdict**: REJECTED. Path resolution is correct.

### Alternative Explanation 2: File Permissions / Read Errors

**Hypothesis**: Some agent files have incorrect permissions, causing read failures.

**Evidence Against**: All 48 files have identical permissions (`-rw-r--r--`) and ownership. The files are readable.

**Verdict**: REJECTED. File permissions are uniform.

### Alternative Explanation 3: `DeploymentContext` Broke Path Resolution

**Hypothesis**: The `bc9418c4` commit changed how paths are resolved, causing a directory mismatch.

**Evidence Against**:
- Old code: `Path.cwd() / ".claude" / "agents"`
- New code: `DeploymentContext.from_project().agents_dir` = `resolve_agents_dir(PROJECT, Path.cwd())` = `Path.cwd() / ".claude" / "agents"`
- Both resolve to the identical path.
- The HAR confirms agents ARE being found in the correct directory (2 are returned).

**Verdict**: REJECTED. Path resolution is identical.

### Alternative Explanation 4: Agent Files Have Corrupt Frontmatter

**Hypothesis**: Some agent files have malformed YAML frontmatter.

**Evidence Against**: All 48 files parse successfully with `python-frontmatter`:
```python
import frontmatter
for f in agents_dir.glob("*.md"):
    post = frontmatter.load(str(f))  # All succeed
```
The frontmatter is valid YAML. The issue is that `type` values are domain-specific strings, not `AgentType` enum members.

**Verdict**: PARTIALLY VALID. The frontmatter IS valid YAML, but the `type` field values are not valid `AgentType` enum members.

### Alternative Explanation 5: The Dashboard Never Worked Correctly

**Hypothesis**: The agent count was always wrong since the Config tab was introduced.

**Evidence**: This is likely the case. The `AgentType` enum and the strict parsing in `_parse_agent_markdown` pre-date the dashboard. The agents in the repository have always used free-form type strings ("engineer", "ops", etc.). The dashboard Config tab (introduced `da5e7c28`) was the first feature to call `AgentManager.list_agents()` to enumerate deployed agents.

**Verdict**: LIKELY TRUE. The dashboard Config tab has probably never shown the correct deployed count for agents with non-standard type values. The user may have recently deployed all 48 agents (March 1), making the discrepancy obvious for the first time.

---

## 7. Additional Issues Discovered

### 7.1 Silent Error Swallowing

The `read_agent()` method catches ALL exceptions and returns `None`:
```python
except Exception as e:
    logger.error(f"Error reading agent '{name}': {e}")
    return None
```

While errors are logged, the caller (`_build_agent_entry`) silently skips the agent. The dashboard provides no indication that agents failed to parse, making this bug invisible to users.

### 7.2 Cascading Validation Errors

Because only 2 agents are visible, the `/api/config/validate` endpoint reports 205 false-positive issues about skills not being referenced by any agent. These are noise caused by the underlying count mismatch.

### 7.3 Inconsistent Type Schema

The deployment pipeline (`configure.py` -> `_deploy_single_agent`) copies agent files verbatim from the git source cache via `shutil.copy2()`. The source agents use free-form type strings. The `AgentType` enum was designed for a different classification scheme and is never enforced during deployment.

### 7.4 `_ctx` Not Used in `handle_agents_deployed`

In `config_routes.py` line 341, the scope context is validated but discarded:
```python
scope_str, _ctx, err = _validate_get_scope(request)
```
The `_ctx` (underscore prefix = intentionally unused) is created but not passed to `_get_agent_manager`. Instead, `_get_agent_manager("project")` creates its own `DeploymentContext` internally. This is architecturally inconsistent, though not the cause of this bug.

---

## 8. Suggested Fix

### Option A: Make `AgentType` Gracefully Accept Unknown Values (Recommended)

**File**: `src/claude_mpm/services/agents/management/agent_management_service.py`, line 444

```python
# Before (strict):
type=AgentType(post.metadata.get("type", "core")),

# After (graceful):
type=self._parse_agent_type(post.metadata.get("type", "core")),
```

Add helper method:
```python
@staticmethod
def _parse_agent_type(type_str: str) -> AgentType:
    """Parse agent type string, falling back to CUSTOM for unknown values."""
    try:
        return AgentType(type_str)
    except ValueError:
        return AgentType.CUSTOM
```

**Pros**: Minimal change, backward compatible, all agents become visible
**Cons**: Loses original type information (maps to "custom")

### Option B: Expand `AgentType` Enum

**File**: `src/claude_mpm/models/agent_definition.py`

Add all observed type values to the enum:
```python
class AgentType(str, Enum):
    CORE = "core"
    PROJECT = "project"
    CUSTOM = "custom"
    SYSTEM = "system"
    SPECIALIZED = "specialized"
    ENGINEER = "engineer"
    OPS = "ops"
    QA = "qa"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    SECURITY = "security"
    CONTENT = "content"
    ANALYSIS = "analysis"
    PRODUCT = "product"
    # ... etc.
```

**Pros**: Preserves type information, type-safe
**Cons**: Must be kept in sync with agent repository, fragile

### Option C: Remove `AgentType` Enum from Parse Path (Best Long-Term)

Store the type as a plain string in `AgentMetadata` instead of an enum:

```python
@dataclass
class AgentMetadata:
    type: str  # Was: AgentType
    # ... rest unchanged
```

**Pros**: Fully flexible, no maintenance burden
**Cons**: Loses type safety for the 5 original types

### Recommendation

**Option A** for an immediate fix (one-line change + 5-line helper).
**Option C** for the long-term architecture, as the deployment pipeline already treats types as free-form strings.

---

## 9. Files and Locations Referenced

| File | Lines | Role |
|------|-------|------|
| `src/claude_mpm/models/agent_definition.py` | 25-36 | `AgentType` enum definition |
| `src/claude_mpm/services/agents/management/agent_management_service.py` | 291-340 | `list_agents()` method |
| `src/claude_mpm/services/agents/management/agent_management_service.py` | 435-497 | `_parse_agent_markdown()` with strict enum |
| `src/claude_mpm/services/agents/management/agent_management_service.py` | 106-128 | `read_agent()` with silent error swallowing |
| `src/claude_mpm/services/monitor/config_routes.py` | 339-397 | `handle_agents_deployed()` handler |
| `src/claude_mpm/services/monitor/config_routes.py` | 36-55 | `_get_agent_manager()` singleton factory |
| `src/claude_mpm/core/deployment_context.py` | 40-47 | `DeploymentContext.from_project()` |
| `src/claude_mpm/core/config_scope.py` | 52-65 | `resolve_agents_dir()` |
| `.claude/agents/*.md` | frontmatter | Agent files with non-standard types |
| `.claude/agents/.mpm_deployment_state` | all | Correct count (48) |

---

## 10. Summary

| Question | Answer |
|----------|--------|
| What does the HAR reveal? | 2 deployed agents returned; 48 available; 205 cascading validation issues |
| What changed in the commits? | `bc9418c4` refactored path resolution (no functional change to agent parsing) |
| Root cause? | `AgentType` enum rejects 46/48 agent types; errors silently swallowed |
| Which commit broke it? | No specific commit -- the enum/agent type mismatch pre-dates the dashboard |
| Suggested fix? | Graceful fallback in `_parse_agent_type()` (Option A) or remove enum (Option C) |
| Additional issues? | Silent error swallowing, cascading validation noise, unused `_ctx` variable |

---

## Impact Analysis: AgentType Usage Across Codebase

**Date**: 2026-03-02
**Scope**: Complete enumeration of every `AgentType` reference across all Python source, Svelte frontend, and test files.

### Critical Finding: TWO Separate `AgentType` Enums Exist

The codebase contains **three distinct `AgentType` enum definitions** in different modules. They have **different members** and serve **different purposes**, creating a fragmented type system.

| # | Location | Members | Purpose |
|---|----------|---------|---------|
| 1 | `src/claude_mpm/models/agent_definition.py:25` | core, project, custom, system, specialized | AgentManager markdown parsing (dashboard API) |
| 2 | `src/claude_mpm/core/unified_agent_registry.py:52` | core, specialized, user_defined, project, memory_aware | UnifiedAgentRegistry discovery & filtering |
| 3 | `tests/eval/agents/shared/agent_response_parser.py:37` | base, research, engineer, qa, ops, documentation, prompt_engineer, pm | Test eval framework response analysis |

Enum #1 and Enum #2 are **both imported as `AgentType`** from different modules depending on the consumer. They share some member names ("core", "specialized", "project") but have different additional members. This is a design-time fragmentation that compounds the runtime mismatch with agent frontmatter.

---

### Usage #1: `AgentManager._parse_agent_markdown()` (CRITICAL)

| Field | Value |
|-------|-------|
| **File** | `src/claude_mpm/services/agents/management/agent_management_service.py` |
| **Line** | 444 |
| **Function** | `_parse_agent_markdown()` |
| **Enum Used** | `models.agent_definition.AgentType` (5 members) |
| **Strict Validation?** | YES -- `AgentType(type_str)` raises `ValueError` |
| **Impact if Fails** | Agent is silently skipped (returns `None` via `read_agent()` catch-all) |
| **Failure Caught?** | Yes, by `read_agent()` at line 126 -- but silently returns `None` |
| **Severity** | **CRITICAL** -- This is the root cause of the dashboard showing 2/48 agents |

```python
# Line 444
type=AgentType(post.metadata.get("type", "core")),
```

46 of 48 agents have frontmatter type values not in the enum. Every one raises `ValueError`, caught at line 126, returned as `None`, silently skipped by `list_agents()`.

---

### Usage #2: `AgentDefinition.to_dict()` -- Serialization

| Field | Value |
|-------|-------|
| **File** | `src/claude_mpm/models/agent_definition.py` |
| **Line** | 177 |
| **Function** | `AgentDefinition.to_dict()` |
| **Enum Used** | `models.agent_definition.AgentType` (via `self.metadata.type.value`) |
| **Strict Validation?** | No -- reads `.value` from already-constructed enum |
| **Impact if Fails** | N/A -- only called on successfully parsed agents |
| **Failure Caught?** | N/A |
| **Severity** | **NONE** -- downstream of Usage #1; only runs on the 2 valid agents |

```python
# Line 177
"type": self.metadata.type.value,
```

This serializes the enum to its string value for API responses. It can only be called on agents that survived the parse step, so it always succeeds. However, it means the API only ever returns `"system"` or `"specialized"` as type values.

---

### Usage #3: `AgentManager._definition_to_markdown()` -- Write Path

| Field | Value |
|-------|-------|
| **File** | `src/claude_mpm/services/agents/management/agent_management_service.py` |
| **Lines** | 625, 723 |
| **Function** | `_definition_to_markdown()` |
| **Enum Used** | `models.agent_definition.AgentType` (via `.type.value`) |
| **Strict Validation?** | No -- reads `.value` from already-constructed enum |
| **Impact if Fails** | N/A -- only called on valid `AgentDefinition` objects |
| **Failure Caught?** | N/A |
| **Severity** | **LOW** -- Write path only produces enum-valid type values |

```python
# Line 625
"type": definition.metadata.type.value,
# Line 723
content.append(f"**Agent Type**: {definition.metadata.type.value}")
```

When writing agent markdown, this always outputs one of the 5 enum values. If an agent was created through `AgentManager`, it will have a valid type. But agents deployed via `shutil.copy2()` from git cache bypass this path entirely, preserving their original free-form type strings.

---

### Usage #4: `AgentDefinitionFactory.create_agent_definition()` -- Lifecycle Manager

| Field | Value |
|-------|-------|
| **File** | `src/claude_mpm/services/agents/deployment/agent_definition_factory.py` |
| **Lines** | 49-57 |
| **Function** | `create_agent_definition()` |
| **Enum Used** | `models.agent_definition.AgentType` |
| **Strict Validation?** | No -- uses `type_map.get(tier, AgentType.CUSTOM)` lookup |
| **Impact if Fails** | Falls back gracefully to `AgentType.CUSTOM` |
| **Failure Caught?** | Yes -- `.get()` default handles unknown tiers |
| **Severity** | **NONE** -- Graceful fallback implemented here (ironically not in the parser) |

```python
type_map = {
    ModificationTier.USER: AgentType.CUSTOM,
    ModificationTier.PROJECT: AgentType.PROJECT,
    ModificationTier.SYSTEM: AgentType.SYSTEM,
}
type=type_map.get(tier, AgentType.CUSTOM),  # Safe fallback
```

This factory correctly uses a dictionary lookup with a default, avoiding the strict enum construction that breaks `_parse_agent_markdown()`. This pattern is exactly what should be adopted in the parser.

---

### Usage #5: `AgentManager.list_agents()` -- API Response Builder

| Field | Value |
|-------|-------|
| **File** | `src/claude_mpm/services/agents/management/agent_management_service.py` |
| **Line** | 318 |
| **Function** | `list_agents()` -> `_build_agent_entry()` |
| **Enum Used** | `models.agent_definition.AgentType` (via `agent_def.metadata.type.value`) |
| **Strict Validation?** | No -- reads from already-parsed `AgentDefinition` |
| **Impact if Fails** | N/A -- only called on successfully parsed agents |
| **Failure Caught?** | N/A |
| **Severity** | **NONE** (direct), **CRITICAL** (indirect -- receives only 2 agents due to Usage #1) |

```python
"type": agent_def.metadata.type.value,
```

The value serialization itself never fails. But because `read_agent()` returns `None` for 46/48 agents (Usage #1), `_build_agent_entry()` returns `None`, and `list_agents()` skips those agents. The API response is thus incomplete.

---

### Usage #6: `UnifiedAgentRegistry.AgentType` -- Separate Enum

| Field | Value |
|-------|-------|
| **File** | `src/claude_mpm/core/unified_agent_registry.py` |
| **Lines** | 52-59, 116, 431-448, 600, 645, 675, 679, 687 |
| **Functions** | `_determine_agent_type()`, `_discover_memory_integration()`, `list_agents()`, etc. |
| **Enum Used** | `unified_agent_registry.AgentType` (5 DIFFERENT members) |
| **Strict Validation?** | Line 116: YES -- `AgentType(data["agent_type"])` in `from_dict()` |
| **Impact if Fails** | `from_dict()` raises `ValueError` when importing registry data |
| **Failure Caught?** | Not directly -- caller must handle |
| **Severity** | **MODERATE** -- `from_dict()` deserialization can fail; `_determine_agent_type()` is safe |

This is a **completely separate `AgentType` enum** with different members:
```python
class AgentType(Enum):
    CORE = "core"
    SPECIALIZED = "specialized"
    USER_DEFINED = "user_defined"  # Not in models enum
    PROJECT = "project"
    MEMORY_AWARE = "memory_aware"  # Not in models enum
```

Key usage points within `unified_agent_registry.py`:

| Line | Function | Strict? | Risk |
|------|----------|---------|------|
| 116 | `AgentMetadata.from_dict()` | YES | Fails on import if `agent_type` not in enum |
| 431-448 | `_determine_agent_type()` | NO | Safe -- uses if/else, always returns valid enum |
| 600 | `_discover_memory_integration()` | NO | Safe -- assigns `AgentType.MEMORY_AWARE` directly |
| 645, 675, 679, 687 | `list_agents()` filters | NO | Safe -- compares against known enum values |

The `from_dict()` at line 116 is the risky path. If a serialized registry JSON contains an `agent_type` value that is not in this enum (e.g., if someone serialized `"custom"` from the models enum, or `"engineer"` from frontmatter), deserialization would fail.

---

### Usage #7: `agent_registry.py` Compatibility Layer

| Field | Value |
|-------|-------|
| **File** | `src/claude_mpm/core/agent_registry.py` |
| **Lines** | 27, 179, 782 |
| **Functions** | `list_agents_filtered()`, module-level `list_agents()` |
| **Enum Used** | `unified_agent_registry.AgentType` (imported from unified) |
| **Strict Validation?** | Mixed |
| **Impact if Fails** | Filtering silently returns no results |
| **Failure Caught?** | Partially |
| **Severity** | **MODERATE** |

**Line 179** (`SimpleAgentRegistry.list_agents_filtered()`):
```python
if agent_type:
    try:
        unified_agent_type = AgentType(agent_type)
    except ValueError:
        # Handle legacy agent types
        unified_agent_type = None
```
This correctly catches `ValueError` and gracefully falls back to `None` (no type filter). This is proper defensive coding.

**Line 782** (module-level `list_agents()` function):
```python
if agent_type:
    with contextlib.suppress(ValueError):
        unified_agent_type = AgentType(agent_type)
```
Also handles `ValueError` gracefully via `contextlib.suppress`. If the type string is invalid, `unified_agent_type` stays `None` and no type filter is applied.

Both of these compatibility functions handle the enum mismatch correctly. However, if a caller passes `"engineer"` as `agent_type`, the filter is silently ignored (returns all agents instead of filtering).

---

### Usage #8: `services/agents/registry/__init__.py` -- Re-export

| Field | Value |
|-------|-------|
| **File** | `src/claude_mpm/services/agents/registry/__init__.py` |
| **Line** | 6 |
| **Function** | Module re-export |
| **Enum Used** | `unified_agent_registry.AgentType` |
| **Strict Validation?** | N/A (just re-exports) |
| **Impact if Fails** | N/A |
| **Severity** | **NONE** |

```python
from claude_mpm.core.unified_agent_registry import (
    AgentType,
    ...
)
```

This re-exports the **unified** `AgentType` (not the models one). Consumers importing from `services.agents.registry` get the unified enum. Consumers importing from `models` or `models.agent_definition` get the models enum. This creates import confusion.

---

### Usage #9: `services/agents/__init__.py` -- Another Re-export

| Field | Value |
|-------|-------|
| **File** | `src/claude_mpm/services/agents/__init__.py` |
| **Line** | 44, 69 |
| **Function** | Module re-export |
| **Enum Used** | Re-exports from `registry` (which is the unified enum) |
| **Severity** | **NONE** (re-export only) |

---

### Usage #10: Test Eval Framework -- Third `AgentType` Enum

| Field | Value |
|-------|-------|
| **File** | `tests/eval/agents/shared/agent_response_parser.py` |
| **Line** | 37-47 |
| **Functions** | Parser, metrics, test base classes |
| **Enum Used** | Own `AgentType` (8 members: base, research, engineer, qa, ops, documentation, prompt_engineer, pm) |
| **Strict Validation?** | Line 199: YES -- `AgentType(agent_type)` |
| **Impact if Fails** | Test assertion failure |
| **Failure Caught?** | No -- would raise `ValueError` in test context |
| **Severity** | **LOW** -- Only affects test eval framework, not production |

```python
class AgentType(str, Enum):
    BASE = "base"
    RESEARCH = "research"
    ENGINEER = "engineer"
    QA = "qa"
    OPS = "ops"
    DOCUMENTATION = "documentation"
    PROMPT_ENGINEER = "prompt_engineer"
    PM = "pm"
```

Ironically, **this test enum has the values that actually match the agent frontmatter** (engineer, ops, qa, etc.) -- the values that the production `models.AgentType` enum rejects. The test framework was designed around the real agent types, while the production model was designed around an abstract classification scheme.

**Used extensively in**: `agent_test_base.py`, `agent_metrics.py`, `test_agent_infrastructure.py`, `agent_fixtures.py`, `conftest.py`. All usages are within the test eval framework and do not affect production behavior.

---

### Usage #11: Dashboard Frontend -- Svelte Components

| Field | Value |
|-------|-------|
| **Files** | `AgentsView.svelte`, `AgentDetail.svelte`, `AgentDetailPanel.svelte`, `EventStream.svelte`, `agents.svelte.ts` |
| **Functions** | `getAgentTypeIcon()`, `getAgentType()`, display rendering |
| **Strict Validation?** | NO -- uses string matching with `.includes()` |
| **Impact if Fails** | Falls back to default icon |
| **Severity** | **NONE** -- Frontend handles arbitrary type strings gracefully |

**`AgentsView.svelte:44` and `AgentDetail.svelte:86`**:
```typescript
function getAgentTypeIcon(agentType: string): string {
    const type = agentType.toLowerCase();
    if (type === 'pm') return '...';
    if (type.includes('research')) return '...';
    if (type.includes('engineer') || type.includes('svelte')) return '...';
    if (type.includes('qa') || type.includes('test')) return '...';
    // ... etc
    return '...'; // Default fallback
}
```

The frontend uses permissive string matching (`.includes()`) with a default fallback. It would correctly handle "engineer", "qa", "ops", and all other free-form type strings. The frontend is NOT the bottleneck -- it would work correctly if the backend API returned agents with any type string.

**`agents.svelte.ts:102`** (`getAgentType()`):
```typescript
function getAgentType(event: ClaudeEvent): string | null {
    // ... extracts agent_type from event data
}
```

This function extracts `agent_type` from real-time Claude events (subagent_start, delegation events). It reads the value as a plain string and never validates against an enum. This is used for the live Agents view, not the Config tab.

**`AgentDetailPanel.svelte:408`**:
```svelte
{#if detailData.agent_type}
    <span>{detailData.agent_type}</span>
{/if}
```

Renders the agent type as-is. No validation. Would display any string value.

---

### Usage #12: Config Routes -- API Endpoints

| Field | Value |
|-------|-------|
| **File** | `src/claude_mpm/services/monitor/config_routes.py` |
| **Lines** | 272-397 |
| **Functions** | `handle_project_summary()`, `handle_agents_deployed()` |
| **Strict Validation?** | No direct enum validation in routes |
| **Impact** | Routes call `AgentManager.list_agents()` which triggers Usage #1 |
| **Severity** | **CRITICAL** (indirect -- propagates the bug to the dashboard) |

The config routes themselves do not perform `AgentType` validation. They delegate to `AgentManager.list_agents()`, which internally triggers `read_agent()` -> `_parse_agent_markdown()` -> `AgentType()` (Usage #1). The routes receive only the 2 successfully parsed agents and faithfully return them to the frontend.

The routes also do NOT use the `UnifiedAgentRegistry` or its `AgentType` (Usage #6). They use `AgentManager` exclusively, which uses the `models.agent_definition.AgentType`.

---

### No CLI Commands Use `AgentType` Directly

A grep of `src/claude_mpm/cli/` for `AgentType` returned zero results. CLI commands interact with agents through higher-level services (`agent_lifecycle_manager`, `agent_operation_service`, etc.) that either:
1. Use `AgentDefinitionFactory` (which has a safe fallback -- Usage #4), or
2. Operate on file paths without parsing frontmatter

---

### Severity Summary Table

| # | Location | Enum Source | Strict? | Caught? | Severity | Impact Description |
|---|----------|-------------|---------|---------|----------|--------------------|
| 1 | `_parse_agent_markdown():444` | models | YES | Silent None | **CRITICAL** | Root cause: 46/48 agents silently rejected |
| 2 | `to_dict():177` | models | No | N/A | None | Only runs on valid agents |
| 3 | `_definition_to_markdown():625,723` | models | No | N/A | Low | Write path always valid |
| 4 | `AgentDefinitionFactory:49-57` | models | No | Safe default | None | Uses `.get()` with fallback |
| 5 | `list_agents():318` | models | No | N/A | None (direct) | Serializes valid agents only |
| 6 | `UnifiedAgentRegistry` (various) | unified | Mixed | Partial | **Moderate** | `from_dict()` strict; others safe |
| 7 | `agent_registry.py:179,782` | unified | YES | Yes (suppress) | **Moderate** | Gracefully degrades, but filter silently ignored |
| 8 | `services/agents/registry/__init__.py` | unified | N/A | N/A | None | Re-export only |
| 9 | `services/agents/__init__.py` | unified | N/A | N/A | None | Re-export only |
| 10 | Test eval `agent_response_parser.py` | test-only | YES | No | Low | Test framework only |
| 11 | Svelte frontend (5 files) | N/A (string) | No | Default fallback | None | Frontend handles any string |
| 12 | Config routes | N/A (delegates) | No | N/A | **Critical** (indirect) | Propagates Usage #1 to API |

---

### Key Findings

1. **Single Point of Failure**: The entire dashboard agent display hinges on ONE line of code -- line 444 in `agent_management_service.py`. All other usages either have graceful fallbacks, operate on already-valid data, or are downstream consumers.

2. **Three Incompatible Enums**: The three `AgentType` enums (`models`, `unified`, `test`) have different member sets. None of them include the actual frontmatter values used by deployed agents ("engineer", "ops", "qa", etc.). The test eval enum comes closest but is not used in production.

3. **Ironic Pattern Inconsistency**: `AgentDefinitionFactory` (Usage #4) demonstrates the correct pattern with `type_map.get(tier, AgentType.CUSTOM)` -- a safe dictionary lookup with fallback. The same pattern should be applied in `_parse_agent_markdown()`.

4. **Frontend Is Ready**: The Svelte dashboard frontend already handles arbitrary type strings via permissive `.includes()` matching with fallback icons. No frontend changes are needed.

5. **Import Confusion Risk**: Two different `AgentType` enums are both importable as `AgentType`:
   - `from claude_mpm.models import AgentType` -- the models enum (5 members)
   - `from claude_mpm.services.agents.registry import AgentType` -- the unified enum (5 different members)
   - A developer importing the wrong one would get silently wrong behavior.

6. **No CLI Impact**: CLI commands do not directly reference `AgentType`. They use higher-level services that either have safe fallbacks or bypass frontmatter parsing.

7. **Unified Registry Is Mostly Safe**: The `UnifiedAgentRegistry` uses `_determine_agent_type()` (lines 431-448) which assigns types based on file path and tier -- never from frontmatter strings. The only risky path is `from_dict()` (line 116) used during registry import/deserialization.

---

### Recommended Fix Priority

| Priority | Action | Fixes |
|----------|--------|-------|
| **P0** | Add fallback in `_parse_agent_markdown()` line 444 | Fixes dashboard showing 2/48 agents |
| **P1** | Consolidate the three `AgentType` enums into one | Eliminates import confusion and member mismatch |
| **P2** | Add `ValueError` handling in `UnifiedAgentRegistry.from_dict()` | Prevents deserialization failures |
| **P3** | Add logging/UI indication when agents fail to parse | Makes future issues visible instead of silent |

### P0 Fix (Immediate -- One Line Change)

```python
# File: src/claude_mpm/services/agents/management/agent_management_service.py
# Line 444 -- Replace:
type=AgentType(post.metadata.get("type", "core")),

# With:
type=self._safe_parse_agent_type(post.metadata.get("type", "core")),
```

```python
# Add helper method to AgentManager:
@staticmethod
def _safe_parse_agent_type(type_str: str) -> AgentType:
    """Parse agent type with graceful fallback for non-enum values."""
    try:
        return AgentType(type_str)
    except ValueError:
        logger.debug(f"Unknown agent type '{type_str}', defaulting to CUSTOM")
        return AgentType.CUSTOM
```

This is identical to the pattern already used in `AgentDefinitionFactory` (Usage #4), making it a consistent, proven approach.
