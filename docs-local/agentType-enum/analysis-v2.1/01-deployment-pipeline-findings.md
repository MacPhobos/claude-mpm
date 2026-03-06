# Deployment Pipeline Findings: Field Name Translation & Duplicate Agents

**Date**: 2026-03-03
**Session**: Interactive Q&A investigation of agent deployment mechanics
**Status**: New findings that supplement analysis-v2

---

## Executive Summary

This investigation uncovered the complete lifecycle of how agents are deployed, revealing:

1. **AgentTemplateBuilder silently converts `agent_type` to `type`** during deployment
2. **Three distinct generations of agent files** coexist in `.claude/agents/`
3. **14 duplicate agent pairs** exist (same logical agent, different files/schemas)
4. **The skill mapping system via `skill_manager.py` is dead code** due to a path bug
5. **All 48 remote agents use `agent_type:`** but get converted to `type:` during deployment

These findings materially change the understanding from analysis-v2, particularly regarding the root cause of the `type` vs `agent_type` split.

---

## Finding 1: AgentTemplateBuilder Field Name Translation

### The Conversion

`AgentTemplateBuilder` in `src/claude_mpm/services/agents/deployment/agent_template_builder.py` performs a silent field name translation:

- **Line 493**: Reads `agent_type` from source template:
  ```python
  agent_type = template_data.get("agent_type", "general")
  ```

- **Line 567-568**: Writes `type` to deployed markdown frontmatter:
  ```python
  if agent_type and agent_type != "general":
      frontmatter_lines.append(f"type: {agent_type}")
  ```

### Verified Conversion Chain

```
Remote source (git cache)          → AgentTemplateBuilder      → Deployed agent
agent_type: engineer                 reads "agent_type"           type: engineer
```

**Evidence** (sampled from live deployment):

| Remote Source File | Remote Field | Deployed File | Deployed Field |
|---|---|---|---|
| golang-engineer.md | `agent_type: engineer` | golang-engineer.md | `type: engineer` |
| research.md | `agent_type: research` | research.md | `type: research` |
| security.md | `agent_type: security` | security.md | `type: security` |
| qa.md | `agent_type: qa` | qa.md | `type: qa` |
| documentation.md | `agent_type: documentation` | documentation.md | `type: documentation` |

### Impact on analysis-v2

Analysis-v2 section 5 ("Code Path #5: AgentTemplateBuilder") identified this conversion but this session **confirms it with live data**: ALL 48 remote agents use `agent_type:`, and ALL deployed kebab-case agents use `type:`. The conversion is 100% consistent for the primary deployment path.

---

## Finding 2: Three Generations of Agent Files

The `.claude/agents/` directory contains **76 agent files** from three distinct deployment mechanisms:

### Generation 1: AgentTemplateBuilder Output (45 files)
- **Naming**: kebab-case (`golang-engineer.md`, `rust-engineer.md`)
- **Field**: `type: engineer`
- **Schema**: Simple frontmatter (name, description, type, version, skills)
- **Source**: Remote git cache → processed by AgentTemplateBuilder
- **Content size**: Large (~30KB, ~860 lines) - includes full instructions + BASE_AGENT

### Generation 2: Migration Script Output (14 files)
- **Naming**: underscore (`golang_engineer.md`, `rust_engineer.md`)
- **Field**: `agent_type: engineer`
- **Schema**: Rich frontmatter (`schema_version: 1.3.0`, `agent_id`, `resource_tier`, `tags`, `category`, `color`, etc.)
- **Source**: JSON templates from `src/claude_mpm/agents/templates/archive/` processed by `scripts/migrate_json_to_markdown.py`
- **Content size**: Smaller (~10KB, ~285 lines) - instructions only, no BASE_AGENT

### Generation 3: Legacy Deployed Agents (12 files with `-agent` suffix)
- **Naming**: kebab-case with `-agent` suffix (`qa-agent.md`, `research-agent.md`)
- **Field**: `agent_type: engineer/qa/research/etc.`
- **Schema**: Mixed (`schema_version: 1.2.0` or `1.3.0`)
- **Source**: Earlier deployment generation (pre-current pipeline)
- **Note**: Most have corresponding Gen 1 counterparts without `-agent` suffix

### Additional files (5)
- Files like `content-agent.md`, `memory-manager-agent.md`, `tmux-agent.md` that only exist in `-agent` form (no duplicate counterpart)

### Counts

| Generation | Count | Field Name | Naming Pattern |
|---|---|---|---|
| Gen 1 (AgentTemplateBuilder) | 45 | `type:` | kebab-case |
| Gen 2 (Migration script) | 14 | `agent_type:` | underscore |
| Gen 3 (Legacy -agent) | 12 | `agent_type:` | kebab-case + `-agent` suffix |
| Gen 3 (Unique -agent) | 5 | mixed | `-agent` suffix, no counterpart |
| **Total** | **76** | | |

---

## Finding 3: 14 Confirmed Duplicate Agent Pairs

Every underscore-named agent has an exact kebab-case counterpart:

| Underscore File (Gen 2) | Kebab File (Gen 1) | Size Difference |
|---|---|---|
| `dart_engineer.md` | `dart-engineer.md` | ~10KB vs ~30KB |
| `golang_engineer.md` | `golang-engineer.md` | 9,914B vs 30,561B |
| `java_engineer.md` | `java-engineer.md` | ~10KB vs ~30KB |
| `nestjs_engineer.md` | `nestjs-engineer.md` | ~10KB vs ~30KB |
| `nextjs_engineer.md` | `nextjs-engineer.md` | ~10KB vs ~30KB |
| `php_engineer.md` | `php-engineer.md` | ~10KB vs ~30KB |
| `product_owner.md` | `product-owner.md` | ~10KB vs ~30KB |
| `react_engineer.md` | `react-engineer.md` | ~10KB vs ~30KB |
| `real_user.md` | `real-user.md` | ~10KB vs ~30KB |
| `ruby_engineer.md` | `ruby-engineer.md` | ~10KB vs ~30KB |
| `rust_engineer.md` | `rust-engineer.md` | ~10KB vs ~30KB |
| `svelte_engineer.md` | `svelte-engineer.md` | ~10KB vs ~30KB |
| `tauri_engineer.md` | `tauri-engineer.md` | ~10KB vs ~30KB |
| `visual_basic_engineer.md` | `visual-basic-engineer.md` | ~10KB vs ~30KB |

Additionally, 12 `-agent` suffixed files have counterparts without the suffix (e.g., `qa-agent.md` ↔ `qa.md`).

### Schema Comparison (golang_engineer.md vs golang-engineer.md)

**Underscore (Gen 2 - Rich Schema)**:
```yaml
name: Golang Engineer
description: 'Go 1.23-1.24 specialist...'
version: 1.0.0
schema_version: 1.3.0
agent_id: golang_engineer
agent_type: engineer
resource_tier: standard
tags: [golang, go, concurrency, ...]
category: engineering
color: cyan
```

**Kebab (Gen 1 - Simple Schema)**:
```yaml
name: golang-engineer
description: "Use this agent when you need to implement..."
type: engineer
version: "1.0.0"
skills: [golang-cli-cobra-viper, golang-database-patterns, ...]
```

Key differences:
- Gen 2 has richer metadata (tags, category, color, resource_tier)
- Gen 1 has skills list and embedded example usage
- Gen 1 is ~3x larger due to full instructions + BASE_AGENT content

---

## Finding 4: Remote Agent Source (Git Cache)

### Location
```
~/.claude-mpm/cache/agents/bobmatnyc/claude-mpm-agents/agents/
```

### Key Facts
- **48 remote agents** discovered in the cache (excluding BASE-AGENT.md files)
- **ALL 48 use `agent_type:`** — not a single one uses `type:`
- These are the authoritative source for Generation 1 deployed agents
- AgentTemplateBuilder processes these and converts `agent_type` → `type`

### Remote Agent Field Values

The `agent_type` values in remote agents are **functional role names**, NOT the AgentType enum values (`core/project/custom/system/specialized`):

| agent_type value | Count | Examples |
|---|---|---|
| `engineer` | 19 | dart-engineer, golang-engineer, web-ui |
| `ops` | 8 | aws-ops, gcp-ops, vercel-ops, tmux-agent |
| `qa` | 3 | api-qa, qa, real-user |
| `research` | 2 | code-analyzer, research |
| `documentation` | 2 | documentation, ticketing |
| `security` | 1 | security |
| `specialized` | 1 | local-ops |
| `product` | 1 | product-owner |
| `analysis` | 1 | prompt-engineer |
| `refactoring` | 1 | refactoring-engineer |
| Other | 9 | Various unique values |

---

## Finding 5: JSON Templates in Archive Are Maintained Manually

### Location
```
src/claude_mpm/agents/templates/archive/*.json
```

### How They Are Used

1. **NOT used by the main deployment pipeline** — AgentDiscoveryService only scans for `*.md` files
2. **NOT used at runtime** — SkillManager path bug means zero JSON files are found (see Finding 6)
3. **Manually maintained** by the project developer working with Claude Code
4. **Used by the migration script** (`scripts/migrate_json_to_markdown.py`) to create Gen 2 underscore files
5. **Read by skills system** (`skills/skill_manager.py`) — but effectively dead (see Finding 6)

### Recent Commits to Archive Templates

```
ab05426a feat: add Java core skill and integrate with java-engineer and code-analyzer
8b14e146 feat: add language core skills and best-practice matching to code-analyzer
f99e3ecf feat: add language-specific core skills paired with engineer agents
9da8823b feat: move language-specific perf directives from BASE_AGENT to each engineer
f1d2364e feat: Migrate google-workspace-mcp to external gworkspace-mcp package
```

All commits are by Bob Matsuoka with `Co-Authored-By: Claude Opus 4.6` — indicating manual updates during development sessions, not automated processes.

### Purpose

The archive JSON templates serve as a **canonical reference** for agent definitions with rich metadata that isn't present in the deployed agents. They appear to be maintained as a source of truth even though the deployment pipeline no longer reads them directly.

---

## Finding 6: Skill Mapping System Is Dead Code

### The Path Bug

`SkillManager._load_agent_mappings()` (line 28 of `skill_manager.py`) scans:
```python
agent_templates_dir = Path(__file__).parent.parent / "agents" / "templates"
# Resolves to: src/claude_mpm/agents/templates/
```

Then line 37 globs for JSON:
```python
for template_file in agent_templates_dir.glob("*.json"):
```

**Result**: Zero files found. All JSON files are in `templates/archive/`, and `*.json` does not recurse into subdirectories.

### Already Labeled Legacy

```python
# src/claude_mpm/skills/__init__.py
"""
New Skills Integration System:
- SkillsService: Core service for skill management
- AgentSkillsInjector: Dynamic skill injection into agent templates

Legacy System (maintained for compatibility):
- SkillManager: Legacy skill manager   # <-- THIS
"""
```

### Usage Points

| Caller | When | Behavior |
|---|---|---|
| `configure.py` → `_manage_skills()` | `claude-mpm configure` → Skills menu | Initializes with 0 mappings; shows empty tables |
| `skills_wizard.py` | Interactive skill configuration | Falls back to registry-based discovery |
| **NOT called at startup** | — | Never initialized during boot |
| **NOT called during deployment** | — | AgentTemplateBuilder ignores it |

### The "New" System Is Also Unwired

`AgentSkillsInjector` (the replacement system) is only referenced in documentation files. It is never imported by any deployment, startup, or hook code. Both the legacy and new skill mapping systems are effectively dormant.

### How Skills Actually Get Assigned

The actual runtime skill assignment bypasses both systems entirely:

```
1. Developer manually edits JSON templates in archive/
   → "skills": ["toolchains-java-core", "test-driven-development"]

2. AgentTemplateBuilder reads skills from source template during deployment
   → writes to markdown frontmatter: skills: [toolchains-java-core, ...]

3. Claude Code reads deployed .md files at runtime
   → picks up skills: field from frontmatter
   → loads matching skill files from .claude/skills/
```

---

## Summary: Corrections to analysis-v2

| analysis-v2 Claim | Correction/Enhancement |
|---|---|
| "47 files use `type:`, 27 use `agent_type:`" | Updated count: 45 use `type:` (Gen 1), 14 underscore + 12 `-agent` + 5 unique use `agent_type:` (29 total). Plus 76 total files identified. |
| "Migration script creates the agent_type files" | Confirmed: underscore files come from migration script processing archive JSON. Additionally identified `-agent` suffix files as a third generation from earlier deployments. |
| "AgentTemplateBuilder converts agent_type to type" | **Confirmed with live data**: All 48 remote agents use `agent_type:`, all 45 Gen 1 deployed agents use `type:`. Conversion is 100% consistent. |
| Field values are functional roles | Confirmed: Remote agents use values like `engineer`, `ops`, `qa`, `research` — NOT the AgentType enum values (`core/project/custom/system/specialized`). |
| "Skills system references JSON templates" | **Major correction**: SkillManager has a path bug — scans `templates/*.json` but files are in `templates/archive/*.json`. System loads zero mappings. Effectively dead code. |
| Not clear how JSON templates are maintained | Confirmed: Manual updates by developer with Claude Code assistance. No automated process. |

---

## Recommendations for analysis-v2 Revision

1. **Update agent counts** with the three-generation model (Gen 1/2/3)
2. **Add the skill mapping dead code finding** as a new section — this is a significant discovery affecting code cleanup decisions
3. **Strengthen the AgentTemplateBuilder conversion evidence** with the remote → deployed verification data
4. **Document the 14 duplicate pairs** explicitly — these represent cleanup opportunities
5. **Clarify that archive JSON templates are manually maintained** and serve as canonical reference, not automated deployment source
6. **Note that both SkillManager (legacy) and AgentSkillsInjector (new) are dormant** — actual skill assignment flows through AgentTemplateBuilder → markdown frontmatter → Claude Code runtime
