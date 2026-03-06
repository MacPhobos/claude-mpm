# Pipeline Trace: Agent Deployment Code Paths & Archive References

## Executive Summary

The `src/claude_mpm/agents/templates/archive/` directory contains **39 JSON template files** that are the **legacy (pre-migration) versions** of agent definitions. They are NOT directly referenced by any deployment pipeline code. However, the `UnifiedAgentRegistry` **does inadvertently discover them** via `rglob("*")`. The primary deployment path uses Git-cached `.md` files from `~/.claude-mpm/cache/agents/`, not archive JSON files.

---

## 1. Agent Source Architecture (Two Systems)

There are **two independent systems** for agent definitions:

### System A: Archive JSON Templates (LEGACY - NOT actively deployed)
- **Location**: `src/claude_mpm/agents/templates/archive/*.json` (39 files)
- **Format**: JSON with `agent_id`, `metadata`, `instructions`, `capabilities`
- **Purpose**: Original bundled agent definitions, kept for reference/migration
- **Used by**: `SimpleAgentManager._discover_local_template_agents()` reads `templates/*.json` (but archive is a subdirectory, not at `*.json` glob level)

### System B: Git-Cached Markdown Agents (ACTIVE - deployed to .claude/agents/)
- **Location**: `~/.claude-mpm/cache/agents/bobmatnyc/claude-mpm-agents/agents/**/*.md`
- **Format**: Markdown with YAML frontmatter
- **Purpose**: Active agent definitions fetched from GitHub
- **Used by**: `GitSourceSyncService.deploy_agents_to_project()`, `SingleTierDeploymentService`, `AgentDeploymentService`

---

## 2. Deployment Flow Sequence Diagrams

### Flow A: `claude-mpm configure` (Interactive)

```
User runs: claude-mpm configure
    |
    v
ConfigureCommand.__init__()
    |
    v
_load_agents_with_spinner()
    |
    +--> SimpleAgentManager.discover_agents(include_remote=True)
    |       |
    |       +--> _discover_local_template_agents()
    |       |       |
    |       |       +--> self.templates_dir.glob("*.json")
    |       |       |    Path: src/claude_mpm/agents/templates/*.json
    |       |       |    Result: NO FILES FOUND (*.json is at top level,
    |       |       |            archive/ is a subdirectory)
    |       |       |
    |       |       +--> Returns [] (empty list)
    |       |
    |       +--> _discover_git_agents()
    |       |       |
    |       |       +--> GitSourceManager().list_cached_agents()
    |       |       |    Path: ~/.claude-mpm/cache/agents/
    |       |       |    Result: 40+ agents from git cache
    |       |       |
    |       |       +--> Returns [AgentConfig, AgentConfig, ...]
    |       |
    |       +--> Returns combined list (git agents only in practice)
    |
    v
User selects agents -> _deploy_agents_unified()
    |
    v
(Calls deployment service to write .md files to .claude/agents/)
```

### Flow B: `claude-mpm agents deploy` (CLI Deploy)

```
User runs: claude-mpm agents deploy [--force]
    |
    v
AgentCommands._deploy_agents(args, force)
    |  (src/claude_mpm/cli/commands/agents.py:606)
    |
    v
GitSourceSyncService().sync_agents()       # Phase 1: Sync from GitHub to cache
    |  (src/claude_mpm/services/agents/sources/git_source_sync_service.py)
    |
    v
git_sync.deploy_agents_to_project()        # Phase 2: Deploy from cache to project
    |  (git_source_sync_service.py:992)
    |
    +--> deployment_dir = project_dir / ".claude" / "agents"
    +--> agent_list = self._discover_cached_agents()
    |       |
    |       +--> Scans ~/.claude-mpm/cache/agents/ for .md files
    |       +--> Returns list of cached agent paths
    |
    +--> For each cached agent:
    |       +--> Copy .md file from cache to .claude/agents/
    |       +--> Track deployed/updated/skipped
    |
    +--> Returns deployment results
```

### Flow C: `claude-mpm auto-configure` (Auto Config)

```
User runs: claude-mpm auto-configure
    |
    v
AutoConfigureCommand._auto_configure_agents()
    |  (src/claude_mpm/cli/commands/auto_configure.py)
    |
    +--> Option 1: _deploy_role_agents() (line ~1050)
    |       |
    |       +--> GitSourceSyncService().deploy_agents_to_project()
    |       |    (Same flow as Flow B Phase 2)
    |
    +--> Option 2: AgentDeploymentService().deploy_agents()
    |       |  (auto_configure.py:192)
    |       |
    |       v
    |    AgentDeploymentService.__init__()
    |       |  (agent_deployment.py:90)
    |       |
    |       +--> templates_dir = paths.agents_dir / "templates"
    |       |    Resolves to: src/claude_mpm/agents/templates/
    |       |
    |       v
    |    deploy_agents()  (agent_deployment.py:294)
    |       |
    |       +--> _sync_remote_agent_sources()  # Sync git sources
    |       +--> _should_use_multi_source_deployment() -> True
    |       +--> _get_multi_source_templates()
    |       |       |
    |       |       +--> MultiSourceAgentDeploymentService.get_agents_for_deployment()
    |       |       |       |
    |       |       |       +--> discover_agents_from_all_sources()
    |       |       |       |       |
    |       |       |       |       +--> Tier 1 (system): AgentDiscoveryService(system_templates_dir)
    |       |       |       |       |       +--> list_available_agents()
    |       |       |       |       |       |   +--> templates_dir.glob("*.md")
    |       |       |       |       |       |   |   Path: src/claude_mpm/agents/templates/*.md
    |       |       |       |       |       |   |   Result: PM instruction templates (not agents)
    |       |       |       |       |       |   |
    |       |       |       |       |       |   +--> discover_git_cached_agents()
    |       |       |       |       |       |       +--> Scans ~/.claude-mpm/cache/agents/
    |       |       |       |       |       |       +--> Returns cached git agents
    |       |       |       |       |       |
    |       |       |       |       |       +--> Returns system agents (mostly git cache)
    |       |       |       |       |
    |       |       |       |       +--> Tier 2 (user): DEPRECATED, ~/.claude-mpm/agents/
    |       |       |       |       +--> Tier 3 (remote): ~/.claude-mpm/cache/agents/
    |       |       |       |       +--> Tier 4 (project): .claude-mpm/agents/
    |       |       |       |
    |       |       |       +--> select_highest_version_agents()
    |       |       |
    |       |       +--> Returns (template_files, agent_sources, cleanup_results)
    |       |
    |       +--> For each template: SingleAgentDeployer.deploy()
    |               +--> Writes .md to .claude/agents/
```

### Flow D: Startup (Hook-Triggered)

```
Claude Code starts -> hooks fire -> claude-mpm startup
    |
    v
startup_checker.py / cli/startup.py
    |
    v
AgentDeploymentService().deploy_agents()
    (Same as Flow C Option 2)
```

---

## 3. All References to `archive/` in Python Source

### Direct Path References (2 files)

| File | Line | Context | Risk Level |
|------|------|---------|------------|
| `scripts/delegation_matrix_poc.py` | 20 | `Path(...) / "src/claude_mpm/agents/templates/archive"` - POC script reading JSON templates | LOW (script only) |
| `scripts/migrate_json_to_markdown.py` | 593 | `--archive` flag to move JSON files to `templates/archive/` | LOW (migration tool) |

### Indirect Discovery via `rglob` (1 file - CRITICAL)

| File | Line | Context | Risk Level |
|------|------|---------|------------|
| `unified_agent_registry.py` | 256 | `path.rglob("*")` discovers ALL files under system agents dir, including `templates/archive/*.json` | **HIGH** |

### "Archive" in Different Context (not `templates/archive/`)

The word "archive" appears in ~59 Python files, but most refer to:
- **Message archiving** (`services/communication/message_service.py`, `messaging_db.py`)
- **Log archiving** (`utils/log_cleanup.py`, `services/event_log.py`)
- **Session archiving** (`services/cli/session_manager.py`)
- **Agent archiving** (moving unused agents to `.claude/agents/unused/`) in `auto_configure.py` and `agent_review_service.py`
- **MCP archive** (`mcp/archive/google_workspace_server.py`)

None of these are related to `src/claude_mpm/agents/templates/archive/`.

---

## 4. Critical Decision Points: Archive vs Cache

### Decision Point 1: `SimpleAgentManager._discover_local_template_agents()`
**File**: `src/claude_mpm/cli/commands/agent_state_manager.py:141`
```python
for template_file in sorted(self.templates_dir.glob("*.json")):
```
- **Path**: `src/claude_mpm/agents/templates/*.json`
- **Archive Impact**: NONE - `*.json` glob does NOT recurse into `archive/` subdirectory
- **Result**: Returns empty list (no `.json` files at top level of `templates/`)

### Decision Point 2: `AgentDiscoveryService.list_available_agents()`
**File**: `src/claude_mpm/services/agents/deployment/agent_discovery_service.py:128`
```python
template_files = list(self.templates_dir.glob("*.md"))
```
- **Path**: `src/claude_mpm/agents/templates/*.md`
- **Archive Impact**: NONE - `*.md` glob does NOT recurse into `archive/` subdirectory
- **Result**: Returns PM instruction `.md` files (not agents), which fail frontmatter validation

### Decision Point 3: `UnifiedAgentRegistry._discover_path()` (**CRITICAL**)
**File**: `src/claude_mpm/core/unified_agent_registry.py:256`
```python
for file_path in path.rglob("*"):
```
- **Path**: `src/claude_mpm/agents/` (system agents dir, includes `templates/` subdirectory)
- **Archive Impact**: **YES** - `rglob("*")` DOES recurse into `templates/archive/` and discovers all 39 `.json` files
- **Result**: Archive JSON files ARE registered in the UnifiedAgentRegistry as SYSTEM tier agents
- **But**: These registrations are only used for agent listing/lookup, NOT for deployment to `.claude/agents/`

### Decision Point 4: `GitSourceSyncService.deploy_agents_to_project()`
**File**: `src/claude_mpm/services/agents/sources/git_source_sync_service.py:992`
```python
agent_list = self._discover_cached_agents()
```
- **Path**: `~/.claude-mpm/cache/agents/`
- **Archive Impact**: NONE - Only reads from git cache directory
- **Result**: Deploys agents from git cache to `.claude/agents/`

---

## 5. Why Archive Agents Are NOT Deployed (Despite Being Discovered)

The archive `.json` files ARE discovered by `UnifiedAgentRegistry` via `rglob`, but they are NOT deployed because:

1. **Deployment uses a separate pipeline**: The deployment pipeline (`deploy_agents()`, `deploy_agents_to_project()`) reads from:
   - Git cache (`~/.claude-mpm/cache/agents/`) via `GitSourceSyncService`
   - System templates (`templates/*.md`) via `AgentDiscoveryService` (which uses `glob("*.md")`, not `rglob`)

2. **Format mismatch**: Archive files are `.json`, but the deployment pipeline expects `.md` files with YAML frontmatter

3. **No deployment path**: No function in the deployment pipeline directly reads from `templates/archive/`

4. **Registry vs Deployment separation**: The `UnifiedAgentRegistry` is used for **agent lookup** (finding prompts, listing agents), NOT for **deployment** (writing to `.claude/agents/`)

---

## 6. Functions/Classes Involved (Complete List)

### CLI Entry Points
| Function | File:Line | Role |
|----------|-----------|------|
| `ConfigureCommand._load_agents_with_spinner()` | `cli/commands/configure.py:402` | Discovers agents for interactive configure |
| `AgentCommands._deploy_agents()` | `cli/commands/agents.py:606` | CLI `agents deploy` handler |
| `AutoConfigureCommand._auto_configure_agents()` | `cli/commands/auto_configure.py` | Auto-configuration handler |

### Agent Discovery
| Function | File:Line | Role |
|----------|-----------|------|
| `SimpleAgentManager.discover_agents()` | `cli/commands/agent_state_manager.py:99` | Discovers agents for configure UI |
| `SimpleAgentManager._discover_local_template_agents()` | `cli/commands/agent_state_manager.py:128` | Reads `templates/*.json` (NO archive) |
| `SimpleAgentManager._discover_git_agents()` | `cli/commands/agent_state_manager.py:211` | Reads git cache agents |
| `AgentDiscoveryService.list_available_agents()` | `services/agents/deployment/agent_discovery_service.py:102` | Lists templates/*.md + git cache |
| `AgentDiscoveryService.discover_git_cached_agents()` | `services/agents/deployment/agent_discovery_service.py:39` | Discovers from git cache |
| `UnifiedAgentRegistry.discover_agents()` | `core/unified_agent_registry.py:201` | Full registry discovery (includes archive via rglob) |
| `UnifiedAgentRegistry._discover_path()` | `core/unified_agent_registry.py:251` | **rglob("*") discovers archive/** |

### Agent Deployment
| Function | File:Line | Role |
|----------|-----------|------|
| `AgentDeploymentService.deploy_agents()` | `services/agents/deployment/agent_deployment.py:294` | Main deployment orchestrator |
| `AgentDeploymentService._get_multi_source_templates()` | `services/agents/deployment/agent_deployment.py:839` | 4-tier source resolution |
| `MultiSourceAgentDeploymentService.discover_agents_from_all_sources()` | `services/agents/deployment/multi_source_deployment_service.py:189` | Multi-tier discovery |
| `SingleTierDeploymentService.deploy_all_agents()` | `services/agents/single_tier_deployment_service.py:100` | Git-source deployment |
| `GitSourceSyncService.deploy_agents_to_project()` | `services/agents/sources/git_source_sync_service.py:992` | Cache-to-project deployment |

### Agent Loading (for prompts, not deployment)
| Function | File:Line | Role |
|----------|-----------|------|
| `AgentLoader.__init__()` | `agents/agent_loader.py:170` | Initializes agent registry for prompt loading |
| `AgentLoader.get_agent_prompt()` | `agents/agent_loader.py:255` | Loads agent instruction text |
| `_get_agent_templates_dir()` | `agents/agent_loader.py:119` | Returns `templates/` path |

### Path Resolution
| Function | File:Line | Role |
|----------|-----------|------|
| `UnifiedPathManager.get_system_agents_dir()` | `core/unified_paths.py:510` | Returns `src/claude_mpm/agents/` |
| `UnifiedPathManager.get_templates_dir()` | `core/unified_paths.py:514` | Returns `agents/templates/` |
| `ClaudeMPMPaths.agents_dir` | `config/paths.py:76` | Returns `src/claude_mpm/agents/` |

---

## 7. What the Archive Files Are

The `templates/archive/` directory contains **39 JSON files** that are the **original agent definitions** before the migration to:
1. Markdown format (`.md` with YAML frontmatter)
2. Git-hosted agent repository (`bobmatnyc/claude-mpm-agents`)

They were created by `scripts/migrate_json_to_markdown.py` with the `--archive` flag, which moved JSON files to `templates/archive/` instead of deleting them.

**Sample JSON structure** (`archive/engineer.json`):
```json
{
  "name": "Engineer Agent",
  "schema_version": "1.3.0",
  "agent_id": "engineer",
  "agent_version": "3.9.1",
  "agent_type": "engineer",
  "metadata": { "name": "...", "description": "..." },
  "capabilities": { "model": "sonnet", "tools": [...] },
  "instructions": "..."
}
```

---

## 8. Risk Assessment for Archive Removal

### Safe to Remove
- No deployment pipeline reads from `templates/archive/`
- No CLI command directly references `templates/archive/`
- No import statement references archive files
- The `*.json` glob in `SimpleAgentManager` only reads top-level `templates/`, not subdirectories

### Potential Side Effects
1. **UnifiedAgentRegistry** will stop discovering 39 JSON agent entries from `rglob("*")`
   - These entries exist in the registry but are never used for deployment
   - They may show up in agent counts/listings (minor cosmetic change)
   - The `AgentLoader.get_agent()` could theoretically load prompts from these JSON files

2. **`scripts/delegation_matrix_poc.py`** will break (but it's just a POC script)

3. **Test files** may reference archive path:
   - `tests/test_archive_manager.py`
   - `tests/services/test_archive_manager.py`
   - These test a different "archive" concept (project archive manager, not agent templates)

### Recommendation
Archive removal is **safe** with respect to the deployment pipeline. The only functional impact is on `UnifiedAgentRegistry` agent discovery, which currently includes these 39 JSON files as SYSTEM-tier agents but never deploys them.
