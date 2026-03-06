# 03 - Naming Standards & Frontmatter Consistency Analysis

**Date**: 2026-03-05
**Analyst**: Naming Standards Analyst
**Scope**: Complete inventory of agent naming across filenames, frontmatter fields, and Python code

---

## 1. Complete Filename Inventory

### 1.1 Deployed Agents (`.claude/agents/`) — 46 files

All deployed agent filenames use **kebab-case** (hyphen separators). Zero files use underscores.

| # | Filename | Separator |
|---|----------|-----------|
| 1 | `mpm-agent-manager.md` | kebab |
| 2 | `mpm-skills-manager.md` | kebab |
| 3 | `documentation.md` | single-word |
| 4 | `ticketing.md` | single-word |
| 5 | `golang-engineer.md` | kebab |
| 6 | `java-engineer.md` | kebab |
| 7 | `javascript-engineer.md` | kebab |
| 8 | `nestjs-engineer.md` | kebab |
| 9 | `phoenix-engineer.md` | kebab |
| 10 | `php-engineer.md` | kebab |
| 11 | `python-engineer.md` | kebab |
| 12 | `ruby-engineer.md` | kebab |
| 13 | `rust-engineer.md` | kebab |
| 14 | `visual-basic-engineer.md` | kebab |
| 15 | `engineer.md` | single-word |
| 16 | `data-engineer.md` | kebab |
| 17 | `data-scientist.md` | kebab |
| 18 | `typescript-engineer.md` | kebab |
| 19 | `nextjs-engineer.md` | kebab |
| 20 | `react-engineer.md` | kebab |
| 21 | `svelte-engineer.md` | kebab |
| 22 | `web-ui.md` | kebab |
| 23 | `dart-engineer.md` | kebab |
| 24 | `tauri-engineer.md` | kebab |
| 25 | `imagemagick.md` | single-word |
| 26 | `prompt-engineer.md` | kebab |
| 27 | `refactoring-engineer.md` | kebab |
| 28 | `agentic-coder-optimizer.md` | kebab |
| 29 | `ops.md` | single-word |
| 30 | `aws-ops.md` | kebab |
| 31 | `clerk-ops.md` | kebab |
| 32 | `digitalocean-ops.md` | kebab |
| 33 | `gcp-ops.md` | kebab |
| 34 | `local-ops.md` | kebab |
| 35 | `vercel-ops.md` | kebab |
| 36 | `project-organizer.md` | kebab |
| 37 | `version-control.md` | kebab |
| 38 | `api-qa.md` | kebab |
| 39 | `qa.md` | single-word |
| 40 | `real-user.md` | kebab |
| 41 | `web-qa.md` | kebab |
| 42 | `security.md` | single-word |
| 43 | `code-analyzer.md` | kebab |
| 44 | `product-owner.md` | kebab |
| 45 | `research.md` | single-word |
| 46 | `content-agent.md` | kebab |
| 47 | `memory-manager-agent.md` | kebab |
| 48 | `tmux-agent.md` | kebab |

**Summary**: 100% kebab-case or single-word. No underscore filenames exist in deployed agents.

### 1.2 Cached Agents (`~/.claude-mpm/cache/agents/`) — 48 agent files + 4 BASE-AGENT files

The cache uses a hierarchical directory structure under `bobmatnyc/claude-mpm-agents/agents/`:

```
agents/
├── BASE-AGENT.md
├── claude-mpm/
│   ├── BASE-AGENT.md
│   ├── mpm-agent-manager.md
│   └── mpm-skills-manager.md
├── documentation/
│   ├── documentation.md
│   └── ticketing.md
├── engineer/
│   ├── BASE-AGENT.md
│   ├── backend/  (golang, java, javascript, nestjs, phoenix, php, python, ruby, rust, visual-basic)
│   ├── core/     (engineer.md)
│   ├── data/     (data-engineer, data-scientist, typescript-engineer)
│   ├── frontend/ (nextjs, react, svelte, web-ui)
│   ├── mobile/   (dart, tauri)
│   └── specialized/ (imagemagick, prompt-engineer, refactoring-engineer)
├── ops/
│   ├── BASE-AGENT.md
│   ├── agentic-coder-optimizer.md
│   ├── core/     (ops.md)
│   ├── platform/ (aws-ops, clerk-ops, digitalocean-ops, gcp-ops, local-ops, vercel-ops)
│   ├── project-organizer.md
│   └── tooling/  (tmux-agent, version-control)
├── qa/
│   ├── BASE-AGENT.md
│   ├── api-qa.md
│   ├── qa.md
│   ├── real-user.md
│   └── web-qa.md
├── security/
│   └── security.md
└── universal/
    ├── code-analyzer.md
    ├── content-agent.md
    ├── memory-manager-agent.md
    ├── product-owner.md
    └── research.md
```

All cache filenames also use kebab-case. No underscore filenames found.

### 1.3 Deployed vs Cached — Content Comparison

**MD5 checksum comparison shows 100% match** — every deployed agent file is byte-identical to its cache counterpart. There are:

- **0 agents only in deployed but not in cache**
- **0 agents only in cache but not deployed** (excluding BASE-AGENT.md files)
- **4 BASE-AGENT.md files** exist only in cache (not deployed): root, claude-mpm, engineer, ops, qa

### 1.4 Templates Directory

`src/claude_mpm/agents/templates/` contains **13 .md files** — none are agent definitions. They are PM instruction fragments:
- `README.md`, `circuit-breakers.md`, `context-management-examples.md`, `git-file-tracking.md`, `pm-examples.md`, `pm-red-flags.md`, `pr-workflow-examples.md`, `research-gate-examples.md`, `response-format.md`, `structured-questions-examples.md`, `ticket-completeness-examples.md`, `ticketing-examples.md`, `validation-templates.md`

---

## 2. Complete Frontmatter Analysis — Every Deployed Agent

### 2.1 Full Inventory Table

| # | Filename | `name:` | `agent_id:` | `agent_type:` | `schema_version:` | `version:` | `author:` |
|---|----------|---------|-------------|---------------|-------------------|------------|-----------|
| 1 | mpm-agent-manager | `mpm_agent_manager` | `mpm-agent-manager` | `system` | 1.3.0 | 1.0.0 | Claude MPM Team |
| 2 | mpm-skills-manager | `mpm_skills_manager` | `mpm-skills-manager` | `claude-mpm` | 1.3.0 | 1.0.0 | Claude MPM Team |
| 3 | documentation | `Documentation Agent` | `documentation-agent` | `documentation` | 1.2.0 | 3.4.2 | Claude MPM Team |
| 4 | ticketing | `ticketing_agent` | `ticketing` | `documentation` | 1.2.0 | 2.7.0 | *(missing)* |
| 5 | golang-engineer | `Golang Engineer` | `golang_engineer` | `engineer` | 1.3.0 | 1.0.0 | *(missing)* |
| 6 | java-engineer | `Java Engineer` | `java_engineer` | `engineer` | 1.3.0 | 1.0.0 | *(missing)* |
| 7 | javascript-engineer | `Javascript Engineer` | `javascript-engineer-agent` | `engineer` | 1.2.0 | 1.0.0 | *(missing)* |
| 8 | nestjs-engineer | `nestjs-engineer` | `nestjs_engineer` | `engineer` | *(missing)* | 1.0.0 | *(missing)* |
| 9 | phoenix-engineer | `Phoenix Engineer` | `phoenix-engineer` | `engineer` | 1.3.0 | 1.0.0 | Claude MPM Team |
| 10 | php-engineer | `Php Engineer` | `php_engineer` | `engineer` | 1.3.0 | 2.1.0 | *(missing)* |
| 11 | python-engineer | `Python Engineer` | `python-engineer` | `engineer` | 1.3.0 | 2.3.0 | *(missing)* |
| 12 | ruby-engineer | `Ruby Engineer` | `ruby_engineer` | `engineer` | 1.3.0 | 2.0.0 | *(missing)* |
| 13 | rust-engineer | `Rust Engineer` | `rust_engineer` | `engineer` | 1.3.0 | 1.1.0 | *(missing)* |
| 14 | visual-basic-engineer | `Visual Basic Engineer` | `visual_basic_engineer` | `engineer` | 1.3.0 | 1.0.0 | *(missing)* |
| 15 | engineer | `Engineer` | `engineer` | `engineer` | 1.3.0 | 3.9.1 | Claude MPM Team |
| 16 | data-engineer | `Data Engineer` | `data-engineer` | `engineer` | 1.2.0 | 2.5.1 | *(missing)* |
| 17 | data-scientist | `Data Scientist` | `data-scientist` | `engineer` | 1.2.0 | 1.0.0 | *(missing)* |
| 18 | typescript-engineer | `Typescript Engineer` | `typescript-engineer` | `engineer` | 1.3.0 | 2.0.0 | *(missing)* |
| 19 | nextjs-engineer | `Nextjs Engineer` | `nextjs_engineer` | `engineer` | 1.3.0 | 2.1.0 | *(missing)* |
| 20 | react-engineer | `React Engineer` | `react_engineer` | `engineer` | 1.3.0 | 1.3.0 | *(missing)* |
| 21 | svelte-engineer | `Svelte Engineer` | `svelte_engineer` | `engineer` | 1.3.0 | 1.1.0 | *(missing)* |
| 22 | web-ui | `Web UI` | `web-ui-engineer` | `engineer` | 1.2.0 | 1.4.2 | *(missing)* |
| 23 | dart-engineer | `Dart Engineer` | `dart_engineer` | `engineer` | 1.3.0 | 1.0.0 | *(missing)* |
| 24 | tauri-engineer | `Tauri Engineer` | `tauri_engineer` | `engineer` | 1.3.0 | 1.0.0 | Claude MPM Team |
| 25 | imagemagick | `Imagemagick` | `imagemagick` | `imagemagick` | 1.1.0 | 1.0.2 | *(missing)* |
| 26 | prompt-engineer | `Prompt Engineer` | `prompt-engineer` | `analysis` | 1.3.0 | 3.0.0 | Claude MPM Team |
| 27 | refactoring-engineer | `Refactoring Engineer` | `refactoring-engineer` | `refactoring` | 1.2.0 | 1.1.3 | *(missing)* |
| 28 | agentic-coder-optimizer | `Agentic Coder Optimizer` | `agentic-coder-optimizer` | `ops` | 1.3.0 | 0.0.9 | Claude MPM Team |
| 29 | ops | `Ops` | `ops-agent` | `ops` | 1.2.0 | 2.2.4 | Claude MPM Team |
| 30 | aws-ops | `aws_ops_agent` | `aws-ops` | `ops` | 1.3.0 | 1.0.0 | *(missing)* |
| 31 | clerk-ops | `Clerk Operations` | `clerk-ops` | `ops` | 1.3.1 | 1.1.1 | *(missing)* |
| 32 | digitalocean-ops | `DigitalOcean Ops` | `digitalocean-ops-agent` | `ops` | 1.3.0 | 1.0.0 | *(missing)* |
| 33 | gcp-ops | `Google Cloud Ops` | `gcp-ops-agent` | `ops` | 1.2.0 | 1.0.2 | *(missing)* |
| 34 | local-ops | `Local Ops` | `local-ops-agent` | `specialized` | 1.3.0 | 2.0.1 | *(missing)* |
| 35 | vercel-ops | `Vercel Ops` | `vercel-ops-agent` | `ops` | 1.2.0 | 2.0.1 | *(missing)* |
| 36 | project-organizer | `Project Organizer` | `project-organizer` | `ops` | 1.2.0 | 1.2.0 | Claude MPM Team |
| 37 | version-control | `Version Control` | `version-control` | `ops` | 1.2.0 | 2.3.2 | Claude MPM Team |
| 38 | api-qa | `API QA` | `api-qa-agent` | `qa` | 1.2.0 | 1.2.2 | Claude MPM Team |
| 39 | qa | `QA` | `qa-agent` | `qa` | 1.3.0 | 3.5.3 | Claude MPM Team |
| 40 | real-user | `real-user` | `real_user` | `qa` | *(missing)* | 1.0.0 | *(missing)* |
| 41 | web-qa | `Web QA` | `web-qa-agent` | `qa` | 1.2.0 | 3.1.0 | *(missing)* |
| 42 | security | `Security` | `security-agent` | `security` | 1.2.0 | 2.5.0 | Claude MPM Team |
| 43 | code-analyzer | `Code Analysis` | `code-analyzer` | `research` | 1.2.0 | 2.6.2 | *(missing)* |
| 44 | product-owner | `Product Owner` | `product_owner` | `product` | 1.3.0 | 1.0.0 | *(missing)* |
| 45 | research | `Research` | `research-agent` | `research` | 1.3.0 | 5.0.0 | *(missing)* |
| 46 | content-agent | `Content Optimization` | `content-agent` | `content` | 1.3.0 | 1.0.0 | *(missing)* |
| 47 | memory-manager-agent | `Memory Manager` | `memory-manager-agent` | `memory_manager` | 1.2.0 | 1.2.0 | *(missing)* |
| 48 | tmux-agent | `Tmux Agent` | `tmux-agent` | `ops` | 1.3.0 | 1.0.0 | *(missing)* |

---

## 3. `name:` Field — Naming Convention Analysis

### 3.1 Convention Categories

| Convention | Count | Agents |
|-----------|-------|--------|
| **Title Case** (standard) | 37 | Engineer, Python Engineer, Golang Engineer, Java Engineer, Javascript Engineer, Phoenix Engineer, Php Engineer, Ruby Engineer, Rust Engineer, Visual Basic Engineer, Data Engineer, Data Scientist, Typescript Engineer, Nextjs Engineer, React Engineer, Svelte Engineer, Web UI, Dart Engineer, Tauri Engineer, Imagemagick, Prompt Engineer, Refactoring Engineer, Agentic Coder Optimizer, Ops, Clerk Operations, DigitalOcean Ops, Google Cloud Ops, Local Ops, Vercel Ops, Project Organizer, Version Control, API QA, QA, Web QA, Security, Code Analysis, Product Owner, Research, Content Optimization, Memory Manager, Tmux Agent, Documentation Agent |
| **snake_case** | 4 | `mpm_agent_manager`, `mpm_skills_manager`, `ticketing_agent`, `aws_ops_agent` |
| **kebab-case** | 2 | `nestjs-engineer`, `real-user` |

### 3.2 Specific Inconsistencies in `name:` Values

| Agent | `name:` value | Expected (Title Case) | Issue |
|-------|--------------|----------------------|-------|
| mpm-agent-manager | `mpm_agent_manager` | `MPM Agent Manager` | snake_case instead of Title Case |
| mpm-skills-manager | `mpm_skills_manager` | `MPM Skills Manager` | snake_case instead of Title Case |
| ticketing | `ticketing_agent` | `Ticketing Agent` | snake_case instead of Title Case |
| aws-ops | `aws_ops_agent` | `AWS Ops` | snake_case instead of Title Case |
| nestjs-engineer | `nestjs-engineer` | `NestJS Engineer` | kebab-case instead of Title Case |
| real-user | `real-user` | `Real User` | kebab-case instead of Title Case |

**Impact**: The `AGENT_NAME_MAP` in `agent_name_registry.py` faithfully maps to these inconsistent values. The PM uses these `name:` values for `subagent_type` delegation, meaning some delegations use snake_case while most use Title Case.

---

## 4. `agent_id:` Field — Naming Convention Analysis

### 4.1 Convention Categories

| Convention | Count | Agents |
|-----------|-------|--------|
| **kebab-case** (no suffix) | 20 | mpm-agent-manager, mpm-skills-manager, phoenix-engineer, python-engineer, typescript-engineer, data-engineer, data-scientist, agentic-coder-optimizer, clerk-ops, aws-ops, project-organizer, version-control, code-analyzer, content-agent, memory-manager-agent, tmux-agent, prompt-engineer, refactoring-engineer, ticketing, imagemagick |
| **kebab-case with `-agent` suffix** | 12 | documentation-agent, ops-agent, local-ops-agent, vercel-ops-agent, gcp-ops-agent, digitalocean-ops-agent, qa-agent, web-qa-agent, api-qa-agent, security-agent, research-agent, web-ui-engineer |
| **snake_case** | 14 | golang_engineer, java_engineer, nestjs_engineer, php_engineer, ruby_engineer, rust_engineer, visual_basic_engineer, nextjs_engineer, react_engineer, svelte_engineer, dart_engineer, tauri_engineer, real_user, product_owner |
| **kebab-case with `-engineer-agent` suffix** | 1 | javascript-engineer-agent |

### 4.2 `agent_id:` vs Filename Stem Comparison

| Filename (stem) | `agent_id:` | Match? | Discrepancy |
|----------------|-------------|--------|-------------|
| mpm-agent-manager | mpm-agent-manager | YES | |
| mpm-skills-manager | mpm-skills-manager | YES | |
| documentation | documentation-agent | NO | `-agent` suffix added |
| ticketing | ticketing | YES | |
| golang-engineer | golang_engineer | NO | underscore vs hyphen |
| java-engineer | java_engineer | NO | underscore vs hyphen |
| javascript-engineer | javascript-engineer-agent | NO | `-agent` suffix added |
| nestjs-engineer | nestjs_engineer | NO | underscore vs hyphen |
| phoenix-engineer | phoenix-engineer | YES | |
| php-engineer | php_engineer | NO | underscore vs hyphen |
| python-engineer | python-engineer | YES | |
| ruby-engineer | ruby_engineer | NO | underscore vs hyphen |
| rust-engineer | rust_engineer | NO | underscore vs hyphen |
| visual-basic-engineer | visual_basic_engineer | NO | underscore vs hyphen |
| engineer | engineer | YES | |
| data-engineer | data-engineer | YES | |
| data-scientist | data-scientist | YES | |
| typescript-engineer | typescript-engineer | YES | |
| nextjs-engineer | nextjs_engineer | NO | underscore vs hyphen |
| react-engineer | react_engineer | NO | underscore vs hyphen |
| svelte-engineer | svelte_engineer | NO | underscore vs hyphen |
| web-ui | web-ui-engineer | NO | `-engineer` suffix added |
| dart-engineer | dart_engineer | NO | underscore vs hyphen |
| tauri-engineer | tauri_engineer | NO | underscore vs hyphen |
| imagemagick | imagemagick | YES | |
| prompt-engineer | prompt-engineer | YES | |
| refactoring-engineer | refactoring-engineer | YES | |
| agentic-coder-optimizer | agentic-coder-optimizer | YES | |
| ops | ops-agent | NO | `-agent` suffix added |
| aws-ops | aws-ops | YES | |
| clerk-ops | clerk-ops | YES | |
| digitalocean-ops | digitalocean-ops-agent | NO | `-agent` suffix added |
| gcp-ops | gcp-ops-agent | NO | `-agent` suffix added |
| local-ops | local-ops-agent | NO | `-agent` suffix added |
| vercel-ops | vercel-ops-agent | NO | `-agent` suffix added |
| project-organizer | project-organizer | YES | |
| version-control | version-control | YES | |
| api-qa | api-qa-agent | NO | `-agent` suffix added |
| qa | qa-agent | NO | `-agent` suffix added |
| real-user | real_user | NO | underscore vs hyphen |
| web-qa | web-qa-agent | NO | `-agent` suffix added |
| security | security-agent | NO | `-agent` suffix added |
| code-analyzer | code-analyzer | YES | |
| product-owner | product_owner | NO | underscore vs hyphen |
| research | research-agent | NO | `-agent` suffix added |
| content-agent | content-agent | YES | |
| memory-manager-agent | memory-manager-agent | YES | |
| tmux-agent | tmux-agent | YES | |

**Match rate: 22/48 (46%) match exactly.**

Discrepancy breakdown:
- **14 agents** use underscore in `agent_id` but hyphen in filename
- **10 agents** add `-agent` suffix in `agent_id` that filename lacks
- **1 agent** (web-ui) adds `-engineer` suffix
- **1 agent** (javascript-engineer) adds `-agent` suffix beyond the stem

---

## 5. `agent_type:` Field — Deep Dive

### 5.1 Field Name Usage

**ALL 48 agents use `agent_type:` — NONE use bare `type:`** in frontmatter.

This is consistent. The field name `agent_type` is the de facto standard in all deployed agents.

### 5.2 `agent_type:` Values Used in Frontmatter

| Value | Count | Agents |
|-------|-------|--------|
| `engineer` | 21 | engineer, python-engineer, golang-engineer, java-engineer, javascript-engineer, nestjs-engineer, phoenix-engineer, php-engineer, ruby-engineer, rust-engineer, visual-basic-engineer, data-engineer, data-scientist, typescript-engineer, nextjs-engineer, react-engineer, svelte-engineer, web-ui, dart-engineer, tauri-engineer |
| `ops` | 10 | ops, agentic-coder-optimizer, aws-ops, clerk-ops, digitalocean-ops, gcp-ops, vercel-ops, project-organizer, version-control, tmux-agent |
| `qa` | 4 | qa, api-qa, web-qa, real-user |
| `documentation` | 2 | documentation, ticketing |
| `research` | 2 | research, code-analyzer |
| `security` | 1 | security |
| `system` | 1 | mpm-agent-manager |
| `claude-mpm` | 1 | mpm-skills-manager |
| `specialized` | 1 | local-ops |
| `analysis` | 1 | prompt-engineer |
| `refactoring` | 1 | refactoring-engineer |
| `imagemagick` | 1 | imagemagick |
| `product` | 1 | product-owner |
| `content` | 1 | content-agent |
| `memory_manager` | 1 | memory-manager-agent |

**15 distinct values** for `agent_type:` in frontmatter.

### 5.3 Python Enum — `AgentType` Definitions

There are **TWO separate AgentType enums** in the codebase:

**Enum 1**: `src/claude_mpm/models/agent_definition.py:25`
```python
class AgentType(str, Enum):
    CORE = "core"
    PROJECT = "project"
    CUSTOM = "custom"
    SYSTEM = "system"
    SPECIALIZED = "specialized"
```
**5 values**: core, project, custom, system, specialized

**Enum 2**: `src/claude_mpm/core/unified_agent_registry.py:52`
```python
class AgentType(Enum):
    CORE = "core"
    SPECIALIZED = "specialized"
    USER_DEFINED = "user_defined"
    PROJECT = "project"
    MEMORY_AWARE = "memory_aware"
```
**5 values**: core, specialized, user_defined, project, memory_aware

### 5.4 Frontmatter vs Enum — Gap Analysis

| Frontmatter `agent_type:` value | In Enum 1? | In Enum 2? | Covered? |
|--------------------------------|------------|------------|----------|
| `engineer` | NO | NO | **UNCOVERED** |
| `ops` | NO | NO | **UNCOVERED** |
| `qa` | NO | NO | **UNCOVERED** |
| `documentation` | NO | NO | **UNCOVERED** |
| `research` | NO | NO | **UNCOVERED** |
| `security` | NO | NO | **UNCOVERED** |
| `system` | YES (system) | NO | Partial |
| `claude-mpm` | NO | NO | **UNCOVERED** |
| `specialized` | YES | YES | Covered |
| `analysis` | NO | NO | **UNCOVERED** |
| `refactoring` | NO | NO | **UNCOVERED** |
| `imagemagick` | NO | NO | **UNCOVERED** |
| `product` | NO | NO | **UNCOVERED** |
| `content` | NO | NO | **UNCOVERED** |
| `memory_manager` | NO | NO | **UNCOVERED** |

**CRITICAL FINDING**: Only 2 of 15 frontmatter `agent_type` values (`system`, `specialized`) match any enum value. The remaining 13 (87%) fall through to fallback/default handling.

### 5.5 How Python Code Handles the Mismatch

1. **`agent_management_service.py:474-476`** — The primary parser:
   ```python
   type=self._safe_parse_agent_type(
       post.metadata.get("agent_type", post.metadata.get("type", "core"))
   )
   ```
   - Tries `agent_type` first, then `type`, defaults to `"core"`
   - `_safe_parse_agent_type()` at line 461: tries `AgentType(value)`, falls back to `AgentType.CUSTOM` on ValueError
   - **Result**: All non-matching values (engineer, ops, qa, etc.) silently become `AgentType.CUSTOM`

2. **`frontmatter_utils.py:12-22`** — The utility function:
   ```python
   def read_agent_type(data, default="general"):
       return data.get("agent_type", data.get("type", default))
   ```
   - Returns raw string value — no validation against enum
   - Used by `deployed_agent_discovery.py`, `dynamic_skills_generator.py`

3. **`agent_registry.py:179`** — The unified registry:
   ```python
   unified_agent_type = AgentType(agent_type)  # ValueError for most values
   ```
   - Catches ValueError, sets `unified_agent_type = None`
   - **Result**: Most agents cannot be filtered by type in the unified registry

### 5.6 `agents_metadata.py` — Third Type System

The `agents_metadata.py` file uses its own `agent_type` values:
- `"core_agent"` — used for 11 agents
- `"optimization_agent"` — used for 2 agents (imagemagick, agentic-coder-optimizer)
- `"system_agent"` — used for 1 agent (agent_manager)

These do NOT match either the frontmatter values OR the enum values.

---

## 6. Missing Fields Analysis

### 6.1 `schema_version:` — Missing from 2 agents

| Agent | Has schema_version? |
|-------|-------------------|
| nestjs-engineer | NO |
| real-user | NO |
| All others (46) | YES |

### 6.2 `author:` — Missing from 30 agents

Only 18 agents have `author: Claude MPM Team`:
- mpm-agent-manager, mpm-skills-manager, documentation, engineer, phoenix-engineer, tauri-engineer, prompt-engineer, agentic-coder-optimizer, ops, project-organizer, version-control, api-qa, qa, security, code-analyzer (via `temperature:` field area)

The remaining 30 agents have no `author:` field.

### 6.3 `category:` — Missing from many agents

Some agents use `category:` (e.g., `engineering`, `operations`, `quality`, `specialized`) but many omit it entirely. Not all frontmatter was read deeply enough to produce exact count but at least 20+ agents have it.

---

## 7. Duplicate Detection

### 7.1 MD5 Comparison: Deployed vs Cache

All 48 deployed agents are **byte-identical** to their cached counterparts. No divergence detected.

### 7.2 Same `name:` Different Filename

No agents share the same `name:` value with different filenames.

### 7.3 Same Filename Different `name:`

No cases found (each filename is unique, each maps to one `name:` value).

### 7.4 `AGENT_NAME_MAP` Accuracy

The `AGENT_NAME_MAP` in `agent_name_registry.py` was compared to actual frontmatter `name:` values:

| Stem (in registry) | Registry value | Actual frontmatter `name:` | Match? |
|--------------------|---------------|---------------------------|--------|
| ticketing | `ticketing_agent` | `ticketing_agent` | YES |
| nestjs-engineer | `nestjs-engineer` | `nestjs-engineer` | YES |
| aws-ops | `aws_ops_agent` | `aws_ops_agent` | YES |
| real-user | `real-user` | `real-user` | YES |
| mpm-agent-manager | `mpm_agent_manager` | `mpm_agent_manager` | YES |
| mpm-skills-manager | `mpm_skills_manager` | `mpm_skills_manager` | YES |

The registry is accurate — it faithfully reflects the inconsistent actual `name:` values.

---

## 8. Summary of Inconsistency Categories

### 8.1 By Severity

| Severity | Category | Count | Impact |
|----------|----------|-------|--------|
| **CRITICAL** | `agent_type:` values not in any enum | 13/15 values | Type-based filtering broken; 87% fall to CUSTOM/null |
| **CRITICAL** | Two separate `AgentType` enums with different values | 2 enums | Code path determines which enum — confusing |
| **HIGH** | `name:` field mixed conventions | 6/48 non-Title-Case | PM delegation uses these values; inconsistent UX |
| **HIGH** | `agent_id:` mixed separators | 14 use `_`, 34 use `-` | agent_id/filename mismatch in 54% of agents |
| **HIGH** | `agent_id:` sometimes adds `-agent` suffix | 11 agents | Breaks filename-to-agent_id derivation |
| **MEDIUM** | `agents_metadata.py` uses third type system | 3 distinct values | Yet another type taxonomy disconnected from frontmatter |
| **MEDIUM** | `schema_version:` missing from 2 agents | 2 agents | Validation may fail for these |
| **LOW** | `author:` missing from 30 agents | 30/48 | Incomplete metadata |

### 8.2 By Count

| Inconsistency | Count |
|--------------|-------|
| Total deployed agents | 48 |
| Agents with non-Title-Case `name:` | 6 (12.5%) |
| Agents with `agent_id` not matching filename stem | 26 (54%) |
| Distinct `agent_type` frontmatter values | 15 |
| `agent_type` values covered by enums | 2 (13%) |
| `agent_type` values NOT in any enum | 13 (87%) |
| Agents missing `schema_version:` | 2 |
| Agents missing `author:` | 30 |

---

## 9. Standardization Recommendations

### 9.1 Immediate — `name:` Field

Standardize all `name:` values to **Title Case** (the dominant convention, used by 87.5%):

```yaml
# Fix these 6 agents:
mpm-agent-manager:    mpm_agent_manager    -> MPM Agent Manager
mpm-skills-manager:   mpm_skills_manager   -> MPM Skills Manager
ticketing:            ticketing_agent       -> Ticketing Agent
aws-ops:              aws_ops_agent        -> AWS Ops
nestjs-engineer:      nestjs-engineer      -> NestJS Engineer
real-user:            real-user            -> Real User
```

Then update `AGENT_NAME_MAP` in `agent_name_registry.py` to match.

### 9.2 Immediate — `agent_id:` Field

Standardize all `agent_id:` values to **kebab-case matching the filename stem** (no `-agent` suffix, no underscores):

- Fix 14 underscore agents: `golang_engineer` -> `golang-engineer`, etc.
- Fix 11 `-agent` suffix agents: `ops-agent` -> `ops`, `qa-agent` -> `qa`, etc.
- Fix 1 `-engineer` suffix: `web-ui-engineer` -> `web-ui`

### 9.3 High Priority — Unified `agent_type:` Enum

Create a SINGLE `AgentType` enum that covers all actual frontmatter values:

```python
class AgentType(str, Enum):
    ENGINEER = "engineer"
    OPS = "ops"
    QA = "qa"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    SECURITY = "security"
    SYSTEM = "system"           # mpm-agent-manager
    SPECIALIZED = "specialized" # catch-all for unique types
    ANALYSIS = "analysis"       # prompt-engineer
    PRODUCT = "product"         # product-owner
    CONTENT = "content"         # content-agent
```

Then standardize the 4 outlier frontmatter values:
- `claude-mpm` -> `system` (mpm-skills-manager)
- `refactoring` -> `engineer` (refactoring-engineer)
- `imagemagick` -> `engineer` or `specialized` (imagemagick)
- `memory_manager` -> `system` (memory-manager-agent)

### 9.4 Medium Priority — Eliminate Duplicate Enums

Consolidate the two `AgentType` enums:
- `src/claude_mpm/models/agent_definition.py:25` (5 values: core, project, custom, system, specialized)
- `src/claude_mpm/core/unified_agent_registry.py:52` (5 values: core, specialized, user_defined, project, memory_aware)

Into a single authoritative enum, likely in `models/agent_definition.py`.

### 9.5 Low Priority — Fill Missing Fields

Add `author: Claude MPM Team` and `schema_version: 1.3.0` to all agents missing these fields.

---

## Appendix A: `agent_type:` Value Distribution Visualization

```
engineer       ████████████████████████████████████████████ 21
ops            ████████████████████ 10
qa             ████████ 4
documentation  ████ 2
research       ████ 2
system         ██ 1
claude-mpm     ██ 1
specialized    ██ 1
analysis       ██ 1
refactoring    ██ 1
imagemagick    ██ 1
product        ██ 1
content        ██ 1
memory_manager ██ 1
security       ██ 1
```

## Appendix B: `name:` Convention Distribution

```
Title Case    ██████████████████████████████████████████████████████████████████████████████ 42  (87.5%)
snake_case    ████████ 4  (8.3%)
kebab-case    ████ 2  (4.2%)
```

## Appendix C: `agent_id:` Separator Distribution

```
kebab-case (match)     ████████████████████████████████████████████████ 22  (45.8%)
kebab + -agent suffix  ████████████████████████ 12  (25.0%)
snake_case             ████████████████████████████ 14  (29.2%)
```
