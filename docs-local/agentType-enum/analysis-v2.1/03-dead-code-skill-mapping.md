# Dead Code: Skill Mapping System Analysis

**Date**: 2026-03-03
**Session**: Interactive Q&A investigation
**New finding**: Not covered in analysis-v2

---

## Executive Summary

The skill mapping system in `skill_manager.py` is effectively dead code due to a directory path mismatch. The JSON templates it's designed to read are in `templates/archive/`, but it scans `templates/` (top-level). This finding extends the `type` vs `agent_type` analysis because the JSON templates that use `agent_type` were supposed to feed the skill mapping system — but they never do.

---

## The Path Bug

### Code Location
`src/claude_mpm/skills/skill_manager.py`, lines 25-59

### The Problem

```python
def _load_agent_mappings(self):
    """Load skill mappings from agent templates."""
    agent_templates_dir = Path(__file__).parent.parent / "agents" / "templates"
    #                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    # Resolves to: src/claude_mpm/agents/templates/
    # This directory contains ONLY .md files (documentation templates)
    # The JSON files are in templates/archive/

    for template_file in agent_templates_dir.glob("*.json"):
        # *.json does NOT recurse into subdirectories
        # Result: ZERO files found, ZERO mappings loaded
```

### Directory Contents

```
src/claude_mpm/agents/templates/
├── circuit-breakers.md          # Documentation template
├── git-file-tracking.md         # Documentation template
├── research-gate-examples.md    # Documentation template
├── archive/                     # <-- JSON files are HERE
│   ├── api_qa.json
│   ├── code_analyzer.json
│   ├── dart_engineer.json
│   ├── golang_engineer.json
│   ├── ... (39 JSON files total)
│   └── web_ui.json
└── (no .json files at top level)
```

### Fix Would Be

Either:
```python
# Option A: Scan archive subdirectory
agent_templates_dir = Path(__file__).parent.parent / "agents" / "templates" / "archive"

# Option B: Use recursive glob
for template_file in agent_templates_dir.glob("**/*.json"):
```

But given the system is labeled "Legacy" (see below), fixing it may not be worthwhile.

---

## Legacy Status

### Package Declaration

```python
# src/claude_mpm/skills/__init__.py

"""
New Skills Integration System:
- SkillsService: Core service for skill management
- AgentSkillsInjector: Dynamic skill injection into agent templates

Legacy System (maintained for compatibility):
- Skill: Dataclass for skill representation
- SkillManager: Legacy skill manager          # <-- THIS
- get_registry: Legacy registry access
"""
```

### The "New" System Is Also Unwired

`AgentSkillsInjector` (the intended replacement) is:
- Defined in `src/claude_mpm/skills/agent_skills_injector.py`
- Only referenced in documentation files (`docs/`)
- **Never imported by any deployment, startup, or hook code**
- Also effectively dead code from a runtime perspective

---

## Usage Analysis

### Where SkillManager Is Called

| Location | When Triggered | What Happens |
|---|---|---|
| `cli/commands/configure.py` line 678 | `claude-mpm configure` → "Skills Management" menu | `get_manager()` creates singleton; `_load_agent_mappings()` finds 0 JSON files; all mapping-dependent features show empty results |
| `cli/interactive/skills_wizard.py` line 83 | Interactive skill configuration wizard | Same as above; wizard falls back to registry-based skill discovery instead |

### Where SkillManager Is NOT Called

| System | Expected? | Status |
|---|---|---|
| Startup / hooks | No | Never initialized during `claude-mpm` boot |
| Agent deployment | No | `AgentTemplateBuilder` handles skills independently |
| `claude-mpm skills` command | No | Uses `GitSkillSourceManager` instead |
| Runtime skill loading | No | Claude Code reads frontmatter directly |

---

## Impact on User-Facing Features

When a user runs `claude-mpm configure` and navigates to "Skills Management":

### Option 2: "Configure skills for agents"
- Runs `SkillsWizard.run_interactive_selection()`
- SkillManager has 0 mappings from JSON templates
- Falls back to registry-based discovery (which works independently)
- **User impact**: Feature works via fallback, but JSON template mappings are invisible

### Option 3: "View current skill mappings"
- Calls `manager.list_agent_skill_mappings()`
- Returns empty dict `{}`
- Displays: `[dim]No skill mappings configured yet.[/dim]`
- **User impact**: Always shows empty, even though skills ARE configured in deployed agents

### Option 4: "Auto-link skills to agents"
- Uses `infer_agents_for_skill()` which works on content matching (not JSON templates)
- **User impact**: Works independently of the bug

---

## How Skills Actually Flow (The Real Path)

```
Developer Session
    ↓ Manually edits archive JSON: "skills": ["toolchains-java-core", ...]
    ↓
Archive JSON Templates (src/claude_mpm/agents/templates/archive/)
    ↓ (not read by SkillManager due to path bug)
    ↓
Remote Agents Repo (bobmatnyc/claude-mpm-agents)
    ↓ Skills defined in agent markdown frontmatter
    ↓
Git Cache (~/.claude-mpm/cache/agents/)
    ↓ skills: [toolchains-java-core, ...]
    ↓
AgentTemplateBuilder
    ↓ Reads skills from template, writes to deployed markdown
    ↓
Deployed Agent (.claude/agents/golang-engineer.md)
    ↓ skills: [toolchains-java-core, ...]
    ↓
Claude Code Runtime
    ↓ Reads skills from frontmatter
    ↓ Loads matching SKILL.md files from .claude/skills/
    ↓
Agent gets skill content injected

SkillManager (skill_manager.py) ← BYPASSED entirely
AgentSkillsInjector              ← BYPASSED entirely
```

---

## Relationship to type vs agent_type Investigation

### Why This Matters

The JSON templates in `archive/` use `agent_type` as their field name. The skill mapping system was designed to read these JSON templates and use the `agent_type` (or `agent_id`) field to map agents to skills:

```python
# Line 42-43 of skill_manager.py
agent_id = agent_data.get("agent_id") or agent_data.get("agent_type")
```

If the path bug were fixed, SkillManager would:
1. Read JSON files from `archive/`
2. Extract `agent_type` values like `"engineer"`, `"qa"`, `"research"`
3. Map skills to agents using these `agent_type` values as keys
4. The mapping keys would be `agent_type` values, creating another code path that depends on `agent_type`

This means:
- **Standardizing to `type`** would also require updating this code if ever reactivated
- **The JSON templates are the single source that uses `agent_type`** in the skill mapping context
- **The dead code status shields the system from the field name inconsistency** — but reactivation would expose it

---

## Recommendations

### Option A: Remove Dead Code (Recommended)
- Delete `SkillManager` class or mark as deprecated more explicitly
- The actual skill flow (AgentTemplateBuilder → frontmatter → Claude Code) works correctly
- The "New" `AgentSkillsInjector` should either be wired in or also removed

### Option B: Fix the Path Bug
- Change line 28 to point to `templates/archive/`
- Useful if the configure UI should show skill mappings from JSON templates
- Would create a new dependency on the `agent_type` field name

### Option C: Wire in AgentSkillsInjector
- Complete the "New Skills Integration System" that was designed but never connected
- Most architecturally sound but highest effort
- Would need to decide on `type` vs `agent_type` field naming first
