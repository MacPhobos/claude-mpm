# Problem Analysis: Incompatible AgentType Enums

**Date**: 2026-03-02
**Investigator**: Research Agent (Claude Opus 4.6)
**Branch**: `dashboard-v2-agent-scope`
**Status**: Analysis complete, consolidation not yet implemented

---

## 1. Problem Statement

The Claude MPM codebase contains **three separate Python enums** all named `AgentType`, each defined in a different module with **different member values** and **different intended purposes**. None of the three enums include the actual `type:` values used in deployed agent markdown frontmatter (e.g., "engineer", "ops", "qa"). This fragmentation caused a critical production bug where the dashboard showed 2 of 48 deployed agents (now patched with a fallback), and creates ongoing confusion about which `AgentType` a developer is working with at any given import site.

**Core tension**: The codebase uses the name `AgentType` to mean three different things:
1. An **abstract deployment classification** (core/project/custom/system/specialized)
2. A **discovery-time classification** (core/specialized/user_defined/project/memory_aware)
3. A **functional role** (engineer/ops/qa/research/documentation/pm)

These three concepts are conflated into one name but never reconciled.

---

## 2. Enum Inventory

### Enum 1: `models.agent_definition.AgentType`

**File**: `src/claude_mpm/models/agent_definition.py`
**Lines**: 25-36
**Base class**: `str, Enum` (string enum -- values are usable as plain strings)

```python
class AgentType(str, Enum):
    """Agent type classification.

    WHY: Enum ensures only valid agent types are used throughout the system,
    preventing typos and making the code more maintainable.
    """

    CORE = "core"
    PROJECT = "project"
    CUSTOM = "custom"
    SYSTEM = "system"
    SPECIALIZED = "specialized"
```

**Member count**: 5
**Member values**: `core`, `project`, `custom`, `system`, `specialized`

**Intended purpose**: Abstract deployment/classification taxonomy. Used when parsing agent markdown frontmatter in `AgentManager._parse_agent_markdown()` and when serializing `AgentDefinition` objects to dictionaries for API responses.

**Who imports it**:

| Importer | Import path | How used |
|----------|-------------|----------|
| `models/__init__.py:13` | `from .agent_definition import AgentType` | Re-export |
| `services/agents/management/agent_management_service.py:24` | `from claude_mpm.models.agent_definition import AgentType` | Frontmatter parsing, serialization |
| `services/agents/deployment/agent_definition_factory.py:11` | `from claude_mpm.models.agent_definition import AgentType` | Factory type mapping |

**Critical observation**: This enum is used for the **read path** (parsing frontmatter) and the **write path** (generating markdown). It is the enum that caused the dashboard bug because deployed agents use frontmatter values like "engineer" and "ops" which are not members.

**Recent fix**: Commit `854fb8f0` added `_safe_parse_agent_type()` to gracefully fall back to `AgentType.CUSTOM` for unknown values. The direct `AgentType(type_str)` call was replaced with this safe wrapper. This mitigates but does not resolve the underlying design problem -- all non-standard types are now silently mapped to "custom", losing their original semantic meaning.

---

### Enum 2: `core.unified_agent_registry.AgentType`

**File**: `src/claude_mpm/core/unified_agent_registry.py`
**Lines**: 52-59
**Base class**: `Enum` (plain enum -- NOT a string enum)

```python
class AgentType(Enum):
    """Agent type classification."""

    CORE = "core"              # Core framework agents
    SPECIALIZED = "specialized"  # Specialized domain agents
    USER_DEFINED = "user_defined"  # User-created agents
    PROJECT = "project"         # Project-specific agents
    MEMORY_AWARE = "memory_aware"  # Memory-enhanced agents
```

**Member count**: 5
**Member values**: `core`, `specialized`, `user_defined`, `project`, `memory_aware`

**Intended purpose**: Discovery-time classification based on file location and tier, not frontmatter content. Assigned programmatically by `_determine_agent_type()` which inspects file paths and agent tiers -- it never reads frontmatter `type:` values.

**Who imports it**:

| Importer | Import path | How used |
|----------|-------------|----------|
| `core/agent_registry.py:27` | `from .unified_agent_registry import AgentType` | Compatibility layer filtering |
| `services/agents/registry/__init__.py:6` | `from claude_mpm.core.unified_agent_registry import AgentType` | Re-export as public API |
| `services/agents/__init__.py:44` | `from .registry import AgentType` | Re-export (transitive) |

**Critical observation**: This enum is **never populated from frontmatter**. It is assigned algorithmically:
- `AgentTier.PROJECT` -> `AgentType.PROJECT`
- `AgentTier.USER` -> `AgentType.USER_DEFINED`
- Path contains "templates" or "core" -> `AgentType.CORE`
- Default -> `AgentType.SPECIALIZED`
- Memory file match -> override to `AgentType.MEMORY_AWARE`

The `from_dict()` classmethod at line 116 is the only strict validation point: `AgentType(data["agent_type"])` will raise `ValueError` if the serialized data contains a value not in this enum.

---

### Enum 3: `tests/eval/agents/shared/agent_response_parser.AgentType`

**File**: `tests/eval/agents/shared/agent_response_parser.py`
**Lines**: 37-47
**Base class**: `str, Enum` (string enum)

```python
class AgentType(str, Enum):
    """Agent types in Claude MPM framework."""

    BASE = "base"                    # BASE_AGENT_TEMPLATE.md only
    RESEARCH = "research"            # BASE_AGENT + BASE_RESEARCH.md
    ENGINEER = "engineer"            # BASE_AGENT + BASE_ENGINEER.md
    QA = "qa"                        # BASE_AGENT + BASE_QA.md
    OPS = "ops"                      # BASE_AGENT + BASE_OPS.md
    DOCUMENTATION = "documentation"  # BASE_AGENT + BASE_DOCUMENTATION.md
    PROMPT_ENGINEER = "prompt_engineer"  # BASE_AGENT + BASE_PROMPT_ENGINEER.md
    PM = "pm"                        # BASE_AGENT + BASE_PM.md
```

**Member count**: 8
**Member values**: `base`, `research`, `engineer`, `qa`, `ops`, `documentation`, `prompt_engineer`, `pm`

**Intended purpose**: Represent the **functional roles** of agents as used in the eval test framework. These values correspond to the actual agent archetypes in the system and closely match the frontmatter `type:` values found in deployed `.md` files.

**Who imports it**:

| Importer | Import path | How used |
|----------|-------------|----------|
| `tests/eval/agents/shared/__init__.py:17` | `from .agent_response_parser import AgentType` | Re-export |
| `tests/eval/agents/shared/agent_metrics.py:30` | `from .agent_response_parser import AgentType` | Metrics aggregation |
| `tests/eval/agents/shared/agent_test_base.py:36` | `from .agent_response_parser import AgentType` | Test base class |
| `tests/eval/agents/shared/test_agent_infrastructure.py:34` | `from .agent_response_parser import AgentType` | Infrastructure tests |

**Critical observation**: This enum is the only one that actually contains values matching agent frontmatter (engineer, ops, qa, research, documentation). However, it is confined to the test framework and has no production impact.

---

## 3. Incompatibility Matrix

### Side-by-Side Member Comparison

| Value | Enum 1 (models) | Enum 2 (unified) | Enum 3 (test) | In frontmatter? |
|-------|:---:|:---:|:---:|:---:|
| `core` | CORE | CORE | -- | No |
| `project` | PROJECT | PROJECT | -- | No |
| `custom` | CUSTOM | -- | -- | No |
| `system` | SYSTEM | -- | -- | Yes (1 agent) |
| `specialized` | SPECIALIZED | SPECIALIZED | -- | Yes (1 agent) |
| `user_defined` | -- | USER_DEFINED | -- | No |
| `memory_aware` | -- | MEMORY_AWARE | -- | No |
| `base` | -- | -- | BASE | No |
| `research` | -- | -- | RESEARCH | Yes (2 agents) |
| `engineer` | -- | -- | ENGINEER | Yes (20 agents) |
| `qa` | -- | -- | QA | Yes (4 agents) |
| `ops` | -- | -- | OPS | Yes (10 agents) |
| `documentation` | -- | -- | DOCUMENTATION | Yes (2 agents) |
| `prompt_engineer` | -- | -- | PROMPT_ENGINEER | No |
| `pm` | -- | -- | PM | No |
| `security` | -- | -- | -- | Yes (1 agent) |
| `content` | -- | -- | -- | Yes (1 agent) |
| `analysis` | -- | -- | -- | Yes (1 agent) |
| `claude-mpm` | -- | -- | -- | Yes (1 agent) |
| `imagemagick` | -- | -- | -- | Yes (1 agent) |
| `memory_manager` | -- | -- | -- | Yes (1 agent) |
| `product` | -- | -- | -- | Yes (1 agent) |
| `refactoring` | -- | -- | -- | Yes (1 agent) |

### Overlap Analysis

**Shared between Enum 1 and Enum 2** (3 values):
- `core` -- same name and value
- `project` -- same name and value
- `specialized` -- same name and value

**Unique to Enum 1** (2 values):
- `custom` -- abstract classification, no frontmatter equivalent
- `system` -- used by exactly 1 agent (`mpm-agent-manager`)

**Unique to Enum 2** (2 values):
- `user_defined` -- assigned by discovery algorithm, never from frontmatter
- `memory_aware` -- assigned when memory files detected

**Unique to Enum 3** (8 values):
- All 8 values are unique to this enum
- 5 of 8 match frontmatter values (`research`, `engineer`, `qa`, `ops`, `documentation`)
- 3 of 8 have no frontmatter equivalent (`base`, `prompt_engineer`, `pm`)

**In frontmatter but in NO enum** (7 values):
- `security`, `content`, `analysis`, `claude-mpm`, `imagemagick`, `memory_manager`, `product`, `refactoring`

### Base Class Incompatibility

| Property | Enum 1 (models) | Enum 2 (unified) | Enum 3 (test) |
|----------|:---:|:---:|:---:|
| Base class | `str, Enum` | `Enum` | `str, Enum` |
| `isinstance(v, str)` | True | **False** | True |
| JSON serializable | Yes (is string) | **No** (needs `.value`) | Yes (is string) |
| Direct comparison with strings | Yes | **No** | Yes |

Enum 2 being a plain `Enum` (not `str, Enum`) means it cannot be compared directly with strings or serialized to JSON without calling `.value`. This creates a subtle API difference where code written for Enum 1 will not work with Enum 2 values.

---

## 4. Actual Agent Types in the Wild

Scanning all 48 files in `.claude/agents/*.md`:

### Complete Frontmatter `type:` Distribution

| Frontmatter `type:` Value | Count | In Enum 1? | In Enum 2? | In Enum 3? | Current behavior |
|---------------------------|-------|:---:|:---:|:---:|------------------|
| `engineer` | 20 | No -> CUSTOM | No (path-based) | Yes | Mapped to `custom` by fallback |
| `ops` | 10 | No -> CUSTOM | No (path-based) | Yes | Mapped to `custom` by fallback |
| `qa` | 4 | No -> CUSTOM | No (path-based) | Yes | Mapped to `custom` by fallback |
| `documentation` | 2 | No -> CUSTOM | No (path-based) | Yes | Mapped to `custom` by fallback |
| `research` | 2 | No -> CUSTOM | No (path-based) | Yes | Mapped to `custom` by fallback |
| `system` | 1 | Yes (SYSTEM) | No (path-based) | No | Correctly parsed |
| `specialized` | 1 | Yes (SPECIALIZED) | Yes (path-based) | No | Correctly parsed |
| `security` | 1 | No -> CUSTOM | No | No | Mapped to `custom` by fallback |
| `content` | 1 | No -> CUSTOM | No | No | Mapped to `custom` by fallback |
| `analysis` | 1 | No -> CUSTOM | No | No | Mapped to `custom` by fallback |
| `claude-mpm` | 1 | No -> CUSTOM | No | No | Mapped to `custom` by fallback |
| `imagemagick` | 1 | No -> CUSTOM | No | No | Mapped to `custom` by fallback |
| `memory_manager` | 1 | No -> CUSTOM | No | No | Mapped to `custom` by fallback |
| `product` | 1 | No -> CUSTOM | No | No | Mapped to `custom` by fallback |
| `refactoring` | 1 | No -> CUSTOM | No | No | Mapped to `custom` by fallback |
| **TOTAL** | **48** | **2 valid** | **0 from frontmatter** | **38 valid** |

### Agent-to-File Mapping (All 48)

| Agent File | Frontmatter `type:` |
|-----------|-------------------|
| `dart-engineer.md` | engineer |
| `data-engineer.md` | engineer |
| `data-scientist.md` | engineer |
| `engineer.md` | engineer |
| `golang-engineer.md` | engineer |
| `java-engineer.md` | engineer |
| `javascript-engineer.md` | engineer |
| `nestjs-engineer.md` | engineer |
| `nextjs-engineer.md` | engineer |
| `phoenix-engineer.md` | engineer |
| `php-engineer.md` | engineer |
| `python-engineer.md` | engineer |
| `react-engineer.md` | engineer |
| `ruby-engineer.md` | engineer |
| `rust-engineer.md` | engineer |
| `svelte-engineer.md` | engineer |
| `tauri-engineer.md` | engineer |
| `typescript-engineer.md` | engineer |
| `visual-basic-engineer.md` | engineer |
| `web-ui.md` | engineer |
| `agentic-coder-optimizer.md` | ops |
| `aws-ops.md` | ops |
| `clerk-ops.md` | ops |
| `digitalocean-ops.md` | ops |
| `gcp-ops.md` | ops |
| `ops.md` | ops |
| `project-organizer.md` | ops |
| `tmux-agent.md` | ops |
| `vercel-ops.md` | ops |
| `version-control.md` | ops |
| `api-qa.md` | qa |
| `qa.md` | qa |
| `real-user.md` | qa |
| `web-qa.md` | qa |
| `documentation.md` | documentation |
| `ticketing.md` | documentation |
| `code-analyzer.md` | research |
| `research.md` | research |
| `mpm-agent-manager.md` | system |
| `local-ops.md` | specialized |
| `security.md` | security |
| `content-agent.md` | content |
| `prompt-engineer.md` | analysis |
| `mpm-skills-manager.md` | claude-mpm |
| `imagemagick.md` | imagemagick |
| `memory-manager-agent.md` | memory_manager |
| `product-owner.md` | product |
| `refactoring-engineer.md` | refactoring |

---

## 5. Dependency Graph

### Import Tree

```
src/claude_mpm/models/agent_definition.py
    defines: AgentType (Enum 1: core/project/custom/system/specialized)
    |
    +-- src/claude_mpm/models/__init__.py
    |       re-exports: AgentType
    |
    +-- src/claude_mpm/services/agents/management/agent_management_service.py
    |       uses: AgentType for frontmatter parsing + serialization
    |       CRITICAL PATH: _safe_parse_agent_type() + to_dict()
    |
    +-- src/claude_mpm/services/agents/deployment/agent_definition_factory.py
            uses: AgentType for tier-to-type mapping (safe .get() with default)


src/claude_mpm/core/unified_agent_registry.py
    defines: AgentType (Enum 2: core/specialized/user_defined/project/memory_aware)
    |
    +-- src/claude_mpm/core/agent_registry.py
    |       uses: AgentType for compatibility layer filtering
    |       handles ValueError with try/except and contextlib.suppress
    |
    +-- src/claude_mpm/services/agents/registry/__init__.py
    |       re-exports: AgentType
    |       |
    |       +-- src/claude_mpm/services/agents/__init__.py
    |               re-exports: AgentType
    |
    +-- tests/test_unified_agent_registry.py
    |       (test file, uses AgentTier but not AgentType directly)
    |
    +-- tests/agents/test_agent_registry.py
            (test file, uses AgentTier but not AgentType directly)


tests/eval/agents/shared/agent_response_parser.py
    defines: AgentType (Enum 3: base/research/engineer/qa/ops/documentation/prompt_engineer/pm)
    |
    +-- tests/eval/agents/shared/__init__.py
    |       re-exports: AgentType
    |
    +-- tests/eval/agents/shared/agent_metrics.py
    |       uses: AgentType for metrics grouping
    |
    +-- tests/eval/agents/shared/agent_test_base.py
    |       uses: AgentType for test parameterization
    |
    +-- tests/eval/agents/shared/test_agent_infrastructure.py
            uses: AgentType for infrastructure assertions
```

### Transitive Import Conflict Paths

**Path 1** -- A module importing from `claude_mpm.models` gets Enum 1:
```python
from claude_mpm.models import AgentType  # -> Enum 1
```

**Path 2** -- A module importing from `claude_mpm.services.agents` gets Enum 2:
```python
from claude_mpm.services.agents import AgentType  # -> Enum 2
```

**Path 3** -- A test module importing from `tests.eval.agents.shared` gets Enum 3:
```python
from tests.eval.agents.shared import AgentType  # -> Enum 3
```

**Could code accidentally import the wrong one?**

YES. Consider this realistic scenario:

```python
# Developer wants to work with agent types in a new service
from claude_mpm.models import AgentType  # Gets Enum 1
# OR
from claude_mpm.services.agents import AgentType  # Gets Enum 2

# These are DIFFERENT enums with DIFFERENT members
# AgentType("user_defined")  -> works with Enum 2, ValueError with Enum 1
# AgentType("custom")  -> works with Enum 1, ValueError with Enum 2
# AgentType("engineer")  -> ValueError with BOTH
```

There is no import-time error. The developer would only discover the mismatch at runtime, when a `ValueError` is raised or a comparison fails silently.

**Cross-system serialization risk**: If Enum 1 serializes `"custom"` to JSON, and Enum 2 tries to deserialize it via `from_dict()`, it will raise `ValueError` because `"custom"` is not a member of Enum 2. Conversely, if Enum 2 serializes `"user_defined"`, Enum 1 cannot parse it.

---

## 6. Impact Analysis

### What Breaks Today

1. **Dashboard "deployed agents" count was wrong** (now patched):
   - `AgentManager._parse_agent_markdown()` used strict `AgentType(type_str)` that rejected 46/48 agents
   - Patched in commit `854fb8f0` with `_safe_parse_agent_type()` fallback to `CUSTOM`
   - **Current state**: All 48 agents now parse, but 46 have their original type replaced with "custom", losing semantic meaning

2. **Original agent type information is lost**:
   - When the dashboard API returns agent data, agents typed "engineer" in frontmatter are reported as type "custom"
   - Any UI filtering, grouping, or display based on type shows incorrect information
   - The `AgentDefinitionFactory` also maps to `CUSTOM` for unknown tiers, compounding the loss

3. **Validation cascade**: The `/api/config/validate` endpoint previously reported 205 false-positive issues because skills appeared "not referenced by any agent" (since only 2 agents were visible). With the fallback fix, this should be resolved, but the underlying type mismatch means validation logic may still make incorrect type-based decisions.

4. **`UnifiedAgentRegistry.from_dict()` deserialization is fragile**:
   - Line 116: `AgentType(data["agent_type"])` has no error handling
   - If registry data was serialized with Enum 1 values (e.g., `"custom"`), deserialization will fail
   - If registry data was serialized from an agent with frontmatter type `"engineer"`, deserialization fails

### What Could Break in the Future

1. **Cross-module data exchange**: Any feature that passes agent type data between `AgentManager` (Enum 1) and `UnifiedAgentRegistry` (Enum 2) will encounter mismatches. For example:
   - A feature that syncs deployed agents into the unified registry
   - A migration tool that converts between formats
   - A dashboard filter that queries both systems

2. **New frontmatter types**: When new agents are created with novel type values (which is inevitable given the free-form nature of frontmatter), they will silently become "custom" in all Enum 1 contexts.

3. **Type-based routing or authorization**: If any future feature routes agent behavior or permissions based on `AgentType`, the three enums will produce inconsistent decisions:
   - Enum 1 sees 46 agents as "custom" -> treats them uniformly
   - Enum 2 sees all project agents as "project" -> ignores functional role
   - Enum 3 distinguishes by role -> but only in tests

4. **Import confusion for new developers**: A new contributor searching for `AgentType` will find three definitions. Without documentation, they must guess which to import. IDE autocompletion may suggest the wrong one.

---

## 7. Design Questions

### Q1: Should there be one canonical enum or is there a valid reason for multiple?

**Arguments for ONE enum**:
- Eliminates import confusion entirely
- Single source of truth for type values
- Simpler maintenance and documentation
- No cross-serialization incompatibilities

**Arguments for MULTIPLE enums** (if they serve genuinely different purposes):
- Enum 2 classifies by **discovery location** (project/user/system), which is orthogonal to functional role
- Enum 3 classifies by **functional role** (engineer/ops/qa), which is what frontmatter captures
- These are conceptually different dimensions that happen to share a name

**Recommendation**: The problem is not that there are multiple classifications, but that they all share the name `AgentType`. If multiple enums are retained, they should have **distinct names** (e.g., `AgentClassification`, `AgentDiscoveryType`, `AgentRole`).

### Q2: What should the canonical set of values be?

The frontmatter values represent the ground truth of how agents are actually typed in the wild. A canonical enum should include at minimum:

**Tier 1 (common, well-established)**: engineer, ops, qa, research, documentation, security
**Tier 2 (framework-specific)**: system, specialized, core
**Tier 3 (niche)**: content, analysis, product, refactoring, claude-mpm, imagemagick, memory_manager

The question is whether to enumerate all possible values or accept free-form strings.

### Q3: How should the enum relate to frontmatter `type:` values vs internal classification?

Two orthogonal dimensions exist:
1. **Functional role** (from frontmatter): engineer, ops, qa, etc. -- what the agent does
2. **Deployment classification** (from discovery): project, user, system -- where the agent lives

These should be **separate fields**, not conflated into one `AgentType`. The current architecture conflates them because:
- Enum 1 mixes deployment classification ("project", "system") with abstract types ("core", "custom")
- Enum 2 mixes deployment tier ("project") with discovery attributes ("memory_aware")
- Neither captures functional role

### Q4: Backward compatibility concerns

Any consolidation must handle:
- **Serialized data**: Registry JSON files, API responses, checkpoint data may contain any of the current enum values
- **Import paths**: Existing code imports `AgentType` from at least 3 different locations
- **Deprecation period**: Old enum values should continue to work during migration
- **Test framework**: Enum 3 is used extensively in eval tests and should be aligned or explicitly separated

---

## 8. Consolidation Options

### Option A: Single Canonical Enum with All Known Values

Replace all three enums with one authoritative enum that includes every known type value.

```python
# src/claude_mpm/models/agent_type.py (new canonical location)

class AgentType(str, Enum):
    """Canonical agent type classification.

    Represents the functional role of an agent as declared in frontmatter.
    """
    # Functional roles (from frontmatter)
    ENGINEER = "engineer"
    OPS = "ops"
    QA = "qa"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    CONTENT = "content"
    ANALYSIS = "analysis"
    PRODUCT = "product"
    PM = "pm"

    # Framework-specific
    SYSTEM = "system"
    SPECIALIZED = "specialized"
    CORE = "core"

    # Catch-all
    CUSTOM = "custom"
```

**Pros**:
- Single import, no confusion
- Preserves type information from frontmatter
- Type-safe with known values
- Backward compatible with all existing serialized values

**Cons**:
- Must be updated when new agent types are created
- Conflates functional role with deployment classification
- Large enum with many values
- Does not address the discovery-time classification (project/user) separately

**Migration effort**: Medium. Update 3 enum definitions, update all import paths, add deprecation aliases.

---

### Option B: Two-Dimensional Type System (Role + Tier)

Separate the two orthogonal concepts into two enums with distinct names.

```python
# src/claude_mpm/models/agent_type.py

class AgentRole(str, Enum):
    """Functional role of an agent (from frontmatter type: field)."""
    ENGINEER = "engineer"
    OPS = "ops"
    QA = "qa"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    SYSTEM = "system"         # MPM infrastructure agents
    CUSTOM = "custom"         # Catch-all for unknown roles
    # Add more as needed

class AgentScope(str, Enum):
    """Where the agent was discovered/deployed (orthogonal to role)."""
    PROJECT = "project"       # .claude/agents/ in project
    USER = "user"             # ~/.claude/agents/
    FRAMEWORK = "framework"   # Built-in to claude-mpm
```

Usage:
```python
@dataclass
class AgentMetadata:
    role: AgentRole          # What it does (from frontmatter)
    scope: AgentScope        # Where it lives (from discovery)
    # ... other fields
```

**Pros**:
- Clean separation of concerns
- No name collision (different names for different concepts)
- Extensible -- new roles don't affect scopes and vice versa
- Eliminates the "project" appearing in both current Enum 1 and Enum 2

**Cons**:
- Larger refactoring effort (rename `type` -> `role` across codebase)
- Existing serialized data uses "type" key, requires migration
- More complex data model (two fields instead of one)
- Test Enum 3 would need updating or explicit separation

**Migration effort**: High. Rename fields, update API contracts, migrate serialized data.

---

### Option C: String-Based with Validation (No Enum)

Remove `AgentType` enums entirely. Store the frontmatter `type:` value as a plain string. Provide a validation function for known types.

```python
# src/claude_mpm/models/agent_definition.py

KNOWN_AGENT_TYPES: set[str] = {
    "engineer", "ops", "qa", "research", "documentation",
    "security", "system", "specialized", "core", "custom",
    "content", "analysis", "product", "pm",
}

def validate_agent_type(type_str: str) -> str:
    """Validate and normalize agent type string."""
    normalized = type_str.lower().strip()
    if normalized not in KNOWN_AGENT_TYPES:
        logger.warning(f"Unknown agent type: {normalized}")
    return normalized

@dataclass
class AgentMetadata:
    type: str  # Free-form string from frontmatter
    # ... other fields
```

**Pros**:
- Zero maintenance burden for new types
- Preserves original frontmatter values exactly
- No ValueError exceptions, ever
- Simplest implementation
- Most flexible for evolving agent taxonomy

**Cons**:
- No compile-time or IDE assistance for valid type values
- Typos in type values are not caught
- Harder to refactor (string comparisons scattered)
- Less structured -- any string is accepted

**Migration effort**: Low. Replace enum references with string, remove enum imports.

---

### Option D: Hybrid -- String Storage with Enum Helpers (Recommended)

Store the raw string but provide enum-like helpers for the common cases.

```python
# src/claude_mpm/models/agent_type.py

class AgentRole:
    """Known agent role constants. Not an enum -- agent types are
    ultimately free-form strings from frontmatter."""

    ENGINEER = "engineer"
    OPS = "ops"
    QA = "qa"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    SYSTEM = "system"
    SPECIALIZED = "specialized"
    CORE = "core"
    CUSTOM = "custom"

    # All known roles for validation
    ALL_KNOWN: frozenset[str] = frozenset({
        ENGINEER, OPS, QA, RESEARCH, DOCUMENTATION,
        SECURITY, SYSTEM, SPECIALIZED, CORE, CUSTOM,
    })

    # Role categories for grouping
    DEVELOPMENT_ROLES: frozenset[str] = frozenset({ENGINEER, QA, RESEARCH})
    OPERATIONS_ROLES: frozenset[str] = frozenset({OPS, SECURITY})
    FRAMEWORK_ROLES: frozenset[str] = frozenset({SYSTEM, SPECIALIZED, CORE})

    @classmethod
    def is_known(cls, role: str) -> bool:
        return role.lower() in cls.ALL_KNOWN


@dataclass
class AgentMetadata:
    type: str  # Raw frontmatter value, free-form string
    # ... other fields
```

**Pros**:
- Constants provide IDE autocompletion and refactoring support
- Free-form strings accepted -- no ValueError, ever
- Grouping sets enable category-based logic
- No enum import confusion (one module, one class)
- Original frontmatter values preserved exactly
- Easy to extend (add constant, add to ALL_KNOWN)

**Cons**:
- Less strict than enum -- developer can pass any string
- No `.value` or `.name` enum niceties
- Migration still required for existing enum usage sites

**Migration effort**: Medium. Replace enum usage with string constants, update type annotations.

---

## 9. Risk Assessment

### Risk of Doing Nothing

| Risk | Likelihood | Impact | Notes |
|------|:---:|:---:|-------|
| New developer imports wrong `AgentType` | High | Medium | Three enums with same name, different members |
| Future feature uses type-based logic incorrectly | High | High | Any filtering, routing, or authorization by type |
| Serialization/deserialization mismatch | Medium | High | Cross-module data exchange fails silently or loudly |
| 46 agents lose their real type in API responses | **Happening now** | Medium | All non-standard types mapped to "custom" |
| New frontmatter types silently become "custom" | **Happening now** | Low | Information loss on every new agent type |

**Overall risk of doing nothing**: **MODERATE-HIGH**. The critical bug is patched, but information loss is ongoing and confusion will compound as the codebase grows.

### Risk of Option A (Single Canonical Enum)

| Risk | Likelihood | Impact | Notes |
|------|:---:|:---:|-------|
| Missing new type values | Medium | Low | Enum must be updated for each new type |
| Migration breaks serialized data | Low | Medium | Backward compatible if all current values included |
| Still conflates role and scope | High | Low | Same conceptual problem, just fewer enums |

**Overall risk**: LOW. Straightforward improvement over status quo.

### Risk of Option B (Two-Dimensional: Role + Scope)

| Risk | Likelihood | Impact | Notes |
|------|:---:|:---:|-------|
| Large refactoring scope | High | Medium | Rename `type` -> `role` across entire codebase |
| API contract changes | High | High | Dashboard and external consumers must update |
| Migration of serialized data | Medium | Medium | JSON keys change from `type` to `role` |

**Overall risk**: MEDIUM. Best long-term architecture but highest migration cost.

### Risk of Option C (String-Based, No Enum)

| Risk | Likelihood | Impact | Notes |
|------|:---:|:---:|-------|
| Typos in type values | Medium | Low | "enginir" silently accepted |
| String comparisons scattered | Medium | Medium | Harder to refactor later |
| Loss of type safety | High | Low | IDE cannot catch invalid types |

**Overall risk**: LOW. Most pragmatic for a system that already uses free-form strings.

### Risk of Option D (Hybrid String + Constants)

| Risk | Likelihood | Impact | Notes |
|------|:---:|:---:|-------|
| Constants not enforced | Medium | Low | Developer can bypass constants |
| Migration effort | Medium | Medium | Replace enum usage across codebase |
| Two representations exist | Low | Low | Constants and raw strings coexist |

**Overall risk**: LOW. Best balance of flexibility, safety, and migration cost.

---

## 10. Summary of Recommendations

| Priority | Recommendation | Rationale |
|----------|---------------|-----------|
| **Immediate** | Document the three enums and their import paths (this document) | Prevent future confusion |
| **Short-term** | Adopt Option A or D to consolidate the production enums | Eliminate import confusion and information loss |
| **Medium-term** | Consider Option B to properly separate role and scope | Clean architecture for long-term maintainability |
| **Low priority** | Align Enum 3 (test) with production enum | Reduce cognitive overhead for test developers |

**Recommended path**: Start with **Option D** (hybrid string + constants) as it provides the best balance of flexibility, safety, and pragmatism. The system already treats agent types as free-form strings in frontmatter and deployment; acknowledging this reality in the type system is the cleanest approach. Option B (two-dimensional) is the ideal long-term architecture but requires a larger coordinated refactoring.

---

## Appendix: Files Referenced

| File | Lines | Role |
|------|-------|------|
| `src/claude_mpm/models/agent_definition.py` | 25-36 | Enum 1 definition |
| `src/claude_mpm/models/__init__.py` | 8-14 | Enum 1 re-export |
| `src/claude_mpm/core/unified_agent_registry.py` | 52-59, 113-119, 431-448 | Enum 2 definition, from_dict, _determine_agent_type |
| `src/claude_mpm/core/agent_registry.py` | 27, 178-182, 777-782 | Enum 2 import and usage |
| `tests/eval/agents/shared/agent_response_parser.py` | 37-47 | Enum 3 definition |
| `tests/eval/agents/shared/__init__.py` | 14-17 | Enum 3 re-export |
| `tests/eval/agents/shared/agent_metrics.py` | 30 | Enum 3 consumer |
| `tests/eval/agents/shared/agent_test_base.py` | 36 | Enum 3 consumer |
| `tests/eval/agents/shared/test_agent_infrastructure.py` | 34 | Enum 3 consumer |
| `src/claude_mpm/services/agents/management/agent_management_service.py` | 435-442, 452-453 | Enum 1 usage (with safe fallback) |
| `src/claude_mpm/services/agents/deployment/agent_definition_factory.py` | 7-12, 49-57 | Enum 1 usage (with safe .get() default) |
| `src/claude_mpm/services/agents/registry/__init__.py` | 3-8 | Enum 2 re-export |
| `src/claude_mpm/services/agents/__init__.py` | 44, 69 | Enum 2 transitive re-export |
| `.claude/agents/*.md` (48 files) | frontmatter | Actual type values in the wild |
