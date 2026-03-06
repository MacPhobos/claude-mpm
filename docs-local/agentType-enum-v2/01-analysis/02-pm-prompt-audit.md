# PM Prompt Audit: Agent Name References

**Date**: 2026-03-05
**Scope**: All PM-related prompt files, hardcoded agent lists, and prompt assembly code
**Branch**: agenttype-enums

---

## Executive Summary

The PM prompt system has a **critical naming inconsistency** problem. PM_INSTRUCTIONS.md and CLAUDE_MPM_OUTPUT_STYLE.md reference agents using a mix of display names, `name:` field values, and ad-hoc strings. Claude Code resolves `Agent(subagent_type="...")` against the `name:` frontmatter field of deployed `.md` files in `.claude/agents/`. **Any reference that doesn't exactly match the `name:` field will fail delegation.**

Additionally, there are **5 separate CORE_AGENTS lists** across the codebase, each using different identifier formats and containing different agent sets.

---

## 1. Ground Truth: Deployed Agent Inventory

Complete mapping of all 47 deployed agents in `.claude/agents/`:

| Filename (stem) | `name:` field | `agent_id:` field | Category |
|---|---|---|---|
| `engineer` | `Engineer` | `engineer` | Core |
| `research` | `Research` | `research-agent` | Core |
| `qa` | `QA` | `qa-agent` | Core |
| `documentation` | `Documentation Agent` | `documentation-agent` | Core |
| `ops` | `Ops` | `ops-agent` | Core |
| `ticketing` | `ticketing_agent` | `ticketing` | Core |
| `local-ops` | `Local Ops` | `local-ops-agent` | Ops |
| `vercel-ops` | `Vercel Ops` | `vercel-ops-agent` | Ops |
| `gcp-ops` | `Google Cloud Ops` | `gcp-ops-agent` | Ops |
| `aws-ops` | `aws_ops_agent` | `aws-ops` | Ops |
| `digitalocean-ops` | `DigitalOcean Ops` | `digitalocean-ops-agent` | Ops |
| `clerk-ops` | `Clerk Operations` | `clerk-ops` | Ops |
| `web-qa` | `Web QA` | `web-qa-agent` | QA |
| `api-qa` | `API QA` | `api-qa-agent` | QA |
| `real-user` | `real-user` | `real_user` | QA |
| `security` | `Security` | `security-agent` | Universal |
| `code-analyzer` | `Code Analysis` | `code-analyzer` | Universal |
| `version-control` | `Version Control` | `version-control` | Universal |
| `project-organizer` | `Project Organizer` | `project-organizer` | Universal |
| `memory-manager-agent` | `Memory Manager` | `memory-manager-agent` | Universal |
| `product-owner` | `Product Owner` | `product_owner` | Universal |
| `content-agent` | `Content Optimization` | `content-agent` | Universal |
| `web-ui` | `Web UI` | `web-ui-engineer` | Universal |
| `imagemagick` | `Imagemagick` | `imagemagick` | Universal |
| `tmux-agent` | `Tmux Agent` | `tmux-agent` | Universal |
| `prompt-engineer` | `Prompt Engineer` | `prompt-engineer` | Engineer |
| `refactoring-engineer` | `Refactoring Engineer` | `refactoring-engineer` | Engineer |
| `agentic-coder-optimizer` | `Agentic Coder Optimizer` | `agentic-coder-optimizer` | Engineer |
| `python-engineer` | `Python Engineer` | `python-engineer` | Engineer |
| `golang-engineer` | `Golang Engineer` | `golang_engineer` | Engineer |
| `java-engineer` | `Java Engineer` | `java_engineer` | Engineer |
| `javascript-engineer` | `Javascript Engineer` | `javascript-engineer-agent` | Engineer |
| `typescript-engineer` | `Typescript Engineer` | `typescript-engineer` | Engineer |
| `rust-engineer` | `Rust Engineer` | `rust_engineer` | Engineer |
| `ruby-engineer` | `Ruby Engineer` | `ruby_engineer` | Engineer |
| `php-engineer` | `Php Engineer` | `php_engineer` | Engineer |
| `phoenix-engineer` | `Phoenix Engineer` | `phoenix-engineer` | Engineer |
| `nestjs-engineer` | `nestjs-engineer` | `nestjs_engineer` | Engineer |
| `react-engineer` | `React Engineer` | `react_engineer` | Engineer |
| `nextjs-engineer` | `Nextjs Engineer` | `nextjs_engineer` | Engineer |
| `svelte-engineer` | `Svelte Engineer` | `svelte_engineer` | Engineer |
| `dart-engineer` | `Dart Engineer` | `dart_engineer` | Engineer |
| `tauri-engineer` | `Tauri Engineer` | `tauri_engineer` | Engineer |
| `visual-basic-engineer` | `Visual Basic Engineer` | `visual_basic_engineer` | Engineer |
| `data-engineer` | `Data Engineer` | `data-engineer` | Engineer |
| `data-scientist` | `Data Scientist` | `data-scientist` | Engineer |
| `mpm-agent-manager` | `mpm_agent_manager` | `mpm-agent-manager` | MPM |
| `mpm-skills-manager` | `mpm_skills_manager` | `mpm-skills-manager` | MPM |

---

## 2. PM_INSTRUCTIONS.md Agent Reference Audit

**File**: `src/claude_mpm/agents/PM_INSTRUCTIONS.md` (v0009, ~1100 lines)

### 2.1 Complete Reference Table

Every agent reference in PM_INSTRUCTIONS.md mapped to the deployed `name:` field:

| PM Reference (as written) | Line(s) | Deployed `name:` field | Match? | Delegation Would Succeed? |
|---|---|---|---|---|
| `Research` | 24, 135, 490, 525, 542, etc. | `Research` | YES | YES |
| `Engineer` | 25, 135, 446, 491, etc. | `Engineer` | YES | YES |
| `QA` | 26, 448, 493, 604, etc. | `QA` | YES | YES |
| `Local Ops` | 26, 83, 279, 292, 294, 399-411, 492, 616, 682, 957, 1062-1066 | `Local Ops` | YES | YES |
| `Local Ops/QA` | 26, 352, 957 | N/A (compound) | N/A | Depends on parsing |
| `Vercel Ops` | 401, 410 | `Vercel Ops` | YES | YES |
| `Google Cloud Ops` | 402, 411 | `Google Cloud Ops` | YES | YES |
| `Documentation Agent` | 135, 453, 494, 658, 692, 1056 | `Documentation Agent` | YES | YES |
| `Code Analysis` | 450, 646, 671, 843, 874 | `Code Analysis` | YES | YES |
| `Web QA` | 354-356, 493, 613-614, 683, 1060 | `Web QA` | YES | YES |
| `API QA` | 615 | `API QA` | YES | YES |
| `Security` | 449, 570 | `Security` | YES | YES |
| `Ops` | 452, 492 | `Ops` | YES | YES |
| `Version Control` | 496, 804, 1070 | `Version Control` | YES | YES |
| `ticketing_agent` | 353, 495, 744, 774, 788, 791-792, 1068 | `ticketing_agent` | YES | YES |
| `mpm_skills_manager` | 497, 1074 | `mpm_skills_manager` | YES | YES |
| `local-ops` (in output style) | CLAUDE_MPM_OUTPUT_STYLE.md:23 | `Local Ops` | **NO** | **NO - WILL FAIL** |

### 2.2 Critical Finding: CLAUDE_MPM_OUTPUT_STYLE.md Mismatch

**File**: `src/claude_mpm/agents/CLAUDE_MPM_OUTPUT_STYLE.md` (line 23)

```markdown
- Run commands (curl/lsof) --> STOP! Delegate to local-ops
```

The deployed agent has `name: Local Ops` (with space, title case). The reference `local-ops` uses the **filename stem** format, not the `name:` field. If Claude Code matches against the `name:` field, this delegation will fail.

**However**, PM_INSTRUCTIONS.md itself consistently uses `Local Ops` (the correct `name:` field value) in all 15+ references.

### 2.3 Agent Reference Consistency Analysis

**Agents referenced using `name:` field values (CORRECT)**:
- Research, Engineer, QA, Local Ops, Vercel Ops, Google Cloud Ops
- Documentation Agent, Code Analysis, Web QA, API QA, Security, Ops
- Version Control, ticketing_agent, mpm_skills_manager

**Agents referenced using filename stems or other formats (INCORRECT)**:
- `local-ops` in CLAUDE_MPM_OUTPUT_STYLE.md (should be `Local Ops`)

### 2.4 Naming Convention Inconsistencies in `name:` Fields Themselves

The `name:` field values across deployed agents use **inconsistent naming conventions**:

| Convention | Examples | Count |
|---|---|---|
| Title Case with spaces | `Local Ops`, `Web QA`, `Python Engineer` | ~35 |
| snake_case | `ticketing_agent`, `mpm_skills_manager`, `mpm_agent_manager`, `aws_ops_agent` | 4 |
| kebab-case | `nestjs-engineer`, `real-user` | 2 |
| Title Case compound | `Documentation Agent`, `Code Analysis`, `Content Optimization` | 3 |

The PM prompt references `ticketing_agent` and `mpm_skills_manager` which happen to match their `name:` fields, but these names use a different convention than most agents.

---

## 3. PM Prompt Assembly Code Paths

### 3.1 How the PM System Prompt is Built

The PM prompt is assembled from multiple sources at runtime:

```
Priority 1: .claude-mpm/PM_INSTRUCTIONS_DEPLOYED.md (merged file)
Priority 2: src/claude_mpm/agents/PM_INSTRUCTIONS.md (dev mode)
Priority 3: src/claude_mpm/agents/INSTRUCTIONS.md (legacy)
```

**Assembly chain**:

1. `InstructionLoader` (`src/claude_mpm/core/framework/loaders/instruction_loader.py`)
   - Loads PM_INSTRUCTIONS.md as `framework_instructions`

2. `PackagedLoader` (`src/claude_mpm/core/framework/loaders/packaged_loader.py`)
   - Used for wheel/package installations
   - Loads same PM_INSTRUCTIONS.md from package data

3. `SystemInstructionsDeployer` (`src/claude_mpm/services/agents/deployment/system_instructions_deployer.py`)
   - Merges: PM_INSTRUCTIONS.md + WORKFLOW.md + MEMORY.md
   - Output: `.claude-mpm/PM_INSTRUCTIONS_DEPLOYED.md`

4. `CLAUDE_MPM_OUTPUT_STYLE.md` is set as the PM's `output_style` (line 2: `name: claude_mpm`)
   - This is a SEPARATE file from PM_INSTRUCTIONS.md
   - Contains the `local-ops` reference (line 23)

### 3.2 Key Observation: No Dynamic Agent Section Generation

There is **NO code that dynamically generates an "Available Agent Capabilities" section** in the PM prompt. The PM_INSTRUCTIONS.md contains a **static, hand-written** delegation matrix (lines 488-497):

```markdown
| Agent | Delegate When | Key Capabilities | Special Notes |
| **Research** | Understanding codebase... | Grep, Glob, Read... | Investigation tools |
| **Engineer** | Writing/modifying code... | Edit, Write... | - |
| **Ops** (Local Ops) | Deploying apps... | Environment config... | Use `Local Ops`... |
| **QA** (Web QA, API QA) | Testing... | Playwright (web)... | For browser: **Web QA** |
| **Documentation Agent** | Creating/updating docs... | Style consistency... | - |
| **ticketing_agent** | ALL ticket operations... | Direct mcp-ticketer... | PM never uses... |
| **Version Control** | Creating PRs... | PR workflows... | Check git user... |
| **mpm_skills_manager** | Creating/improving skills... | manifest.json... | Triggers: "skill"... |
```

This table is entirely static. Agent identifiers here must be manually kept in sync with deployed `name:` fields.

### 3.3 FrameworkAgentLoader Profile Loading

`FrameworkAgentLoader._load_profile_from_directory()` at `framework_agent_loader.py:219`:
```python
profile_file = directory / f"{agent_type}.md"
```

This loads profiles by **filename stem**, not by `name:` field. The `name:` field is only relevant for Claude Code's own `Agent(subagent_type="...")` resolution.

---

## 4. Hardcoded CORE_AGENTS Lists

### 4.1 Complete Inventory (5 separate lists)

#### List 1: `framework_agent_loader.py:35-42`
```python
CORE_AGENTS: List[str] = [
    "engineer",       # filename stem
    "research",       # filename stem
    "qa",             # filename stem
    "documentation",  # filename stem
    "ops",            # filename stem
    "ticketing",      # filename stem
]
```
- **Format**: Filename stems (6 agents)
- **Self-described as**: "canonical source - other modules should import from here"
- **Note**: Claims canonical but other modules define their own lists

#### List 2: `toolchain_detector.py:162-170`
```python
CORE_AGENTS = [
    "engineer",              # filename stem
    "qa-agent",              # agent_id format
    "memory-manager-agent",  # agent_id format
    "local-ops-agent",       # agent_id format
    "research-agent",        # agent_id format
    "documentation-agent",   # agent_id format
    "security-agent",        # agent_id format
]
```
- **Format**: Mixed filename stems and agent_id values (7 agents)
- **Different agents**: Includes memory-manager, local-ops, security; EXCLUDES ticketing, ops
- **Inconsistency**: Uses `agent_id` format for most but `engineer` (filename stem)

#### List 3: `agent_presets.py:29-39`
```python
CORE_AGENTS = [
    "claude-mpm/mpm-agent-manager",        # path format
    "claude-mpm/mpm-skills-manager",       # path format
    "engineer/core/engineer",              # path format
    "universal/research",                  # path format
    "qa/qa",                               # path format
    "qa/web-qa",                           # path format
    "documentation/documentation",         # path format
    "ops/core/ops",                        # path format
    "documentation/ticketing",             # path format
]
```
- **Format**: AUTO-DEPLOY-INDEX.md path format (9 agents)
- **Different agents**: Includes mpm-agent-manager, mpm-skills-manager, web-qa; EXCLUDES local-ops, security, memory-manager

#### List 4: `agent_recommendation_service.py:36-43`
```python
CORE_AGENTS = {
    "engineer",       # filename stem
    "research",       # filename stem
    "qa",             # filename stem
    "documentation",  # filename stem
    "ops",            # filename stem
    "ticketing",      # filename stem
}
```
- **Format**: Filename stems as a set (6 agents)
- **Matches**: framework_agent_loader.py list exactly

#### List 5: `agent_deployment_handler.py:26-34`
```python
CORE_AGENTS = [
    "engineer",       # filename stem
    "research",       # filename stem
    "qa",             # filename stem
    "web-qa",         # filename stem
    "documentation",  # filename stem
    "ops",            # filename stem
    "ticketing",      # filename stem
]
```
- **Format**: Filename stems (7 agents)
- **Different**: Adds web-qa compared to framework_agent_loader

### 4.2 CORE_AGENTS Comparison Matrix

| Agent | framework_agent_loader | toolchain_detector | agent_presets | recommendation_svc | deployment_handler |
|---|---|---|---|---|---|
| engineer | `"engineer"` | `"engineer"` | `"engineer/core/engineer"` | `"engineer"` | `"engineer"` |
| research | `"research"` | `"research-agent"` | `"universal/research"` | `"research"` | `"research"` |
| qa | `"qa"` | `"qa-agent"` | `"qa/qa"` | `"qa"` | `"qa"` |
| documentation | `"documentation"` | `"documentation-agent"` | `"documentation/documentation"` | `"documentation"` | `"documentation"` |
| ops | `"ops"` | - | `"ops/core/ops"` | `"ops"` | `"ops"` |
| ticketing | `"ticketing"` | - | `"documentation/ticketing"` | `"ticketing"` | `"ticketing"` |
| web-qa | - | - | `"qa/web-qa"` | - | `"web-qa"` |
| local-ops | - | `"local-ops-agent"` | - | - | - |
| security | - | `"security-agent"` | - | - | - |
| memory-manager | - | `"memory-manager-agent"` | - | - | - |
| mpm-agent-manager | - | - | `"claude-mpm/mpm-agent-manager"` | - | - |
| mpm-skills-manager | - | - | `"claude-mpm/mpm-skills-manager"` | - | - |

### 4.3 TOOLCHAIN_TO_AGENTS Inconsistencies (toolchain_detector.py:137-159)

```python
TOOLCHAIN_TO_AGENTS = {
    "javascript": ["javascript-engineer-agent"],  # agent_id format
    "docker": ["ops", "local-ops-agent"],          # mixed: stem + agent_id
    "vercel": ["vercel-ops-agent"],                # agent_id format
    "gcp": ["gcp-ops-agent"],                      # agent_id format
    # vs
    "python": ["python-engineer"],                 # filename stem
    "typescript": ["typescript-engineer"],          # filename stem
    "make": ["ops"],                               # filename stem
}
```

This list uses a **chaotic mix** of filename stems and agent_id values.

---

## 5. WORKFLOW.md Agent References

**File**: `src/claude_mpm/agents/WORKFLOW.md`

| Reference | Line | Matches `name:` field? |
|---|---|---|
| `Research` | 8 | YES |
| `Code Analysis (Opus model)` | 19 | Partial - `Code Analysis` matches but "(Opus model)" is extra context |
| `API QA` | 39 | YES |
| `Web QA` | 39 | YES |
| `qa` (lowercase) | 39 | NO - deployed `name:` is `QA` (uppercase) |
| `Documentation Agent` | 91 | YES |
| `Security` | 97-99 | YES |
| `Local Ops` | 110-111 | YES |

**Issue**: Line 39 uses lowercase `qa` instead of `QA`.

---

## 6. CLAUDE_MPM_OUTPUT_STYLE.md Agent References

**File**: `src/claude_mpm/agents/CLAUDE_MPM_OUTPUT_STYLE.md`

| Reference | Line | Matches `name:` field? |
|---|---|---|
| `Engineer` | 20 | YES |
| `Research` | 21-22, 25 | YES |
| `local-ops` | 23 | **NO** - should be `Local Ops` |
| `Documentation` | 75 | **NO** - deployed name is `Documentation Agent` |

**Two mismatches found** in the output style file.

---

## 7. The Critical Question: How Does Claude Code Resolve `subagent_type`?

**Answer**: Claude Code matches `Agent(subagent_type="X")` against the `name:` field in YAML frontmatter of `.claude/agents/*.md` files.

**Evidence**:
1. The deprecation warning in `src/claude_mpm/agents/templates/__init__.py:136,146` confirms: "Agent definitions now live in `.claude/agents/*.md` with `name:` field in YAML frontmatter."
2. Recent commit `f392f54e` ("fix: PM references agents by name: field values") confirms the team is actively fixing this exact issue.
3. The `FrameworkAgentLoader` uses filename stems for its own profile loading (`profile_file = directory / f"{agent_type}.md"`), but this is MPM's internal system - Claude Code's `Agent()` tool uses the `name:` field.

**Therefore**:
- `Agent(subagent_type="Research")` -> matches `research.md` `name: Research` -> **SUCCESS**
- `Agent(subagent_type="Local Ops")` -> matches `local-ops.md` `name: Local Ops` -> **SUCCESS**
- `Agent(subagent_type="local-ops")` -> no agent has `name: local-ops` -> **FAILURE**
- `Agent(subagent_type="Documentation")` -> no agent has `name: Documentation` (it's `Documentation Agent`) -> **FAILURE**

---

## 8. Summary of Issues Found

### 8.1 PM Prompt Reference Issues (Priority: HIGH)

| Issue | Location | Current Value | Should Be | Impact |
|---|---|---|---|---|
| Wrong agent name | `CLAUDE_MPM_OUTPUT_STYLE.md:23` | `local-ops` | `Local Ops` | Delegation failure |
| Truncated agent name | `CLAUDE_MPM_OUTPUT_STYLE.md:75` | `Documentation` | `Documentation Agent` | Delegation failure |
| Lowercase qa | `WORKFLOW.md:39` | `qa` | `QA` | May fail delegation |

### 8.2 Hardcoded CORE_AGENTS Fragmentation (Priority: MEDIUM)

5 separate CORE_AGENTS lists across the codebase with:
- Different identifier formats (stems vs agent_ids vs paths)
- Different agent sets (6 to 9 agents)
- No single source of truth despite `framework_agent_loader.py` claiming to be canonical

### 8.3 Naming Convention Chaos in `name:` Fields (Priority: MEDIUM)

4 different conventions used in `name:` fields:
- Title Case: `Local Ops` (majority)
- snake_case: `ticketing_agent`, `mpm_skills_manager`
- kebab-case: `nestjs-engineer`, `real-user`
- Compound: `Documentation Agent`, `Content Optimization`

### 8.4 TOOLCHAIN_TO_AGENTS Mixed Formats (Priority: LOW)

`toolchain_detector.py` TOOLCHAIN_TO_AGENTS dict mixes filename stems and agent_id values inconsistently.

---

## 9. Recommendations

### Immediate Fixes (Blocking)

1. **Fix CLAUDE_MPM_OUTPUT_STYLE.md line 23**: Change `local-ops` to `Local Ops`
2. **Fix CLAUDE_MPM_OUTPUT_STYLE.md line 75**: Change `Documentation` to `Documentation Agent`
3. **Fix WORKFLOW.md line 39**: Change `qa` to `QA`

### Short-term (This Sprint)

4. **Consolidate CORE_AGENTS**: Create a single canonical registry that all 5 modules import from, using a consistent identifier format
5. **Standardize `name:` field convention**: Pick one convention (recommend Title Case) and normalize all deployed agents

### Medium-term

6. **Create AgentType enum**: Replace string-based agent references with a type-safe enum that maps between name fields, filename stems, and agent_ids
7. **Add CI validation**: Test that all PM prompt agent references match deployed `name:` fields
8. **Generate delegation table dynamically**: Instead of a static markdown table in PM_INSTRUCTIONS.md, generate the "When to Delegate" section from deployed agent metadata
