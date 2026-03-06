# AgentType Enum Relationship Analysis (Deep Dive)

**Date**: 2026-03-03
**Investigator**: Research Agent (Claude Opus 4.6)
**Branch**: `agenttype-enums`
**Task**: Task #2 -- How the three AgentType enums relate to frontmatter fields

---

## Executive Summary

The three `AgentType` enums represent three fundamentally different concepts that should never have shared a name. This analysis traces exactly how each enum gets its values, what frontmatter fields feed into it, what information is lost, and where dead code lives. It also documents a **fourth classification system** (`AgentCategory` in `core/enums.py`) and **three separate `AgentTier` enums** that compound the confusion.

Key findings:
1. **Enum 1** (models) parses the `type:` frontmatter field but fails for 95%+ of real agents
2. **Enum 2** (unified registry) NEVER reads frontmatter -- it classifies by file path and tier
3. **Enum 3** (test parser) is the only enum whose values match actual frontmatter, but it lives in tests only
4. **The `_safe_parse_agent_type()` fix referenced in the v1 analysis does NOT exist** in the current codebase -- line 444 still uses raw `AgentType(post.metadata.get("type", "core"))` which throws `ValueError` for most agents
5. Agents use TWO different frontmatter field names: `type:` (48 hyphenated agents) and `agent_type:` (27 underscored agents), and different code paths read different fields
6. The `AgentCategory` enum in `core/enums.py` is a fourth overlapping classification with 17 members
7. `AgentTier` has three separate definitions with incompatible value casing

---

## 1. Enum-by-Enum Deep Dive

### 1.1 Enum 1: `models.agent_definition.AgentType`

**File**: `src/claude_mpm/models/agent_definition.py:25-36`
**Base class**: `str, Enum`

```python
class AgentType(str, Enum):
    CORE = "core"
    PROJECT = "project"
    CUSTOM = "custom"
    SYSTEM = "system"
    SPECIALIZED = "specialized"
```

#### How Values Get Populated

**Primary source**: Frontmatter `type:` field via `AgentManagementService._parse_agent_markdown()` at line 444:

```python
# src/claude_mpm/services/agents/management/agent_management_service.py:444
metadata = AgentMetadata(
    type=AgentType(post.metadata.get("type", "core")),
    ...
)
```

**Population chain**:
1. `frontmatter.loads(content)` parses the YAML frontmatter from agent `.md` files
2. `post.metadata.get("type", "core")` extracts the `type:` field, defaulting to `"core"`
3. `AgentType(type_str)` attempts strict enum conversion
4. If the value is not one of {core, project, custom, system, specialized}, this **raises `ValueError`**

**CRITICAL BUG (CONFIRMED)**: The previous analysis (v1) referenced a `_safe_parse_agent_type()` fallback introduced in commit `854fb8f0`. **This function does NOT exist in the current codebase.** A grep for `safe_parse` across the entire repository returns zero production code results. The line at `agent_management_service.py:444` still uses the raw `AgentType()` constructor call.

This means:
- 2 of 75 agents (`mpm-agent-manager.md` with `type: system`, `local-ops.md` with `type: specialized`) parse correctly
- 46 hyphen-format agents with `type:` values like `engineer`, `ops`, `qa`, `research`, etc. will **crash** with `ValueError`
- 27 underscore-format agents with `agent_type:` (not `type:`) fields will default to `"core"` since `post.metadata.get("type", "core")` finds no `type:` key

**Secondary source**: `AgentDefinitionFactory.create_agent_definition()` at line 49:

```python
# src/claude_mpm/services/agents/deployment/agent_definition_factory.py:49-53
type_map = {
    ModificationTier.USER: AgentType.CUSTOM,
    ModificationTier.PROJECT: AgentType.PROJECT,
    ModificationTier.SYSTEM: AgentType.SYSTEM,
}
```

This maps `ModificationTier` -> `AgentType` programmatically. Note:
- `CORE` and `SPECIALIZED` are **never assigned** by this factory
- This factory ignores the frontmatter `type:`/`agent_type:` field entirely
- The `agent_type` parameter passed to `create_agent_definition()` is accepted but **never used** -- it's shadowed by the `type_map.get(tier, AgentType.CUSTOM)` logic

#### Serialization: `to_dict()`

```python
# src/claude_mpm/models/agent_definition.py:177
"metadata": {
    "type": self.metadata.type.value,  # Serializes as string (e.g., "custom")
    ...
}
```

The `to_dict()` method serializes `AgentType.value` as a plain string under the key `"type"`. Because this is a `str, Enum`, JSON serialization works naturally.

#### No `from_dict()` Method

Enum 1's `AgentDefinition` has a `to_dict()` but **NO `from_dict()`** classmethod. Deserialization must be done manually, which means there is no standardized round-trip pattern. Any consumer reconstructing an `AgentDefinition` from a dictionary must call `AgentType(dict_data["metadata"]["type"])` directly -- and that will fail for values like `"engineer"`.

#### Dead Code Analysis

| Member | Assigned By | Used In Production? | Notes |
|--------|-------------|:---:|-------|
| `CORE` | Default value in frontmatter parsing | Yes (default) | Assigned when `type:` field is missing |
| `PROJECT` | `AgentDefinitionFactory` | Yes | Mapped from `ModificationTier.PROJECT` |
| `CUSTOM` | `AgentDefinitionFactory` | Yes | Default fallback in factory |
| `SYSTEM` | Frontmatter + factory | Yes | Only 1 agent (`mpm-agent-manager.md`) |
| `SPECIALIZED` | Frontmatter only | Barely | Only 1 agent (`local-ops.md`), never assigned by factory |

**Verdict**: `SPECIALIZED` is near-dead code since it can only be assigned from frontmatter parsing, and the parsing itself crashes for most agents. `CORE` is over-assigned as the default for agents that lack a `type:` field.

---

### 1.2 Enum 2: `core.unified_agent_registry.AgentType`

**File**: `src/claude_mpm/core/unified_agent_registry.py:52-59`
**Base class**: `Enum` (plain, NOT `str, Enum`)

```python
class AgentType(Enum):
    CORE = "core"
    SPECIALIZED = "specialized"
    USER_DEFINED = "user_defined"
    PROJECT = "project"
    MEMORY_AWARE = "memory_aware"
```

#### How Values Get Populated

**This enum NEVER reads frontmatter.** Values are assigned algorithmically by `_determine_agent_type()` at line 431:

```python
# src/claude_mpm/core/unified_agent_registry.py:431-448
def _determine_agent_type(self, file_path: Path, tier: AgentTier) -> AgentType:
    path_str = str(file_path).lower()

    if tier == AgentTier.PROJECT:
        return AgentType.PROJECT          # All project-tier -> PROJECT
    if tier == AgentTier.USER:
        return AgentType.USER_DEFINED     # All user-tier -> USER_DEFINED
    if "templates" in path_str or "core" in path_str:
        return AgentType.CORE             # Path contains "templates" or "core"
    return AgentType.SPECIALIZED          # Default for system-tier
```

**Plus a post-discovery override** in `_discover_memory_integration()` at line 600:

```python
# src/claude_mpm/core/unified_agent_registry.py:600
metadata.agent_type = AgentType.MEMORY_AWARE  # Overrides whatever was set
```

**Population flow**:
1. `_discover_path()` iterates files in discovery directories
2. `_determine_tier()` assigns `AgentTier` based on path (PROJECT/USER/SYSTEM)
3. `_determine_agent_type()` maps tier + path -> `AgentType`
4. After all discovery, `_discover_memory_integration()` overrides type to `MEMORY_AWARE` for agents with matching memory files

**Result**: The agent's frontmatter `type:` or `agent_type:` is **completely irrelevant** to Enum 2. An agent with `type: engineer` in its frontmatter could be classified as `PROJECT`, `CORE`, `SPECIALIZED`, `USER_DEFINED`, or `MEMORY_AWARE` depending solely on where its file lives and whether it has memory files.

#### Serialization: `to_dict()` / `from_dict()`

```python
# src/claude_mpm/core/unified_agent_registry.py:105-119
def to_dict(self) -> Dict[str, Any]:
    data = asdict(self)
    data["agent_type"] = self.agent_type.value   # Key is "agent_type", not "type"
    data["tier"] = self.tier.value
    data["format"] = self.format.value
    return data

@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "AgentMetadata":
    data["agent_type"] = AgentType(data["agent_type"])   # STRICT -- will raise ValueError
    data["tier"] = AgentTier(data["tier"])
    data["format"] = AgentFormat(data["format"])
    return cls(**data)
```

**Cross-serialization incompatibility**:
- Enum 1 serializes to key `"type"` with values from {core, project, custom, system, specialized}
- Enum 2 serializes to key `"agent_type"` with values from {core, specialized, user_defined, project, memory_aware}
- `from_dict()` is strict: `AgentType("custom")` raises `ValueError` because `"custom"` is not in Enum 2

**Field name mismatch**: The `AgentMetadata` in Enum 1's world uses `type` as the field name. The `AgentMetadata` in Enum 2's world uses `agent_type`. These are two different dataclasses with the same name, different fields, and different enum types stored in them.

#### Dead Code Analysis

| Member | Assigned By | Used In Production? | Notes |
|--------|-------------|:---:|-------|
| `CORE` | Path analysis ("templates" or "core" in path) | Yes | System-tier agents in template/core directories |
| `SPECIALIZED` | Default for system-tier | Yes | Catch-all for system agents not in templates/core |
| `USER_DEFINED` | User-tier agents | Possibly | Only if user-tier directory exists and has agents |
| `PROJECT` | Project-tier agents | Yes | All agents in `.claude/agents/` |
| `MEMORY_AWARE` | Memory file integration override | Possibly | Only if memory files exist and match agent names |

**Verdict**: `USER_DEFINED` and `MEMORY_AWARE` are conditionally used -- they depend on runtime environment. In a typical deployment where agents are in `.claude/agents/`, all agents become `PROJECT` and these two members are never used.

---

### 1.3 Enum 3: `tests/eval/agents/shared/agent_response_parser.AgentType`

**File**: `tests/eval/agents/shared/agent_response_parser.py:37-47`
**Base class**: `str, Enum`

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

#### How Values Get Populated

Values are passed as strings to the `parse()` method and converted:

```python
# tests/eval/agents/shared/agent_response_parser.py:196-199
def parse(self, response_text: str, agent_type: AgentType | str = AgentType.BASE):
    if isinstance(agent_type, str):
        agent_type = AgentType(agent_type)
```

**Population source**: Test code passes agent type strings explicitly. The `AgentType` here represents the **functional role** of the agent being tested and is used to select the appropriate specialized parser:

```python
# Line 227-250: Agent-type-specific parsing dispatch
if agent_type == AgentType.RESEARCH:
    analysis.agent_specific_data = self._parse_research_agent(...)
elif agent_type == AgentType.ENGINEER:
    analysis.agent_specific_data = self._parse_engineer_agent(...)
# etc.
```

#### Relationship to Frontmatter

This enum is the **only one whose values match actual frontmatter** `type:` values (5 of 8 match):

| Enum 3 Member | Matches frontmatter `type:` ? | Agent count |
|---|:---:|---|
| `BASE` | No | 0 (abstract concept) |
| `RESEARCH` | Yes | `type: research` (2 agents) |
| `ENGINEER` | Yes | `type: engineer` (20 agents) |
| `QA` | Yes | `type: qa` (4 agents) |
| `OPS` | Yes | `type: ops` (10 agents) |
| `DOCUMENTATION` | Yes | `type: documentation` (2 agents) |
| `PROMPT_ENGINEER` | No | `type: analysis` (1 agent, different value) |
| `PM` | No | 0 (PM is the orchestrator, not a deployed agent) |

#### Dead Code Analysis

| Member | Used In | Notes |
|--------|---------|-------|
| `BASE` | Default in `parse()` | Always used as fallback |
| `RESEARCH` | `_parse_research_agent()` dispatch | Active in tests |
| `ENGINEER` | `_parse_engineer_agent()` dispatch | Active in tests |
| `QA` | `_parse_qa_agent()` dispatch | Active in tests |
| `OPS` | `_parse_ops_agent()` dispatch | Active in tests |
| `DOCUMENTATION` | `_parse_documentation_agent()` dispatch | Active in tests |
| `PROMPT_ENGINEER` | `_parse_prompt_engineer_agent()` dispatch | Active in tests |
| `PM` | Referenced in docstring only | **Near-dead** -- "already tested in Phase 1" but no dispatch case in `parse()` |

**Verdict**: `PM` has no dispatch handler and is dead code within the parser. All others are actively used.

---

## 2. Frontmatter Field Analysis

### 2.1 Two Frontmatter Field Names Exist

Agents in `.claude/agents/` use TWO different YAML frontmatter field names:

| Field Name | Used By | Count | Origin |
|---|---|:---:|---|
| `type:` | Hyphenated agents (`dart-engineer.md`) | ~48 files | Built by `AgentTemplateBuilder.build_agent_markdown()` which writes `type: {agent_type}` |
| `agent_type:` | Underscored agents (`dart_engineer.md`) | ~27 files | Appears to be from a different source (collection/external), also used in `test_base_agent_hierarchy.py` |

**The two formats represent different agent file generations**:
- **Hyphenated files** (e.g., `dart-engineer.md`): Created by the MPM deployment pipeline via `AgentTemplateBuilder`. Use `type:` field. Contain long inline descriptions with XML examples.
- **Underscored files** (e.g., `dart_engineer.md`): Appear to be from an external collection (have `schema_version`, `agent_id`, `resource_tier` fields). Use `agent_type:` field. More structured frontmatter.

### 2.2 Which Code Reads Which Field

| Code Path | Reads `type:` | Reads `agent_type:` | Fallback |
|---|:---:|:---:|---|
| `AgentManagementService._parse_agent_markdown()` | Yes | No | Default `"core"` |
| `AgentDiscoveryService._extract_template_metadata()` | No | Yes | Falls through to `category:`, then `"agent"` |
| `UnifiedAgentRegistry._determine_agent_type()` | No | No | Ignores frontmatter entirely |
| `AgentTemplateBuilder.build_agent_markdown()` | Writes `type:` | N/A | Only writes if `agent_type != "general"` |
| `test_base_agent_hierarchy.py` | No | Writes `agent_type:` | N/A |

**Critical disconnect**: `AgentDiscoveryService` reads `agent_type:` first, `category:` second, and defaults to `"agent"`:

```python
# src/claude_mpm/services/agents/deployment/agent_discovery_service.py:320-321
"type": frontmatter.get("agent_type", frontmatter.get("category", "agent"))
```

While `AgentManagementService` reads `type:` only:

```python
# src/claude_mpm/services/agents/management/agent_management_service.py:444
type=AgentType(post.metadata.get("type", "core"))
```

**Result**: The SAME agent file processed by different code paths will get different type classifications:
- `dart_engineer.md` (has `agent_type: engineer`, no `type:` field):
  - `AgentManagementService` -> defaults to `"core"` -> `AgentType.CORE`
  - `AgentDiscoveryService` -> reads `"engineer"` -> stored as string `"engineer"`
  - `UnifiedAgentRegistry` -> ignores frontmatter -> `AgentType.PROJECT` (based on path)

---

## 3. Comprehensive Mapping Table

### 3.1 How Each Agent Gets Classified Across All Three Systems

For agents with `type:` in frontmatter (example: `engineer.md` with `type: engineer`):

| System | Classification | Source of Truth | Value |
|---|---|---|---|
| Enum 1 (models) | `AgentMetadata.type` | frontmatter `type:` field | **ValueError** (crashes) |
| Enum 2 (registry) | `AgentMetadata.agent_type` | file path + tier | `AgentType.PROJECT` |
| Enum 3 (test) | function parameter | test code | `AgentType.ENGINEER` |
| `AgentDiscoveryService` | dict `"type"` key | frontmatter `agent_type:` then `category:` | `"agent"` (no `agent_type:` in this file) |
| `AgentCategory` (enums.py) | string constant | static mapping | `ENGINEERING` |

For agents with `agent_type:` in frontmatter (example: `dart_engineer.md` with `agent_type: engineer`):

| System | Classification | Source of Truth | Value |
|---|---|---|---|
| Enum 1 (models) | `AgentMetadata.type` | frontmatter `type:` (missing) | `AgentType.CORE` (default) |
| Enum 2 (registry) | `AgentMetadata.agent_type` | file path + tier | `AgentType.PROJECT` |
| Enum 3 (test) | function parameter | test code | `AgentType.ENGINEER` |
| `AgentDiscoveryService` | dict `"type"` key | frontmatter `agent_type:` | `"engineer"` |
| `AgentCategory` (enums.py) | string constant | static mapping | `ENGINEERING` |

### 3.2 Complete Frontmatter Value Distribution (75 agent files)

| Frontmatter Value | Using `type:` | Using `agent_type:` | Total | In Enum 1? | In Enum 2? | In Enum 3? | In AgentCategory? |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `engineer` | 20 | 14 | 34 | No | No | Yes | No (ENGINEERING) |
| `ops` | 10 | 3 | 13 | No | No | Yes | No (OPERATIONS) |
| `qa` | 4 | 4 | 8 | No | No | Yes | Yes (QA) |
| `research` | 2 | 1 | 3 | No | No | Yes | Yes (RESEARCH) |
| `documentation` | 2 | 1 | 3 | No | No | Yes | Yes |
| `security` | 1 | 1 | 2 | No | No | No | Yes |
| `product` | 1 | 1 | 2 | No | No | No | Yes |
| `system` | 1 | 0 | 1 | Yes | No | No | Yes |
| `specialized` | 1 | 1 | 2 | Yes | Yes | No | Yes |
| `content` | 1 | 0 | 1 | No | No | No | Yes |
| `analysis` | 1 | 0 | 1 | No | No | No | Yes |
| `claude-mpm` | 1 | 0 | 1 | No | No | No | No |
| `imagemagick` | 1 | 0 | 1 | No | No | No | No |
| `memory_manager` | 1 | 0 | 1 | No | No | No | No |
| `refactoring` | 1 | 0 | 1 | No | No | No | No |

---

## 4. The AgentTier Parallel Problem

The `AgentTier` enum has the SAME fragmentation as `AgentType`:

### Three Separate AgentTier Definitions

| Location | Base Class | Values | Casing |
|---|---|---|---|
| `core/unified_agent_registry.py:44` | `Enum` | project, user, system | **lowercase** |
| `core/types.py:78` | `Enum` | PROJECT, USER, SYSTEM | **UPPERCASE** |
| `agents/async_agent_loader.py:47` | `Enum` | project, user, system | **lowercase** |

### Plus ModificationTier

| Location | Base Class | Values | Casing |
|---|---|---|---|
| `services/agents/registry/modification_tracker.py:62` | `Enum` | project, user, system | **lowercase** |

The `AgentTier` in `core/types.py` uses UPPERCASE values (`"PROJECT"`, `"USER"`, `"SYSTEM"`) while the one in `unified_agent_registry.py` and `async_agent_loader.py` use lowercase (`"project"`, `"user"`, `"system"`). The `from_string()` classmethod in `core/types.py` converts to uppercase before comparison, but direct enum construction (e.g., `AgentTier("project")`) will **fail** with the `core/types.py` version.

### AgentTier Import Chain

- `agent_loader.py` imports from `unified_agent_registry` (lowercase values)
- `framework_agent_loader.py` imports from `agent_loader` (lowercase values)
- `core/types.py` defines its own (UPPERCASE values)
- `async_agent_loader.py` defines its own (lowercase values, duplicate)

---

## 5. The Fourth Classification: AgentCategory

**File**: `src/claude_mpm/core/enums.py:360-443`
**Base class**: `StrEnum`

```python
class AgentCategory(StrEnum):
    ENGINEERING = "engineering"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    QUALITY = "quality"
    QA = "qa"
    SECURITY = "security"
    OPERATIONS = "operations"
    INFRASTRUCTURE = "infrastructure"
    DOCUMENTATION = "documentation"
    CONTENT = "content"
    DATA = "data"
    OPTIMIZATION = "optimization"
    SPECIALIZED = "specialized"
    SYSTEM = "system"
    PROJECT_MANAGEMENT = "project-management"
    PRODUCT = "product"
    VERSION_CONTROL = "version_control"
    DESIGN = "design"
    GENERAL = "general"
    CUSTOM = "custom"
```

**17 members** -- the most comprehensive enum but with DIFFERENT values than frontmatter:
- Frontmatter uses `engineer`, AgentCategory uses `engineering`
- Frontmatter uses `ops`, AgentCategory uses `operations`
- AgentCategory includes `QUALITY` as the "new" name for `QA` (but both exist)

**This enum has its own docstring stating**: `Migration Priority: MEDIUM (Week 3)` and `Coverage: ~3% of all magic strings` -- suggesting it was defined aspirationally but has not been widely adopted.

---

## 6. Safe Parse Fallback Analysis

### What the Fallback Logic Does (When It Exists)

The `_safe_parse_agent_type()` from the v1 analysis was described as:
```python
def _safe_parse_agent_type(type_str: str) -> AgentType:
    try:
        return AgentType(type_str)
    except ValueError:
        return AgentType.CUSTOM  # Fallback
```

**This does NOT exist in the current codebase.** The current code at line 444 uses the raw constructor, meaning:

**Information lost when/if a safe fallback is implemented**:
- The original frontmatter `type:` value (e.g., `"engineer"`, `"ops"`, `"qa"`) is replaced with `AgentType.CUSTOM`
- All 34 engineer agents become "custom"
- All 13 ops agents become "custom"
- All 8 qa agents become "custom"
- The type-based grouping, filtering, and display loses its semantic meaning
- Only the `to_dict()` output is affected -- the `raw_content` field still contains the original markdown

### What the Discovery Service Does Differently

The `AgentDiscoveryService` at line 320-321 takes a more pragmatic approach:
```python
"type": frontmatter.get("agent_type", frontmatter.get("category", "agent"))
```

This preserves the original value as a **plain string**, never tries to convert it to an enum, and thus never loses information. This is the only code path that correctly preserves the frontmatter type value.

---

## 7. The AgentDefinitionFactory Tier-to-Type Mapping

**File**: `src/claude_mpm/services/agents/deployment/agent_definition_factory.py:49-57`

```python
type_map = {
    ModificationTier.USER: AgentType.CUSTOM,
    ModificationTier.PROJECT: AgentType.PROJECT,
    ModificationTier.SYSTEM: AgentType.SYSTEM,
}
metadata = AgentMetadata(
    type=type_map.get(tier, AgentType.CUSTOM),
    ...
)
```

### Issues

1. **The `agent_type` parameter is accepted but ignored**: The method signature takes `agent_type: str` but the `type_map` only uses `tier`. The `agent_type` parameter is dead code within this method.

2. **Incomplete mapping**: Only 3 of 5 Enum 1 members are mapped:
   - `CORE` -- never assigned
   - `SPECIALIZED` -- never assigned

3. **Cross-enum confusion**: The factory uses `ModificationTier` (from `modification_tracker.py`) to map to Enum 1's `AgentType` (from `agent_definition.py`). These are different concepts:
   - `ModificationTier` = where the agent was changed (user/project/system)
   - `AgentType` = what category the agent belongs to (core/project/custom/system/specialized)

   Mapping `ModificationTier.USER` -> `AgentType.CUSTOM` conflates "changed by user" with "custom type", which are not the same thing. A user could modify a `CORE` agent, and it would become `CUSTOM`.

---

## 8. Complete Classification Overlap Matrix

All classification systems in the codebase, side by side:

| Concept | Enum 1 (models) | Enum 2 (registry) | Enum 3 (test) | AgentCategory | ModificationTier | AgentTier (unified) | AgentTier (types.py) |
|---|---|---|---|---|---|---|---|
| What it classifies | Frontmatter label | File location | Functional role | Specialization domain | Change origin | Discovery location | Discovery location |
| Base class | str, Enum | Enum | str, Enum | StrEnum | Enum | Enum | Enum |
| Source of truth | YAML `type:` | File path | Test param | Code mapping | Lifecycle tracking | File path | File path |
| Member count | 5 | 5 | 8 | 17 | 3 | 3 | 3 |
| Contains "engineer" | No | No | Yes | No (engineering) | N/A | N/A | N/A |
| Contains "ops" | No | No | Yes | No (operations) | N/A | N/A | N/A |
| Contains "project" | Yes | Yes | No | No (project-management) | Yes | Yes | Yes |
| Value casing | lowercase | lowercase | lowercase | lowercase | lowercase | lowercase | UPPERCASE |
| JSON serializable | Yes (str) | No (.value needed) | Yes (str) | Yes (StrEnum) | No (.value needed) | No (.value needed) | No (.value needed) |

---

## 9. Critical Finding: The `_parse_agent_markdown` Bug

The code at `agent_management_service.py:444` will raise `ValueError` for any agent whose `type:` field is not in {core, project, custom, system, specialized}. This affects 46 of the 48 hyphen-format agents.

**How this hasn't been catastrophic**: The `_parse_agent_markdown()` method is likely called in a try/except context, or the `AgentManagementService` is rarely invoked for the full set of deployed agents. The primary discovery path through `UnifiedAgentRegistry.discover_agents()` does NOT call `_parse_agent_markdown()` -- it uses its own `_extract_file_metadata()` which reads description/specializations but NOT the type field.

**Potential crash paths**:
- `AgentManagementService.load_agent(name)` calls `_parse_agent_markdown()`
- `AgentManagementService.load_all_agents()` calls `_parse_agent_markdown()` for each agent
- Any API endpoint that uses `AgentManagementService` to load individual agents

---

## 10. Summary of Relationships

```
YAML Frontmatter
    |
    +-- "type:" field (48 hyphenated agents)
    |     |
    |     +-- AgentManagementService._parse_agent_markdown()
    |     |     -> AgentType(value) [Enum 1] -- CRASHES for 46/48 agents
    |     |
    |     +-- UnifiedAgentRegistry._extract_markdown_description()
    |           -> Reads description only, IGNORES type field
    |
    +-- "agent_type:" field (27 underscored agents)
          |
          +-- AgentDiscoveryService._extract_template_metadata()
          |     -> Stored as plain string, never converted to enum
          |
          +-- AgentManagementService._parse_agent_markdown()
                -> NOT READ (only reads "type:", defaults to "core")


File Path / Tier
    |
    +-- UnifiedAgentRegistry._determine_agent_type()
          -> AgentType [Enum 2] -- Programmatic, ignores frontmatter
          -> Overridden to MEMORY_AWARE if memory files exist


Test Code
    |
    +-- AgentResponseParser.parse(response, agent_type="engineer")
          -> AgentType [Enum 3] -- Passed by test, matches functional role
```

---

## 11. Recommendations (Analysis-Only)

1. **The `_safe_parse_agent_type` fix needs to be re-applied** -- the current code at line 444 will crash for most agents
2. **The `type:` vs `agent_type:` field name split needs resolution** -- two different fields serving the same purpose creates a maintenance burden
3. **Three `AgentTier` enums need consolidation** alongside the three `AgentType` enums
4. **The `AgentCategory` enum overlaps significantly** with what a unified `AgentType` should be
5. **The factory's `agent_type` parameter is dead code** and should be either used or removed
6. **75 agent files (not 48)** exist in `.claude/agents/` -- many are duplicates in two formats (hyphenated with `type:` and underscored with `agent_type:`)

---

## Appendix A: Files Referenced

| File | Lines | Role |
|------|-------|------|
| `src/claude_mpm/models/agent_definition.py` | 25-36, 99, 164-213 | Enum 1 definition, AgentMetadata, to_dict() |
| `src/claude_mpm/core/unified_agent_registry.py` | 44-59, 105-119, 431-448, 587-603 | Enum 2, AgentTier, from_dict/to_dict, _determine_agent_type, memory override |
| `tests/eval/agents/shared/agent_response_parser.py` | 37-47, 196-252 | Enum 3, parse dispatch |
| `src/claude_mpm/services/agents/deployment/agent_definition_factory.py` | 7-12, 49-81 | Factory tier-to-type mapping |
| `src/claude_mpm/services/agents/management/agent_management_service.py` | 440-497 | _parse_agent_markdown() frontmatter parsing |
| `src/claude_mpm/services/agents/deployment/agent_discovery_service.py` | 314-332 | agent_type/category frontmatter reading |
| `src/claude_mpm/services/agents/deployment/agent_template_builder.py` | 493, 566-568 | Writes `type:` to frontmatter |
| `src/claude_mpm/core/types.py` | 78-93 | AgentTier (UPPERCASE values) |
| `src/claude_mpm/agents/async_agent_loader.py` | 47-52 | AgentTier (duplicate, lowercase) |
| `src/claude_mpm/core/enums.py` | 360-443 | AgentCategory (17 members) |
| `src/claude_mpm/services/agents/registry/modification_tracker.py` | 62-67 | ModificationTier |
| `src/claude_mpm/core/agent_registry.py` | 24-35, 48-79, 167-188 | Compatibility layer, from_unified() |
| `.claude/agents/*.md` | frontmatter | 75 agent files with type/agent_type |
