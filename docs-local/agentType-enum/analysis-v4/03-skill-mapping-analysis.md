# Skill Mapping & Deployment Metadata Analysis

**Task**: Map skill-to-agent bindings, deployment metadata, and archive removal impact
**Date**: 2026-03-03
**Scope**: archive JSON templates vs git-cached .md files, skill routing, memory_routing

---

## 1. Executive Summary

The archive JSON templates (`src/claude_mpm/agents/templates/archive/*.json`) are **NOT read by any production code at runtime**. This is explicitly stated in the archive's own `README.md`. The git-cached `.md` files in `~/.claude-mpm/cache/agents/` contain **equivalent or near-equivalent metadata** in their YAML frontmatter, including `memory_routing`, `skills`, `knowledge`, `interactions`, `dependencies`, and `capabilities`.

Removing the archive directory has **LOW risk** to skill routing and memory routing, with two notable metadata gaps that need attention: the `routing` field (present in only 5 archive JSONs) and the `testing` field (performance benchmarks and test cases).

---

## 2. Complete Metadata Field Inventory (Archive JSON)

Every archive JSON file was analyzed. The following table documents every field, its presence, and whether the cached .md equivalent exists.

| Field | Archive JSON | Cached .md (YAML frontmatter) | Status |
|-------|-------------|-------------------------------|--------|
| `name` | All 39 files | All files (`name:`) | **Equivalent** |
| `description` | All 39 files | All files (`description:`) | **Equivalent** |
| `schema_version` | All 39 files | All files (`schema_version:`) | **Equivalent** |
| `agent_id` | All 39 files | All files (`agent_id:`) | **Equivalent** |
| `agent_version` | All 39 files | Mapped to `version:` | **Equivalent** (different key name) |
| `agent_type` | All 39 files | All files (`agent_type:`) | **Equivalent** |
| `template_version` | All 39 files | All files (`template_version:`) | **Equivalent** |
| `template_changelog` | All 39 files | All files (`template_changelog:`) | **Equivalent** |
| `skills` | ~30 files (as array) | All files (`skills:` as array) | **Equivalent** (often richer in .md) |
| `metadata.name` | All 39 files | Redundant with top-level `name` | N/A |
| `metadata.description` | All 39 files | Redundant with top-level `description` | N/A |
| `metadata.category` | All 39 files | `category:` | **Equivalent** |
| `metadata.tags` | All 39 files | `tags:` | **Equivalent** |
| `metadata.author` | All 39 files | `author:` | **Equivalent** |
| `metadata.color` | Most files | `color:` | **Equivalent** |
| `metadata.created_at` | All 39 files | **NOT present** | **MISSING from .md** |
| `metadata.updated_at` | All 39 files | **NOT present** | **MISSING from .md** |
| `capabilities.model` | All 39 files | **NOT present** (implicit) | **MISSING from .md** |
| `capabilities.tools` | All 39 files | **NOT present** (inherited from BASE_AGENT) | **MISSING from .md** |
| `capabilities.resource_tier` | All 39 files | `resource_tier:` | **Equivalent** |
| `capabilities.max_tokens` | All 39 files | `max_tokens:` | **Equivalent** |
| `capabilities.temperature` | All 39 files | `temperature:` | **Equivalent** |
| `capabilities.timeout` | All 39 files | `timeout:` | **Equivalent** |
| `capabilities.memory_limit` | All 39 files | `capabilities.memory_limit:` | **Equivalent** |
| `capabilities.cpu_limit` | All 39 files | `capabilities.cpu_limit:` | **Equivalent** |
| `capabilities.network_access` | All 39 files | `capabilities.network_access:` | **Equivalent** |
| `capabilities.file_access` | ~20 files | **NOT present** | **MISSING from .md** |
| `instructions` | All 39 files (single string) | Markdown body (after `---`) | **Equivalent** (different format) |
| `knowledge.domain_expertise` | All 39 files | `knowledge.domain_expertise:` | **Equivalent** |
| `knowledge.best_practices` | All 39 files | `knowledge.best_practices:` | **Equivalent** |
| `knowledge.constraints` | All 39 files | `knowledge.constraints:` | **Equivalent** |
| `knowledge.examples` | ~5 files (empty `[]`) | **NOT present** | Negligible (always empty) |
| `dependencies.python` | All 39 files | `dependencies.python:` | **Equivalent** |
| `dependencies.system` | All 39 files | `dependencies.system:` | **Equivalent** |
| `memory_routing.description` | ~30 files | `memory_routing.description:` | **Equivalent** |
| `memory_routing.categories` | ~30 files | `memory_routing.categories:` | **Equivalent** |
| `memory_routing.keywords` | ~30 files | `memory_routing.keywords:` | **Equivalent** |
| `routing.keywords` | 5 files only | **NOT present** (1 exception) | **MISSING from .md** |
| `routing.paths` | 5 files only | **NOT present** | **MISSING from .md** |
| `routing.extensions` | 5 files only | **NOT present** | **MISSING from .md** |
| `routing.priority` | 5 files only | **NOT present** | **MISSING from .md** |
| `routing.confidence_threshold` | 5 files only | **NOT present** | **MISSING from .md** |
| `interactions.input_format` | All 39 files | `interactions.input_format:` | **Equivalent** |
| `interactions.output_format` | All 39 files | `interactions.output_format:` | **Equivalent** |
| `interactions.handoff_agents` | All 39 files | `interactions.handoff_agents:` | **Equivalent** |
| `interactions.triggers` | All 39 files (empty) | `interactions.triggers:` | **Equivalent** |
| `testing.test_cases` | All 39 files | **NOT present** | **MISSING from .md** |
| `testing.performance_benchmarks` | All 39 files | **NOT present** | **MISSING from .md** |
| `display_name` | 1 file (local_ops) | **NOT present** | Negligible |
| `authority` | 1 file (local_ops) | **NOT present** | Negligible (very specialized) |

---

## 3. Side-by-Side Comparison: Archive JSON vs Cached .md

### 3.1 Engineer Agent

| Aspect | Archive JSON (`engineer.json`) | Cached .md (`engineer/core/engineer.md`) |
|--------|-------------------------------|------------------------------------------|
| **Skills** | 11 skills: `test-driven-development`, `systematic-debugging`, `async-testing`, `performance-profiling`, `security-scanning`, `api-documentation`, `git-workflow`, `code-review`, `refactoring-patterns`, `database-migration`, `docker-containerization` | 11 skills: `brainstorming`, `dispatching-parallel-agents`, `git-workflow`, `requesting-code-review`, `writing-plans`, `json-data-handling`, `root-cause-tracing`, `systematic-debugging`, `verification-before-completion`, `internal-comms`, `test-driven-development` |
| **Observation** | Skills are **different lists** - JSON lists template-specific skills, .md lists deployed/discovered skills. Only 2 overlap (`test-driven-development`, `systematic-debugging`) | .md version has more collaboration skills (brainstorming, dispatching, etc.) |
| **memory_routing** | Full routing with 17 keywords | Identical structure and content |
| **routing** | NOT present | NOT present |
| **testing** | Basic test case + benchmarks (`response_time: 300`, `token_usage: 8192`, `success_rate: 0.95`) | NOT present |
| **capabilities.tools** | `["Read", "Write", "Edit", "MultiEdit", "Bash", "Grep", "Glob", "LS", "WebSearch", "TodoWrite"]` | NOT present (inherited from BASE_AGENT) |
| **capabilities.file_access** | `read_paths: ["./"], write_paths: ["./"]` | NOT present |
| **instructions** | Single JSON string (1 line) | Full markdown body (~100+ lines) |

### 3.2 QA Agent

| Aspect | Archive JSON (`qa.json`) | Cached .md (`qa/qa.md`) |
|--------|-------------------------|--------------------------|
| **Skills** | 5 skills: `test-driven-development`, `systematic-debugging`, `async-testing`, `performance-profiling`, `test-quality-inspector` | 18 skills: `pr-quality-checklist`, `brainstorming`, `dispatching-parallel-agents`, `git-workflow`, ... `test-driven-development`, `test-quality-inspector`, `testing-anti-patterns`, `webapp-testing`, `bug-fix-verification`, `pre-merge-verification`, `screenshot-verification` |
| **Observation** | .md has **significantly more skills** (18 vs 5). .md includes all JSON skills plus many additional ones | Git-cached agents get enhanced skill assignments from the skill deployment pipeline |
| **memory_routing** | Full routing with 16 keywords | Identical structure and content |
| **routing** | Present: `keywords`, `paths`, `extensions`, `priority: 50`, `confidence_threshold: 0.7` | **NOT present** |
| **testing** | Basic test case + benchmarks | NOT present |
| **capabilities.tools** | `["Read", "Write", "Edit", "Bash", "Grep", "Glob", "LS", "TodoWrite"]` | NOT present |
| **capabilities.file_access** | `write_paths: ["./tests/", "./test/", "./scripts/"]` | NOT present |

### 3.3 Local Ops Agent

| Aspect | Archive JSON (`local_ops_agent.json`) | Cached .md (`ops/platform/local-ops.md`) |
|--------|--------------------------------------|------------------------------------------|
| **Size** | ~64.6KB (massive) | ~2-3KB (concise) |
| **Skills** | NOT present in JSON | 14 skills in .md |
| **Structure** | Deeply nested: `authority`, `capabilities.local_deploy_cli.commands.{start,status,monitor,health,...}`, `guidelines`, `examples`, `deployment_protocol`, `port_management`, `process_lifecycle` | Flat YAML frontmatter + markdown prose |
| **memory_routing** | NOT present | NOT present |
| **routing** | NOT present | NOT present |
| **agent_type** | NOT present (different schema) | `agent_type: specialized` |
| **Observation** | JSON contains extensive structured deployment protocols not representable in .md frontmatter | .md version is a completely different representation - markdown prose covers the same concepts but in narrative form |

**Key Insight**: The local_ops_agent.json uses a **completely different schema** than the other archive JSONs. It has `authority`, `guidelines`, `deployment_protocol`, `process_lifecycle`, `port_management` etc. - none of which exist in the standard archive schema. This agent is an outlier.

---

## 4. Skill Binding Architecture

### 4.1 Skill Binding Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    SKILL BINDING PIPELINE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Source 1: Archive JSON (NOT USED AT RUNTIME)                   │
│  ┌──────────────────────────────────┐                           │
│  │ templates/archive/engineer.json  │                           │
│  │ "skills": ["test-driven-dev",..] │  ← DEAD CODE PATH        │
│  └──────────────────────────────────┘                           │
│                                                                  │
│  Source 2: Git-Cached .md (PRIMARY SOURCE)                      │
│  ┌──────────────────────────────────┐                           │
│  │ ~/.claude-mpm/cache/agents/      │                           │
│  │   /bobmatnyc/claude-mpm-agents/  │                           │
│  │   /agents/engineer/core/         │                           │
│  │     engineer.md                  │                           │
│  │ YAML frontmatter:                │                           │
│  │   skills:                        │                           │
│  │     - brainstorming              │                           │
│  │     - git-workflow               │                           │
│  │     - test-driven-development    │                           │
│  └──────────────────────────────────┘                           │
│              │                                                   │
│              ▼                                                   │
│  ┌──────────────────────────────────┐                           │
│  │  SkillManager._load_agent_       │                           │
│  │  mappings()                      │                           │
│  │  Path: templates/*.json          │  ← FINDS NOTHING!        │
│  │  (bug: doesn't scan archive/)   │     (no .json in root)    │
│  └──────────────────────────────────┘                           │
│              │                                                   │
│              ▼                                                   │
│  ┌──────────────────────────────────┐                           │
│  │  SkillsRegistry.                 │                           │
│  │  get_skills_for_agent()          │                           │
│  │                                  │                           │
│  │  Checks: skill.agent_types       │                           │
│  │  If empty → skill available to   │                           │
│  │  ALL agents                      │                           │
│  └──────────────────────────────────┘                           │
│              │                                                   │
│              ▼                                                   │
│  ┌──────────────────────────────────┐                           │
│  │  AgentSkillsInjector.            │                           │
│  │  enhance_agent_template()        │                           │
│  │                                  │                           │
│  │  → Reads from SkillsService      │                           │
│  │  → Adds skills to JSON template  │                           │
│  │  → Generates YAML frontmatter    │                           │
│  │  → Injects docs after frontmatter│                           │
│  └──────────────────────────────────┘                           │
│              │                                                   │
│              ▼                                                   │
│  ┌──────────────────────────────────┐                           │
│  │  Deployed agent in               │                           │
│  │  .claude/agents/engineer.md      │                           │
│  │  WITH skills in frontmatter      │                           │
│  └──────────────────────────────────┘                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Critical SkillManager Bug

**File**: `src/claude_mpm/skills/skill_manager.py:28-37`

```python
def _load_agent_mappings(self):
    agent_templates_dir = Path(__file__).parent.parent / "agents" / "templates"
    # This scans: src/claude_mpm/agents/templates/*.json
    # But ALL JSON files are in: src/claude_mpm/agents/templates/archive/*.json
    for template_file in agent_templates_dir.glob("*.json"):
        # This glob finds ZERO files!
```

The `SkillManager._load_agent_mappings()` method scans `templates/*.json` but all JSON templates are in `templates/archive/*.json`. This means:
- **No agent-skill mappings are ever loaded from archive JSON templates**
- The `agent_skill_mapping` dict is always empty from this source
- Skills are resolved through the `SkillsRegistry` fallback path instead

**Impact**: The archive JSON `skills` arrays are **never used** for skill routing.

### 4.3 Dual Skill Mapping Sources

Skills reach agents through two independent paths:

1. **Git-cached .md frontmatter** → `skills:` array in YAML → Directly used during deployment
2. **SkillsRegistry** → `get_skills_for_agent(agent_type)` → Matches based on `skill.agent_types` field

The archive JSON `skills` arrays are a **third, dead path** that feeds nothing.

---

## 5. Memory Routing Architecture

### 5.1 How memory_routing Data Flows

```
┌─────────────────────────────────────────────────────────────┐
│                 MEMORY ROUTING DATA FLOW                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Step 1: capability_generator.py loads agent .md files       │
│  ┌───────────────────────────────────┐                      │
│  │ parse_agent_metadata(agent_file)  │                      │
│  │ → Parses YAML frontmatter        │                      │
│  │ → Checks for memory_routing:     │                      │
│  │   in frontmatter (FOUND!)        │                      │
│  └───────────────────────────────────┘                      │
│              │                                               │
│              ▼                                               │
│  Step 2: Falls back to JSON only if missing                 │
│  ┌───────────────────────────────────┐                      │
│  │ if "memory_routing" not in data:  │                      │
│  │   load_memory_routing_from_       │                      │
│  │   template(agent_name)           │                      │
│  │   → Looks in templates/*.json     │  ← NEVER FINDS      │
│  │   → (no JSONs in templates/)      │     ANYTHING         │
│  └───────────────────────────────────┘                      │
│              │                                               │
│              ▼                                               │
│  Step 3: Memory router uses patterns                        │
│  ┌───────────────────────────────────┐                      │
│  │ router.py: _load_dynamic_patterns │                      │
│  │ → Calls framework_loader.         │                      │
│  │   _load_memory_routing_from_      │                      │
│  │   template()                      │                      │
│  │ → Gets keywords + categories      │                      │
│  │ → Builds AGENT_PATTERNS dict      │                      │
│  │ → Used for content routing        │                      │
│  └───────────────────────────────────┘                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Key Finding

Since cached .md files already contain `memory_routing` in their YAML frontmatter:
- **Step 2 never triggers** — memory_routing is always found in Step 1
- The JSON template fallback is **dead code** for memory_routing
- Removing archive/ has **ZERO impact** on memory routing

---

## 6. Routing Data (Non-Memory Routing)

### 6.1 Archive JSON Files with `routing` Field

Only **5 of 39** archive JSON files contain a `routing` field:

| File | routing.keywords | routing.priority | routing.confidence_threshold |
|------|-----------------|------------------|------------------------------|
| `qa.json` | 11 keywords (test, quality, ...) | 50 | 0.7 |
| `api_qa.json` | 8 keywords (api, endpoint, ...) | 80 | 0.8 |
| `web_qa.json` | 9 keywords (web, browser, ...) | 80 | 0.8 |
| `prompt-engineer.json` | Keywords present | Priority present | Threshold present |
| `javascript_engineer_agent.json` | Keywords present | Priority present | Threshold present |

### 6.2 Cached .md Files with `routing` Data

Only **1** cached .md file has routing data: `phoenix-engineer.md` (line 29: `routing:`). The QA, web-qa, and api-qa cached .md files do **NOT** contain routing data.

### 6.3 Where Routing Data Is Consumed

The `routing` field is consumed by:
- `capability_generator.py:90-105` — Displays routing hints (keywords, priority)
- `remote_agent_discovery_service.py:734-799` — Builds agent discovery with routing keywords/paths/priority

The `load_routing_from_template()` fallback in `capability_generator.py:209-273` looks in `templates/*.json` (not `archive/`) — so it **never finds routing data** from archive JSONs.

### 6.4 Risk Assessment for `routing`

**LOW RISK** — The routing data in archive JSONs is currently **not loaded** by any runtime code (due to the path bug). However, this data IS valuable reference metadata. If routing from JSON templates is ever needed, it should be migrated to the cached .md frontmatter.

---

## 7. Hardcoded Archive References in Python Files

### 7.1 Direct References to `templates/archive` Path

**NONE FOUND.** No Python file contains a hardcoded reference to `templates/archive` or `templates\\archive`.

### 7.2 References to "archive" (Unrelated to templates/archive)

The following uses of "archive" in Python files are **NOT related** to `templates/archive/`:

| File | Line | Context |
|------|------|---------|
| `core/unified_config.py` | 226 | `archive_old_sessions: bool` — session archival config |
| `cli/commands/auto_configure.py` | 475-1270 | Agent archival (moving unused agents to `.claude/agents/unused/`) |
| `services/communication/message_service.py` | 446-456 | Message archival |
| `services/skills_deployer.py` | 16 | GitHub ZIP archive download comment |
| `services/github/github_cli_service.py` | 126-127 | apt keyring archive URL |
| `migrations/migrate_messages_to_db.py` | 84-128 | Inbox archive migration |
| `core/session_manager.py` | 224-286 | Session archives directory |
| `services/infrastructure/context_preservation.py` | 217-238 | Conversation archival |

**Conclusion**: No Python code has a hard dependency on the `templates/archive/` path.

---

## 8. agent_type Enum Analysis

### 8.1 Multiple AgentType Definitions

There are **3 separate** `AgentType` enums in the codebase:

| Location | Values | Usage |
|----------|--------|-------|
| `core/unified_agent_registry.py:52` | `CORE`, `SPECIALIZED`, `USER_DEFINED`, `PROJECT`, `MEMORY_AWARE` | Agent classification in unified registry |
| `models/agent_definition.py:25` | `CORE`, `PROJECT`, `CUSTOM`, `SYSTEM`, `SPECIALIZED` | Agent definition model |
| `core/enums.py:360` | `AgentCategory` (StrEnum): `ENGINEERING`, `RESEARCH`, `ANALYSIS`, ... | Category classification |

### 8.2 agent_type Field in Archive vs Cached .md

| Archive JSON Example | Cached .md Example | Difference |
|---------------------|---------------------|------------|
| `"agent_type": "engineer"` | `agent_type: engineer` | Same |
| `"agent_type": "qa"` | `agent_type: qa` | Same |
| `"agent_type": "ops"` (in ops.json) | `agent_type: ops` | Same |
| N/A (local_ops_agent.json has no agent_type) | `agent_type: specialized` | .md adds classification |

### 8.3 How agent_type Connects to Skill Routing

The `agent_type` field is used in:
1. **SkillManager.get_agent_skills(agent_type)** — Maps agent type to skills list
2. **SkillsRegistry.get_skills_for_agent(agent_type)** — Filters skills by `skill.agent_types`
3. **Memory router** — Patterns use agent type to route memory content
4. **capability_generator** — Uses agent_type for formatting and display
5. **Framework CLAUDE.md generator** — Lists valid `subagent_type` values

The `agent_type` values in archive JSONs match those in cached .md files. No routing logic depends on the archive as a source.

---

## 9. Risk Assessment: Removing archive/

### 9.1 What Metadata Would Be Lost

| Data Category | In Archive Only? | Impact | Recommendation |
|---------------|-----------------|--------|----------------|
| `testing.test_cases` | Yes | LOW — Generic stubs, never executed | Can be recreated if needed |
| `testing.performance_benchmarks` | Yes | LOW — Not consumed by any runtime code | Document in ADR |
| `routing` (5 files) | Yes (mostly) | LOW — Not loaded due to path bug | Migrate to .md frontmatter |
| `capabilities.file_access` | Yes | LOW — Not enforced at runtime | Migrate if needed |
| `capabilities.tools` (list) | Yes | MEDIUM — Useful reference for tool restrictions | Migrate to .md frontmatter |
| `capabilities.model` | Yes | LOW — Defaults applied elsewhere | Migrate to .md frontmatter |
| `metadata.created_at` | Yes | NEGLIGIBLE — Historical only | Accept loss |
| `metadata.updated_at` | Yes | NEGLIGIBLE — Historical only | Accept loss |
| `local_ops_agent.json` full schema | Yes | LOW — Unique schema, converted to .md prose | Already represented in .md |

### 9.2 What Would NOT Break

| System | Status | Reason |
|--------|--------|--------|
| Skill routing | SAFE | `SkillManager` doesn't scan `archive/` (path bug) |
| Memory routing | SAFE | Cached .md files contain `memory_routing` in frontmatter |
| Agent deployment | SAFE | Deploys from git cache, not archive |
| Capability generation | SAFE | Reads from .md frontmatter first; JSON fallback looks in `templates/` not `archive/` |
| Agent configuration | SAFE | `auto_configure.py` operates on `.claude/agents/`, not archive |

### 9.3 Overall Risk Level: **LOW**

The archive directory is functionally inert. No production code path reads from it. All critical metadata already exists in the git-cached .md files.

---

## 10. Recommendations

### 10.1 Pre-Removal Checklist

1. **Migrate routing data** from 5 archive JSONs to their cached .md equivalents:
   - `qa.json` → `qa/qa.md` (add `routing:` to frontmatter)
   - `api_qa.json` → `qa/api-qa.md`
   - `web_qa.json` → `qa/web-qa.md`
   - `prompt-engineer.json` → corresponding .md
   - `javascript_engineer_agent.json` → corresponding .md

2. **Fix SkillManager path bug** (if skill mapping from templates is desired):
   - Change `agent_templates_dir.glob("*.json")` to also scan git cache
   - OR: Accept that skill mappings come from .md frontmatter and SkillsRegistry

3. **Document lost testing metadata** in an ADR (architectural decision record)

4. **Keep archive as git history** — don't delete the commit history, just remove the directory

### 10.2 Post-Removal Validation

- Verify `memory_routing` still loads for all agents via `capability_generator.py`
- Verify `SkillManager.get_agent_skills()` returns correct skills
- Verify `routing` data for QA agents (if migrated to .md frontmatter)
- Run full test suite to catch any hidden dependencies

---

## 11. Appendix: Archive JSON Files with routing Field

### qa.json routing block:
```json
"routing": {
    "keywords": ["test", "quality", "validation", "cli", "library", "utility",
                 "coverage", "unit", "integration", "smoke", "regression"],
    "paths": ["/tests/", "/test/", "/spec/", "/src/", "/__tests__/", "/lib/", "/utils/"],
    "extensions": [".py", ".js", ".ts", ".sh", ".yaml", ".json", ".test.js",
                   ".test.ts", ".spec.js", ".spec.ts"],
    "priority": 50,
    "confidence_threshold": 0.7,
    "description": "Use for general testing when no specific API or Web indicators are present"
}
```

This data is valuable for intelligent agent selection but is currently not loaded from archive due to path resolution. Should be migrated to .md frontmatter or a dedicated routing configuration file.
