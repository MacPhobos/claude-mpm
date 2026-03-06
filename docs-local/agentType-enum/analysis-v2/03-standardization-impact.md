# Standardization Impact Analysis: "type" vs "agent_type" Frontmatter Field

**Date**: 2026-03-03
**Analyst**: Research Agent (Claude Opus 4.6)
**Branch**: `agenttype-enums`
**Status**: Complete
**Predecessor**: `docs-local/agentType-enum/problem-analysis.md`

---

## Executive Summary

The codebase has a split personality: **47 agent `.md` files use `type:` in frontmatter** while **27 agent `.md` files use `agent_type:`** in frontmatter. These two groups represent different generations of agent definitions (deployed vs template-format). The Python source code is similarly split, with some paths reading `type:` and others reading `agent_type:`. This analysis quantifies the impact of three standardization approaches and provides a recommendation.

---

## 1. Current State: Frontmatter Field Census

### Agent Markdown Files in `.claude/agents/`

| Frontmatter Field | File Count | Naming Pattern |
|---|---|---|
| `type:` | **47 files** | Kebab-case names (e.g., `python-engineer.md`, `aws-ops.md`) |
| `agent_type:` | **27 files** | Underscore or `-agent` suffix (e.g., `php_engineer.md`, `research-agent.md`) |
| **Both fields** | 0 files | No overlap detected |
| **Neither field** | 1 file | `README.md` (not an agent file) |

### Files Using `type:` (47 total)

```
agentic-coder-optimizer.md  api-qa.md          aws-ops.md
clerk-ops.md                code-analyzer.md   content-agent.md
dart-engineer.md            data-engineer.md   data-scientist.md
digitalocean-ops.md         documentation.md   engineer.md
gcp-ops.md                  golang-engineer.md imagemagick.md
java-engineer.md            javascript-engineer.md  local-ops.md
memory-manager-agent.md     mpm-agent-manager.md    mpm-skills-manager.md
nestjs-engineer.md          nextjs-engineer.md      ops.md
phoenix-engineer.md         php-engineer.md         product-owner.md
project-organizer.md        prompt-engineer.md      python-engineer.md
qa.md                       react-engineer.md       real-user.md
refactoring-engineer.md     research.md             ruby-engineer.md
rust-engineer.md            security.md             svelte-engineer.md
tauri-engineer.md           ticketing.md            tmux-agent.md
typescript-engineer.md      vercel-ops.md           version-control.md
visual-basic-engineer.md    web-qa.md               web-ui.md
```

### Files Using `agent_type:` (27 total)

```
api-qa-agent.md             dart_engineer.md
digitalocean-ops-agent.md   documentation-agent.md
gcp-ops-agent.md            golang_engineer.md
java_engineer.md            javascript-engineer-agent.md
local-ops-agent.md          nestjs_engineer.md
nextjs_engineer.md          ops-agent.md
php_engineer.md             product_owner.md
qa-agent.md                 react_engineer.md
real_user.md                research-agent.md
ruby_engineer.md            rust_engineer.md
security-agent.md           svelte_engineer.md
tauri_engineer.md           vercel-ops-agent.md
visual_basic_engineer.md    web-qa-agent.md
web-ui-engineer.md
```

**Observation**: The 27 `agent_type:` files appear to be older-format duplicates of the 47 `type:` files. They use different naming conventions (underscore vs kebab-case, `-agent` suffix) and have a different frontmatter schema (includes `schema_version`, `agent_id`, `resource_tier` fields). These appear to be legacy template-format files that coexist with the newer deployed-format files.

### Also Referenced in Documentation

The AGENT-SYSTEM.md developer documentation uses `agent_type:` in all its examples:
- Line 44: `agent_type: engineer` (Markdown Agent Format example)
- Line 312: `agent_type` listed as required field in schema
- Line 319: `agent_type: enum [engineer, qa, ops, research, documentation, security]`
- Line 335: `agent_type: engineer` (Creating New Agents example)
- Line 358: `"agent_type": "my_agent"` (Python config example)

---

## 2. Python Source Code References

### Code Reading `"type"` from Frontmatter/Agent Data (Production)

| File | Line | Code | Context |
|---|---|---|---|
| `services/agents/management/agent_management_service.py` | 444 | `type=AgentType(post.metadata.get("type", "core"))` | Primary markdown parser -- reads `type:` from frontmatter |
| `services/agents/deployment/agent_discovery_service.py` | 320-322 | `"type": frontmatter.get("agent_type", frontmatter.get("category", "agent"))` | **HYBRID**: reads `agent_type` first, falls back to `category`, writes to `"type"` key |
| `services/agents/deployment/agent_validator.py` | 362-363 | `elif stripped_line.startswith("type:"):` | Reads `type:` from frontmatter during validation |
| `services/agents/deployment/deployment_wrapper.py` | 111 | `"type": agent.get("type", "agent")` | Reads `type` from agent dict |
| `services/agents/registry/deployed_agent_discovery.py` | 109 | `"id": agent.get("type", agent.get("name", "unknown"))` | Reads `type` as fallback for ID |
| `services/agents/registry/deployed_agent_discovery.py` | 193 | `"id": json_data.get("agent_type", registry_info.get("type", "unknown"))` | **HYBRID**: reads `agent_type` first, falls back to `type` |
| `services/cli/agent_listing_service.py` | 214, 250, 296 | `type=agent_data.get("type", "agent")` / `type=metadata.get("type", "agent")` | Reads `type` for CLI display |
| `core/agent_registry.py` | 239 | `all_types = {metadata["type"] for metadata in self.agents.values()}` | Reads `type` from agent metadata |
| `agents/agents_metadata.py` | 14+ | `"type": "core_agent"` (15 entries) | Hardcoded metadata dicts use `"type"` key |

### Code Reading `"agent_type"` from Frontmatter/Agent Data (Production)

| File | Line | Code | Context |
|---|---|---|---|
| `services/agents/deployment/agent_template_builder.py` | 493 | `agent_type = template_data.get("agent_type", "general")` | Reads `agent_type` from template data |
| `services/agents/deployment/agent_template_builder.py` | 568 | `frontmatter_lines.append(f"type: {agent_type}")` | **WRITES `type:` to frontmatter from `agent_type` source** |
| `services/agents/deployment/agent_template_builder.py` | 910, 1052, 1083 | `agent_type = template_data.get("agent_type", "general")` | Multiple methods read `agent_type` |
| `services/agents/deployment/validation/template_validator.py` | 31 | `"agent_type": str` | Requires `agent_type` field in templates |
| `services/agents/deployment/remote_agent_discovery_service.py` | 234 | `"agent_type"` in `simple_keys` list | Reads `agent_type` from remote YAML |
| `services/agents/local_template_manager.py` | 83, 109 | `"agent_type": self.agent_type` / `agent_type=data.get("agent_type", "")` | Uses `agent_type` for local templates |
| `services/monitor/config_routes.py` | 817 | `"agent_type": fmdata.get("agent_type", "")` | Dashboard API reads `agent_type` from frontmatter |
| `core/unified_agent_registry.py` | 108, 116 | `data["agent_type"] = self.agent_type.value` / `AgentType(data["agent_type"])` | Serialization/deserialization uses `agent_type` key |
| `hooks/claude_hooks/event_handlers.py` | 442+ | `"agent_type": agent_type` | Event data uses `agent_type` key |
| `hooks/claude_hooks/services/subagent_processor.py` | 147+ | `agent_type = event.get("agent_type", ...)` | Event processing reads `agent_type` |
| `models/agent_session.py` | 112, 282, 488 | `"agent_type": self.agent_type` / `agent_type = data.get("agent_type", ...)` | Session model uses `agent_type` |
| `agents/agent_loader.py` | 410 | `agent_type = getattr(agent, "agent_type", None)` | Agent loader reads `agent_type` attribute |

### Critical Translation Point

**`agent_template_builder.py`** is the key translation layer:
- **INPUT**: Reads `template_data.get("agent_type", "general")` (line 493)
- **OUTPUT**: Writes `type: {agent_type}` to frontmatter (line 568)

This means the template builder **translates `agent_type` -> `type`** during deployment. The deployed agent files use `type:` because the builder writes it that way.

### Code Count Summary

| Context | References `"type"` | References `"agent_type"` |
|---|---|---|
| Production src/ (Python) | ~15 locations in 8 files | ~40+ locations in 15 files |
| Test files | ~10 locations | ~250+ locations |
| Event/hook data (runtime) | ~5 locations | ~50+ locations |
| Agent `.md` frontmatter | 47 files | 27 files |

---

## 3. Approach A: Standardize on "type" (Remove "agent_type")

### Description
All agent markdown files would use `type:` in frontmatter. All Python code would read/write `type:` as the canonical field name for agent type classification.

### Changes Required

**Agent markdown files requiring frontmatter changes**: 27 files
- All files currently using `agent_type:` would change to `type:`
- Files: All 27 listed in Section 1 above

**Python source files requiring code changes**: ~15 files

| File | Change Required |
|---|---|
| `services/agents/deployment/agent_template_builder.py` | Change `.get("agent_type")` to `.get("type")` at 4 locations |
| `services/agents/deployment/validation/template_validator.py` | Change required field from `"agent_type"` to `"type"` |
| `services/agents/deployment/remote_agent_discovery_service.py` | Change `"agent_type"` to `"type"` in `simple_keys` |
| `services/agents/local_template_manager.py` | Change `"agent_type"` to `"type"` at 2 locations |
| `services/monitor/config_routes.py` | Change `fmdata.get("agent_type")` to `fmdata.get("type")` |
| `core/unified_agent_registry.py` | Change `data["agent_type"]` to `data["type"]` at 2 locations |
| `hooks/claude_hooks/event_handlers.py` | Change `"agent_type"` to `"type"` at 6+ locations |
| `hooks/claude_hooks/services/subagent_processor.py` | Change event key references |
| `hooks/claude_hooks/services/state_manager.py` | Change `"agent_type"` key |
| `hooks/claude_hooks/services/connection_manager.py` | Change `"agent_type"` key references |
| `hooks/claude_hooks/services/connection_manager_http.py` | Change `"agent_type"` key references |
| `models/agent_session.py` | Change `"agent_type"` to `"type"` at 3 locations |
| `agents/agent_loader.py` | Change `getattr(agent, "agent_type")` |
| `skills/skill_manager.py` | Change `agent_data.get("agent_type")` |
| `services/memory_hook_service.py` | Change `data.get("agent_type")` |

**Test files requiring changes**: ~30+ files (250+ individual references)

### Advantages
1. **`type:` is shorter and simpler** -- less verbose in frontmatter
2. **Already dominant in deployed files** -- 47 vs 27 files already use `type:`
3. **Consistent with the template builder output** -- builder already writes `type:` to frontmatter
4. **Less disruptive to deployed agents** -- the 47 "current" format files don't change

### Disadvantages
1. **Python builtin shadow**: `type` is a Python builtin. The `AgentMetadata` dataclass already has `type: AgentType` which shadows it at line 99 of `agent_definition.py`. This prevents using `type()` inside methods that receive this field as a parameter.
2. **Ambiguity**: In YAML frontmatter, `type:` is extremely generic. Without context, it's unclear what "type" refers to (agent type? document type? template type?).
3. **Massive test file changes**: Over 250 test references use `"agent_type"` and would need updating.
4. **Event data contract breakage**: The hook/event system extensively uses `"agent_type"` in event payloads. Changing this field name affects any external consumers of event data (dashboards, monitoring tools, WebSocket clients).
5. **Serialization breakage**: The `unified_agent_registry` serializes/deserializes with `"agent_type"` key. Changing this breaks existing serialized registry data.

### Risk of Regression: HIGH
- Event data format is a public contract consumed by the dashboard frontend
- Serialized registry data would fail to deserialize
- Any external tools parsing event data would break

### Claude Code Platform Impact: NONE
- Claude Code ignores the `type`/`agent_type` field entirely (see Appendix C)
- Only `name`, `description`, and `model` are platform-recognized fields
- The field name choice has zero effect on how Claude Code loads or runs agents

### External User Impact: LOW-MEDIUM
- Users who created agents with `type:` (the deployed format) see no change
- Users who created agents with `agent_type:` (the template format) must update their frontmatter
- The ambiguity of `type:` may confuse users creating new agents

---

## 4. Approach B: Standardize on "agent_type" (Remove "type")

### Description
All agent markdown files would use `agent_type:` in frontmatter. All Python code would read/write `agent_type:` as the canonical field name.

### Changes Required

**Agent markdown files requiring frontmatter changes**: 47 files
- All files currently using `type:` would change to `agent_type:`
- Files: All 47 listed in Section 1 above

**Python source files requiring code changes**: ~8 files

| File | Change Required |
|---|---|
| `services/agents/management/agent_management_service.py` | Change `post.metadata.get("type")` to `post.metadata.get("agent_type")` |
| `services/agents/deployment/agent_validator.py` | Change `startswith("type:")` to `startswith("agent_type:")` |
| `services/agents/deployment/agent_discovery_service.py` | Already reads `agent_type` first, just remove `category` fallback |
| `services/agents/deployment/deployment_wrapper.py` | Change `agent.get("type")` to `agent.get("agent_type")` |
| `services/agents/registry/deployed_agent_discovery.py` | Change `agent.get("type")` references |
| `services/cli/agent_listing_service.py` | Change `agent_data.get("type")` at 3 locations |
| `core/agent_registry.py` | Change `metadata["type"]` to `metadata["agent_type"]` |
| `agents/agents_metadata.py` | Change `"type": "core_agent"` to `"agent_type": "core_agent"` at 15 locations |
| `models/agent_definition.py` | Rename `AgentMetadata.type` field to `AgentMetadata.agent_type` |
| `services/agents/management/agent_management_service.py` | Update field name in serialization |
| `services/agents/deployment/agent_definition_factory.py` | Update `type=` to `agent_type=` |

**Test files requiring changes**: ~10 files (minimal, since most tests already use `"agent_type"`)

### Advantages
1. **Avoids Python builtin shadow**: `agent_type` does not conflict with Python's `type()` builtin. This eliminates a subtle source of bugs in methods that work with the type field.
2. **More explicit and self-documenting**: `agent_type:` in YAML is unambiguous -- it clearly means "the type of this agent." `type:` could mean anything.
3. **Dominant in Python code**: The Python source already uses `"agent_type"` in ~40+ production locations vs ~15 for `"type"` (when used as a frontmatter/agent-data key).
4. **Dominant in test code**: ~250+ test references use `"agent_type"`.
5. **Event data remains stable**: The hook/event system already uses `"agent_type"`, so no event contract changes needed.
6. **Serialization remains stable**: The unified registry already uses `"agent_type"` for serialization.
7. **Documentation already uses it**: AGENT-SYSTEM.md uses `agent_type:` in all examples.
8. **Template validator already requires it**: `template_validator.py` lists `"agent_type"` as a required field.

### Disadvantages
1. **More frontmatter changes needed**: 47 files need updating vs 27 for Approach A.
2. **Longer field name**: `agent_type:` is 11 chars vs `type:` is 5 chars (minor).
3. **The template builder currently writes `type:`**: This is the deployment pipeline output -- needs to be changed to write `agent_type:`.

### Risk of Regression: LOW
- Event data contract unchanged
- Serialized registry data unchanged
- Most Python code already uses `"agent_type"`
- Main risk is the 47 frontmatter changes which are mechanical
- Agent validator line-by-line parser needs updating (straightforward)

### Claude Code Platform Impact: NONE
- Claude Code ignores the `type`/`agent_type` field entirely (see Appendix C)
- Only `name`, `description`, and `model` are platform-recognized fields
- The field name choice has zero effect on how Claude Code loads or runs agents

### External User Impact: MEDIUM
- Users who created agents using `type:` (the more common deployed format) must update to `agent_type:`
- New agents should use `agent_type:` -- which the documentation already recommends
- The more explicit field name is easier for new users to understand

### Python Builtin Conflict Analysis

The current `AgentMetadata` dataclass:
```python
@dataclass
class AgentMetadata:
    type: AgentType    # <-- shadows Python builtin type()
    model_preference: str = "claude-3-sonnet"
```

With `agent_type`:
```python
@dataclass
class AgentMetadata:
    agent_type: AgentType    # <-- no shadow, clean Python
    model_preference: str = "claude-3-sonnet"
```

This is not just aesthetic. In any method of `AgentMetadata` or any function receiving `type` as a parameter, `type()` becomes inaccessible without importing `builtins`. While Python allows this, it is widely considered a code smell per PEP 8 and linting tools like `pylint` flag it with `W0622 (redefined-builtin)`.

---

## 5. Approach C: Support Both "type" and "agent_type"

### Description
The parser accepts either `type:` or `agent_type:` in frontmatter. When both are present, one takes precedence. The system normalizes to a single internal representation.

### Precedence Rules Needed

If both `type:` and `agent_type:` appear in a single file's frontmatter, the system needs a rule:

**Option C1**: `agent_type:` takes precedence (more specific wins)
**Option C2**: `type:` takes precedence (shorter/simpler wins)
**Option C3**: Raise an error if both present (strict mode)

**Recommendation**: C1 (`agent_type:` precedence) since it is more specific and avoids accidental overrides.

### Parser Complexity Added

The current parsing code is split across multiple files. Each would need dual-field handling:

```python
# Current (agent_discovery_service.py line 320-322):
"type": frontmatter.get("agent_type", frontmatter.get("category", "agent"))

# With dual support:
"type": frontmatter.get("agent_type", frontmatter.get("type", frontmatter.get("category", "agent")))
```

**Files requiring parser changes**: ~8 files (same as Approach B, but with fallback chains instead of renames)

| File | Change Required |
|---|---|
| `agent_management_service.py` | Add `post.metadata.get("agent_type") or post.metadata.get("type", "core")` |
| `agent_validator.py` | Check both `startswith("type:")` and `startswith("agent_type:")` |
| `agent_discovery_service.py` | Already partially supports both -- extend |
| `remote_agent_discovery_service.py` | Add `"type"` to `simple_keys` (already has `"agent_type"`) |
| `agent_listing_service.py` | Add fallback chain at 3 locations |
| `config_routes.py` | Add fallback chain |
| `agents_metadata.py` | No change needed (internal data) |
| `agent_template_builder.py` | Decide which field to write on output |

### Serialization Question: Which Field Name Gets Written?

When the system writes frontmatter (e.g., during deployment or template generation), it must choose ONE field name. This creates an asymmetry:
- **Read path**: Accepts both `type:` and `agent_type:`
- **Write path**: Must pick one

**Current behavior**: Template builder reads `agent_type` from template data, writes `type:` to frontmatter. This is already an implicit "support both" pattern, just undocumented.

### Confusion for Agent Authors

Dual support creates a "which should I use?" problem:
- Documentation says `agent_type:` (AGENT-SYSTEM.md examples)
- Deployed agents use `type:` (template builder output)
- Both are accepted

This is the kind of implicit behavior that causes long-term maintenance headaches. New contributors will wonder why two field names exist, whether they're different, and which to prefer.

### Standard Pattern for Field Aliases in Python YAML Parsing

Python has established patterns for field aliases:

1. **Pydantic `Field(alias=...)`**: Pydantic v2 supports `alias`, `validation_alias`, and `serialization_alias` for exactly this case. Example:
   ```python
   class AgentFrontmatter(BaseModel):
       agent_type: str = Field(alias="type", validation_alias=AliasChoices("agent_type", "type"))
   ```

2. **dataclasses-json `field(metadata=...)`**: The `dataclasses-json` library supports aliases via metadata dict.

3. **Manual normalization**: A `normalize_frontmatter()` function that maps aliases before validation. This is what `_normalize_metadata_structure()` in `agent_template_builder.py` already does partially.

The project does not currently use Pydantic for agent frontmatter parsing, so a manual normalization approach would be needed.

### Risk of Regression: LOW
- No breaking changes to existing files
- Both formats continue to work

### Risk of Long-Term Confusion: HIGH
- Two names for the same concept is technical debt
- Every new parsing location must remember to check both
- Documentation conflicts (which to recommend?)
- Output format inconsistency across different code paths

### Claude Code Platform Impact: NONE
- Claude Code ignores the `type`/`agent_type` field entirely (see Appendix C)
- Only `name`, `description`, and `model` are platform-recognized fields
- The field name choice has zero effect on how Claude Code loads or runs agents

### External User Impact: LOW (initially)
- No files need to change
- But users may be confused by seeing both patterns in different agents

---

## 6. Quantitative Comparison Matrix

| Metric | Approach A: `type` | Approach B: `agent_type` | Approach C: Both |
|---|---|---|---|
| Agent `.md` files needing frontmatter changes | **27** | **47** | **0** |
| Python `src/` files needing code changes | **~15** | **~8** | **~8** |
| Test files needing changes | **~30+** (250+ refs) | **~10** (minimal) | **~0** |
| Event data contract breakage | **YES** (high risk) | **NO** | **NO** |
| Serialization breakage | **YES** (high risk) | **NO** | **NO** |
| Python builtin shadow | **YES** (existing) | **NO** (fixed) | **YES** (existing) |
| Claude Code platform impact | **NONE** | **NONE** | **NONE** |
| Documentation alignment | Needs update | Already aligned | Already works |
| Template validator alignment | Needs update | Already aligned | Already works |
| Agent authors confusion | Low | Low | **HIGH** |
| Long-term maintenance burden | Low | Low | **MEDIUM** |
| Risk of regression | **HIGH** | **LOW** | **LOW** |
| External user impact | LOW-MEDIUM | MEDIUM | **LOW** |

---

## 7. Recommendation

### Primary Recommendation: Approach B (Standardize on `agent_type`)

**Rationale**:

1. **Lower risk**: The event data contract and serialized registry data remain unchanged, avoiding the highest-risk breakage scenarios.

2. **Fewer Python code changes**: Only ~8 production source files need updating, vs ~15 for Approach A.

3. **Far fewer test changes**: ~10 test files vs ~30+ with 250+ individual references for Approach A.

4. **Eliminates Python builtin shadow**: The `type` field name in `AgentMetadata` is a known code smell. Renaming to `agent_type` fixes this cleanly.

5. **Documentation already uses `agent_type`**: The developer documentation and schema definition already standardize on `agent_type`, reducing confusion.

6. **Template validator already requires `agent_type`**: The validation pipeline is already aligned.

7. **More frontmatter changes but lower risk**: While 47 `.md` files need updating (vs 27), these are mechanical find-and-replace changes with near-zero risk. The Python code changes are where regression risk lives, and Approach B requires fewer and safer Python changes.

### Secondary Recommendation: Implement Approach C as Transitional Step

During migration to Approach B, implement dual-field reading (Approach C) as a **temporary compatibility layer**:

1. **Phase 1**: Add `agent_type` fallback reading to all parsers (Approach C)
2. **Phase 2**: Update the template builder to write `agent_type:` instead of `type:`
3. **Phase 3**: Bulk-update all 47 deployed agent files from `type:` to `agent_type:`
4. **Phase 4**: Remove `type:` fallback code (clean up Approach C scaffolding)
5. **Phase 5**: Add deprecation warning when `type:` is encountered

This phased approach ensures zero downtime and backward compatibility throughout the migration.

### Anti-Recommendation: Approach A

Approach A (standardize on `type`) is **not recommended** because:
- It breaks the event data contract (used by dashboard frontend and WebSocket clients)
- It breaks serialized registry data
- It requires 250+ test reference changes
- It preserves the Python builtin shadow issue
- It conflicts with existing documentation
- The shorter field name does not justify the higher risk and effort

---

## 8. Files Affected Summary (Approach B)

### Frontmatter Changes (47 files)
All files in `.claude/agents/` currently using `type:` -- mechanical find-and-replace.

### Python Source Changes (8 files)

| File | Lines Affected | Complexity |
|---|---|---|
| `models/agent_definition.py` | 99 | Rename field `type` -> `agent_type` |
| `services/agents/management/agent_management_service.py` | 318, 444, 625 | Change `"type"` -> `"agent_type"` in 3 locations |
| `services/agents/deployment/agent_validator.py` | 329, 362-363 | Change default and parser |
| `services/agents/deployment/agent_template_builder.py` | 544, 568 | Change comment and frontmatter output |
| `services/agents/deployment/deployment_wrapper.py` | 111 | Change dict key |
| `services/agents/registry/deployed_agent_discovery.py` | 109 | Change fallback key |
| `services/cli/agent_listing_service.py` | 214, 250, 296 | Change dict key in 3 locations |
| `agents/agents_metadata.py` | 14+ (15 entries) | Change `"type"` -> `"agent_type"` |
| `services/agents/deployment/agent_definition_factory.py` | 57 | Change kwarg name |

### Test File Changes (~10 files, minimal)
Most test files already use `"agent_type"`. Only tests that construct agent data using `"type"` key would need updating.

---

## Appendix A: The Template Builder Translation (Key Finding)

The most important finding in this analysis is the **implicit field name translation** in `agent_template_builder.py`:

```python
# Line 493: Reads "agent_type" from template data
agent_type = template_data.get("agent_type", "general")

# Line 568: Writes "type" to frontmatter output
frontmatter_lines.append(f"type: {agent_type}")
```

This single code path is WHY the deployed agents use `type:` while the template format uses `agent_type:`. The translation happens silently during deployment. This is the root cause of the field name split and should be the first thing addressed in any standardization effort.

## Appendix B: Python Builtin `type` Shadow Details

Python's `type()` builtin is used for:
- `type(obj)` -- get the type of an object
- `type(name, bases, dict)` -- create a new type dynamically

When a variable, parameter, or dataclass field is named `type`, it shadows this builtin within that scope. Examples from the codebase:

```python
# agent_definition.py:99 -- shadows type() in all AgentMetadata methods
@dataclass
class AgentMetadata:
    type: AgentType  # shadows builtin

# agent_definition_factory.py:57 -- shadows type() in this scope
metadata = AgentMetadata(
    type=type_map.get(tier, AgentType.CUSTOM),  # 'type' as kwarg
```

While this works in practice (Python allows it), it is flagged by linters and can cause subtle bugs if a developer later needs `type()` within the same scope.

## Appendix C: Impact on Claude Code Platform Parsing

Claude Code (the Anthropic platform that runs agents) parses agent `.md` files from `~/.claude/agents/` and `.claude/agents/` at startup. Based on analysis of the codebase:

### Fields Recognized by Claude Code Platform

Claude Code recognizes these frontmatter fields natively:
- **`name`**: Agent name displayed in Claude Code UI (required)
- **`description`**: When/why to use this agent, shown for agent selection (required)
- **`model`**: Which Claude model to use (optional, defaults to current model)

### Fields NOT Recognized by Claude Code Platform

The `type:` and `agent_type:` fields are **claude-mpm extensions**, not Claude Code platform fields. Evidence:

1. **`agent_format_converter.py`** (lines 174-191): The Claude Code compatible format converter deliberately excludes `type`/`agent_type` from output, including only `name`, `description`, `model`, `version`, and `author`.

2. **Output styles research** (`output-styles-system-analysis-2026-01-05.md`, line 69): "Custom metadata fields (not used by Claude Code but can be informative)" -- confirms Claude Code ignores unrecognized frontmatter fields.

3. **Migration docs** (`JSON_TO_MARKDOWN_MIGRATION_SUMMARY.md`, line 63): Lists `agent_type` as a schema field in the claude-mpm migration format, not a Claude Code format.

### Impact Assessment by Approach

| Approach | Impact on Claude Code Platform |
|---|---|
| **A: Standardize on `type`** | **NONE** -- Claude Code ignores both fields |
| **B: Standardize on `agent_type`** | **NONE** -- Claude Code ignores both fields |
| **C: Support both** | **NONE** -- Claude Code ignores both fields |

**Conclusion**: The choice between `type` and `agent_type` has **zero impact on Claude Code platform parsing**. Claude Code reads `name`, `description`, and `model` from frontmatter and passes the entire markdown body as agent instructions. All other frontmatter fields are claude-mpm metadata used by MPM's own agent management, discovery, deployment, and dashboard systems. The standardization decision is entirely within claude-mpm's domain.

---

## Appendix D: External User Agents

Users who create their own agents in `.claude/agents/` can use either field name depending on which examples they followed:
- If they followed deployed agent examples, they use `type:`
- If they followed AGENT-SYSTEM.md documentation, they use `agent_type:`

The agent discovery service (line 320-322) already handles this by trying `agent_type` first, then falling back to `category`. However, `agent_management_service.py` (line 444) ONLY reads `type:`. This means user agents with `agent_type:` in frontmatter may be silently defaulting to `type="core"` in some code paths.

---
