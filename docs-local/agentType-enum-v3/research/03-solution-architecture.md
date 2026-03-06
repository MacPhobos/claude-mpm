# Solution Architecture: Agent Identity & Deployment Unification

**Date**: 2026-03-06
**Author**: Solution Architect (Research Agent)
**Target Branch**: Fresh branch off `main`
**Prerequisites**: Read 01-branch-history-analysis.md, 02-main-branch-baseline.md, and all v2 analysis documents

---

## Executive Summary

This document designs a comprehensive solution to unify the agent identity model, type system, deployment pipeline, and PM prompt references in claude-mpm. The design is organized into 8 components across 5 implementation phases, each leaving the codebase in a working state. All changes target the `main` branch baseline -- no dependencies on the `agenttype-enums` branch.

### Design Principles

1. **Single Source of Truth (SSOT)**: One canonical definition, imported everywhere
2. **`name:` field is sacred**: Empirically confirmed as the ONLY resolution key for Claude Code
3. **Delete, don't deprecate**: Remove dead code immediately
4. **Verify before commit**: Run comprehensive grep BEFORE any commit, not after
5. **Dependency-ordered phases**: Most foundational changes first
6. **Each phase is independently shippable**: Tests pass after every phase

---

## Architecture Overview: Before vs After

### BEFORE (Current Main)

```
                    AGENT IDENTITY (3 competing systems)
                    ====================================

  CANONICAL_NAMES (64 entries)     AGENT_NAME_MAP (does not exist on main)
  agent_name_normalizer.py:21      agent_name_registry.py (branch only)
  "python_engineer" -> "Python
   Engineer"
  "ticketing" -> "Ticketing"  <--- WRONG for delegation
  "gcp_ops" -> "GCP Ops"     <--- WRONG for delegation
         |
         v
  ALIASES (90+ entries)
  agent_name_normalizer.py:79
  "python" -> "python_engineer"
         |
         v
  normalize() -> Title Case
  agent_name_normalizer.py:262


                    AGENT TYPE (3 competing enums)
                    ==============================

  AgentType #1                AgentType #2              agents_metadata.py
  agent_definition.py:25      unified_agent_registry    "type": "core_agent"
  CORE, PROJECT, CUSTOM,      .py:52                    "type": "optimization_agent"
  SYSTEM, SPECIALIZED         CORE, SPECIALIZED,        "type": "system_agent"
                              USER_DEFINED, PROJECT,
                              MEMORY_AWARE


                    CORE_AGENTS (4+ competing lists)
                    ================================

  toolchain_detector:162    recommendation_service:36   system_context:17
  7 agents, mixed format    6 agents, bare names        8 agents, kebab
  "qa-agent"               "research"                   "version-control"
  "research-agent"         "ticketing"                  "data-engineer"


                    DEPLOYMENT (3 paths, different normalization)
                    =============================================

  deploy_agent_file()        SingleAgentDeployer        configure.py
  deployment_utils:299       single_agent_deployer      _deploy_single_agent:3081
  normalizes, strips         inline normalization,      raw shutil.copy2,
  -agent, ensures            no frontmatter,            no normalization
  frontmatter                no legacy cleanup


                    NORMALIZATION (5+ functions)
                    ============================

  normalize_deployment_filename    _normalize_agent_name
  deployment_utils:36              multi_source_deployment:29
  AgentNameNormalizer.normalize    DynamicAgentRegistry.normalize_agent_id
  agent_name_normalizer:262        agent_registry:594
                                   SingleAgentDeployer inline :68
```

### AFTER (Target Architecture)

```
                    AGENT IDENTITY (Single Source of Truth)
                    =======================================

  ┌─────────────────────────────────────────────────────────┐
  │  src/claude_mpm/core/agent_identity.py  (NEW MODULE)    │
  │                                                          │
  │  AGENT_REGISTRY: dict[str, AgentIdentity]               │
  │  ┌──────────────────────────────────────────────┐       │
  │  │ "research": AgentIdentity(                    │       │
  │  │   agent_id="research",        # kebab stem    │       │
  │  │   name="Research",            # from name:    │       │
  │  │   agent_type=AgentCategory.RESEARCH,          │       │
  │  │   is_core=True,                               │       │
  │  │ )                                             │       │
  │  │ "ticketing": AgentIdentity(                   │       │
  │  │   agent_id="ticketing",                       │       │
  │  │   name="ticketing_agent",     # exact name:   │       │
  │  │   agent_type=AgentCategory.SYSTEM,            │       │
  │  │   is_core=True,                               │       │
  │  │ )                                             │       │
  │  └──────────────────────────────────────────────┘       │
  │                                                          │
  │  class AgentCategory(str, Enum):  # unified type enum   │
  │    ENGINEER, OPS, QA, RESEARCH, SECURITY, ...           │
  │                                                          │
  │  CORE_AGENTS: set[str]  # single canonical set          │
  │                                                          │
  │  def get_name(agent_id) -> str        # delegation name │
  │  def get_agent_id(any_input) -> str   # normalize to id │
  │  def get_display_name(agent_id) -> str # human-readable │
  │  def get_category(agent_id) -> AgentCategory            │
  └─────────────────────────────────────────────────────────┘
        │              │              │              │
        │ imports      │ imports      │ imports      │ imports
        ▼              ▼              ▼              ▼
  normalizer.py   toolchain_     recommend_    system_context
  (delegates)     detector.py    service.py    .py


                    DEPLOYMENT (Single Path)
                    ========================

  All paths -> deploy_agent_file()
               deployment_utils.py
               ├── normalize_deployment_filename()
               ├── ensure_agent_id_in_frontmatter(update_existing=True)
               └── cleanup_legacy_variants()


                    NORMALIZATION (2 functions, clear purposes)
                    ==========================================

  get_agent_id(input) -> "python-engineer"    # for internal comparison
  get_name(agent_id) -> "Python Engineer"     # for Claude Code delegation
```

---

## Component 1: Agent Identity Model

### Design

An agent's identity consists of four related values:

| Field | Format | Source | Purpose | Example |
|-------|--------|--------|---------|---------|
| **filename** | `{agent_id}.md` | Derived from `agent_id` | Filesystem storage | `golang-engineer.md` |
| **`name:`** | Exact upstream value | Git repo frontmatter | Claude Code resolution (SACRED) | `Golang Engineer` |
| **`agent_id:`** | kebab-case, no suffix | Derived from filename | MPM internal identifier | `golang-engineer` |
| **`agent_type:`** | AgentCategory enum value | Frontmatter | Categorization/filtering | `engineer` |

### Derivation Rules

```
                filename stem
                     │
            ┌────────┴────────┐
            │  Canonical ID   │
            │ (kebab-case,    │
            │  no -agent,     │
            │  lowercase)     │
            └────────┬────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    agent_id:    filename:    lookup key for
    (= stem)    (stem.md)    AGENT_REGISTRY
                                  │
                                  v
                             AgentIdentity
                             .name -> "Golang Engineer"
                             .agent_type -> AgentCategory.ENGINEER
                             .is_core -> False
```

**Derivation from any input** (the single normalization function):

```python
def get_agent_id(raw_input: str) -> str:
    """Normalize ANY agent reference to canonical kebab-case ID.

    Handles: "Python Engineer", "python_engineer", "python-engineer-agent",
             "python-engineer.md", "python_engineer_agent"
    Returns: "python-engineer"
    """
    cleaned = raw_input.strip().lower()
    cleaned = Path(cleaned).stem if cleaned.endswith(".md") else cleaned
    cleaned = cleaned.replace("_", "-").replace(" ", "-")
    # Strip -agent suffix (and -agent-agent for double-suffixed)
    for suffix in ("-agent-agent", "-agent"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[: -len(suffix)]
            break
    return cleaned
```

**Lookup from ID to name** (the delegation function):

```python
def get_name(agent_id: str) -> str:
    """Get the exact name: field value for delegation.

    Returns the EXACT value from the upstream name: field.
    This is what Claude Code uses for subagent_type resolution.
    """
    canonical = get_agent_id(agent_id)
    identity = AGENT_REGISTRY.get(canonical)
    if identity:
        return identity.name
    # Fallback: Title Case from kebab
    return canonical.replace("-", " ").title()
```

**Display name** (for human-readable output like TODO prefixes):

```python
def get_display_name(agent_id: str) -> str:
    """Get human-readable display name.

    Unlike get_name(), this always returns Title Case.
    Use for TODO prefixes, UI display, logs -- NOT for delegation.
    """
    canonical = get_agent_id(agent_id)
    identity = AGENT_REGISTRY.get(canonical)
    if identity:
        # If name is already Title Case, use it
        # If name is ugly (ticketing_agent), prettify it
        name = identity.name
        if "_" in name or name == name.lower():
            return canonical.replace("-", " ").title()
        return name
    return canonical.replace("-", " ").title()
```

### The 6 Non-Conforming Upstream `name:` Values

These agents have `name:` values that don't follow Title Case convention:

| agent_id | Current `name:` | Display Name | Notes |
|----------|----------------|--------------|-------|
| `ticketing` | `ticketing_agent` | `Ticketing` | PM must use `ticketing_agent` |
| `aws-ops` | `aws_ops_agent` | `AWS Ops` | PM must use `aws_ops_agent` |
| `mpm-agent-manager` | `mpm_agent_manager` | `MPM Agent Manager` | PM must use `mpm_agent_manager` |
| `mpm-skills-manager` | `mpm_skills_manager` | `MPM Skills Manager` | PM must use `mpm_skills_manager` |
| `nestjs-engineer` | `nestjs-engineer` | `NestJS Engineer` | PM must use `nestjs-engineer` |
| `real-user` | `real-user` | `Real User` | PM must use `real-user` |

**Architecture decision**: The `get_name()` function returns the EXACT upstream value (including ugly ones). The `get_display_name()` function returns the pretty version. These are SEPARATE concerns. Code that touches Claude Code delegation MUST use `get_name()`. Code that shows UI/logs SHOULD use `get_display_name()`.

### Data Structure

```python
@dataclass(frozen=True)
class AgentIdentity:
    """Immutable agent identity record."""
    agent_id: str              # kebab-case canonical ID
    name: str                  # EXACT name: field value (sacred)
    agent_type: AgentCategory  # unified category enum
    is_core: bool = False      # whether included in CORE_AGENTS

AGENT_REGISTRY: dict[str, AgentIdentity] = {
    "engineer": AgentIdentity("engineer", "Engineer", AgentCategory.ENGINEER, is_core=True),
    "research": AgentIdentity("research", "Research", AgentCategory.RESEARCH, is_core=True),
    "qa": AgentIdentity("qa", "QA", AgentCategory.QA, is_core=True),
    "documentation": AgentIdentity("documentation", "Documentation Agent", AgentCategory.DOCUMENTATION, is_core=True),
    "security": AgentIdentity("security", "Security", AgentCategory.SECURITY, is_core=True),
    "ops": AgentIdentity("ops", "Ops", AgentCategory.OPS, is_core=True),
    "local-ops": AgentIdentity("local-ops", "Local Ops", AgentCategory.OPS, is_core=True),
    "version-control": AgentIdentity("version-control", "Version Control", AgentCategory.SYSTEM, is_core=True),
    "ticketing": AgentIdentity("ticketing", "ticketing_agent", AgentCategory.SYSTEM, is_core=True),
    "memory-manager": AgentIdentity("memory-manager", "Memory Manager", AgentCategory.SYSTEM, is_core=True),
    # ... all 48+ agents
}

CORE_AGENTS: frozenset[str] = frozenset(
    aid for aid, identity in AGENT_REGISTRY.items() if identity.is_core
)
```

### File Target

**New file**: `src/claude_mpm/core/agent_identity.py`

**Replaces/consolidates**:
- `agent_name_normalizer.py:21` (CANONICAL_NAMES) -> `AGENT_REGISTRY`
- `agent_name_normalizer.py:79` (ALIASES) -> kept but delegating to `get_agent_id()`
- `agent_name_registry.py` (branch-only, AGENT_NAME_MAP) -> `AGENT_REGISTRY`
- `toolchain_detector.py:162` (CORE_AGENTS) -> imports from `agent_identity`
- `agent_recommendation_service.py:36` (CORE_AGENTS) -> imports from `agent_identity`
- `system_context.py:17-29` (hardcoded agent list) -> generated from `AGENT_REGISTRY`

---

## Component 2: Unified AgentCategory Enum

### Design

Replace the three competing `AgentType` enums with a single `AgentCategory` enum that covers ALL 15 frontmatter values.

**Why rename to `AgentCategory`**: The existing `AgentType` name is ambiguous -- it's used for both "deployment tier" (core/custom/project) and "functional category" (engineer/ops/qa). Using `AgentCategory` makes it clear this is about functional categorization. The deployment tier concept (`CORE`/`PROJECT`/`CUSTOM`) is handled separately by the `is_core` flag and existing deployment logic.

### Enum Design

```python
class AgentCategory(str, Enum):
    """Functional category for agents. Maps 1:1 to agent_type: frontmatter values."""

    # Primary categories (high-frequency)
    ENGINEER = "engineer"           # 21 agents
    OPS = "ops"                     # 10 agents
    QA = "qa"                       # 4 agents
    DOCUMENTATION = "documentation" # 2 agents
    RESEARCH = "research"           # 2 agents
    SECURITY = "security"           # 1 agent

    # Secondary categories
    SYSTEM = "system"               # 1 agent (+ remap claude-mpm, memory_manager)
    SPECIALIZED = "specialized"     # 1 agent (+ remap imagemagick)
    ANALYSIS = "analysis"           # 1 agent (code-analyzer)
    PRODUCT = "product"             # 1 agent (product-owner)
    CONTENT = "content"             # 1 agent (content optimization)
    REFACTORING = "refactoring"     # 1 agent
```

### Outlier Remapping

| Current Frontmatter Value | Current Count | Remap To | Rationale |
|--------------------------|---------------|----------|-----------|
| `engineer` | 21 | `ENGINEER` | Direct match |
| `ops` | 10 | `OPS` | Direct match |
| `qa` | 4 | `QA` | Direct match |
| `documentation` | 2 | `DOCUMENTATION` | Direct match |
| `research` | 2 | `RESEARCH` | Direct match |
| `security` | 1 | `SECURITY` | Direct match |
| `system` | 1 | `SYSTEM` | Direct match |
| `specialized` | 1 | `SPECIALIZED` | Direct match |
| `analysis` | 1 | `ANALYSIS` | Direct match |
| `product` | 1 | `PRODUCT` | Direct match |
| `content` | 1 | `CONTENT` | Direct match |
| `refactoring` | 1 | `REFACTORING` | Direct match |
| `claude-mpm` | 1 | `SYSTEM` | PM output style is a system agent |
| `imagemagick` | 1 | `SPECIALIZED` | Tool-specific, not a category |
| `memory_manager` | 1 | `SYSTEM` | Infrastructure concern |

### Safe Parse Function

Replace `_safe_parse_agent_type()` with:

```python
def parse_agent_category(value: str) -> AgentCategory:
    """Parse agent_type: frontmatter value to AgentCategory.

    Handles all 15 known values plus outlier remapping.
    Never raises -- returns SPECIALIZED for unknown values.
    """
    REMAPS = {
        "claude-mpm": AgentCategory.SYSTEM,
        "imagemagick": AgentCategory.SPECIALIZED,
        "memory_manager": AgentCategory.SYSTEM,
    }
    cleaned = value.strip().lower().replace("-", "_")
    if cleaned in REMAPS:
        return REMAPS[cleaned]
    try:
        return AgentCategory(cleaned.replace("_", ""))  # handle memory_manager etc.
    except ValueError:
        try:
            return AgentCategory(value.strip().lower())
        except ValueError:
            logger.warning(f"Unknown agent_type '{value}', defaulting to SPECIALIZED")
            return AgentCategory.SPECIALIZED
```

### File Targets

**New**: `AgentCategory` in `src/claude_mpm/core/agent_identity.py`

**Modify** (remove old enums):
- `src/claude_mpm/models/agent_definition.py:25` -- Remove `AgentType` enum, add `from core.agent_identity import AgentCategory`. Keep `AgentType = AgentCategory` alias for backward compat during transition.
- `src/claude_mpm/core/unified_agent_registry.py:52` -- Remove `AgentType` enum, import from `agent_identity`. Update all references.

**Modify** (update third type system):
- `src/claude_mpm/agents/agents_metadata.py` -- Replace string `"type": "core_agent"` with `"category": AgentCategory.X` or just remove the type field entirely (it's not used for routing).

### Risk Assessment

- **LOW risk**: The existing enums are barely used for functional logic (87% of agents fall through to CUSTOM/None). Replacing them with a comprehensive enum can only improve coverage.
- **Migration**: Any code doing `if agent.type == AgentType.CORE` needs to change to `if identity.is_core` (different concept). Search for all `AgentType.CORE` references.

---

## Component 3: Agent Name Registry (Merged)

### Design Decision: Hardcoded vs Dynamic

**Decision: Hardcoded registry with CI drift detection.**

Rationale:
- Dynamic resolution requires `.claude/agents/` to exist at import time (fails during testing, CI, fresh installs)
- Hardcoded map enables static analysis and IDE support
- CI test detects drift between registry and deployed agents
- The extraction script (`scripts/extract_agent_names.sh` from the branch) regenerates the map on demand

### Merge Strategy

On main, only `CANONICAL_NAMES` exists (in `agent_name_normalizer.py`). On the branch, `AGENT_NAME_MAP` was added in `agent_name_registry.py`. The solution merges both into `AGENT_REGISTRY` in the new `agent_identity.py`.

**What happens to each**:

| Source | Disposition |
|--------|------------|
| `CANONICAL_NAMES` (normalizer:21) | Values merged into `AGENT_REGISTRY.name` field. Wrong values corrected to match actual `name:` fields. Dict removed. |
| `ALIASES` (normalizer:79) | Kept in `agent_name_normalizer.py` but normalize() delegates to `agent_identity.get_agent_id()` for the core logic. Aliases map variant inputs to canonical IDs. |
| `AGENT_NAME_MAP` (branch only) | Not on main. Its correct values inform `AGENT_REGISTRY` entries. File not created -- merged into `agent_identity.py`. |

### Correcting the 10 Divergent CANONICAL_NAMES Entries

These CANONICAL_NAMES values are WRONG (they don't match the upstream `name:` field):

| Key | Current CANONICAL_NAMES | Correct `name:` value | Action |
|-----|------------------------|----------------------|--------|
| `ticketing` | `Ticketing` | `ticketing_agent` | Fix in AGENT_REGISTRY |
| `code_analyzer` | `Code Analyzer` | `Code Analysis` | Fix in AGENT_REGISTRY |
| `gcp_ops` | `GCP Ops` | `Google Cloud Ops` | Fix in AGENT_REGISTRY |
| `clerk_ops` | `Clerk Ops` | `Clerk Operations` | Fix in AGENT_REGISTRY |
| `real_user` | `Real User` | `real-user` | Fix in AGENT_REGISTRY |
| `mpm_agent_manager` | `MPM Agent Manager` | `mpm_agent_manager` | Fix in AGENT_REGISTRY |
| `mpm_skills_manager` | `MPM Skills Manager` | `mpm_skills_manager` | Fix in AGENT_REGISTRY |
| `javascript_engineer` | `JavaScript Engineer` | `Javascript Engineer` | Fix in AGENT_REGISTRY |
| `typescript_engineer` | `TypeScript Engineer` | `Typescript Engineer` | Fix in AGENT_REGISTRY |
| `nestjs_engineer` | `NestJS Engineer` | `nestjs-engineer` | Fix in AGENT_REGISTRY |

### File Targets

- **New**: `src/claude_mpm/core/agent_identity.py` (AGENT_REGISTRY + functions)
- **Modify**: `src/claude_mpm/core/agent_name_normalizer.py:21-75` -- Remove CANONICAL_NAMES dict. Have `normalize()` delegate to `agent_identity.get_display_name()`.
- **Delete** (if created on branch): `src/claude_mpm/core/agent_name_registry.py` -- Absorbed into `agent_identity.py`
- **New**: `tests/core/test_agent_identity.py` -- Comprehensive tests
- **New**: `tests/integration/test_agent_identity_drift.py` -- CI drift detection

---

## Component 4: Deployment Pipeline Unification

### Design

Route ALL deployment through `deploy_agent_file()` with two key fixes:

1. **`ensure_agent_id_in_frontmatter(update_existing=True)`** -- Fix the 54% agent_id mismatch
2. **`SingleAgentDeployer` routes through `deploy_agent_file()`** -- Eliminate dual deployer

### Current Three Paths (on main)

```
Path A: GitSourceSyncService.deploy_cached_agents()
        git_source_sync_service.py:1129
        -> deploy_agent_file() ✅ (already unified)

Path B: SingleTierDeploymentService._deploy_agent_file()
        single_tier_deployment_service.py:681
        -> deploy_agent_file() ✅ (already unified)

Path C: SingleAgentDeployer.deploy_single_agent()
        single_agent_deployer.py:38
        -> INLINE normalization + direct write ❌ (NOT unified)

Path D: configure.py._deploy_single_agent()
        configure.py:3081
        -> shutil.copy2 ❌ (NO normalization)
```

### Target: All Through deploy_agent_file()

```
All Paths -> deploy_agent_file(
    source_file,
    deployment_dir,
    cleanup_legacy=True,
    ensure_frontmatter=True,
    update_existing_id=True,   # NEW parameter
    force=False,
)
```

### Changes

#### Fix 1: `ensure_agent_id_in_frontmatter` -- add `update_existing=True` default

**File**: `src/claude_mpm/services/agents/deployment_utils.py:83`

Current behavior: `update_existing=False` -- never overwrites existing `agent_id` values.

New behavior: `update_existing=True` -- derives correct `agent_id` from normalized filename and writes it, overwriting stale values like `research-agent` -> `research`.

```python
def ensure_agent_id_in_frontmatter(
    content: str,
    filename: str,
    update_existing: bool = True,  # CHANGED from False
) -> str:
```

**Risk**: LOW. The `agent_id` field is used internally by MPM, not by Claude Code. Claude Code uses `name:`. Fixing `agent_id` to match filename stems improves internal consistency.

#### Fix 2: `SingleAgentDeployer` uses `deploy_agent_file()`

**File**: `src/claude_mpm/services/agents/deployment/single_agent_deployer.py:38`

Replace the inline normalization + direct write with a call to `deploy_agent_file()`:

```python
# BEFORE (line 68-71):
agent_name = template_file.stem.lower().replace("_", "-")
if agent_name.endswith("-agent"):
    agent_name = agent_name[:-6]
target_file = agents_dir / f"{agent_name}.md"
# ... direct write

# AFTER:
from claude_mpm.services.agents.deployment_utils import deploy_agent_file
result = deploy_agent_file(
    source_file=template_file,
    deployment_dir=agents_dir,
    cleanup_legacy=True,
    ensure_frontmatter=True,
)
```

#### Fix 3: `configure.py._deploy_single_agent()` uses `deploy_agent_file()`

**File**: `src/claude_mpm/cli/commands/configure.py:3081`

Replace `shutil.copy2` with `deploy_agent_file()`:

```python
# BEFORE:
shutil.copy2(source_path, target_path)

# AFTER:
from claude_mpm.services.agents.deployment_utils import deploy_agent_file
deploy_agent_file(
    source_file=source_path,
    deployment_dir=agents_dir,
    cleanup_legacy=True,
    ensure_frontmatter=True,
)
```

#### Fix 4: Handle 3 `-agent` suffixed filenames

Three agents in the upstream repo have `-agent` in their filename:
- `content-agent.md` -> deploys as `content.md`
- `memory-manager-agent.md` -> deploys as `memory-manager.md`
- `tmux-agent.md` -> deploys as `tmux.md`

`normalize_deployment_filename()` already handles this. The fix is ensuring ALL paths go through it (Fixes 2-3 above). After deployment, verify no `-agent` suffixed files remain in `.claude/agents/`.

### File Targets

- **Modify**: `deployment_utils.py:83` -- Change `update_existing` default to `True`
- **Modify**: `deployment_utils.py:299` -- Add `update_existing_id` parameter passthrough
- **Modify**: `single_agent_deployer.py:38` -- Replace inline normalization with `deploy_agent_file()` call
- **Modify**: `configure.py:3081` -- Replace `shutil.copy2` with `deploy_agent_file()` call

### Risk Assessment

- **MEDIUM risk** for `update_existing=True`: Will change `agent_id` values in 26 deployed agents on next deployment. Non-breaking since `agent_id` is not used by Claude Code.
- **LOW risk** for SingleAgentDeployer change: Same normalization logic, just routed through unified function.
- **MEDIUM risk** for configure.py change: configure has complex agent resolution logic. Test carefully.

---

## Component 5: CORE_AGENTS Consolidation

### Design

Single canonical set in `agent_identity.py`, imported by all consumers.

### Canonical Set Definition

Based on analysis of what agents are considered "core" across all 4 lists, plus functional necessity:

```python
# In agent_identity.py

CORE_AGENTS: frozenset[str] = frozenset({
    "engineer",         # in all lists
    "research",         # in all lists
    "qa",               # in all lists
    "documentation",    # in all lists
    "security",         # in 3/4 lists
    "ops",              # in 2/4 lists
    "local-ops",        # in 2/4 lists (critical for PM default fallback)
    "version-control",  # in 1/4 lists but functionally essential
    "ticketing",        # in 2/4 lists
    "memory-manager",   # in 1/4 lists but system-critical
})
```

**Rationale for 10 agents**: These are agents that should ALWAYS be deployed regardless of project type. Specialized engineers (python, golang, etc.) are project-specific and deployed based on toolchain detection.

### Consumer Adaptation

| Consumer | File:Line (on main) | Current Format | Adaptation |
|----------|---------------------|----------------|------------|
| `toolchain_detector.py` | `:162` | `["engineer", "qa-agent", ...]` | `from core.agent_identity import CORE_AGENTS` |
| `agent_recommendation_service.py` | `:36` | `{"engineer", "research", ...}` | `from core.agent_identity import CORE_AGENTS` |
| `system_context.py` | `:17` | Inline string list | Generate from `AGENT_REGISTRY` |
| `templates/__init__.py` | `:16` | `AGENT_TEMPLATES` dict | Delete file entirely (dead code) |

### Special Case: `toolchain_detector.py` TOOLCHAIN_TO_AGENTS

The `TOOLCHAIN_TO_AGENTS` mapping (line 137) uses inconsistent formats:

```python
# BEFORE:
"python": ["python-engineer"],
"javascript": ["javascript-engineer-agent"],  # -agent suffix!
"docker": ["ops", "local-ops-agent"],         # mixed!
```

```python
# AFTER:
"python": ["python-engineer"],
"javascript": ["javascript-engineer"],   # normalized
"docker": ["ops", "local-ops"],          # normalized
```

All values should be canonical `agent_id` format (kebab-case, no suffix).

### File Targets

- **Source**: `src/claude_mpm/core/agent_identity.py` (CORE_AGENTS definition)
- **Modify**: `src/claude_mpm/services/agents/toolchain_detector.py:137,162` -- Import CORE_AGENTS, fix TOOLCHAIN_TO_AGENTS format
- **Modify**: `src/claude_mpm/services/agents/agent_recommendation_service.py:36` -- Import CORE_AGENTS
- **Delete**: `src/claude_mpm/agents/templates/__init__.py` -- Dead code, all referenced templates don't exist

---

## Component 6: PM Prompt Correctness

### Design

Fix all PM-facing text to use exact `name:` field values for delegation references, and correct the `system_context.py` guidance.

### Broken References to Fix

#### CLAUDE_MPM_OUTPUT_STYLE.md

| Line | Current | Correct | Issue |
|------|---------|---------|-------|
| ~23 | `local-ops` | `Local Ops` | Wrong format for delegation |
| ~75 | `Documentation` | `Documentation Agent` | Truncated name |

#### WORKFLOW.md

| Line | Current | Correct | Issue |
|------|---------|---------|-------|
| ~39 | `qa` | `QA` | Capitalization matters for multi-context |
| Various | `api-qa` | `API QA` | Wrong format |
| Various | `web-qa` | `Web QA` | Wrong format |
| Various | `local-ops` | `Local Ops` | Wrong format |
| Various | `ticketing-agent` | `ticketing_agent` | Wrong format (actual name uses underscore) |

#### system_context.py (Lines 17-29 on main)

**Current** (WRONG):
```python
"""You have access to native subagents via the Task tool with subagent_type parameter:
- engineer: For coding, implementation, and technical tasks
- qa: For testing, validation, and quality assurance
...
IMPORTANT: The Task tool accepts both naming formats:
- Capitalized format: "Research", "Engineer", "QA", "Version Control", "Data Engineer"
- Lowercase format: "research", "engineer", "qa", "version-control", "data-engineer"
Both formats work correctly."""
```

**New** (CORRECT):
```python
"""You have access to native subagents via the Agent tool with subagent_type parameter.

IMPORTANT: The subagent_type must EXACTLY match the agent's `name:` frontmatter field.
Examples of correct subagent_type values:
- "Research" (not "research")
- "Engineer" (not "engineer")
- "QA" (not "qa")
- "Golang Engineer" (not "golang-engineer")
- "Local Ops" (not "local-ops")
- "ticketing_agent" (not "ticketing" or "Ticketing")
- "mpm_agent_manager" (not "mpm-agent-manager")

Single-word agents like "Research", "Engineer", "QA" are case-insensitive.
Multi-word agents MUST use the exact name: field value including spaces and casing.

For the complete list of available agents and their exact names, check .claude/agents/."""
```

#### PM_INSTRUCTIONS.md

The branch already fixed 47 references (commit f392f54e). These same fixes need to be applied to the main branch version. Key patterns:

| Pattern to Find | Replace With |
|----------------|--------------|
| `local-ops` (in delegation context) | `Local Ops` |
| `web-qa-agent` | `Web QA` |
| `api-qa-agent` | `API QA` |
| `ticketing-agent` | `ticketing_agent` |
| `Security Agent` | `Security` |

### Prevention: Drift Detection Test

```python
# tests/integration/test_pm_prompt_agent_refs.py
def test_pm_prompts_use_valid_agent_names():
    """Ensure PM prompts reference agents by their exact name: field values."""
    from claude_mpm.core.agent_identity import AGENT_REGISTRY
    valid_names = {identity.name for identity in AGENT_REGISTRY.values()}

    pm_files = [
        "src/claude_mpm/agents/PM_INSTRUCTIONS.md",
        "src/claude_mpm/agents/WORKFLOW.md",
        "src/claude_mpm/agents/CLAUDE_MPM_OUTPUT_STYLE.md",
    ]
    # Extract subagent_type references and validate against valid_names
```

### File Targets

- **Modify**: `src/claude_mpm/agents/CLAUDE_MPM_OUTPUT_STYLE.md` -- Fix 2 references
- **Modify**: `src/claude_mpm/agents/WORKFLOW.md` -- Fix ~6 references
- **Modify**: `src/claude_mpm/core/system_context.py:17-29` -- Rewrite agent guidance
- **Modify**: `src/claude_mpm/agents/PM_INSTRUCTIONS.md` -- Fix ~47 references (port from branch)
- **New**: `tests/integration/test_pm_prompt_agent_refs.py` -- Drift detection

---

## Component 7: Archive Removal

### Status on Main

The `src/claude_mpm/agents/templates/archive/` directory **EXISTS on main** with 39 JSON files (confirmed in baseline analysis). The v2 team analysis noted it doesn't exist because they were checking the branch (where it was already deleted).

### Design

Delete the entire archive directory and all references.

### Changes

1. **Delete**: `src/claude_mpm/agents/templates/archive/` (39 JSON files)
2. **Modify**: `pyproject.toml` -- Ensure `norecursedirs` still includes "archive" (for any other archive dirs). Verify the entry exists and won't break.
3. **Delete**: `src/claude_mpm/agents/templates/__init__.py` -- Dead code. The `AGENT_TEMPLATES` dict references files that don't exist (`documentation_agent.md`, etc.). This module is never imported for functional purposes.
4. **Verify**: No code imports from `templates.archive` or references archive JSON files.

### Verification Grep

Before deleting, run:
```bash
grep -rn "templates/archive\|templates\.archive\|from.*templates.*import" src/claude_mpm/ --include="*.py"
grep -rn "\.json" src/claude_mpm/agents/templates/__init__.py
```

### Risk Assessment

- **LOW risk**: Archive JSON files are dead code from a previous generation. No runtime code loads them.
- **Lesson from branch**: Commit bb9923cb deleted the archive but accidentally removed a `norecursedirs` entry. Fix: verify `pyproject.toml` AFTER deletion.

---

## Component 8: Normalization Consolidation

### Design

Reduce from 5+ normalization functions to 2 with clear, non-overlapping purposes:

| Function | Purpose | Location | Input Example | Output |
|----------|---------|----------|---------------|--------|
| `get_agent_id()` | Internal ID comparison, filenames, CORE_AGENTS lookup | `agent_identity.py` | `"Python Engineer"`, `"python_engineer_agent"` | `"python-engineer"` |
| `get_name()` | Claude Code delegation (EXACT `name:` value) | `agent_identity.py` | `"python-engineer"` | `"Python Engineer"` |

**Auxiliary** (kept but simplified):
| Function | Purpose | Location | Notes |
|----------|---------|----------|-------|
| `get_display_name()` | Human-readable output | `agent_identity.py` | Title Case, even for ugly upstream names |
| `normalize_deployment_filename()` | Filename for .md files | `deployment_utils.py` | Thin wrapper: `get_agent_id(stem) + ".md"` |

### Functions to Remove/Replace

| Current Function | File:Line (main) | Disposition |
|-----------------|-------------------|-------------|
| `CANONICAL_NAMES` dict | `agent_name_normalizer.py:21` | **REMOVE** -- absorbed into AGENT_REGISTRY |
| `normalize()` method | `agent_name_normalizer.py:262` | **REWRITE** -- delegate to `get_display_name()` |
| `to_task_format()` method | `agent_name_normalizer.py` | **REWRITE** -- delegate to `get_name()` |
| `_normalize_agent_name()` | `multi_source_deployment_service.py:29` | **REPLACE** -- call `get_agent_id()` |
| `normalize_agent_id()` | `agent_registry.py:594` | **REPLACE** -- call `get_agent_id()` |
| `SingleAgentDeployer` inline | `single_agent_deployer.py:68` | **REMOVE** -- use `deploy_agent_file()` |
| `normalize_deployment_filename()` | `deployment_utils.py:36` | **SIMPLIFY** -- `return get_agent_id(stem) + ".md"` |

### AgentNameNormalizer Refactoring

The `AgentNameNormalizer` class is widely used for TODO prefixes, color coding, and display. It should NOT be deleted -- but it should delegate to `agent_identity.py`:

```python
# agent_name_normalizer.py (AFTER refactoring)
from claude_mpm.core.agent_identity import get_agent_id, get_display_name, get_name

class AgentNameNormalizer:
    """Agent name normalization for display and delegation."""

    # ALIASES kept for backward compatibility (maps informal names to canonical IDs)
    ALIASES = {
        "researcher": "research",
        "dev": "engineer",
        "python": "python-engineer",
        # ... (migrated from current ALIASES, keys normalized to kebab)
    }

    @classmethod
    def normalize(cls, agent_name: str) -> str:
        """Return display name for TODO prefixes and UI."""
        agent_id = get_agent_id(agent_name)
        # Check aliases for informal names
        if agent_id in cls.ALIASES:
            agent_id = cls.ALIASES[agent_id]
        return get_display_name(agent_id)

    @classmethod
    def to_task_format(cls, agent_name: str) -> str:
        """Return exact name: field value for delegation."""
        agent_id = get_agent_id(agent_name)
        if agent_id in cls.ALIASES:
            agent_id = cls.ALIASES[agent_id]
        return get_name(agent_id)
```

---

## Dependency Graph

```
Phase 1: Foundation
  ├── C1: agent_identity.py (AgentCategory + AGENT_REGISTRY + CORE_AGENTS + functions)
  │
  └── C7: Archive removal (independent, no dependencies)

Phase 2: Registry Integration
  ├── C3: Merge CANONICAL_NAMES into AGENT_REGISTRY (depends on C1)
  │   └── Refactor agent_name_normalizer.py to delegate
  │
  └── C2: Replace AgentType enums with AgentCategory (depends on C1)
      ├── Update agent_definition.py
      └── Update unified_agent_registry.py

Phase 3: Deployment Unification
  └── C4: Route all paths through deploy_agent_file() (depends on C1 for get_agent_id)
      ├── Fix ensure_agent_id_in_frontmatter
      ├── Fix SingleAgentDeployer
      └── Fix configure.py

Phase 4: Consumer Updates
  ├── C5: CORE_AGENTS consolidation (depends on C1 for CORE_AGENTS)
  │   ├── Update toolchain_detector.py
  │   ├── Update agent_recommendation_service.py
  │   └── Delete templates/__init__.py
  │
  ├── C6: PM prompt fixes (depends on C1 for valid names)
  │   ├── Fix CLAUDE_MPM_OUTPUT_STYLE.md
  │   ├── Fix WORKFLOW.md
  │   ├── Fix PM_INSTRUCTIONS.md
  │   └── Fix system_context.py
  │
  └── C8: Normalization consolidation (depends on C1 + C3)
      ├── Simplify normalize_deployment_filename()
      ├── Replace _normalize_agent_name()
      └── Replace DynamicAgentRegistry.normalize_agent_id()

Phase 5: Verification & CI
  └── Drift detection tests (depends on all above)
      ├── test_agent_identity_drift.py
      ├── test_pm_prompt_agent_refs.py
      └── test_agent_type_coverage.py
```

---

## Phased Implementation Plan

### Phase 1: Foundation (CRITICAL -- everything depends on this)

**Goal**: Create the single source of truth module and remove dead archive code.

**Changes**:
1. Create `src/claude_mpm/core/agent_identity.py` with:
   - `AgentCategory` enum (12 values)
   - `AgentIdentity` dataclass
   - `AGENT_REGISTRY` (all 48 agents with correct `name:` values)
   - `CORE_AGENTS` frozenset (10 agents)
   - `get_agent_id()`, `get_name()`, `get_display_name()`, `parse_agent_category()`
2. Create `tests/core/test_agent_identity.py` with comprehensive tests
3. Delete `src/claude_mpm/agents/templates/archive/` (39 JSON files)
4. Delete `src/claude_mpm/agents/templates/__init__.py` (dead code)
5. Verify `pyproject.toml` norecursedirs still correct

**Files created**: 2
**Files deleted**: 40+
**Files modified**: 1 (pyproject.toml verification)
**Risk**: LOW -- new module added, dead code removed, no existing behavior changed

### Phase 2: Registry Integration

**Goal**: Wire the new identity module into existing name resolution.

**Changes**:
1. Refactor `agent_name_normalizer.py`:
   - Remove `CANONICAL_NAMES` dict (lines 21-75)
   - Update `normalize()` to delegate to `agent_identity.get_display_name()`
   - Update `to_task_format()` to delegate to `agent_identity.get_name()`
   - Keep `ALIASES` dict for backward compatibility
2. Replace `AgentType` in `models/agent_definition.py:25`:
   - Import `AgentCategory` from `agent_identity`
   - Add `AgentType = AgentCategory` alias
3. Replace `AgentType` in `core/unified_agent_registry.py:52`:
   - Import `AgentCategory` from `agent_identity`
   - Update `_safe_parse_agent_type()` -> `parse_agent_category()`
4. Update `agents_metadata.py` type strings to use `AgentCategory` or remove unused type fields

**Files modified**: 4
**Risk**: MEDIUM -- existing normalize() behavior changes for 10 agents. Run all tests. Key validation: `normalize("ticketing")` now returns `"ticketing_agent"` (correct for delegation) instead of `"Ticketing"` (wrong).

**Critical test**: After this phase, run:
```bash
uv run pytest tests/core/test_agent_name_normalizer.py -v
uv run pytest tests/ -k "agent_type or AgentType" -v
```

### Phase 3: Deployment Unification

**Goal**: Route all deployment through `deploy_agent_file()`.

**Changes**:
1. Modify `deployment_utils.py:83` -- `ensure_agent_id_in_frontmatter()` default `update_existing=True`
2. Modify `deployment_utils.py:36` -- Simplify `normalize_deployment_filename()` to use `get_agent_id()`
3. Modify `single_agent_deployer.py:38` -- Use `deploy_agent_file()` instead of inline normalization
4. Modify `configure.py:3081` -- Use `deploy_agent_file()` instead of `shutil.copy2`

**Files modified**: 3
**Risk**: MEDIUM -- deployment behavior changes. Test with:
```bash
uv run pytest tests/services/agents/test_deployment_utils.py -v
uv run pytest tests/ -k "deploy" -v
```

### Phase 4: Consumer Updates & PM Fixes

**Goal**: Fix all consumers and PM-facing references.

**Changes**:
1. Fix `toolchain_detector.py:137,162` -- Import CORE_AGENTS, normalize TOOLCHAIN_TO_AGENTS values
2. Fix `agent_recommendation_service.py:36` -- Import CORE_AGENTS
3. Fix `system_context.py:17-29` -- Rewrite agent guidance (correct format, no lowercase claim)
4. Fix `CLAUDE_MPM_OUTPUT_STYLE.md` -- 2 broken references
5. Fix `WORKFLOW.md` -- ~6 broken references
6. Fix `PM_INSTRUCTIONS.md` -- ~47 references (port from branch commit f392f54e)
7. Replace `_normalize_agent_name()` in `multi_source_deployment_service.py:29` with `get_agent_id()`
8. Replace `normalize_agent_id()` in `agent_registry.py:594` with `get_agent_id()`

**Files modified**: 8
**Risk**: LOW-MEDIUM -- PM prompt changes are high-visibility but don't affect code logic. Normalization replacements maintain identical behavior for all common cases.

### Phase 5: Verification & CI

**Goal**: Add drift detection to prevent regression.

**Changes**:
1. Create `tests/integration/test_agent_identity_drift.py`:
   - Assert AGENT_REGISTRY covers all deployed agents
   - Assert CORE_AGENTS is a subset of AGENT_REGISTRY
   - Assert no duplicate entries
2. Create `tests/integration/test_pm_prompt_agent_refs.py`:
   - Extract agent references from PM prompt files
   - Validate they match AGENT_REGISTRY name values
3. Create `tests/integration/test_agent_type_coverage.py`:
   - Assert all frontmatter `agent_type:` values parse to valid AgentCategory
   - Assert no silent fallbacks to SPECIALIZED (or document them)
4. Add extraction script `scripts/extract_agent_names.sh` (port from branch)

**Files created**: 4
**Risk**: LOW -- only adds tests, no behavior changes

---

## Risk Assessment Summary

| Phase | Risk | Primary Concern | Mitigation |
|-------|------|----------------|------------|
| Phase 1 | LOW | Dead code removal might break obscure references | Grep verification before deletion |
| Phase 2 | MEDIUM | normalize() behavior change for 10 agents | Test all normalizer consumers |
| Phase 3 | MEDIUM | Deployment path changes could affect agent availability | Test deployment end-to-end |
| Phase 4 | LOW-MEDIUM | PM prompt changes visible to users | Manual spot-check delegation |
| Phase 5 | LOW | Tests only | N/A |

### Cross-Cutting Risks

1. **Circular imports**: `agent_identity.py` must be importable without importing heavy modules. Keep it dependency-free (stdlib only).
2. **Test fixture breakage**: Many tests mock agent-related functions. Search for all mocks before refactoring.
3. **Upstream sync**: After changes, a `claude-mpm agents sync` will redeploy with new normalization. Existing `agent_id:` values will change. This is intentional and correct.

---

## Verification Checklist (Run After Each Phase)

```bash
# Full test suite
make test

# Specific agent-related tests
uv run pytest tests/core/test_agent_name_normalizer.py -v
uv run pytest tests/services/agents/test_deployment_utils.py -v
uv run pytest tests/ -k "agent" -n auto --timeout=60

# Grep for stale references (run after EVERY phase)
grep -rn "CANONICAL_NAMES" src/ --include="*.py"  # Should decrease each phase
grep -rn "AgentType\." src/ --include="*.py"      # Should migrate to AgentCategory
grep -rn "_agent\b" src/claude_mpm/agents/*.md     # Check frontmatter consistency
grep -rn "local-ops\b" src/claude_mpm/agents/*.md  # Verify PM prompt fixes

# Deployment smoke test
# (deploy agents to temp dir and verify filenames + frontmatter)
```

---

## Appendix A: Complete AGENT_REGISTRY Reference

All 48 agents with their correct identity values:

| agent_id | name (exact) | agent_type | is_core |
|----------|-------------|------------|---------|
| `engineer` | `Engineer` | ENGINEER | YES |
| `research` | `Research` | RESEARCH | YES |
| `qa` | `QA` | QA | YES |
| `documentation` | `Documentation Agent` | DOCUMENTATION | YES |
| `security` | `Security` | SECURITY | YES |
| `ops` | `Ops` | OPS | YES |
| `local-ops` | `Local Ops` | OPS | YES |
| `version-control` | `Version Control` | SYSTEM | YES |
| `ticketing` | `ticketing_agent` | SYSTEM | YES |
| `memory-manager` | `Memory Manager` | SYSTEM | YES |
| `python-engineer` | `Python Engineer` | ENGINEER | no |
| `golang-engineer` | `Golang Engineer` | ENGINEER | no |
| `java-engineer` | `Java Engineer` | ENGINEER | no |
| `javascript-engineer` | `Javascript Engineer` | ENGINEER | no |
| `typescript-engineer` | `Typescript Engineer` | ENGINEER | no |
| `rust-engineer` | `Rust Engineer` | ENGINEER | no |
| `ruby-engineer` | `Ruby Engineer` | ENGINEER | no |
| `php-engineer` | `Php Engineer` | ENGINEER | no |
| `phoenix-engineer` | `Phoenix Engineer` | ENGINEER | no |
| `nestjs-engineer` | `nestjs-engineer` | ENGINEER | no |
| `react-engineer` | `React Engineer` | ENGINEER | no |
| `nextjs-engineer` | `Nextjs Engineer` | ENGINEER | no |
| `svelte-engineer` | `Svelte Engineer` | ENGINEER | no |
| `dart-engineer` | `Dart Engineer` | ENGINEER | no |
| `tauri-engineer` | `Tauri Engineer` | ENGINEER | no |
| `visual-basic-engineer` | `Visual Basic Engineer` | ENGINEER | no |
| `refactoring-engineer` | `Refactoring Engineer` | REFACTORING | no |
| `prompt-engineer` | `Prompt Engineer` | ENGINEER | no |
| `api-qa` | `API QA` | QA | no |
| `web-qa` | `Web QA` | QA | no |
| `real-user` | `real-user` | QA | no |
| `clerk-ops` | `Clerk Operations` | OPS | no |
| `digitalocean-ops` | `DigitalOcean Ops` | OPS | no |
| `gcp-ops` | `Google Cloud Ops` | OPS | no |
| `vercel-ops` | `Vercel Ops` | OPS | no |
| `aws-ops` | `aws_ops_agent` | OPS | no |
| `project-organizer` | `Project Organizer` | SYSTEM | no |
| `agentic-coder-optimizer` | `Agentic Coder Optimizer` | SYSTEM | no |
| `tmux` | `Tmux Agent` | SYSTEM | no |
| `code-analyzer` | `Code Analysis` | ANALYSIS | no |
| `content` | `Content Optimization` | CONTENT | no |
| `product-owner` | `Product Owner` | PRODUCT | no |
| `web-ui` | `Web UI` | ENGINEER | no |
| `imagemagick` | `Imagemagick` | SPECIALIZED | no |
| `data-engineer` | `Data Engineer` | ENGINEER | no |
| `data-scientist` | `Data Scientist` | RESEARCH | no |
| `mpm-agent-manager` | `mpm_agent_manager` | SYSTEM | no |
| `mpm-skills-manager` | `mpm_skills_manager` | SYSTEM | no |

**Note**: The `name` column contains the EXACT value that must be used for `subagent_type` in delegation. Values like `ticketing_agent`, `aws_ops_agent`, `mpm_agent_manager`, `mpm_skills_manager`, `nestjs-engineer`, and `real-user` are intentionally non-standard -- they come from the upstream repo and are the values Claude Code actually resolves against.

---

## Appendix B: Migration Mapping for Existing Code

### Import Changes

```python
# BEFORE (scattered imports)
from claude_mpm.core.agent_name_normalizer import AgentNameNormalizer
from claude_mpm.models.agent_definition import AgentType
from claude_mpm.core.unified_agent_registry import AgentType as UnifiedAgentType

# AFTER (unified imports)
from claude_mpm.core.agent_identity import (
    AgentCategory,          # replaces both AgentType enums
    AGENT_REGISTRY,         # replaces CANONICAL_NAMES and AGENT_NAME_MAP
    CORE_AGENTS,            # replaces all CORE_AGENTS lists
    get_agent_id,           # replaces 5+ normalize functions
    get_name,               # for delegation (exact name: value)
    get_display_name,       # for UI/logs (Title Case)
    parse_agent_category,   # replaces _safe_parse_agent_type
)
# AgentNameNormalizer still works but delegates internally
```

### Behavioral Changes

| Scenario | Before | After | Breaking? |
|----------|--------|-------|-----------|
| `normalize("ticketing")` | `"Ticketing"` | `"ticketing_agent"` | YES (display change) |
| `normalize("gcp-ops")` | `"GCP Ops"` | `"Google Cloud Ops"` | YES (display change) |
| `to_task_format("ticketing")` | `"ticketing"` | `"ticketing_agent"` | YES (fixes bug) |
| `AgentType.CORE` | Available | `AgentCategory` has no CORE | YES (use `is_core` flag) |
| `AgentType.CUSTOM` | Catch-all | `AgentCategory.SPECIALIZED` | YES (rename) |
| `ensure_agent_id_in_frontmatter()` | Preserves stale IDs | Overwrites with correct IDs | YES (intentional fix) |
| CORE_AGENTS in toolchain_detector | 7 agents, `-agent` suffix | 10 agents, clean IDs | YES (fixes bugs) |

---

## Appendix C: Out of Scope (Upstream Changes)

These changes would further simplify the system but require modifying the upstream `claude-mpm-agents` repository:

1. **Fix 6 non-conforming `name:` values** to Title Case
2. **Fix `agent_id:` values** to match filename stems (kebab-case, no suffix)
3. **Fix `ticketing.md` `agent_type: documentation`** -> `system` or `ticketing`
4. **Rename 3 `-agent` suffixed source files** (content-agent, memory-manager-agent, tmux-agent)
5. **Add missing `author:` and `schema_version:` fields**

These are tracked as recommendations for Phase D in the consolidated findings document (Section 5, Phase D).

---

## Appendix D: Lessons Applied from Branch History

| Branch Lesson | How Applied in This Design |
|---------------|--------------------------|
| #1: Verify scope BEFORE implementing | Phase plan includes grep verification at every step |
| #2: `name:` field is sacred | `get_name()` returns EXACT upstream values, never "prettified" |
| #3: Two normalization systems worse than none | Single AGENT_REGISTRY replaces both CANONICAL_NAMES and AGENT_NAME_MAP |
| #4: Don't add to dead code -- remove it | Phase 1 deletes archive + templates/__init__.py immediately |
| #5: Test AFTER dust settles | Verification tests in Phase 5 (last), not Phase 1 |
| #6: Devil's advocate catches real bugs | Architecture reviewed by devil's advocate (task #4) |
| #7: `agents deploy` was broken | Phase 3 unifies all deployment through proven `deploy_agent_file()` |
| #8: Upstream name values are messy | Design explicitly handles ugly names via `get_name()` vs `get_display_name()` separation |
