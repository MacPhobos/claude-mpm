# Agent Deployment Pipeline Trace

**Date:** 2026-03-05
**Branch:** `agenttype-enums`
**Scope:** Complete code trace of agent deployment pipeline, archive paths, naming resolution, and duplication vectors

---

## Table of Contents

1. [Pipeline Overview](#1-pipeline-overview)
2. [Stage 1: Git Source Sync (Remote -> Cache)](#2-stage-1-git-source-sync)
3. [Stage 2: Cache -> Deployment (.claude/agents/)](#3-stage-2-cache-to-deployment)
4. [Stage 3: Filename Normalization (The Single Source of Truth)](#4-stage-3-filename-normalization)
5. [Archive Code Paths](#5-archive-code-paths)
6. [Agent Resolution Logic (subagent_type -> file)](#6-agent-resolution-logic)
7. [Duplication Vectors](#7-duplication-vectors)
8. [Naming Inconsistencies in Deployed Agents](#8-naming-inconsistencies-in-deployed-agents)
9. [Complete File Inventory](#9-complete-file-inventory)
10. [Flow Diagrams](#10-flow-diagrams)

---

## 1. Pipeline Overview

The agent deployment pipeline has three stages with two distinct deployment paths:

```
                          ┌─────────────────────┐
                          │  GitHub Repository   │
                          │ (bobmatnyc/claude-   │
                          │  mpm-agents)         │
                          └──────────┬──────────┘
                                     │
                         Git Tree API Discovery
                                     │
                          ┌──────────▼──────────┐
                          │  STAGE 1: Git Sync   │
                          │ GitSourceSyncService │
                          │  (HTTP download)     │
                          └──────────┬──────────┘
                                     │
                          ┌──────────▼──────────┐
                          │  LOCAL CACHE          │
                          │ ~/.claude-mpm/cache/  │
                          │ agents/               │
                          │ (nested repo struct)  │
                          └──────────┬──────────┘
                                     │
                    ┌────────────────┼────────────────┐
                    │                                  │
         PATH A: deploy_cached    PATH B: SingleTier
         _agents (git sync svc)   DeploymentService
                    │                                  │
                    ▼                                  ▼
         ┌──────────────────┐           ┌──────────────────┐
         │ deploy_agent_file│           │ deploy_agent_file │
         │ (deployment_utils│           │ (deployment_utils │
         │  SHARED function)│           │  SHARED function) │
         └────────┬─────────┘           └────────┬─────────┘
                  │                               │
                  └───────────┬───────────────────┘
                              │
                   ┌──────────▼──────────┐
                   │  .claude/agents/     │
                   │  (deployed agents)   │
                   │  Claude Code reads   │
                   │  these at startup    │
                   └─────────────────────┘
```

**Key code files in the pipeline:**

| Stage | File | Purpose |
|-------|------|---------|
| Sync | `services/agents/sources/git_source_sync_service.py` | HTTP download from GitHub, cache management |
| Sync | `services/agents/startup_sync.py` | Startup integration, calls GitSourceSyncService |
| Sync | `services/agents/sources/agent_sync_state.py` | SQLite state tracking for sync |
| Deploy | `services/agents/deployment_utils.py` | **SINGLE SOURCE OF TRUTH** for filename normalization & deployment |
| Deploy | `services/agents/single_tier_deployment_service.py` | Git-source-based deployment orchestrator |
| Deploy | `services/agents/deployment/single_agent_deployer.py` | Legacy individual agent deployer (SEPARATE normalization!) |
| Deploy | `services/agents/deployment/multi_source_deployment_service.py` | Multi-source version comparison |
| Discover | `services/agents/deployment/agent_discovery_service.py` | Template discovery and filtering |
| Registry | `core/agent_name_registry.py` | Canonical stem-to-name mapping |
| Normalize | `core/agent_name_normalizer.py` | Display name normalization for PM |
| Normalize | `utils/agent_filters.py` | `normalize_agent_id_for_comparison()` for configure UI |

---

## 2. Stage 1: Git Source Sync

### Entry Point

Sync is triggered at startup via `startup_sync.py:sync_agents_on_startup()` (line 35):

```python
# startup_sync.py:155-162
sync_service = GitSourceSyncService(
    source_url=source_url,
    cache_dir=cache_dir,
    source_id=source_id,
)
sync_result = sync_service.sync_agents(force_refresh=force_refresh)
```

### Agent Discovery via Git Tree API

`git_source_sync_service.py:684-775` - `_get_agent_list()`:

The service uses GitHub's Git Tree API for recursive discovery (single API call):

```python
# git_source_sync_service.py:732-734
agent_files = self._discover_agents_via_tree_api(
    owner, repo, branch, base_path
)
```

This discovers files like:
- `universal/research.md`
- `engineer/core/engineer.md`
- `ops/platform/local-ops.md`

**Fallback list** (lines 761-775) uses hardcoded paths if API fails.

### Cache Storage

Files are saved to `~/.claude-mpm/cache/agents/` preserving the **nested repository structure**:

```
~/.claude-mpm/cache/agents/
  github-remote/
    claude-mpm-agents/
      agents/
        universal/
          research.md
        engineer/
          core/
            engineer.md
        ops/
          platform/
            local-ops.md
            aws-ops.md
```

**Key observation:** Cache preserves nested directories from the git repo. The **filename in the repo** (e.g., `aws-ops.md`) is the source-of-truth filename that flows through to deployment.

### Cache Discovery

`_discover_cached_agents()` (lines 1196-1248) uses `rglob("*.md")` to find all cached agents:

```python
# git_source_sync_service.py:1223-1243
for file_path in self.cache_dir.rglob("*.md"):
    relative_path = file_path.relative_to(self.cache_dir)
    parts = relative_path.parts
    if "agents" not in parts:
        continue
    agents_idx = parts.index("agents")
    agent_relative = Path(*parts[agents_idx + 1:])
    cached_agents.append(str(agent_relative))
```

**This strips the prefix up to `agents/`** and returns paths like `ops/platform/aws-ops.md`.

**IMPORTANT:** This `rglob("*.md")` searches recursively but has no filter for archive directories or non-agent markdown files within the `agents/` tree. Any `.md` file under any `agents/` directory in the cache will be discovered.

---

## 3. Stage 2: Cache to Deployment

### Path A: GitSourceSyncService.deploy_cached_agents()

`git_source_sync_service.py:1020-1162` - Called by `deploy_agents_to_project()`:

```python
# git_source_sync_service.py:1051-1053
# Deploy to .claude/agents/ where Claude Code expects them
deployment_dir = project_dir / ".claude" / "agents"
deployment_dir.mkdir(parents=True, exist_ok=True)
```

For each cached agent, it:
1. Resolves the cache path via `_resolve_cache_path()` (line 1119)
2. Calls `deploy_agent_file()` from `deployment_utils.py` (lines 1129-1135)

```python
# git_source_sync_service.py:1129-1135
result = deploy_agent_file(
    source_file=cache_file,
    deployment_dir=deployment_dir,
    cleanup_legacy=True,
    ensure_frontmatter=True,
    force=force,
)
```

### Path B: SingleTierDeploymentService._deploy_agent_file()

`single_tier_deployment_service.py:655-700`:

```python
# single_tier_deployment_service.py:681-687
result = deploy_agent_file(
    source_file=source_file,
    deployment_dir=self.deployment_dir,
    cleanup_legacy=True,
    ensure_frontmatter=True,
    force=False,
)
```

**Both paths converge on the same `deploy_agent_file()` function** -- this is the Phase 3 unification (Issue #299).

### Path C: SingleAgentDeployer.deploy_single_agent() (LEGACY - DIFFERENT NORMALIZATION!)

`deployment/single_agent_deployer.py:64-71` has its **OWN normalization** that does NOT call `deploy_agent_file()`:

```python
# single_agent_deployer.py:68-71
agent_name = template_file.stem.lower().replace("_", "-")
if agent_name.endswith("-agent"):
    agent_name = agent_name[:-6]
target_file = agents_dir / f"{agent_name}.md"
```

This is **inline normalization** that duplicates (but matches) the logic in `deployment_utils.py`. However, it does NOT:
- Call `deploy_agent_file()` (writes directly via `target_file.write_text()`)
- Clean up legacy underscore variants
- Ensure agent_id in frontmatter

**This is a duplication vector.** If `SingleAgentDeployer` is used alongside `deploy_agent_file()`, both could write the same agent but with different frontmatter treatment.

### _resolve_cache_path() - How nested cache maps to flat deployment

`git_source_sync_service.py:1164-1194`:

```python
# Uses rglob to find the file inside nested cache structure
candidates = list(self.cache_dir.rglob(f"**/agents/{agent_path}"))
if candidates:
    return candidates[0]

# Fallback: flat cache (legacy)
flat_path = self.cache_dir / agent_path
if flat_path.exists():
    return flat_path
```

The `rglob` search means a path like `ops/platform/aws-ops.md` will match:
`~/.claude-mpm/cache/agents/github-remote/claude-mpm-agents/agents/ops/platform/aws-ops.md`

---

## 4. Stage 3: Filename Normalization (The Single Source of Truth)

### deploy_agent_file() - deployment_utils.py:316-465

This is documented as the "SINGLE SOURCE OF TRUTH" for agent file deployment.

**Algorithm:**

```python
# deployment_utils.py:381
normalized_filename = normalize_deployment_filename(source_file.name)
target_file = deployment_dir / normalized_filename
```

### normalize_deployment_filename() - deployment_utils.py:36-80

```python
def normalize_deployment_filename(source_filename, agent_id=None):
    path = Path(source_filename)
    stem = path.stem

    # Normalize: lowercase, replace underscores with dashes
    normalized_stem = stem.lower().replace("_", "-")

    # Strip -agent suffix
    if normalized_stem.endswith("-agent"):
        normalized_stem = normalized_stem[:-6]

    return f"{normalized_stem}.md"
```

**Examples:**
| Input | Output |
|-------|--------|
| `python-engineer.md` | `python-engineer.md` |
| `python_engineer.md` | `python-engineer.md` |
| `QA.md` | `qa.md` |
| `research-agent.md` | `research.md` |
| `memory-manager-agent.md` | `memory-manager.md` |

### Legacy Underscore Cleanup

`deployment_utils.py:386-395`:

```python
if cleanup_legacy:
    underscore_variant = get_underscore_variant_filename(normalized_filename)
    if underscore_variant:
        underscore_path = deployment_dir / underscore_variant
        if underscore_path.exists() and underscore_path != target_file:
            underscore_path.unlink()
            cleaned_legacy.append(underscore_variant)
```

### Frontmatter Injection

`deployment_utils.py:426-430`:

```python
if ensure_frontmatter:
    deploy_content = ensure_agent_id_in_frontmatter(
        source_content, normalized_filename
    )
```

`ensure_agent_id_in_frontmatter()` (lines 83-149) derives `agent_id` from the **normalized filename**:

```python
derived_agent_id = Path(filename).stem.lower().replace("_", "-")
if derived_agent_id.endswith("-agent"):
    derived_agent_id = derived_agent_id[:-6]
```

**CRITICAL BUG:** The `agent_id` is derived from the **already-normalized** deployment filename, but `update_existing=False` by default. This means if the original source file already has an `agent_id` in its frontmatter (e.g., `agent_id: research-agent`), **it is NOT overwritten**. The deployed file at `research.md` will have `agent_id: research-agent` in its frontmatter, creating a mismatch between filename stem and agent_id.

---

## 5. Archive Code Paths

### Archive Directory Status

**The `src/claude_mpm/agents/templates/archive/` directory does NOT exist.**

```
$ find src/claude_mpm/agents/templates/archive/ -> No files found
$ grep -r "archive" src/claude_mpm/agents/ -> No matches
```

The templates directory contains only:
- `__init__.py` (deprecated template mappings)
- Various `.md` example/instruction files (pm-examples, circuit-breakers, etc.)
- No JSON files, no archive directory

### Can Archive Templates Get Deployed?

**No, through the current pipeline.** Here's why:

1. **Discovery filters by `.md` extension only** -- `agent_discovery_service.py:129`:
   ```python
   template_files = list(self.templates_dir.glob("*.md"))
   ```

2. **Templates directory is NOT in the deployment path for remote agents.** The git sync path (`GitSourceSyncService`) pulls from GitHub, not from `src/claude_mpm/agents/templates/`.

3. **The old `templates/__init__.py` is fully deprecated** (line 5-7):
   ```python
   # This module is deprecated. The AGENT_TEMPLATES dict references .md template files
   # (e.g., documentation_agent.md, engineer_agent.md) that no longer exist in this
   # directory.
   ```
   It maps to underscore-format filenames (`documentation_agent.md`, `engineer_agent.md`) that don't exist.

4. **The base_agent.json path** (used by `SingleAgentDeployer`) references a JSON config, not markdown agents.

### Remaining Risk: templates/*.md files

The `templates/` directory contains `.md` files like `pm-examples.md`, `circuit-breakers.md`, etc. If `AgentDiscoveryService.get_filtered_templates()` is pointed at this directory, it would discover these instruction files. However:

- These files lack YAML frontmatter with `name`/`description` fields
- `_validate_template_file()` (line 483) would reject them (missing required fields)
- The validator also checks `agent_id` format via regex: `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`

**Verdict: Archive contamination is NOT a current risk.** The archive directory was removed, and the template files in `templates/` are filtered out by validation.

---

## 6. Agent Resolution Logic

### How subagent_type Gets Resolved to an Agent File

Claude Code resolves agents by **filename stem** in `.claude/agents/`. When the PM delegates with `subagent_type="research"`, Claude Code looks for `.claude/agents/research.md`.

However, there's a second resolution mechanism via the `name:` frontmatter field. Claude Code can also match agents by their `name:` field value.

### Agent Name Registry (core/agent_name_registry.py)

This module provides the canonical mapping between filename stems and `name:` values:

```python
# agent_name_registry.py:43-116
AGENT_NAME_MAP = {
    "engineer": "Engineer",
    "research": "Research",
    "qa": "QA",
    "ticketing": "ticketing_agent",        # INCONSISTENT - underscore format
    "aws-ops": "aws_ops_agent",            # INCONSISTENT - underscore format
    "nestjs-engineer": "nestjs-engineer",  # INCONSISTENT - stem format, not display name
    "real-user": "real-user",              # INCONSISTENT - stem format
    "mpm-agent-manager": "mpm_agent_manager",  # INCONSISTENT - underscore format
    "mpm-skills-manager": "mpm_skills_manager", # INCONSISTENT - underscore format
    ...
}
```

### AgentNameNormalizer (core/agent_name_normalizer.py)

This is used by the PM for TodoWrite prefixes and Task tool formatting:

```python
# agent_name_normalizer.py:262-318
@classmethod
def normalize(cls, agent_name: str) -> str:
    cleaned = agent_name.strip().lower()
    cleaned = cleaned.replace("_", "-").replace(" ", "-")

    for suffix in ("-agent", "-agent-agent"):
        if cleaned.endswith(suffix):
            cleaned = cleaned[:-len(suffix)]
            break

    if cleaned in cls.ALIASES:
        canonical_key = cls.ALIASES[cleaned]
        return cls.CANONICAL_NAMES.get(canonical_key, "Engineer")
    ...
```

### normalize_agent_id_for_comparison (utils/agent_filters.py)

Used by the `configure` CLI command for installed detection:

```python
# agent_filters.py:27-42
def normalize_agent_id_for_comparison(agent_id: str) -> str:
    # 1. Convert underscores to hyphens
    # 2. Strip '-agent' suffix
    # 3. Lowercase
```

### _normalize_agent_name (multi_source_deployment_service.py)

```python
# multi_source_deployment_service.py:29-38
def _normalize_agent_name(name: str) -> str:
    return name.lower().replace(" ", "-").replace("_", "-")
```

**PROBLEM: There are 5+ DIFFERENT normalization functions**, each slightly different:

| Function | Location | Strips `-agent`? | Strips spaces? | Handles `_`? |
|----------|----------|------------------|----------------|-------------|
| `normalize_deployment_filename` | deployment_utils.py | Yes | No | Yes -> `-` |
| `_normalize_agent_name` | multi_source_deployment_service.py | No | Yes -> `-` | Yes -> `-` |
| `AgentNameNormalizer.normalize` | agent_name_normalizer.py | Yes (+ `-agent-agent`) | Yes -> `-` | Yes -> `-` |
| `normalize_agent_id_for_comparison` | agent_filters.py | Yes | No | Yes -> `-` |
| `DynamicAgentRegistry.normalize_agent_id` | agent_registry.py | Yes | Yes -> `-` | Yes -> `-` |
| `SingleAgentDeployer` inline | single_agent_deployer.py:68 | Yes | No | Yes -> `-` |

---

## 7. Duplication Vectors

### Vector 1: `-agent` Suffix Inconsistency

The `normalize_deployment_filename()` strips `-agent` suffix. But some agents are deployed with the suffix NOT stripped because their **source filenames** in the git repo already include `-agent`:

**Currently deployed agents with `-agent` in filename:**
- `content-agent.md` (name: "Content Optimization")
- `memory-manager-agent.md` (name: "Memory Manager")
- `tmux-agent.md` (name: "Tmux Agent")

**Why these weren't stripped:** The `-agent` suffix stripping in `normalize_deployment_filename()` strips `"-agent"` from the stem. But:
- `content-agent` -> stem is `content-agent` -> stripped to `content` -> deployed as `content.md`

Wait - but the deployed file IS named `content-agent.md`. This means either:
1. These files were deployed by a code path that does NOT call `normalize_deployment_filename()`
2. Or the source filename in the cache is something different

**Investigation:** The `SingleAgentDeployer.deploy_single_agent()` (line 68) DOES strip `-agent`:
```python
agent_name = template_file.stem.lower().replace("_", "-")
if agent_name.endswith("-agent"):
    agent_name = agent_name[:-6]
```

But `deploy_agent_file()` also strips it. So the existence of `content-agent.md`, `memory-manager-agent.md`, and `tmux-agent.md` in `.claude/agents/` means they were deployed by a path that does NOT normalize, OR the source filenames are literally `content-agent.md` etc. in the git repository and the normalization runs on the LAST segment only.

**Root cause:** Looking at `normalize_deployment_filename()`:
```python
stem = path.stem  # "content-agent"
normalized_stem = stem.lower().replace("_", "-")  # "content-agent"
if normalized_stem.endswith("-agent"):
    normalized_stem = normalized_stem[:-6]  # "content"
```

This WOULD produce `content.md`. But the deployed file is `content-agent.md`. This confirms these were deployed by a NON-normalizing code path, or the normalization was added after these files were deployed and they haven't been redeployed since.

### Vector 2: agent_id vs filename mismatch

From the deployed agents grep, many agents have `agent_id` values that don't match their filename stem:

| Deployed Filename | `agent_id:` in frontmatter | Match? |
|---|---|---|
| `research.md` | `research-agent` | MISMATCH |
| `qa.md` | `qa-agent` | MISMATCH |
| `documentation.md` | `documentation-agent` | MISMATCH |
| `ops.md` | `ops-agent` | MISMATCH |
| `security.md` | `security-agent` | MISMATCH |
| `local-ops.md` | `local-ops-agent` | MISMATCH |
| `vercel-ops.md` | `vercel-ops-agent` | MISMATCH |
| `gcp-ops.md` | `gcp-ops-agent` | MISMATCH |
| `digitalocean-ops.md` | `digitalocean-ops-agent` | MISMATCH |
| `api-qa.md` | `api-qa-agent` | MISMATCH |
| `web-qa.md` | `web-qa-agent` | MISMATCH |
| `javascript-engineer.md` | `javascript-engineer-agent` | MISMATCH |
| `web-ui.md` | `web-ui-engineer` | MISMATCH |
| `ruby-engineer.md` | `ruby_engineer` (underscore!) | MISMATCH |
| `golang-engineer.md` | `golang_engineer` (underscore!) | MISMATCH |
| `java-engineer.md` | `java_engineer` (underscore!) | MISMATCH |
| `dart-engineer.md` | `dart_engineer` (underscore!) | MISMATCH |
| `php-engineer.md` | `php_engineer` (underscore!) | MISMATCH |
| `svelte-engineer.md` | `svelte_engineer` (underscore!) | MISMATCH |
| `rust-engineer.md` | `rust_engineer` (underscore!) | MISMATCH |
| `react-engineer.md` | `react_engineer` (underscore!) | MISMATCH |
| `nextjs-engineer.md` | `nextjs_engineer` (underscore!) | MISMATCH |
| `tauri-engineer.md` | `tauri_engineer` (underscore!) | MISMATCH |
| `visual-basic-engineer.md` | `visual_basic_engineer` (underscore!) | MISMATCH |
| `nestjs-engineer.md` | `nestjs_engineer` (underscore!) | MISMATCH |
| `product-owner.md` | `product_owner` (underscore!) | MISMATCH |
| `real-user.md` | `real_user` (underscore!) | MISMATCH |
| `content-agent.md` | `content-agent` | match (but file has -agent suffix!) |
| `memory-manager-agent.md` | `memory-manager-agent` | match (but file has -agent suffix!) |
| `tmux-agent.md` | `tmux-agent` | match (but file has -agent suffix!) |

**Root cause:** `ensure_agent_id_in_frontmatter()` has `update_existing=False` by default. The `agent_id` values come from the original source files in the git repo and are never overwritten during deployment.

### Vector 3: `name:` Field Inconsistencies

| Deployed Filename | `name:` value | Issue |
|---|---|---|
| `ticketing.md` | `ticketing_agent` | Underscore format, not human-readable |
| `aws-ops.md` | `aws_ops_agent` | Underscore format, not human-readable |
| `nestjs-engineer.md` | `nestjs-engineer` | Stem format, not "NestJS Engineer" |
| `real-user.md` | `real-user` | Stem format, not "Real User" |
| `mpm-agent-manager.md` | `mpm_agent_manager` | Underscore format |
| `mpm-skills-manager.md` | `mpm_skills_manager` | Underscore format |

These `name:` values are what Claude Code uses for agent matching via `subagent_type`. If the PM delegates to `subagent_type="ticketing"`, Claude Code needs to find an agent with `name: "ticketing"` or filename `ticketing.md`. But the `name:` is `ticketing_agent`, which may or may not match depending on Claude Code's internal resolution.

### Vector 4: Dual Deployer Code Paths

Two active deployers can write to `.claude/agents/`:

1. **`deploy_agent_file()`** (deployment_utils.py) - The unified path
2. **`SingleAgentDeployer.deploy_single_agent()`** (single_agent_deployer.py) - Legacy path

The legacy path:
- Does NOT clean up underscore variants
- Does NOT ensure agent_id in frontmatter
- Writes directly via `target_file.write_text(agent_content)`

If both paths deploy the same agent, the last writer wins, potentially with different frontmatter.

### Vector 5: agents_metadata.py Name Inconsistencies

The `agents_metadata.py` file uses **different naming conventions** for agent names:

```python
DOCUMENTATION_CONFIG = {"name": "documentation_agent", ...}  # underscore + _agent
VERSION_CONTROL_CONFIG = {"name": "version-control-agent", ...}  # dash + -agent
QA_CONFIG = {"name": "qa_agent", ...}  # underscore + _agent
DATA_ENGINEER_CONFIG = {"name": "data-engineer-agent", ...}  # dash + -agent
ENGINEER_CONFIG = {"name": "engineer_agent", ...}  # underscore + _agent
PROJECT_ORGANIZER_CONFIG = {"name": "project_organizer_agent", ...}  # underscore + _agent
IMAGEMAGICK_CONFIG = {"name": "imagemagick_agent", ...}  # underscore + _agent
```

Mixed conventions: some use underscores, some use dashes, all have `_agent` or `-agent` suffix.

---

## 8. Naming Inconsistencies in Deployed Agents

### Summary of All 48 Deployed Agents

From `.claude/agents/` directory:

**Consistent agents (filename = stem, name = Human Readable):**
- `engineer.md` -> name: "Engineer", agent_id: "engineer"
- `python-engineer.md` -> name: "Python Engineer", agent_id: "python-engineer"
- `data-engineer.md` -> name: "Data Engineer", agent_id: "data-engineer"
- `data-scientist.md` -> name: "Data Scientist", agent_id: "data-scientist"
- `prompt-engineer.md` -> name: "Prompt Engineer", agent_id: "prompt-engineer"
- `refactoring-engineer.md` -> name: "Refactoring Engineer", agent_id: "refactoring-engineer"
- `typescript-engineer.md` -> name: "Typescript Engineer", agent_id: "typescript-engineer"
- `version-control.md` -> name: "Version Control", agent_id: "version-control"
- `project-organizer.md` -> name: "Project Organizer", agent_id: "project-organizer"
- `imagemagick.md` -> name: "Imagemagick", agent_id: "imagemagick"
- `agentic-coder-optimizer.md` -> name: "Agentic Coder Optimizer", agent_id: "agentic-coder-optimizer"
- `clerk-ops.md` -> name: "Clerk Operations", agent_id: "clerk-ops"

**Agents with agent_id mismatch (underscore or -agent suffix):**
- 13 agents with underscore `agent_id` (e.g., `ruby_engineer`, `golang_engineer`)
- 12 agents with `-agent` suffix in `agent_id` (e.g., `research-agent`, `qa-agent`)
- 1 agent with `-engineer` suffix mismatch (`web-ui-engineer` for `web-ui.md`)

**Agents with non-standard `name:` values:**
- 6 agents with underscore/stem format names (e.g., `ticketing_agent`, `aws_ops_agent`)

---

## 9. Complete File Inventory

### Pipeline Code Files

```
src/claude_mpm/
├── agents/
│   ├── __init__.py
│   ├── agent_loader.py                    # Legacy agent loader
│   ├── agent_loader_integration.py        # Integration layer
│   ├── agents_metadata.py                 # Hardcoded agent configs (mixed naming)
│   ├── async_agent_loader.py              # Async agent loader
│   ├── base_agent.json                    # Base agent config (JSON)
│   ├── BASE_AGENT.md                      # Base agent template
│   ├── BASE_ENGINEER.md                   # Base engineer template
│   ├── frontmatter_validator.py           # YAML frontmatter validation
│   ├── PM_INSTRUCTIONS.md                 # PM instructions template
│   ├── system_agent_config.py             # System agent model assignments
│   ├── bundled/
│   │   └── ticketing.md                   # Bundled ticketing agent
│   └── templates/
│       ├── __init__.py                    # DEPRECATED template mappings
│       ├── README.md
│       ├── circuit-breakers.md            # PM instruction template
│       ├── context-management-examples.md
│       ├── git-file-tracking.md
│       ├── pm-examples.md
│       ├── pm-red-flags.md
│       ├── pr-workflow-examples.md
│       ├── research-gate-examples.md
│       ├── response-format.md
│       ├── structured-questions-examples.md
│       ├── ticket-completeness-examples.md
│       ├── ticketing-examples.md
│       └── validation-templates.md
├── core/
│   ├── agent_name_normalizer.py           # Display name normalization
│   ├── agent_name_registry.py             # Canonical stem<->name mapping
│   ├── agent_registry.py                  # Consolidated registry (delegates to unified)
│   └── deployment_context.py              # Deployment context
├── services/agents/
│   ├── deployment_utils.py                # SINGLE SOURCE OF TRUTH for deployment
│   ├── single_tier_deployment_service.py  # Git-source deployment orchestrator
│   ├── startup_sync.py                    # Startup sync integration
│   ├── deployment/
│   │   ├── agent_discovery_service.py     # Template discovery & filtering
│   │   ├── agent_deployment.py            # Legacy deployment service
│   │   ├── multi_source_deployment_service.py  # Multi-source version comparison
│   │   ├── single_agent_deployer.py       # Legacy single agent deployer
│   │   ├── deployment_reconciler.py       # Deployment reconciliation
│   │   ├── local_template_deployment.py   # Local template deployment
│   │   └── remote_agent_discovery_service.py  # Remote agent discovery
│   ├── sources/
│   │   ├── git_source_sync_service.py     # HTTP sync from GitHub
│   │   └── agent_sync_state.py            # SQLite state tracking
│   └── registry/
│       └── deployed_agent_discovery.py    # Deployed agent analysis
└── utils/
    └── agent_filters.py                   # normalize_agent_id_for_comparison
```

### Deployed Agents (48 files in .claude/agents/)

All 48 deployed `.md` files with their `name:` and `agent_id:` values are documented in Section 8 above.

---

## 10. Flow Diagrams

### Filename Normalization Flow

```
Source file in git repo
  e.g., "research-agent.md" or "dart_engineer.md"
         │
         ▼
┌─────────────────────────┐
│ normalize_deployment_    │
│ filename()               │
│ deployment_utils.py:36   │
│                          │
│ 1. stem = path.stem      │
│    "research-agent"      │
│ 2. lower().replace(_,-)  │
│    "research-agent"      │
│ 3. strip "-agent" suffix │
│    "research"            │
│ 4. add ".md"             │
│    "research.md"         │
└────────┬────────────────┘
         │
         ▼
Target: .claude/agents/research.md
         │
         ▼
┌─────────────────────────┐
│ ensure_agent_id_in_     │
│ frontmatter()            │
│ deployment_utils.py:83   │
│                          │
│ Derives agent_id from    │
│ normalized filename:     │
│  "research"              │
│                          │
│ BUT: update_existing=    │
│ False (default)          │
│                          │
│ Original agent_id:       │
│  "research-agent"        │
│ -> NOT OVERWRITTEN!      │
└─────────────────────────┘
```

### Agent Resolution Flow (PM Delegation)

```
PM delegates: subagent_type="research"
         │
         ▼
┌─────────────────────────┐
│ Claude Code Resolution   │
│                          │
│ 1. Look for file:        │
│    .claude/agents/       │
│    research.md           │
│    -> FOUND              │
│                          │
│ 2. Read name: field      │
│    name: "Research"      │
│    -> MATCH              │
│                          │
│ 3. Use agent content     │
│    as system prompt      │
└─────────────────────────┘

PM delegates: subagent_type="ticketing_agent"
         │
         ▼
┌─────────────────────────┐
│ Claude Code Resolution   │
│                          │
│ 1. Look for file:        │
│    .claude/agents/       │
│    ticketing_agent.md    │
│    -> NOT FOUND          │
│                          │
│ 2. Scan name: fields     │
│    ticketing.md has      │
│    name: "ticketing_     │
│    agent"                │
│    -> POSSIBLE MATCH     │
│    (depends on Claude    │
│    Code's matching)      │
└─────────────────────────┘
```

### Multiple Normalizer Problem

```
Same agent "Python Engineer" needs normalization in different contexts:

For deployment filename:
  normalize_deployment_filename("python_engineer.md")
  -> "python-engineer.md"

For exclusion filtering:
  _normalize_agent_name("Python Engineer")
  -> "python-engineer"

For PM TodoWrite prefix:
  AgentNameNormalizer.normalize("python-engineer")
  -> "Python Engineer"

For configure installed detection:
  normalize_agent_id_for_comparison("python_engineer")
  -> "python-engineer"

For registry lookup:
  DynamicAgentRegistry.normalize_agent_id("python_engineer")
  -> "python-engineer"

ALL produce consistent results for THIS case.
But edge cases diverge (e.g., "-agent" suffix handling,
space handling, "engineer" alias matching).
```

---

## Key Findings Summary

1. **Archive contamination: NOT a risk.** The archive directory doesn't exist, and template validation filters out non-agent `.md` files.

2. **Filename separator handling: RESOLVED at deployment level** via `normalize_deployment_filename()`, but **NOT resolved in frontmatter**. Deployed agents have mismatched `agent_id` values (underscores and `-agent` suffixes) that don't match their dash-based filenames.

3. **Dual deployer paths exist.** `SingleAgentDeployer` writes agents without calling the unified `deploy_agent_file()`, creating a vector for inconsistent frontmatter.

4. **5+ normalization functions** with subtly different behavior. While they mostly agree for common cases, edge cases in `-agent` suffix stripping and space handling could cause mismatches.

5. **`name:` field inconsistencies** in 6 deployed agents use underscore or stem formats instead of human-readable display names, which may affect Claude Code's agent resolution.

6. **`agent_id` mismatches are pervasive** -- 26 of 48 deployed agents have `agent_id` values that don't match their filename stem, due to `update_existing=False` in `ensure_agent_id_in_frontmatter()`.

7. **`agent_name_registry.py` mirrors the inconsistencies** rather than fixing them -- it maps stems to the actual (inconsistent) `name:` values from deployed files.
