# Main Branch Baseline Audit

**Date**: 2026-03-06
**Branch**: `main` (all data read via `git show main:` / `git ls-tree main`)
**Purpose**: Document exact state of all agent naming/deployment code on main before fresh implementation

---

## 1. Agent Files on Main

### 1.1 Deployed Agents Directory

The `.claude/agents/` directory **does not exist on the main branch** (the directory tree is empty). Agent files are deployed at runtime to the user's `.claude/agents/` directory via the deployment system — they are not committed to the repo.

### 1.2 Archive Templates (JSON)

Located at `src/claude_mpm/agents/templates/archive/`. These are legacy JSON templates:

| Filename | Naming Convention |
|----------|------------------|
| agent-manager.json | kebab-case |
| agentic-coder-optimizer.json | kebab-case |
| api_qa.json | **snake_case** |
| clerk-ops.json | kebab-case |
| code_analyzer.json | **snake_case** |
| content-agent.json | kebab-case |
| dart_engineer.json | **snake_case** |
| data_engineer.json | **snake_case** |
| documentation.json | single-word |
| engineer.json | single-word |
| gcp_ops_agent.json | **snake_case** |
| golang_engineer.json | **snake_case** |
| imagemagick.json | single-word |
| java_engineer.json | **snake_case** |
| javascript_engineer_agent.json | **snake_case** |
| local_ops_agent.json | **snake_case** |
| memory_manager.json | **snake_case** |
| nextjs_engineer.json | **snake_case** |
| ops.json | single-word |
| php-engineer.json | kebab-case |
| product_owner.json | **snake_case** |
| project_organizer.json | **snake_case** |
| prompt-engineer.json | kebab-case |
| python_engineer.json | **snake_case** |
| qa.json | single-word |
| react_engineer.json | **snake_case** |
| refactoring_engineer.json | **snake_case** |
| research.json | single-word |
| ruby-engineer.json | kebab-case |
| rust_engineer.json | **snake_case** |
| security.json | single-word |
| svelte-engineer.json | kebab-case |
| tauri_engineer.json | **snake_case** |
| ticketing.json | single-word |
| typescript_engineer.json | **snake_case** |
| vercel_ops_agent.json | **snake_case** |
| version_control.json | **snake_case** |
| web_qa.json | **snake_case** |
| web_ui.json | **snake_case** |

**Key Observation**: Archive templates use **mixed naming** — some kebab-case, some snake_case, some single-word. This inconsistency propagates through the system.

### 1.3 Active Template Directory

`src/claude_mpm/agents/templates/` contains mostly PM workflow support files (not agent definitions):
- `__init__.py` — Template mappings (see Section 3.7)
- `circuit-breakers.md`, `pm-examples.md`, `research-gate-examples.md`, etc.
- `archive/` — The JSON templates above

---

## 2. Key Python Files on Main

### 2.1 AgentNameNormalizer (`src/claude_mpm/core/agent_name_normalizer.py`)

**EXISTS ON MAIN: YES**

#### CANONICAL_NAMES dict (64 entries)

Maps `snake_case_key` -> `Title Case Display Name`:

| Key | Display Name |
|-----|-------------|
| research | Research |
| engineer | Engineer |
| qa | QA |
| security | Security |
| documentation | Documentation |
| ops | Ops |
| version_control | Version Control |
| data_engineer | Data Engineer |
| architect | Architect |
| pm | PM |
| python_engineer | Python Engineer |
| golang_engineer | Golang Engineer |
| java_engineer | Java Engineer |
| javascript_engineer | JavaScript Engineer |
| typescript_engineer | TypeScript Engineer |
| rust_engineer | Rust Engineer |
| ruby_engineer | Ruby Engineer |
| php_engineer | PHP Engineer |
| phoenix_engineer | Phoenix Engineer |
| nestjs_engineer | NestJS Engineer |
| react_engineer | React Engineer |
| nextjs_engineer | NextJS Engineer |
| svelte_engineer | Svelte Engineer |
| dart_engineer | Dart Engineer |
| tauri_engineer | Tauri Engineer |
| prompt_engineer | Prompt Engineer |
| refactoring_engineer | Refactoring Engineer |
| api_qa | API QA |
| web_qa | Web QA |
| real_user | Real User |
| clerk_ops | Clerk Ops |
| digitalocean_ops | DigitalOcean Ops |
| gcp_ops | GCP Ops |
| local_ops | Local Ops |
| vercel_ops | Vercel Ops |
| project_organizer | Project Organizer |
| agentic_coder_optimizer | Agentic Coder Optimizer |
| tmux | Tmux |
| code_analyzer | Code Analyzer |
| content | Content |
| memory_manager | Memory Manager |
| product_owner | Product Owner |
| web_ui | Web UI |
| imagemagick | ImageMagick |
| ticketing | Ticketing |
| mpm_agent_manager | MPM Agent Manager |
| mpm_skills_manager | MPM Skills Manager |
| tavily_research | Research *(alias)* |

#### ALIASES dict (90+ entries)

Maps variations to canonical keys. Examples:
- `researcher` -> `research`
- `dev`, `developer`, `engineering` -> `engineer`
- `python` -> `python_engineer`
- `sec` -> `security`
- `docs`, `doc` -> `documentation`
- `devops`, `operations` -> `ops`
- `git`, `vcs` -> `version_control`

#### normalize() method logic

1. Strip whitespace, lowercase
2. Replace hyphens/spaces with underscores
3. Strip `_agent` or `_agent_agent` suffix
4. Look up in ALIASES (exact match) -> return CANONICAL_NAMES
5. Look up directly in CANONICAL_NAMES
6. Partial matching: sorted by length (longest first), only single-word aliases can match parts
7. Default: return "Engineer" with warning

### 2.2 Agent Name Registry (`src/claude_mpm/core/agent_name_registry.py`)

**DOES NOT EXIST ON MAIN** — This was created on the `agenttype-enums` branch.

### 2.3 AgentType Enums (THREE separate definitions)

#### Location 1: `src/claude_mpm/models/agent_definition.py`

```python
class AgentType(str, Enum):
    CORE = "core"
    PROJECT = "project"
    CUSTOM = "custom"
    SYSTEM = "system"
    SPECIALIZED = "specialized"
```

This is about **deployment tier**, not agent identity.

#### Location 2: `src/claude_mpm/core/unified_agent_registry.py`

```python
class AgentType(Enum):
    CORE = "core"
    SPECIALIZED = "specialized"
    USER_DEFINED = "user_defined"
    PROJECT = "project"
    MEMORY_AWARE = "memory_aware"
```

Similar but **different values** — adds `USER_DEFINED` and `MEMORY_AWARE`, removes `CUSTOM` and `SYSTEM`. Also not `str, Enum`.

#### Location 3: `src/claude_mpm/agents/agents_metadata.py`

Uses string `"type": "core_agent"` in dicts (not an enum). All agents use `type: "core_agent"`.

**Key Problem**: Three different type systems that don't align with each other.

### 2.4 CORE_AGENTS Lists (4 locations on main, 1 doesn't exist)

#### Location 1: `src/claude_mpm/services/agents/toolchain_detector.py` (line 162)

```python
CORE_AGENTS = [
    "engineer",
    "qa-agent",
    "memory-manager-agent",
    "local-ops-agent",
    "research-agent",
    "documentation-agent",
    "security-agent",
]
```

Uses **mixed naming**: `engineer` (no suffix) but `qa-agent` (with suffix). 7 agents.

#### Location 2: `src/claude_mpm/services/agents/agent_recommendation_service.py` (line ~43)

```python
CORE_AGENTS = {
    "engineer",
    "research",
    "qa",
    "documentation",
    "ops",
    "ticketing",
}
```

Uses **bare names** (no suffix). Only 6 agents. Includes `ticketing` (not in Location 1). Missing `security`, `memory-manager`, `local-ops`.

#### Location 3: `src/claude_mpm/services/agents/agent_presets.py`

**No CORE_AGENTS found** in this file on main.

#### Location 4: `src/claude_mpm/agents/framework_agent_loader.py`

**No CORE_AGENTS found** in this file on main.

#### Location 5: `src/claude_mpm/services/agents/deployment/agent_deployment_handler.py`

**File does not exist on main.**

#### TOOLCHAIN_TO_AGENTS mapping (toolchain_detector.py, line 137)

Also uses inconsistent naming:
```python
"python": ["python-engineer"],           # kebab, no suffix
"javascript": ["javascript-engineer-agent"],  # kebab, WITH suffix
"typescript": ["typescript-engineer"],     # kebab, no suffix
"docker": ["ops", "local-ops-agent"],     # bare AND suffixed
"vercel": ["vercel-ops-agent"],           # suffixed
```

**Key Problem**: CORE_AGENTS lists are different across locations — different agents included, different naming conventions (suffixed vs bare, kebab vs snake).

### 2.5 Deployment Code

#### `src/claude_mpm/services/agents/deployment_utils.py`

**normalize_deployment_filename()** (line ~40):
1. Get stem, lowercase
2. Replace underscores with dashes
3. Strip `-agent` suffix
4. Always `.md` extension

Example: `"python_engineer_agent.md"` -> `"python-engineer.md"`

**ensure_agent_id_in_frontmatter()** (line 83):
1. Derives `agent_id` from filename: stem, lowercase, underscores to dashes, strip `-agent`
2. If no frontmatter, adds `---\nagent_id: {derived}\n---`
3. If frontmatter exists but no `agent_id`, injects it

**deploy_agent_file()** (line 299):
- Single source of truth for deployment
- Normalizes filename via `normalize_deployment_filename()`
- Cleans up legacy underscore variants
- Ensures frontmatter has `agent_id`
- Content-based comparison for skip detection

#### `src/claude_mpm/services/agents/deployment/single_agent_deployer.py`

Legacy deployer. Uses `template_file.stem` as `agent_name`, writes to `agents_dir / f"{agent_name}.md"`. Does NOT call `normalize_deployment_filename()`.

#### `src/claude_mpm/cli/commands/configure.py` — `_deploy_single_agent()` (line 3081)

- Uses `agent.name` or `full_agent_id` for naming
- For remote agents: uses leaf of hierarchical ID (e.g., `engineer/backend/python-engineer` -> `python-engineer.md`)
- Uses `shutil.copy2` (raw copy, no normalization)
- Does NOT call `normalize_deployment_filename()` or `deploy_agent_file()`

**Key Problem**: Three deployment paths with different normalization behavior.

#### `src/claude_mpm/utils/agent_filters.py` — `get_deployed_agent_ids()` (line 87)

Detection logic:
1. Check virtual deployment state (`.mpm_deployment_state`)
2. Fallback: scan physical `.md` files in `.claude/agents/`
3. Returns leaf names (e.g., `"python-engineer"`, `"qa"`)

### 2.6 PM Prompts

#### PM_INSTRUCTIONS.md

References agents by various names:
- `local-ops` / `local-ops/QA` — kebab-case
- `Research`, `Engineer`, `QA`, `Ops` — Title Case
- `web-qa-agent`, `api-qa-agent` — kebab with suffix
- `ticketing-agent` — kebab with suffix
- `Security Agent` — Title Case with "Agent"

Agent delegation matrix (line ~399+):
```
| localhost, PM2... | local-ops | Local development |
| version, release... | local-ops | Version management |
| Unknown/ambiguous | local-ops | Default fallback |
```

#### WORKFLOW.md

References agents as:
- `Research` — Title Case (Phase 1)
- `Code Analyzer` — Title Case (Phase 2)
- `api-qa`, `web-qa`, `qa` — kebab lowercase (Phase 4 routing)
- `Documentation` — Title Case (Phase 5)
- `Security Agent` — Title Case (security review)
- `local-ops` — kebab lowercase (release delegation)
- `ticketing-agent` — kebab with suffix

#### CLAUDE_MPM_OUTPUT_STYLE.md

**EXISTS ON MAIN** — contains frontmatter:
```yaml
---
name: claude_mpm
description: Multi-Agent Project Manager orchestration mode with mandatory delegation
---
```

### 2.7 system_context.py — Agent Name Guidance

`src/claude_mpm/core/system_context.py` (lines 19-36):

```python
"""You have access to native subagents via the Task tool with subagent_type parameter:
- engineer: For coding, implementation, and technical tasks
- qa: For testing, validation, and quality assurance
- documentation: For docs, guides, and explanations
- research: For investigation and analysis
- security: For security-related tasks
- ops: For deployment and infrastructure
- version-control: For git and version management
- data-engineer: For data processing and APIs

Use these agents by calling: Task(description="task description", subagent_type="agent_name")

IMPORTANT: The Task tool accepts both naming formats:
- Capitalized format: "Research", "Engineer", "QA", "Version Control", "Data Engineer"
- Lowercase format: "research", "engineer", "qa", "version-control", "data-engineer"

Both formats work correctly. When you see capitalized names (matching TodoWrite prefixes),
automatically normalize them to lowercase-hyphenated format for the Task tool."""
```

**Key Problem**: Lists only 8 agents (bare names), but the system has 48+ agents. Tells PM to use lowercase-hyphenated format, which conflicts with the `name:` field format in deployed agents.

### 2.8 templates/__init__.py — Deprecated Template Mappings

`src/claude_mpm/agents/templates/__init__.py`:

```python
AGENT_TEMPLATES = {
    "documentation": "documentation_agent.md",
    "engineer": "engineer_agent.md",
    "qa": "qa_agent.md",
    "api_qa": "api_qa_agent.md",
    "web_qa": "web_qa_agent.md",
    "version_control": "version_control_agent.md",
    "research": "research_agent.md",
    "ops": "ops_agent.md",
    "security": "security_agent.md",
    "data_engineer": "data_engineer_agent.md",
}
```

Uses `snake_case` keys mapping to `snake_case_agent.md` filenames. Only 10 agents. These template files (`documentation_agent.md`, etc.) likely no longer exist — they were replaced by the archive JSON format.

---

## 3. CORE_AGENTS Comparison Table (Main Branch)

| Agent | toolchain_detector | recommendation_service | system_context | templates/__init__ |
|-------|-------------------|----------------------|----------------|-------------------|
| engineer | `"engineer"` | `"engineer"` | `engineer` | `"engineer"` |
| research | `"research-agent"` | `"research"` | `research` | `"research"` |
| qa | `"qa-agent"` | `"qa"` | `qa` | `"qa"` |
| documentation | `"documentation-agent"` | `"documentation"` | `documentation` | `"documentation"` |
| security | `"security-agent"` | -- | `security` | `"security"` |
| ops | -- | `"ops"` | `ops` | `"ops"` |
| local-ops | `"local-ops-agent"` | -- | -- | -- |
| memory-manager | `"memory-manager-agent"` | -- | -- | -- |
| ticketing | -- | `"ticketing"` | -- | -- |
| version-control | -- | -- | `version-control` | `"version_control"` |
| data-engineer | -- | -- | `data-engineer` | `"data_engineer"` |
| api_qa | -- | -- | -- | `"api_qa"` |
| web_qa | -- | -- | -- | `"web_qa"` |

**Observations**:
- `toolchain_detector` uses `-agent` suffix for most but not `engineer`
- `recommendation_service` uses bare names, different set of 6 agents
- `system_context` uses kebab-case bare names, 8 agents
- `templates/__init__` uses snake_case, 10 agents
- No two locations agree on the complete list or naming format

---

## 4. Tests on Main

### 4.1 Agent-Related Test Inventory

There are **150+ test files** related to agents. Key categories:

#### Core Name/Type Tests:
- `tests/core/test_agent_name_normalizer.py` — Tests suffix stripping, extended aliases, name formats
- `tests/test_agent_name_consistency.py` — Agent name consistency checks
- `tests/test_agent_name_formats.py` — Format validation
- `tests/test_agent_name_normalization.py` — Normalization edge cases
- `tests/test_unified_agent_registry.py` — Registry tests

#### Deployment Tests:
- `tests/services/agents/test_deployment_utils.py` — deployment_utils tests
- `tests/test_agent_deployment.py` — Basic deployment
- `tests/test_agent_deployment_baseline.py` — Baseline deployment
- `tests/test_agent_deployment_comprehensive.py` — Comprehensive deployment
- `tests/test_agent_deployment_integration.py` — Integration tests
- `tests/test_agent_deployment_paths.py` — Path handling
- `tests/services/agents/deployment/` — 12 deployment sub-tests

#### CLI Agent Tests:
- `tests/cli/commands/test_agents_command.py` — CLI commands
- `tests/cli/commands/test_agents_comprehensive.py` — Comprehensive CLI
- `tests/cli/commands/test_agents_deploy_preset.py` — Preset deployment
- `tests/cli/test_agent_startup_deployment.py` — Startup deployment

#### Key Test Assertions (from test_agent_name_normalizer.py):

```python
# Suffix stripping tests
("research-agent", "Research")
("qa-agent", "QA")
("python-engineer-agent", "Python Engineer")

# Extended alias tests
("research", "Research")
("python_engineer", "Python Engineer")
("python-engineer", "Python Engineer")

# These establish the contract that normalize() returns Title Case
```

---

## 5. New Files on Branch (Not on Main)

Files that were **ADDED** on `agenttype-enums` branch and don't exist on main:

| File | Purpose |
|------|---------|
| `src/claude_mpm/core/agent_name_registry.py` | Authoritative agent name registry (v8 Phase 2) |
| `src/claude_mpm/utils/frontmatter_utils.py` | Frontmatter parsing utilities |
| `tests/integration/agents/test_agent_field_consistency.py` | Field consistency validation |
| `tests/unit/utils/__init__.py` | Test package init |
| `tests/unit/utils/test_frontmatter_utils.py` | Frontmatter utils tests |

These would need to be **recreated from scratch** on a fresh branch.

---

## 6. Summary of Inconsistencies on Main

### 6.1 Naming Convention Chaos

| Context | Format | Example |
|---------|--------|---------|
| CANONICAL_NAMES keys | snake_case | `python_engineer` |
| CANONICAL_NAMES values | Title Case | `Python Engineer` |
| CORE_AGENTS (toolchain) | kebab-case + suffix | `research-agent` |
| CORE_AGENTS (recommend) | bare kebab | `research` |
| system_context listing | bare kebab | `research` |
| templates/__init__ | snake_case | `research` |
| PM_INSTRUCTIONS | mixed | `local-ops`, `Research`, `web-qa-agent` |
| WORKFLOW.md | mixed | `Research`, `api-qa`, `ticketing-agent` |
| Archive filenames | mixed | `api_qa.json`, `php-engineer.json` |
| TOOLCHAIN_TO_AGENTS | mixed | `python-engineer`, `javascript-engineer-agent` |
| normalize_deployment_filename | kebab, strip suffix | `python-engineer.md` |

### 6.2 CORE_AGENTS Set Disagreement

No two files agree on what constitutes "core agents":
- **toolchain_detector**: 7 agents (includes memory-manager, local-ops, security; excludes ops, ticketing)
- **recommendation_service**: 6 agents (includes ops, ticketing; excludes security, memory-manager, local-ops)
- **system_context**: 8 agents (includes version-control, data-engineer; excludes ticketing, memory-manager, local-ops)
- **templates/__init__**: 10 agents (includes api_qa, web_qa, data_engineer; excludes ticketing, memory-manager, local-ops)

### 6.3 Triple AgentType Enum

Three separate `AgentType` definitions with overlapping but different values:
1. `agent_definition.py`: `CORE, PROJECT, CUSTOM, SYSTEM, SPECIALIZED`
2. `unified_agent_registry.py`: `CORE, SPECIALIZED, USER_DEFINED, PROJECT, MEMORY_AWARE`
3. `agents_metadata.py`: String `"core_agent"` (not enum)

### 6.4 Triple Deployment Path

Three deployment code paths with different normalization:
1. `deploy_agent_file()` — normalizes filename, strips `-agent`, ensures frontmatter
2. `SingleAgentDeployer.deploy_single_agent()` — uses template stem directly, no normalization
3. `configure.py._deploy_single_agent()` — uses `shutil.copy2`, no normalization

### 6.5 Agent Suffix Inconsistency

The `-agent` suffix is stripped by `normalize_deployment_filename()` but is used in:
- `CORE_AGENTS` in toolchain_detector: `"qa-agent"`, `"research-agent"`, etc.
- `TOOLCHAIN_TO_AGENTS`: `"javascript-engineer-agent"`, `"local-ops-agent"`
- PM prompts: `"web-qa-agent"`, `"ticketing-agent"`

This means the deployment system strips a suffix that other parts of the system rely on.

---

## 7. Critical Questions for Fresh Implementation

1. **What should `name:` in frontmatter be?** Title Case (matching CANONICAL_NAMES values) or kebab-case?
2. **Should `-agent` suffix exist?** deployment_utils strips it, but toolchain_detector uses it
3. **What is the canonical CORE_AGENTS set?** 6, 7, 8, or 10 agents?
4. **Should there be one or three AgentType enums?** And what values?
5. **Should all deployment go through `deploy_agent_file()`?** Currently 3 separate paths
6. **What format should `agent_id:` use?** kebab-case without suffix (current deploy behavior)
7. **How should PM prompts reference agents?** Currently uses at least 4 different formats
