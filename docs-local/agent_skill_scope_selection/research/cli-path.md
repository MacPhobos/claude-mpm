# CLI Configuration Path Research: Agent & Skill Deployment

**Date**: 2026-02-28
**Researcher**: cli-researcher
**Task**: Research CLI path for deploying/undeploying agents and skills in claude-mpm

---

## Architecture Overview

The CLI path for agent/skill configuration follows a classic command-based architecture using Python's `argparse` module with a modular parser structure.

```
User invokes: claude-mpm configure [options]
       │
       ▼
pyproject.toml: claude-mpm = "claude_mpm.cli:main"
       │
       ▼
cli/__init__.py: main()
  ├── create_parser() → SuggestingArgumentParser
  ├── preprocess_args()
  └── execute_command("configure", args)
       │
       ▼
cli/executor.py: execute_command()
  └── CLICommands.CONFIGURE → manage_configure(args)
       │
       ▼
cli/commands/configure.py: manage_configure(args)
  └── ConfigureCommand().execute(args)
```

---

## Entry Points

### Binary Entry Point
```
pyproject.toml [project.scripts]:
  claude-mpm = "claude_mpm.cli:main"
```

### CLI Main Function
**File**: `src/claude_mpm/cli/__init__.py:47` — `main(argv)`

1. `setup_early_environment(argv)` — sets env vars, captures project dir
2. `create_parser(version=__version__)` — builds argparse hierarchy
3. `preprocess_args(argv)` — normalizes arguments
4. `parser.parse_args(processed_argv)` — parses args
5. `setup_configure_command_environment(args)` — prepares env for configure
6. `execute_command(command, args)` — routes to implementation

### Command Routing
**File**: `src/claude_mpm/cli/executor.py:383`

```python
command_map = {
    CLICommands.CONFIGURE.value: manage_configure,  # "configure"
    CLICommands.SKILLS.value: manage_skills,        # "skills"
    CLICommands.CONFIG.value: manage_config,        # "config"
    ...
}
```

---

## Parser Structure

### Configure Parser
**File**: `src/claude_mpm/cli/parsers/configure_parser.py`

The `add_configure_subparser()` function registers the `configure` subcommand with these argument groups:

#### Configuration Scope (KEY for this research)
```python
scope_group.add_argument(
    "--scope",
    choices=["project", "user"],
    default="project",
    help="Configuration scope to manage (default: project)",
)
# --project-dir from base_parser (common args)
```

#### Direct Navigation (Skip Main Menu)
```python
--agents     # Jump directly to agent management
--templates  # Jump directly to template editing
--behaviors  # Jump directly to behavior file management
--startup    # Configure startup services and agents
--version-info
```

#### Non-Interactive Mode
```python
--list-agents              # List all available agents and exit
--enable-agent AGENT_NAME  # Enable a specific agent and exit
--disable-agent AGENT_NAME # Disable a specific agent and exit
--export-config FILE       # Export current configuration to file
--import-config FILE       # Import configuration from file
```

#### Hook Management
```python
--install-hooks    # Install Claude MPM hooks
--verify-hooks     # Verify hooks properly installed
--uninstall-hooks  # Uninstall Claude MPM hooks
--force            # Force reinstallation of hooks
```

---

## ConfigureCommand: Core Implementation

**File**: `src/claude_mpm/cli/commands/configure.py`
**Class**: `ConfigureCommand(BaseCommand)`

### Initialization
```python
class ConfigureCommand(BaseCommand):
    def __init__(self):
        super().__init__("configure")
        self.current_scope = "project"      # Default scope
        self.project_dir = Path.cwd()        # Default project dir
        self.agent_manager = None            # SimpleAgentManager (lazy-init)
        self.behavior_manager = None         # BehaviorManager (lazy-init)
        # Plus lazy-init properties for agent_display, persistence,
        # navigation, template_editor, startup_manager, etc.
```

### Scope Resolution in `run()`
```python
def run(self, args) -> CommandResult:
    # 1. Read scope from CLI args (project or user)
    self.current_scope = getattr(args, "scope", "project")
    if getattr(args, "project_dir", None):
        self.project_dir = Path(args.project_dir)

    # 2. Resolve config_dir based on scope
    if self.current_scope == "project":
        config_dir = self.project_dir / ".claude-mpm"
    else:
        config_dir = Path.home() / ".claude-mpm"

    # 3. Initialize managers with scope-appropriate config directory
    self.agent_manager = SimpleAgentManager(config_dir)
    self.behavior_manager = BehaviorManager(config_dir, self.current_scope, self.console)
```

**Scope affects `config_dir` only** — where agent enable/disable states (agent_states.json) are persisted.

---

## Code Flow: Agent Deployment

### Interactive TUI Flow
```
_run_interactive_tui(args)
  └── while True: show_main_menu()
        ├── "1" → _manage_agents()
        │     └── _deploy_agents_unified(agents)  [primary path]
        │           ├── get_deployed_agent_ids()   [check current state]
        │           ├── build checkbox UI
        │           ├── process user selection
        │           └── apply changes:
        │                 ├── to_deploy → _deploy_single_agent(agent)
        │                 └── to_remove → path.unlink() + state update
        └── "6" → _switch_scope()
```

### Agent Discovery
**File**: `src/claude_mpm/cli/commands/agent_state_manager.py`
**Class**: `SimpleAgentManager`

```python
def discover_agents(include_remote=True) -> List[AgentConfig]:
    local_agents = _discover_local_template_agents()
    # Scans: src/claude_mpm/agents/templates/*.json

    if include_remote:
        git_agents = _discover_git_agents()
        # Reads AgentSourceConfiguration → GitSourceManager
        # Cache in: ~/.claude-mpm/cache/agents/{repo_identifier}/
```

### Deployed Agent Detection
**File**: `src/claude_mpm/utils/agent_filters.py:87` — `get_deployed_agent_ids()`

Detection checks in order:
1. **Virtual deployment state** (primary): `{project_dir}/.claude/agents/.mpm_deployment_state`
   → JSON file with `{"last_check_results": {"agents": {"agent-name": {...}}}}`
2. **Physical `.md` files** (fallback): `{project_dir}/.claude/agents/*.md`

Returns set of leaf names (e.g., `{"python-engineer", "qa", "engineer"}`).

### Agent Deployment: `_deploy_single_agent()`
**File**: `src/claude_mpm/cli/commands/configure.py:3047`

```python
def _deploy_single_agent(agent, show_feedback=True) -> bool:
    source_dict = getattr(agent, "source_dict", None)
    full_agent_id = getattr(agent, "full_agent_id", agent.name)

    if source_dict:  # Remote (Git-sourced) agent
        source_file = Path(source_dict["source_file"])
        target_name = full_agent_id.split("/")[-1] + ".md"

        # ALWAYS deploys to project-level, regardless of scope!
        target_dir = self.project_dir / ".claude" / "agents"
        target_dir.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source_file, target_dir / target_name)
        return True
    else:
        # Local template: Not implemented (returns False)
        return False
```

### Agent Removal (in `_deploy_agents_unified()`)
```python
# Paths checked for removal
paths_to_check = [
    Path.cwd() / ".claude-mpm" / "agents" / f"{leaf_name}.md",  # legacy
    Path.cwd() / ".claude" / "agents" / f"{leaf_name}.md",      # project
    Path.home() / ".claude" / "agents" / f"{leaf_name}.md",     # user
]

# Also removes from virtual deployment state files:
deployment_state_paths = [
    Path.cwd() / ".claude" / "agents" / ".mpm_deployment_state",
    Path.home() / ".claude" / "agents" / ".mpm_deployment_state",
]
```

---

## Code Flow: Skill Deployment

### Skills Management Entry
```
_manage_agents() → menu choice "2"
  └── _manage_skills()
        └── choice "1" → _manage_skill_installation()
              ├── _get_all_skills_from_git()
              ├── _get_deployed_skill_ids()
              ├── checkbox selection
              ├── to_install → _install_skill_from_dict(skill_dict)
              └── to_uninstall → _uninstall_skill_by_name(name)
```

### Deployed Skill Detection
**File**: `src/claude_mpm/cli/commands/configure.py:1271` — `_get_deployed_skill_ids()`

```python
skills_dir = Path.cwd() / ".claude" / "skills"
# Lists subdirectories (each skill = one directory)
deployed_ids = {d.name for d in skills_dir.iterdir() if d.is_dir()}
```

### Skill Installation: `_install_skill_from_dict()`
**File**: `src/claude_mpm/cli/commands/configure.py:1325`

```python
def _install_skill_from_dict(skill_dict: dict) -> None:
    skill_id = skill_dict.get("name", skill_dict.get("skill_id"))
    content = skill_dict.get("content", "")
    deploy_name = skill_dict.get("deployment_name", skill_id)

    # ALWAYS project-level, regardless of scope!
    target_dir = Path.cwd() / ".claude" / "skills" / deploy_name
    target_dir.mkdir(parents=True, exist_ok=True)

    skill_file = target_dir / "skill.md"
    skill_file.write_text(content, encoding="utf-8")
```

Also: `_install_skill(skill)` (for local SkillManager skills):
```python
target_dir = Path.cwd() / ".claude" / "skills" / skill.skill_id
```

### Skill Uninstallation: `_uninstall_skill_by_name()`
```python
target_dir = Path.cwd() / ".claude" / "skills" / skill_name
if target_dir.exists():
    shutil.rmtree(target_dir)
```

---

## Scope Handling Details

### The Scope Toggle
**File**: `src/claude_mpm/cli/commands/configure_navigation.py:152` — `switch_scope()`

```python
def switch_scope(self) -> None:
    self.current_scope = "user" if self.current_scope == "project" else "project"
```

Simple binary toggle. The new scope is synced back to `ConfigureCommand.current_scope` after the call.

### What Scope Actually Controls

| Scope | Config Dir (agent_states.json) | Agent Deploy Target | Skill Deploy Target |
|-------|-------------------------------|---------------------|---------------------|
| `project` | `.claude-mpm/agent_states.json` | `.claude/agents/` (cwd) | `.claude/skills/` (cwd) |
| `user` | `~/.claude-mpm/agent_states.json` | `.claude/agents/` (cwd) | `.claude/skills/` (cwd) |

**Critical finding**: The scope toggle currently only affects **where agent enable/disable states (metadata) are stored**. The actual **file deployment operations** always use `Path.cwd()` or `self.project_dir` for both agents and skills — they do **not** deploy to `~/.claude/agents/` or `~/.claude/skills/` (user scope) from the interactive UI.

### Removal Paths Check User Scope (But Not Deployment)
The removal code in `_deploy_agents_unified()` and `_deploy_agents_individual()` **does** check `Path.home() / ".claude" / "agents"` as a fallback during removal, but this is backward compatibility handling rather than intentional user-scoped deployment.

---

## Key Files and Functions Summary

### Primary Files

| File | Purpose |
|------|---------|
| `cli/commands/configure.py` | Main `ConfigureCommand` class + `manage_configure()` |
| `cli/commands/agent_state_manager.py` | `SimpleAgentManager` — agent discovery & state |
| `cli/commands/configure_navigation.py` | `ConfigNavigation` — scope toggle, header, menu |
| `cli/commands/configure_persistence.py` | `ConfigPersistence` — import/export config |
| `cli/commands/configure_models.py` | `AgentConfig` data model |
| `cli/parsers/configure_parser.py` | argparse definitions for `configure` |
| `utils/agent_filters.py` | `get_deployed_agent_ids()`, `filter_base_agents()` |
| `cli/executor.py` | Command routing table |

### Key Functions

| Function | File:Line | Purpose |
|----------|-----------|---------|
| `manage_configure(args)` | configure.py:3241 | Entry point, creates ConfigureCommand |
| `ConfigureCommand.run(args)` | configure.py:179 | Scope init, routes to interactive/non-interactive |
| `_deploy_agents_unified(agents)` | configure.py:1867 | Main UI for agent deploy/undeploy |
| `_deploy_single_agent(agent)` | configure.py:3047 | Copies agent .md to target dir |
| `_manage_skill_installation()` | configure.py:~900 | Main UI for skill install/uninstall |
| `_install_skill_from_dict(skill_dict)` | configure.py:1325 | Copies skill content to .claude/skills/ |
| `_uninstall_skill_by_name(name)` | configure.py:1351 | Removes skill directory |
| `get_deployed_agent_ids()` | agent_filters.py:87 | Detects currently deployed agents |
| `SimpleAgentManager.discover_agents()` | agent_state_manager.py:99 | Finds local + remote agents |
| `ConfigNavigation.switch_scope()` | configure_navigation.py:152 | Toggles project↔user scope |

---

## Existing Abstractions

### `SimpleAgentManager`
Manages agent state (enabled/disabled) and discovery. Scope-aware for config directory but not deployment directory.

### `ConfigNavigation`
Holds `current_scope` and provides `switch_scope()`. Scope is a simple string attribute — no polymorphism or strategy pattern.

### `AgentConfig` (dataclass)
```python
# configure_models.py
@dataclass
class AgentConfig:
    name: str
    description: str
    dependencies: List[str]
    source_type: str = "local"     # "local" | "remote"
    source_dict: Optional[dict] = None
    agent_id: str = ""
    is_deployed: bool = False
    ...
```

### `BehaviorManager`
Receives `current_scope` but uses it for display purposes.

---

## Complete Code Flow Diagram

### Deploy Agent (CLI Path)
```
claude-mpm configure [--scope project|user]
  │
  ▼
cli/__init__.py:main()
  │  argparse → args.scope, args.command="configure"
  ▼
cli/executor.py:execute_command("configure", args)
  │
  ▼
cli/commands/configure.py:manage_configure(args)
  │
  ▼
ConfigureCommand.run(args)
  │  scope → config_dir (.claude-mpm/ or ~/.claude-mpm/)
  │  SimpleAgentManager(config_dir)
  ▼
_run_interactive_tui(args) [or non-interactive path]
  │
  ▼
show_main_menu() → "1" Agent Management
  │
  ▼
_manage_agents()
  │  SimpleAgentManager.discover_agents(include_remote=True)
  │  get_deployed_agent_ids()  ← reads .claude/agents/.mpm_deployment_state
  ▼
_deploy_agents_unified(agents)
  │  checkbox UI: select/deselect agents
  │  to_deploy = final_selection - deployed_full_paths
  │  to_remove = deployed_full_paths - final_selection
  ▼
for agent_id in to_deploy:
  _deploy_single_agent(agent)
  │  shutil.copy2(source_file,
  │               project_dir/.claude/agents/{leaf_name}.md)
  └── TARGET: {project_dir}/.claude/agents/

for agent_id in to_remove:
  path.unlink() for paths in:
  │  [cwd/.claude-mpm/agents/, cwd/.claude/agents/,
  │   home/.claude/agents/]
  │  + updates .mpm_deployment_state JSON
```

### Deploy Skill (CLI Path)
```
claude-mpm configure
  │ (same routing as above)
  ▼
_manage_skills() → choice "1" Install/Uninstall
  │
  ▼
_manage_skill_installation()
  │  _get_all_skills_from_git()  ← GitSkillSourceManager
  │  _get_deployed_skill_ids()   ← lists cwd/.claude/skills/
  ▼
checkbox UI → selected skills
  │
to_install → _install_skill_from_dict(skill_dict)
  │  write content to:
  │  cwd/.claude/skills/{deploy_name}/skill.md
  └── TARGET: {cwd}/.claude/skills/

to_uninstall → _uninstall_skill_by_name(name)
  │  shutil.rmtree(cwd/.claude/skills/{name})
```

---

## Scope Handling: Detailed Analysis

### Current State: Partial Scope Support

The CLI exposes scope as a concept (via `--scope` flag and interactive toggle), but the actual deployment operations are **not fully scope-aware**:

1. **Config state** (agent_states.json) IS scope-aware:
   - Project: `.claude-mpm/agent_states.json`
   - User: `~/.claude-mpm/agent_states.json`

2. **Agent files** are NOT scope-aware in deployment:
   - Always: `{project_dir}/.claude/agents/{name}.md`
   - `self.project_dir` is set from `args.project_dir` or `Path.cwd()`, never `Path.home()`

3. **Skill files** are NOT scope-aware:
   - Always: `Path.cwd() / ".claude" / "skills" / name`
   - Hardcoded to use `Path.cwd()`, not scope-sensitive

4. **Removal** partially checks user paths (`~/.claude/agents/`) as legacy fallback.

### Why the Gap Exists
The `scope` concept was likely added with the intent of supporting both project-level (`.claude/`) and user-level (`~/.claude/`) deployment. However, the implementation only wired scope to the metadata config directory (`.claude-mpm/`), not to the actual file deployment operations.

---

## Non-Interactive CLI Path

For scripting/automation, the configure command supports these non-interactive flags:

```bash
# List agents
claude-mpm configure --list-agents [--scope project|user]

# Enable/disable agents (updates agent_states.json only, does NOT deploy files)
claude-mpm configure --enable-agent python-engineer [--scope user]
claude-mpm configure --disable-agent qa [--scope project]

# Export/import configuration
claude-mpm configure --export-config ./config.json
claude-mpm configure --import-config ./config.json
```

**Note**: `--enable-agent` / `--disable-agent` update the `agent_states.json` file (metadata) but do NOT actually deploy/remove agent files from `.claude/agents/`. File deployment only happens through the interactive UI's `_deploy_single_agent()` call.

---

## Configuration State Files

### Agent States (metadata, scope-aware)
```
{config_dir}/agent_states.json
  {
    "python-engineer": {"enabled": true},
    "qa": {"enabled": false}
  }
```

### Virtual Deployment State (scope-unaware, always project-level)
```
{project_dir}/.claude/agents/.mpm_deployment_state
  {
    "last_check_results": {
      "agents": {
        "python-engineer": {...},
        "engineer": {...}
      }
    }
  }
```

### Skill Configuration
No virtual state file for skills — only physical directory presence is checked.

---

## Implications for Unified Abstraction

### Key Observations

1. **Scope is partially implemented**: The UI exposes scope switching but only metadata (agent_states.json) respects it. Actual file operations don't.

2. **Multiple "deployment locations"**: Code checks 3+ paths during removal, indicating historical drift between locations.

3. **No unified "scope resolver"**: Scope-to-path resolution is duplicated across multiple methods (`_deploy_single_agent`, `_remove_agents`, `_deploy_agents_unified`).

4. **Skills and agents use different detection mechanisms**:
   - Agents: virtual state file + physical .md files
   - Skills: only physical directory listing

5. **No abstraction between CLI and API paths**: The `ConfigureCommand` directly manipulates file system — no service layer separating business logic from I/O.

### Proposed Abstraction Points

For a unified scope abstraction, the key interface would need to:

```python
class ScopeAwareDeploymentPaths:
    def get_agents_dir(self, scope: str, project_dir: Path) -> Path:
        # project → project_dir/.claude/agents/
        # user    → Path.home()/.claude/agents/

    def get_skills_dir(self, scope: str, project_dir: Path) -> Path:
        # project → project_dir/.claude/skills/
        # user    → Path.home()/.claude/skills/

    def get_config_dir(self, scope: str, project_dir: Path) -> Path:
        # project → project_dir/.claude-mpm/
        # user    → Path.home()/.claude-mpm/
```

Currently, the CLI path has `get_config_dir` working correctly (via `ConfigureCommand.run()`), but `get_agents_dir` and `get_skills_dir` are hardcoded to project-level.

---

## Summary

The CLI configuration path is a mature, feature-rich interactive TUI built on argparse + Rich + questionary. The scope concept exists in the UI but is only partially wired to the backend:

- **Fully scope-aware**: Config metadata (agent_states.json location)
- **Not scope-aware**: Agent file deployment (`.claude/agents/`)
- **Not scope-aware**: Skill file deployment (`.claude/skills/`)

A unified abstraction layer would need to introduce a `ScopeResolver` or `DeploymentPathProvider` that maps `(scope, project_dir)` → `target_path` consistently across both CLI and API paths.
