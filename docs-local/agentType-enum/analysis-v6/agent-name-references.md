# Agent Name/ID Reference Map — Analysis v6

**Task**: Map ALL agent name/ID references across the codebase
**Author**: reference-mapper teammate
**Date**: 2026-03-04
**Branch**: agenttype-enums

---

## Executive Summary

Agent names appear across **7 major reference categories** with **3 naming conventions** and highly inconsistent conventions between even closely related files. The core issue: the system simultaneously uses hyphens (`local-ops`), underscores (`local_ops`), display names (`Local Ops`), and `-agent` suffixes (`local-ops-agent`) with no single canonical form — even the canonical form varies by context.

**Hardcoded agent names found in**: Python code, YAML configs, Markdown docs, PM instructions, skills files, test files, CLI defaults.

---

## Naming Convention Reference

| Convention | Example | Where Used |
|---|---|---|
| **hyphen** | `local-ops`, `web-qa`, `python-engineer` | skill_to_agent_mapping.yaml, skills_wizard.py, PM docs |
| **underscore** | `local_ops`, `web_qa`, `python_engineer` | agent_name_normalizer.py, agents_metadata.py, templates/__init__.py |
| **display** | `Local Ops`, `Web QA`, `Python Engineer` | agent_name_normalizer.py display_names dict |
| **hyphen + -agent suffix** | `local-ops-agent`, `qa-agent`, `research-agent` | PM_INSTRUCTIONS.md, pm-examples.md, todo_task_tools.py |
| **bare lowercase** | `engineer`, `qa`, `research` | Most Python code, registry, YAML config |

---

## Category 1: Core Python Code (HARD references)

### 1.1 `src/claude_mpm/core/agent_name_normalizer.py` — THE canonical mapping file

This is the authoritative normalizer. It defines:
- `display_names` dict (underscore → display string): `"research"→"Research"`, `"engineer"→"Engineer"`, `"qa"→"QA"`, `"web_qa"→"Web QA"`, `"local_ops"→"Local Ops"`, `"python_engineer"→"Python Engineer"`, etc.
- `alias_map` (many-to-one normalization):
  - `"researcher" → "research"`, `"tavily_research" → "research"`, `"dev" → "engineer"`, `"developer" → "engineer"`, `"golang" → "golang_engineer"`, `"java" → "java_engineer"`, etc.
  - All underscore forms map to underscore canonical: `"python_engineer" → "python_engineer"` (NOT hyphen)
  - `"local_ops"`, `"local" → "local_ops"` (underscore)
  - `"web_qa"` → `"web_qa"` (underscore)
- `color_map` keys: underscore form (`"python_engineer"`, `"web_qa"`, `"local_ops"`)
- **Naming convention**: underscore (normalized form) + display name (for output)
- **Risk**: HARD. The normalization functions are the source of truth for Python code paths.

### 1.2 `src/claude_mpm/core/agent_registry.py` — Registry with canonical aliases

Key references (all bare lowercase/hyphen):
- L129-132: `"engineer"`, `"qa"`, `"research"`, `"ops"` in capability maps (HARD dict keys)
- L227-230: default agents list `["engineer", "qa", "research", "ops"]`
- L358-361: fallback agents list (same)
- L374-377: display name map `"engineer"→"Engineer"`, `"qa"→"QA"`, `"research"→"Researcher"`, `"ops"→"Ops"`
- L429-443: alias dict: `"python_engineer"→"python-engineer"` (maps underscore → hyphen!), `"eng"→"engineer"`
- L492-494: mock agent structure with `"engineer"` as ID
- **Naming convention**: Mixed — bare lowercase for simple agents, hyphen for specialized (`python-engineer`)
- **CONFLICT**: Registry normalizes `python_engineer` → `python-engineer` (hyphen), but `agent_name_normalizer.py` normalizes `python_engineer` → `python_engineer` (underscore). **These two modules disagree.**
- **Risk**: HARD. Registry is used by agent lookup/resolution code.

### 1.3 `src/claude_mpm/core/enums.py` — Enum definitions

- `AgentCategory` enum: `RESEARCH = "research"`, `QA = "qa"`, `ENGINEERING = "engineering"`, `PROJECT_MANAGEMENT = "project-management"` (hyphen for multi-word!)
- **Naming convention**: bare lowercase for simple, hyphen for multi-word categories
- **Risk**: MEDIUM. Enums used in routing decisions.

### 1.4 `src/claude_mpm/core/unified_config.py`

- L80-85: hardcoded list `["engineer", "research", "qa", "web-qa", "ops"]`
- **Naming convention**: bare lowercase + hyphen (`web-qa`)
- **Risk**: HARD. Default agent list.

### 1.5 `src/claude_mpm/core/tool_access_control.py`

- L44-51: dict keyed by `"pm"`, `"engineer"`, `"research"`, `"qa"`, `"ops"`
- L77, L125, L168: string comparisons `agent_type == "pm"` etc.
- **Risk**: HARD. These are literal equality comparisons — if agent_type value changes, tool access breaks.

### 1.6 `src/claude_mpm/core/agent_session_manager.py`

- L189-194: hardcoded prompts keyed by `"engineer"`, `"qa"`, `"research"`, `"ops"`
- L245: list `['engineer', 'qa', 'documentation']`
- **Risk**: HARD. Session initialization prompts.

### 1.7 `src/claude_mpm/core/minimal_framework_loader.py`

- L101-107: list `["engineer", "qa", "research", "ops"]`
- **Risk**: HARD. Minimal bootstrap list.

### 1.8 `src/claude_mpm/core/framework/formatters/content_formatter.py`

- L168-194: `"engineer" in agent_name.lower()`, `"qa" in agent_name.lower()`, `"research" in agent_name.lower()`, `"ops" in agent_name.lower()`
- **Naming convention**: substring match (tolerant)
- **Risk**: MEDIUM. Substring match — survives most renames if the keyword is preserved.

### 1.9 `src/claude_mpm/core/claude_runner.py`

- L574: `EXCLUDED_AGENTS = {"pm", "project_manager"}` — underscore + bare
- **Risk**: HARD. Exclusion set for agent processing.

---

## Category 2: Agents Package (HARD references)

### 2.1 `src/claude_mpm/agents/templates/__init__.py`

| Line | Key | Convention | Risk |
|---|---|---|---|
| L18 | `"engineer": "engineer_agent.md"` | bare lowercase → underscore filename | HARD |
| L19 | `"qa": "qa_agent.md"` | bare lowercase | HARD |
| L21 | `"web_qa": "web_qa_agent.md"` | underscore | HARD |
| L23 | `"research": "research_agent.md"` | bare | HARD |
| L32 | `"engineer": "Engineer"` display | bare → display | HARD |
| L33 | `"qa": "QA"` display | bare → display | HARD |
| L35 | `"web_qa": "Web QA"` display | underscore → display | HARD |
| L37 | `"research": "Researcher"` display | bare → display | HARD |

**Risk**: HARD. If agent type strings change, template loading breaks.

### 2.2 `src/claude_mpm/agents/agents_metadata.py`

- L351: `"qa": QA_CONFIG`, L353: `"web_qa": WEB_QA_CONFIG`, L354: `"research": RESEARCH_CONFIG`, L357: `"engineer": ENGINEER_CONFIG`
- **Naming convention**: bare/underscore (no hyphens here)
- **Risk**: HARD. Metadata registry lookup.

### 2.3 `src/claude_mpm/agents/__init__.py`

- L74: `"qa"`, L80: `"research"`, L98: `"engineer"` — all bare lowercase
- **Risk**: HARD. Package-level exports.

### 2.4 `src/claude_mpm/agents/system_agent_config.py`

- L109-110: `self._agents["engineer"] = SystemAgentConfig(agent_type="engineer", ...)`
- L192-193: `self._agents["qa"] = SystemAgentConfig(agent_type="qa", ...)`
- L219-220: `self._agents["research"] = SystemAgentConfig(agent_type="research", ...)`
- **Risk**: HARD. System agent initialization.

### 2.5 `src/claude_mpm/agents/frontmatter_validator.py`

- L376: `"research"` in valid agent type list
- **Risk**: HARD. Validation logic.

### 2.6 `src/claude_mpm/agents/agent_loader.py`

- L798: comment about stripping `_agent` suffix: `"engineer_agent" -> "engineer"`
- L806: normalized key examples: `"engineer"`, `"research"`, `"qa"`
- **Risk**: HARD. Agent loading path.

---

## Category 3: Services (HARD/MEDIUM references)

### 3.1 `src/claude_mpm/services/framework_claude_md_generator/section_generators/todo_task_tools.py`

This is the file that generates PM-facing instructions. **Critically inconsistent**:
- L50: `subagent_type="research-agent"` (hyphen + -agent suffix)
- L51: `subagent_type="engineer"` (bare — no suffix!)
- L52: `subagent_type="qa-agent"` (hyphen + -agent suffix)
- L68: `subagent_type="engineer"` (bare, correct example)
- L71: marks `subagent_type="research"` as ❌ WRONG — missing `-agent` suffix
- **Naming convention**: **Mixed and self-contradictory**. Engineer is bare, but research/qa require `-agent` suffix.
- **Risk**: HARD. Directly generates the PM's operating instructions.

### 3.2 `src/claude_mpm/services/framework_claude_md_generator/section_generators/agents.py`

- L238: `"research"` in generated markdown
- L471: `agent_ids=['documentation', 'qa', 'engineer']` — bare lowercase in example
- **Risk**: MEDIUM. Generated documentation.

### 3.3 `src/claude_mpm/services/agents/deployment/agent_template_builder.py`

- L514-517: color map `"engineer"→"blue"`, `"qa"→"green"`, `"research"→"purple"`
- L971-973: description map for `"engineer"`, `"qa"`, `"research"`
- L1087-1117: capability lists keyed by `"engineer"`, `"qa"`, `"research"`
- **Risk**: HARD. Template building logic.

### 3.4 `src/claude_mpm/services/agents/deployment/agent_configuration_manager.py`

- L119: `"qa"` in tool assignment dict
- L134: `"research"` in tool assignment dict
- L185: `"qa" in agent_name_lower` (substring match — tolerant)
- L215: `"research" in agent_name_lower` (substring match)
- **Risk**: HARD for dict keys, MEDIUM for substring matches.

### 3.5 `src/claude_mpm/services/config_api/agent_deployment_handler.py`

- L27-30: list `["engineer", "research", "qa", "web-qa"]` (bare + hyphen!)
- **Risk**: HARD. Deployment handler allowlist.

### 3.6 `src/claude_mpm/services/agents/agent_recommendation_service.py`

- L37-39: `["engineer", "research", "qa"]`
- **Risk**: HARD. Default recommendation list.

### 3.7 `src/claude_mpm/services/memory/router.py`

- L45: `"engineer"` key in routing dict
- L85-87: `"research"` key with substring `"research"` in match patterns
- L118: `"qa"` key
- L819-822: keyword→agent map: `"implementation"→"engineer"`, `"coding"→"engineer"`, `"analysis"→"research"`, `"testing"→"qa"`
- **Risk**: HARD. Memory routing by agent type.

### 3.8 `src/claude_mpm/services/utility_service.py`

- L81-84: list `["engineer", "qa", "research"]`
- **Risk**: HARD.

### 3.9 `src/claude_mpm/services/agents/deployment/deployment_utils.py`

- L75: code strips `-agent` suffix: `"qa-agent" → "qa"` — demonstrates the suffix pattern is in use.
- **Risk**: MEDIUM. Normalization utility.

---

## Category 4: Hooks (HARD/MEDIUM references)

### 4.1 `src/claude_mpm/hooks/claude_hooks/tool_analysis.py`

- L85-86: `tool_input.get("subagent_type") == "research"`, `== "engineer"` — equality comparisons
- **Risk**: HARD. Event classification breaks if subagent_type value changes.

### 4.2 `src/claude_mpm/hooks/claude_hooks/services/subagent_processor.py`

- L155-158: `if "research" in task_desc: agent_type = "research"`, `elif "engineer" in task_desc: agent_type = "engineer"`
- L352: list `["research", "engineer", "pm", "ops", "qa", "documentation", "security"]`
- **Risk**: HARD (L352 list), MEDIUM (substring matches).

### 4.3 `src/claude_mpm/hooks/claude_hooks/event_handlers.py`

- L475: `agent_type in ["research", "engineer", "qa", "documentation"]`
- **Risk**: HARD. Event filtering.

### 4.4 `src/claude_mpm/hooks/failure_learning/learning_extraction_hook.py`

- L202: returns `"qa"`, L204: returns `"engineer"` as agent type strings
- **Risk**: HARD.

---

## Category 5: CLI Commands (HARD/MEDIUM references)

### 5.1 `src/claude_mpm/cli/commands/auto_configure.py`

- L44-60: hardcoded lists including `"engineer"`, `"qa"`, `"research"`, `"documentation"`, `"local-ops"` (hyphen!), `"web-qa"` (not found here but related context)
- **Naming convention**: bare lowercase + hyphen for multi-word
- **Risk**: HARD. Auto-configuration agent lists.

### 5.2 `src/claude_mpm/cli/commands/agent_state_manager.py`

- L126: `AgentConfig("engineer", "No agents found", [])` — fallback default
- **Risk**: HARD. Fallback initialization.

### 5.3 `src/claude_mpm/cli/commands/agents_discover.py`

- L51, L55, L88, L92, L102: `"qa"` and `"ops"` as category strings for formatting
- **Risk**: MEDIUM. Display formatting.

### 5.4 `src/claude_mpm/cli/interactive/skills_wizard.py`

- L54: `"engineer": ENGINEER_CORE_SKILLS`
- L64: `"local-ops": OPS_SKILLS` (hyphen)
- L70-71: `"qa": QA_SKILLS`, `"web-qa": QA_SKILLS` (hyphen)
- L201: `any(qa in agent_id_lower for qa in ["qa", "test", "quality"])`
- L474: `["ops", "devops", "local-ops"]` (hyphen)
- L481: `["qa", "web-qa", "api-qa"]` (hyphen)
- **Naming convention**: mixed — bare for `engineer`/`qa`, hyphen for `local-ops`/`web-qa`
- **Risk**: HARD. Skills assignment logic.

### 5.5 `src/claude_mpm/cli/commands/agent_source.py`

- L104: `['engineer', 'pm', 'research']`
- **Risk**: MEDIUM. Example/documentation.

### 5.6 `src/claude_mpm/cli/interactive/agent_wizard.py`

- L484, L489, L494: `"research"`, `"engineer"`, `"qa"` in wizard options
- L663-665: template descriptions keyed by `"research"`, `"engineer"`, `"qa"`
- L725-727: system prompts keyed by `"research"`, `"engineer"`, `"qa"`
- L1321: `"qa"` in list
- **Risk**: HARD. Wizard logic flow.

### 5.7 `src/claude_mpm/slack_client/handlers/commands.py`

- L117: `agent_type = parts[1] if len(parts) > 1 else "engineer"` — default fallback
- **Risk**: HARD. Slack command default.

---

## Category 6: Skills Files (SOFT references)

### 6.1 `.claude/skills/mpm-delegation-patterns/SKILL.md`

Contains agent references with **multiple conventions in the same file**:
- `react-engineer` (hyphen)
- `local-ops` (hyphen)
- `web-qa` (hyphen)
- `api-qa` (hyphen)
- `vercel-ops` (hyphen)

Table at L151-156 uses: `local-ops`, `web-qa` (hyphen throughout).

- **Naming convention**: hyphen throughout the skills doc
- **Risk**: SOFT (documentation). PM reads these as instructions — if the PM's internal understanding of agent names changes, the skill docs become confusing/wrong.

### 6.2 `src/claude_mpm/agents/templates/pm-examples.md`

- `local-ops-agent` (hyphen + -agent suffix) — used 10+ times
- `web-qa-agent` (hyphen + -agent suffix)
- `api-qa` (hyphen, no suffix)
- **Naming convention**: hyphen + `-agent` suffix for most agents
- **Risk**: SOFT but influential. PM examples directly shape PM behavior.

### 6.3 `src/claude_mpm/agents/templates/circuit-breakers.md`

- `"research"`, `"engineer"`, `"qa"`, `"local-ops"`, `"api-qa"`, `"web-qa"` — all in `Task(agent="...", ...)` calls
- Also `local-ops-agent`, `web-qa-agent` with suffix
- **Naming convention**: mixed (with and without -agent suffix in same file)
- **Risk**: SOFT but influential.

---

## Category 7: PM Instructions (HARD-SOFT boundary)

### 7.1 `src/claude_mpm/agents/PM_INSTRUCTIONS.md`

PM instructions are **injected verbatim into the PM system prompt** (hard reference for PM behavior):

- `local-ops` (hyphen, no suffix): L279, L292, L294, L309, L352, L399-404, L409, L493, L616
- `local-ops-agent` (hyphen + -agent suffix): none directly, but referenced as "local-ops"
- `web-qa-agent` (hyphen + -agent suffix): L354, L355, L613, L614, L683
- `api-qa-agent` (hyphen + -agent suffix): L355
- `web-qa` (no suffix): implied through context
- Tool reference table: `**local-ops**`, `**QA** (web-qa-agent, api-qa-agent)` — display style for tools section
- `engineer` without suffix: L477, L535

**Critical**: The PM instructions say to use `local-ops` but also reference `local-ops-agent` — inconsistent.

- **Risk**: HARD for PM behavior. The PM will use whatever string is in PM_INSTRUCTIONS as the `subagent_type`.

### 7.2 `src/claude_mpm/agents/WORKFLOW.md`

- `web_qa` (underscore): L44 `elif "UI" in implementation: use web_qa`
- `api-qa`, `web-qa` (hyphen): L38
- `local-ops` (hyphen): L111, L113, L115
- **Naming convention**: Mixed (underscore and hyphen in same file!)
- **Risk**: SOFT but PM reads this.

---

## Category 8: YAML Config Files (HARD references)

### 8.1 `src/claude_mpm/config/agent_capabilities.yaml`

Agent IDs in this file are **inconsistent**:
- `python_engineer` (underscore) → `agent_id: "python_engineer"`
- `typescript_engineer` (underscore) → `agent_id: "typescript_engineer"`
- `php_engineer` (underscore key) BUT `agent_id: "php-engineer"` (hyphen!) — **inconsistency within same entry**
- `ruby_engineer` (underscore key) BUT `agent_id: "ruby-engineer"` (hyphen!)
- `local_ops_agent` (underscore key) → `agent_id: "local_ops_agent"` (underscore)
- `engineer`, `research`, `qa`, `documentation` — bare lowercase
- **Risk**: HARD. The `agent_id` field is what gets deployed as the YAML filename.

### 8.2 `src/claude_mpm/config/skill_to_agent_mapping.yaml`

All agent IDs use **hyphen format**:
- `python-engineer`, `typescript-engineer`, `golang-engineer`, `nextjs-engineer`, `react-engineer`, `svelte-engineer`, `dart-engineer`, `tauri-engineer`, `web-ui`, `data-engineer`, `refactoring-engineer`, `agentic-coder-optimizer`, `prompt-engineer`
- `qa`, `web-qa`, `api-qa`
- `ops`, `local-ops`, `vercel-ops`, `gcp-ops`, `clerk-ops`
- `security`, `research`, `documentation`, `ticketing`, `code-analyzer`, `content-agent`, `memory-manager`, `product-owner`, `project-organizer`, `version-control`, `mpm-agent-manager`, `mpm-skills-manager`
- **Naming convention**: hyphen throughout (most consistent file in codebase)
- **Risk**: HARD. Skill routing depends on these exact agent ID strings.

### 8.3 `default_configuration` in `agent_capabilities.yaml`

```yaml
agents:
  - agent_id: engineer    # bare
  - agent_id: research    # bare
  - agent_id: qa          # bare
  - agent_id: documentation  # bare
  - agent_id: ops         # bare
  - agent_id: ticketing   # bare
```
**Risk**: HARD. Default deployment list.

---

## Category 9: Agent Registry / Catalog (HARD references)

### 9.1 `src/claude_mpm/core/agent_registry.py`

- Canonical alias map (L429-443) normalizes to **hyphen** for specialized agents:
  - `"python_engineer" → "python-engineer"`
  - `"Python Engineer" → "python-engineer"`
  - `"python engineer" → "python-engineer"`
- But bare agents stay bare: `"eng" → "engineer"`, `"ENGINEER" → "engineer"`
- **Critical question**: Does the registry produce `python-engineer` (hyphen) or `python_engineer` (underscore) as the canonical ID?
  **Answer**: Registry → hyphen. Normalizer → underscore. **These conflict.**

### 9.2 `src/claude_mpm/core/unified_agent_registry.py`

- L736: `["pm", "engineer", "qa", ...]` in comments
- **Risk**: MEDIUM (comment), but indicates expected agent IDs.

---

## Category 10: Test Files (HARD references — will break on rename)

### 10.1 `tests/test_agent_name_normalization.py`

Hardcoded test cases including:
- `"engineer"`, `"research"`, `"qa"`, `"data_engineer"`, `"data engineer"`, `"data-engineer"`, `"researcher"`, `"engineering"` → various normalized forms
- Tests cover: `AgentNameNormalizer.normalize("data-engineer")` → `"Data Engineer"`
- Tests cover: `AgentNameNormalizer.to_task_format("Data Engineer")` → `"data_engineer"` or `"data-engineer"`

**Critical ambiguity found**: The test at L172 expects `"Data Engineer" → "data_engineer"` (underscore). The registry at L436 maps `"python engineer" → "python-engineer"` (hyphen). **Tests and registry disagree on the canonical form.**

### 10.2 `tests/test_agent_name_formats.py`

- Test cases: `("Research", "Research", "research")`, `("Engineer", "Engineer", "engineer")`, `("QA", "QA", "qa")`
- `("Unknown Agent", "Engineer", "engineer")` — shows Engineer as the default fallback

### 10.3 `tests/test_agent_name_consistency.py`

- Hardcoded: `"research"`, `"qa"`, `"engineer"` in expected lists
- **Risk**: HARD. Test assertions will fail on rename.

### 10.4 `tests/integration/agents/test_agent_names_fix.py`

Name specifically: tests for agent naming fixes — likely contains many hardcoded agent name assertions.

### 10.5 Multiple other test files

139 test files reference `agent_type` or `agent_name`. Most of these have hardcoded agent name strings as:
- String literals in `assert` statements
- Dict keys in test fixtures
- `subagent_type=` arguments to mock calls

---

## Category 11: Skills Files with Agent References

### 11.1 `src/claude_mpm/skills/skill_manager.py`

- L135: docstring uses `'engineer'`, `'python_engineer'`, `'pm'`
- L325: `agents.extend(["ops", "devops", "local-ops"])` — mixed bare/hyphen
- L330-332: `["qa", "web-qa", "api-qa"]` — mixed bare/hyphen
- **Risk**: HARD. Skill assignment logic.

### 11.2 `src/claude_mpm/skills/agent_skills_injector.py`

- L139: docstring: `'agent_id': 'engineer'`
- L250, L305: `'engineer'` in examples
- **Risk**: MEDIUM (docstrings), but API contracts.

### 11.3 `src/claude_mpm/skills/registry.py`, `src/claude_mpm/skills/skills_registry.py`, `src/claude_mpm/skills/skills_service.py`

- All docstrings use `'engineer'` and `'python_engineer'` as example agent IDs
- **Risk**: MEDIUM (docs), but establishes expected API contract.

---

## Normalization Gap Analysis

| Reference Pattern | Normalization Catches It? | Notes |
|---|---|---|
| `"engineer"` → rename to enum | No — literal string matches will break | `tool_access_control.py`, `event_handlers.py` |
| `"python_engineer"` vs `"python-engineer"` | Partially — normalizer produces underscore, registry produces hyphen | **Active conflict** |
| `subagent_type="research-agent"` | No — suffix handling is inconsistent | `todo_task_tools.py` says research needs suffix, engineer doesn't |
| `"local-ops"` vs `"local_ops"` vs `"local-ops-agent"` | Normalizer handles underscore→display but not hyphen→underscore | Three conventions for one agent |
| Substring matches (`"qa" in name.lower()`) | Survives rename if keyword preserved | `content_formatter.py`, `skills_wizard.py` |
| YAML `agent_id: local_ops_agent` | No — YAML not processed by Python normalizer | Must update manually |
| Test assertions | No | 139 test files have hardcoded expectations |

---

## Critical Inconsistencies Found

### Inconsistency 1: Normalizer vs Registry conflict
- `agent_name_normalizer.py` → `"python_engineer"` (underscore canonical)
- `agent_registry.py` alias map → `"python-engineer"` (hyphen canonical)
- **Impact**: Code that goes through normalizer produces different results than code through registry.

### Inconsistency 2: PM instructions mixed conventions
- `PM_INSTRUCTIONS.md` uses `local-ops` (hyphen, no suffix)
- `pm-examples.md` uses `local-ops-agent` (hyphen + suffix)
- `circuit-breakers.md` uses both `"local-ops"` and `local-ops-agent`
- **Impact**: PM behavior is shaped by contradictory examples.

### Inconsistency 3: `todo_task_tools.py` engineer has no suffix, others do
- `subagent_type="engineer"` ✅ (per file)
- `subagent_type="research-agent"` ✅ (per file)
- `subagent_type="qa-agent"` ✅ (per file)
- But the same file marks `subagent_type="research"` ❌ WRONG
- **Impact**: PM is taught that engineer is special (no suffix needed) but research/qa need `-agent`.

### Inconsistency 4: `agent_capabilities.yaml` mixed within single file
- `php_engineer` as YAML key → `agent_id: "php-engineer"` (different conventions!)
- `local_ops_agent` as YAML key → `agent_id: "local_ops_agent"` (consistent underscore)
- **Impact**: The YAML key ≠ agent_id in some entries.

### Inconsistency 5: `skill_to_agent_mapping.yaml` uses hyphen, Python code uses underscore
- YAML: `local-ops`, `web-qa` (hyphen)
- Python normalizer: `local_ops`, `web_qa` (underscore)
- **Impact**: Skill routing uses different IDs than the Python agent model.

---

## Summary Table: All Agent Name Variants Found

| Agent | Bare | Underscore | Hyphen | +suffix | Display |
|---|---|---|---|---|---|
| Engineer | `engineer` | — | — | — | `Engineer` |
| Research | `research` | — | — | `research-agent` | `Research`/`Researcher` |
| QA | `qa` | — | — | `qa-agent` | `QA` |
| Web QA | — | `web_qa` | `web-qa` | `web-qa-agent` | `Web QA` |
| Local Ops | — | `local_ops` | `local-ops` | `local-ops-agent` | `Local Ops` |
| Python Engineer | — | `python_engineer` | `python-engineer` | — | `Python Engineer` |
| TypeScript Engineer | — | `typescript_engineer` | `typescript-engineer` | — | `TypeScript Engineer` |
| Golang Engineer | — | `golang_engineer` | `golang-engineer` | — | `Golang Engineer` |
| Ops | `ops` | — | — | `ops-agent` | `Ops` |
| PM | `pm` | `project_manager` | — | — | `PM` |
| Data Engineer | — | — | `data-engineer` | — | `Data Engineer` |
| Version Control | — | `version_control` | `version-control` | — | `Version Control` |

---

## Files with Highest Hardcoding Risk

These files have literal string comparisons (not substring/normalization) that WILL break if agent names change:

1. `src/claude_mpm/core/tool_access_control.py` — dict key lookup + equality checks
2. `src/claude_mpm/hooks/claude_hooks/tool_analysis.py` — `== "research"`, `== "engineer"`
3. `src/claude_mpm/hooks/claude_hooks/event_handlers.py` — membership test in hardcoded list
4. `src/claude_mpm/hooks/claude_hooks/services/subagent_processor.py` — list membership
5. `src/claude_mpm/agents/templates/__init__.py` — dict key lookup for template filename
6. `src/claude_mpm/agents/agents_metadata.py` — dict key lookup for metadata
7. `src/claude_mpm/core/agent_session_manager.py` — dict key lookup for session prompts
8. `src/claude_mpm/agents/system_agent_config.py` — dict key and `agent_type=` parameter
9. `src/claude_mpm/services/config_api/agent_deployment_handler.py` — allowlist membership
10. `src/claude_mpm/slack_client/handlers/commands.py` — default value assignment

---

## Files in `docs-local/agentType-enum/analysis-v6/` directory
This document: `agent-name-references.md`
