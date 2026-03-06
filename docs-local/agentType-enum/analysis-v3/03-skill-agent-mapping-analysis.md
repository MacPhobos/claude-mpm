# Skill-to-Agent Mapping System: Complete Analysis

**Date**: 2026-03-03
**Author**: skill-analyst (Research Agent, team agenttype-enum-v3)
**Task**: Task #3 — Analyze skill-to-agent mapping system in detail
**Supplements**: analysis-v2 (5 documents), analysis-v2.1 (5 documents)

---

## Executive Summary

The skill-to-agent mapping system in claude-mpm has **three independent mapping mechanisms**, all of which are effectively dormant or dead code. The actual runtime skill assignment bypasses all three systems entirely, flowing through a simple frontmatter-based pipeline: source template `skills:` field -> AgentTemplateBuilder -> deployed markdown `skills:` field -> Claude Code runtime.

**Critical finding**: Changing deployed agent frontmatter from `type:` to `agent_type:` will **NOT break skill matching**. The skill-to-agent join is performed using agent names/IDs (e.g., `python-engineer`, `golang_engineer`), never via the `type`/`agent_type` field value. All three mapping systems are dead code at runtime.

---

## Table of Contents

1. [Skill System Architecture Overview](#1-skill-system-architecture-overview)
2. [Three Skill Mapping Systems](#2-three-skill-mapping-systems)
3. [The Actual Runtime Skill Flow](#3-the-actual-runtime-skill-flow)
4. [Field Name Impact Analysis](#4-field-name-impact-analysis)
5. [Agent Naming Inconsistencies in Skill Registries](#5-agent-naming-inconsistencies-in-skill-registries)
6. [Key Questions Answered](#6-key-questions-answered)
7. [Risk Assessment](#7-risk-assessment)
8. [Recommendations](#8-recommendations)

---

## 1. Skill System Architecture Overview

The skills package (`src/claude_mpm/skills/`) contains two labeled generations of code:

### Package Declaration (`skills/__init__.py`)

```python
"""
New Skills Integration System:
- SkillsService: Core service for skill management
- AgentSkillsInjector: Dynamic skill injection into agent templates

Legacy System (maintained for compatibility):
- Skill: Dataclass for skill representation
- SkillManager: Legacy skill manager
- get_registry: Legacy registry access
"""
```

### Components Inventory

| Component | File | Status | Uses `type`/`agent_type`? |
|---|---|---|---|
| SkillManager | `skill_manager.py` | Dead code (path bug) | Yes — `agent_type` as fallback key |
| AgentSkillsInjector | `agent_skills_injector.py` | Unwired (never imported) | No — uses `agent_id` only |
| SkillsRegistry (dataclass) | `registry.py` | Active but mapping unused | Has `agent_types: List[str]` field |
| SkillsService | `skills_service.py` | Active for registry lookup | Uses `agent_id` for lookup |
| SkillsRegistryHelper | `skills_registry.py` | Active for registry lookup | Uses `agent_id` for lookup |
| skills_registry.yaml | `_archive/config/` | Archived | Uses underscore agent IDs |
| skill_to_agent_mapping.yaml | `config/` | Active for deployment filtering | Uses kebab-case agent names |

---

## 2. Three Skill Mapping Systems

### System A: SkillManager (Legacy — Dead Code)

**File**: `src/claude_mpm/skills/skill_manager.py`

**Status**: Dead code due to a path bug. Loads zero agent-to-skill mappings on every initialization.

**The Path Bug** (lines 25-37):
```python
def _load_agent_mappings(self):
    """Load skill mappings from agent templates."""
    agent_templates_dir = Path(__file__).parent.parent / "agents" / "templates"
    # Resolves to: src/claude_mpm/agents/templates/
    # This directory contains ONLY .md files
    # JSON files are in templates/archive/

    for template_file in agent_templates_dir.glob("*.json"):
        # *.json does NOT recurse into subdirectories
        # Result: ZERO files found, ZERO mappings loaded
```

**How it maps agents to skills** (lines 42-43):
```python
agent_id = agent_data.get("agent_id") or agent_data.get("agent_type")
# Uses agent_id as primary key, falls back to agent_type VALUE
# e.g., "golang_engineer" or "engineer" — NOT the field name
```

**Key method** (lines 130-140):
```python
def get_agent_skills(self, agent_type: str) -> List[Skill]:
    """Get skills mapped to a specific agent type."""
    skill_names = self.agent_skill_mapping.get(agent_type, [])
    # agent_type parameter is an agent ID string, NOT the frontmatter field
    # With 0 mappings loaded, always returns empty list
```

**Where it's called** (only 2 places, both in configure UI):
- `cli/commands/configure.py` line 678 — Skills Management menu
- `cli/interactive/skills_wizard.py` line 83 — Interactive wizard

**Where it's NOT called**: startup, deployment, runtime, hooks.

**Impact of `type` → `agent_type` change**: None. System is dead code.

---

### System B: AgentSkillsInjector (New — Unwired)

**File**: `src/claude_mpm/skills/agent_skills_injector.py`

**Status**: Designed as replacement for SkillManager but never connected to the deployment pipeline or runtime.

**How it identifies agents** (lines 96-102):
```python
agent_id = template.get("agent_id")
if not agent_id:
    self.logger.error(f"Template missing agent_id: {template_path}")
    return template

# Get skills by agent_id — NOT by type or agent_type
skills = self.skills_service.get_skills_for_agent(agent_id)
```

**Key observation**: Uses `agent_id` exclusively. Does NOT read `type` or `agent_type` from templates.

**Where it's referenced**: Only in documentation files (`docs/`). Never imported by deployment, startup, or hook code.

**Impact of `type` → `agent_type` change**: None. System is unwired.

---

### System C: SkillsService + SkillsRegistryHelper (Active — Registry Lookup)

**File**: `src/claude_mpm/skills/skills_service.py` and `skills_registry.py`

**Status**: Active code, but the registry data (YAML files) is what drives the mapping.

**SkillsService.get_skills_for_agent()** (lines 328-353):
```python
def get_skills_for_agent(self, agent_id: str) -> List[str]:
    """Get list of skills for an agent by agent_id."""
    agent_skills = self.registry["agent_skills"].get(agent_id, {})
    required = agent_skills.get("required", [])
    optional = agent_skills.get("optional", [])
    return required + optional
```

**SkillsRegistryHelper.get_agent_skills()** (lines 87-110):
```python
def get_agent_skills(self, agent_id: str) -> List[str]:
    """Get skills for a specific agent."""
    agent_skills = self.data.get("agent_skills", {}).get(agent_id, {})
    required = agent_skills.get("required", [])
    optional = agent_skills.get("optional", [])
    return required + optional
```

**Key observation**: Both use `agent_id` string for lookup — NOT the `type`/`agent_type` field value.

**Impact of `type` → `agent_type` change**: None. Lookup is by agent name/ID.

---

### Skill Dataclass (`registry.py`)

The `Skill` dataclass (line 62) has an `agent_types` field:

```python
@dataclass
class Skill:
    name: str
    description: str
    path: str
    # ... other fields ...
    agent_types: List[str] = None  # Which agent types can use this skill
```

And the `SkillsRegistry.get_skills_for_agent()` method (lines 454-470):

```python
def get_skills_for_agent(self, agent_type: str) -> List[Skill]:
    """Get skills available for a specific agent type."""
    return [
        skill for skill in self.skills.values()
        if not skill.agent_types or agent_type in skill.agent_types
    ]
```

**Key observation**: The `agent_type` parameter name is misleading — it's actually an agent **name/ID** string used to filter skills. The `agent_types` field on `Skill` contains a list of agent names that can use the skill (e.g., `["python-engineer", "data-scientist"]`), not AgentType enum values.

---

## 3. The Actual Runtime Skill Flow

All three mapping systems above are bypassed at runtime. The actual skill assignment chain is:

```
Step 1: Remote Agent Source (GitHub repo)
    └── bobmatnyc/claude-mpm-agents/agents/golang-engineer.md
        └── frontmatter: skills: [golang-cli-cobra-viper, golang-database-patterns, ...]

Step 2: Git Sync (GitSourceSyncService)
    └── ~/.claude-mpm/cache/agents/bobmatnyc/claude-mpm-agents/agents/
        └── Skills preserved in cached markdown

Step 3: AgentTemplateBuilder.build_agent_markdown()
    └── src/claude_mpm/services/agents/deployment/agent_template_builder.py
    └── Lines 589-595:
        # CRITICAL: Preserve skills field from template for selective skill deployment
        skills = template_data.get("skills", [])
        if skills and isinstance(skills, list):
            frontmatter_lines.append("skills:")
            for skill in skills:
                frontmatter_lines.append(f"- {skill}")

Step 4: Deployed Agent Markdown
    └── .claude/agents/golang-engineer.md
        └── frontmatter: skills: [golang-cli-cobra-viper, golang-database-patterns, ...]

Step 5: Claude Code Runtime
    └── Reads skills: field from deployed agent frontmatter
    └── Loads matching SKILL.md files from .claude/skills/
    └── Injects skill content into agent context

BYPASSED:
    ✗ SkillManager (dead code — path bug)
    ✗ AgentSkillsInjector (unwired — never imported)
    ✗ SkillsService/SkillsRegistryHelper (active code but not in this path)
```

### Evidence: Skills Field Preservation

The `skills:` field passes through the deployment pipeline **unchanged**:

| Stage | Field | Example Value |
|---|---|---|
| Remote source | `skills:` | `[golang-cli-cobra-viper, golang-database-patterns, ...]` |
| Git cache | `skills:` | `[golang-cli-cobra-viper, golang-database-patterns, ...]` |
| AgentTemplateBuilder output | `skills:` | `[golang-cli-cobra-viper, golang-database-patterns, ...]` |
| Deployed agent | `skills:` | `[golang-cli-cobra-viper, golang-database-patterns, ...]` |

The skill names are **skill directory names** (matching `.claude/skills/<name>/SKILL.md`), not agent type values.

### Evidence: SKILL.md Files Have No Agent Type References

Searched all 189 skill directories in `.claude/skills/`:
- `grep -r "agent_type" .claude/skills/*/SKILL.md` — **0 matches**
- `grep -r "^type:" .claude/skills/*/SKILL.md` — **0 matches**

SKILL.md files contain skill instructions and metadata, but do NOT reference the `type` or `agent_type` field of agents.

### Evidence: manifest.json Files

Only 2 manifest.json files exist (both in `skills/bundled/pm/`):
- `mpm-message/manifest.json` — `"type": "framework"` (this is skill type, not agent type)
- `mpm-tool-usage-guide/manifest.json` — `"type": "framework"` (same)

These manifest files describe the skill's own type classification, not agent type references.

---

## 4. Field Name Impact Analysis

### The Core Question

**If we change deployed agents from `type: engineer` to `agent_type: engineer`, does skill matching break?**

### Answer: No.

Here's why, system by system:

| System | Reads `type`? | Reads `agent_type`? | Impact of Change |
|---|---|---|---|
| Runtime skill flow | No (reads `skills:` field) | No | **None** |
| SkillManager | No (dead code) | Would read if path fixed | **None** |
| AgentSkillsInjector | No (reads `agent_id`) | No | **None** |
| SkillsService | No (reads by agent_id) | No | **None** |
| skill_to_agent_mapping.yaml | No (uses agent name) | No | **None** |
| skills_registry.yaml | No (uses agent ID) | No | **None** |
| SKILL.md files | No | No | **None** |
| manifest.json | No (different `type` field) | No | **None** |

### The Only Code That Reads `agent_type` in Skill Context

**SkillManager line 42** (dead code):
```python
agent_id = agent_data.get("agent_id") or agent_data.get("agent_type")
```

This reads `agent_type` from JSON templates as a **fallback lookup key** when `agent_id` is missing. But:
1. This code never executes (path bug)
2. It reads from JSON templates, not deployed agent frontmatter
3. The `agent_type` value used would be a role name (e.g., "engineer"), not a field name

### Claude Code Platform Behavior

Claude Code (the platform runtime) reads these frontmatter fields from deployed `.claude/agents/*.md` files:
- `name` — agent name for selection
- `description` — agent description for display
- `tools` — tool restrictions
- `model` — model override
- `skills` — skill list to load

Claude Code does **NOT** read `type` or `agent_type` from agent frontmatter. These fields are used only by claude-mpm's internal systems.

---

## 5. Agent Naming Inconsistencies in Skill Registries

While `type`/`agent_type` field naming does NOT affect skill matching, there is a **separate naming inconsistency** in skill registries worth documenting:

### Two Naming Conventions

**skills_registry.yaml** (`_archive/config/`) uses UNDERSCORE agent IDs:
```yaml
agent_skills:
  engineer:
    required: [test-driven-development, systematic-debugging]
  python_engineer:       # UNDERSCORE
    required: [test-driven-development, systematic-debugging]
  golang_engineer:       # UNDERSCORE
    required: [test-driven-development, systematic-debugging]
  web_qa:                # UNDERSCORE
    required: [webapp-testing, test-driven-development]
```

**skill_to_agent_mapping.yaml** (`src/claude_mpm/config/`) uses KEBAB-CASE agent names:
```yaml
skill_mappings:
  toolchains/golang/cli:
    - golang-engineer    # KEBAB
  toolchains/python/testing/pytest:
    - python-engineer    # KEBAB
  universal/testing/webapp-testing:
    - web-qa             # KEBAB

all_agents_list:
  - python-engineer      # KEBAB
  - golang-engineer      # KEBAB
```

### Impact

- `skills_registry.yaml` is in `_archive/` — likely no longer actively used
- `skill_to_agent_mapping.yaml` is active and uses the Gen 1 kebab-case names
- The Gen 2 underscore agent IDs (e.g., `golang_engineer`) match `skills_registry.yaml` but NOT `skill_to_agent_mapping.yaml`
- The Gen 1 kebab-case names (e.g., `golang-engineer`) match `skill_to_agent_mapping.yaml` but NOT `skills_registry.yaml`
- This inconsistency would matter if both registries were actively used for the same lookup — but `skills_registry.yaml` appears archived

### Relationship to `type`/`agent_type`

This naming inconsistency is **orthogonal** to the `type`/`agent_type` field name split. The registries use agent **names/IDs** for lookup, not the frontmatter field name or its value. Fixing the `type`/`agent_type` split will not fix or worsen this naming inconsistency.

---

## 6. Key Questions Answered

### Q1: When a skill references an agent, does it use `type` or `agent_type`?

**Answer**: Neither. Skills reference agents by **name/ID string** (e.g., `python-engineer`, `golang_engineer`, `engineer`). The `type`/`agent_type` frontmatter field is not used in any skill-to-agent mapping.

Evidence:
- `skill_to_agent_mapping.yaml` — maps skill paths to agent names (kebab-case)
- `skills_registry.yaml` — maps agent IDs (underscore) to skill lists
- `SkillsService.get_skills_for_agent(agent_id)` — takes agent ID string
- `SKILL.md` files — contain no agent type references
- `manifest.json` files — use `type` for skill classification, not agent type

### Q2: If we change deployed agents from `type` to `agent_type`, does skill matching break?

**Answer**: No. The runtime skill flow reads the `skills:` frontmatter field (which lists skill names), not `type` or `agent_type`. All three skill mapping systems are either dead code or use agent names for lookup.

### Q3: Where in the code is the skill-to-agent join performed?

**Answer**: There are four potential join points, all using agent name/ID:

| Location | Method | Join Key | Status |
|---|---|---|---|
| `skill_manager.py:42` | `_load_agent_mappings()` | `agent_id` or `agent_type` value | Dead code (path bug) |
| `skills_service.py:328` | `get_skills_for_agent()` | `agent_id` string | Active but not in runtime path |
| `skills_registry.py:87` | `get_agent_skills()` | `agent_id` string | Active but not in runtime path |
| `registry.py:454` | `get_skills_for_agent()` | `agent_type` string (actually agent name) | Active for filtering |

The **actual runtime join** happens implicitly in Claude Code: it reads the `skills:` field from deployed agent frontmatter and loads matching `SKILL.md` files from `.claude/skills/`. No programmatic join via claude-mpm code.

### Q4: Are there any hardcoded `type` references in the skill system?

**Answer**: No hardcoded `type` references that would break. The only relevant reference is:

- `skill_manager.py:42`: `agent_data.get("agent_type")` — reads `agent_type` from JSON templates as fallback key. This is dead code (path bug) and reads from JSON files, not deployed agent frontmatter.
- `manifest.json` files use `"type": "framework"` — this describes the skill's own classification, completely unrelated to agent type.

---

## 7. Risk Assessment

### Risk: Reactivating Dead Code

If someone fixes the SkillManager path bug (changing the directory to `templates/archive/`), the system would:
1. Read JSON templates from `archive/`
2. Use `agent_data.get("agent_id") or agent_data.get("agent_type")` as mapping key
3. For templates with `agent_id` (e.g., `"agent_id": "golang_engineer"`): use that as key
4. For templates without `agent_id`: fall back to `agent_type` value (e.g., `"engineer"`)

**Risk level**: Low. The path bug fix would need to be intentional, and the mapping behavior uses agent_id first.

### Risk: AgentSkillsInjector Gets Wired In

If someone connects AgentSkillsInjector to the deployment pipeline:
1. It reads `agent_id` from templates exclusively
2. Does NOT read `type` or `agent_type`
3. Would NOT be affected by the field name change

**Risk level**: None for `type`/`agent_type` change.

### Risk: New Code Reads `type` from Deployed Agents

If future code reads the `type` field from deployed agents for skill routing:
1. After standardization to `agent_type`, the `type` field would no longer exist
2. New code would need to use `agent_type` instead

**Risk level**: Low. Standard practice would be to check the standardized field name.

### Risk: Naming Convention Confusion

The three naming conventions in agent identifiers could cause confusion:
- Kebab-case: `golang-engineer` (Gen 1 deployed, `skill_to_agent_mapping.yaml`)
- Underscore: `golang_engineer` (Gen 2 deployed, `skills_registry.yaml`, JSON templates)
- Bare role: `engineer` (frontmatter `type`/`agent_type` value)

**Risk level**: Medium. Not caused by `type`/`agent_type` change, but worth addressing as part of broader cleanup.

---

## 8. Recommendations

### For the `type` → `agent_type` Standardization

1. **Proceed with confidence** — The skill system will NOT be affected by changing `type:` to `agent_type:` in deployed agent frontmatter.

2. **No skill-related code changes needed** — None of the skill mapping systems read the `type`/`agent_type` field from deployed agents.

3. **The `skills:` frontmatter field is independent** — It passes through the deployment pipeline unchanged and is the sole mechanism for skill assignment at runtime.

### For Skill System Cleanup (Separate from `type`/`agent_type`)

4. **Remove or explicitly deprecate SkillManager** — The path bug makes it dead code. Either fix the bug or remove the class. The current state is confusing (labeled "legacy" but not marked as deprecated).

5. **Decide on AgentSkillsInjector** — Either wire it into the deployment pipeline or remove it. Having an unwired "new system" alongside a broken "legacy system" is technical debt.

6. **Standardize agent naming in registries** — Unify on kebab-case (matching Gen 1/deployed agents) or underscore (matching Gen 2/JSON templates). Currently:
   - `skill_to_agent_mapping.yaml` uses kebab-case
   - `skills_registry.yaml` (archived) uses underscore
   - These should be consistent after duplicate agents are cleaned up

7. **Document the actual skill flow** — The runtime skill assignment bypasses all three mapping systems. This should be documented in the codebase to prevent future developers from trying to use or fix the dead systems.

---

## Appendix A: Complete Code Path Trace

### `type`/`agent_type` References in Skill Code

| File | Line | Code | Context |
|---|---|---|---|
| `skill_manager.py` | 42 | `agent_data.get("agent_type")` | Fallback key in dead code |
| `skill_manager.py` | 130 | `def get_agent_skills(self, agent_type: str)` | Parameter name (takes agent ID) |
| `skill_manager.py` | 140 | `self.agent_skill_mapping.get(agent_type, [])` | Dict lookup by agent ID |
| `registry.py` | 62 | `agent_types: List[str] = None` | Skill dataclass field (agent names list) |
| `registry.py` | 454 | `def get_skills_for_agent(self, agent_type: str)` | Parameter name (takes agent name) |
| `registry.py` | 459 | `agent_type in skill.agent_types` | Membership check (agent name in list) |

### Files with NO `type`/`agent_type` References

| File | Confirmed Clean |
|---|---|
| `agent_skills_injector.py` | Uses `agent_id` only |
| `skills_service.py` | Uses `agent_id` only |
| `skills_registry.py` | Uses `agent_id` only |
| `.claude/skills/*/SKILL.md` (189 files) | No agent type references |
| `skills/bundled/pm/*/manifest.json` | Uses `type` for skill classification |
| `skill_to_agent_mapping.yaml` | Uses agent names only |

---

## Appendix B: Deployed Skill Directories

189 skill directories exist in `.claude/skills/`, each containing a `SKILL.md` file. These are loaded by Claude Code at runtime when an agent's `skills:` frontmatter lists their name. None contain agent type field references.

Example skill directory structure:
```
.claude/skills/
├── golang-cli-cobra-viper/
│   └── SKILL.md
├── golang-database-patterns/
│   └── SKILL.md
├── test-driven-development/
│   └── SKILL.md
├── webapp-testing/
│   └── SKILL.md
└── ... (189 total)
```

---

## Appendix C: Relationship to Previous Research

### From analysis-v2.1/03-dead-code-skill-mapping.md
- **Confirmed**: SkillManager path bug (scans `templates/*.json`, files in `templates/archive/*.json`)
- **Confirmed**: AgentSkillsInjector is unwired
- **Extended**: Traced complete skill flow including `skills_registry.yaml` and `skill_to_agent_mapping.yaml`
- **New finding**: Agent naming inconsistency between registries (underscore vs kebab-case)

### From analysis-v2/03-standardization-impact.md
- **Confirmed**: Skill system is NOT a blocker for `type` → `agent_type` standardization
- **Extended**: Provided concrete evidence from all code paths and data files
- **New finding**: `Skill.agent_types` field uses agent names, not AgentType enum values

### From analysis-v2.1/04-remote-agent-source-analysis.md
- **Confirmed**: `agent_type` values in remote agents are functional roles (e.g., "engineer", "ops")
- **Extended**: These values are NOT used for skill matching — skill matching uses full agent names
