# Baseline Snapshot: `type` -> `agent_type` Field Standardization

**Date**: 2026-03-03
**Branch**: `agenttype-enums`
**Purpose**: Capture exact current state BEFORE any migration changes

---

## 1. Summary Statistics

| Metric | Count |
|--------|-------|
| Total agent files in `.claude/agents/` | 75 |
| Files using `type:` in frontmatter | 48 |
| Files using `agent_type:` in frontmatter | 27 |
| Files with neither field | 0 |

**Frontmatter parsing method**: Only content between the first two `---` markers was examined. Content-body occurrences of `type:` or `agent_type:` were NOT counted.

### Unique `type:` values (48 files)

| Value | Count | Would crash `AgentType` enum? |
|-------|-------|-------------------------------|
| engineer | 20 | YES |
| ops | 10 | YES |
| qa | 4 | YES |
| research | 2 | YES |
| documentation | 2 | YES |
| system | 1 | No (`SYSTEM`) |
| specialized | 1 | No (`SPECIALIZED`) |
| security | 1 | YES |
| refactoring | 1 | YES |
| product | 1 | YES |
| memory_manager | 1 | YES |
| imagemagick | 1 | YES |
| content | 1 | YES |
| claude-mpm | 1 | YES |
| analysis | 1 | YES |

**Crash risk**: 45 out of 48 `type:` files use values NOT in the `AgentType` enum. Only `system` (1 file) and `specialized` (1 file) would survive. The value `core` (the enum default) appears in 0 files.

### Unique `agent_type:` values (27 files)

| Value | Count |
|-------|-------|
| engineer | 14 |
| qa | 4 |
| ops | 4 |
| specialized | 1 |
| security | 1 |
| research | 1 |
| product | 1 |
| documentation | 1 |

---

## 2. Complete Agent File Inventory

| File Name | Frontmatter Field | Value | Generation |
|-----------|-------------------|-------|------------|
| agentic-coder-optimizer.md | `type` | ops | Gen 1 |
| api-qa-agent.md | `agent_type` | qa | Gen 2/3 |
| api-qa.md | `type` | qa | Gen 1 |
| aws-ops.md | `type` | ops | Gen 1 |
| clerk-ops.md | `type` | ops | Gen 1 |
| code-analyzer.md | `type` | research | Gen 1 |
| content-agent.md | `type` | content | Gen 1 |
| dart_engineer.md | `agent_type` | engineer | Gen 2/3 (underscore variant) |
| dart-engineer.md | `type` | engineer | Gen 1 |
| data-engineer.md | `type` | engineer | Gen 1 |
| data-scientist.md | `type` | engineer | Gen 1 |
| digitalocean-ops-agent.md | `agent_type` | ops | Gen 2/3 (-agent variant) |
| digitalocean-ops.md | `type` | ops | Gen 1 |
| documentation-agent.md | `agent_type` | documentation | Gen 2/3 (-agent variant) |
| documentation.md | `type` | documentation | Gen 1 |
| engineer.md | `type` | engineer | Gen 1 |
| gcp-ops-agent.md | `agent_type` | ops | Gen 2/3 (-agent variant) |
| gcp-ops.md | `type` | ops | Gen 1 |
| golang_engineer.md | `agent_type` | engineer | Gen 2/3 (underscore variant) |
| golang-engineer.md | `type` | engineer | Gen 1 |
| imagemagick.md | `type` | imagemagick | Gen 1 |
| java_engineer.md | `agent_type` | engineer | Gen 2/3 (underscore variant) |
| java-engineer.md | `type` | engineer | Gen 1 |
| javascript-engineer-agent.md | `agent_type` | engineer | Gen 2/3 (-agent variant) |
| javascript-engineer.md | `type` | engineer | Gen 1 |
| local-ops-agent.md | `agent_type` | specialized | Gen 2/3 (-agent variant) |
| local-ops.md | `type` | specialized | Gen 1 |
| memory-manager-agent.md | `type` | memory_manager | Gen 1 (-agent suffix, but `type:` field) |
| mpm-agent-manager.md | `type` | system | Gen 1 |
| mpm-skills-manager.md | `type` | claude-mpm | Gen 1 |
| nestjs_engineer.md | `agent_type` | engineer | Gen 2/3 (underscore variant) |
| nestjs-engineer.md | `type` | engineer | Gen 1 |
| nextjs_engineer.md | `agent_type` | engineer | Gen 2/3 (underscore variant) |
| nextjs-engineer.md | `type` | engineer | Gen 1 |
| ops-agent.md | `agent_type` | ops | Gen 2/3 (-agent variant) |
| ops.md | `type` | ops | Gen 1 |
| phoenix-engineer.md | `type` | engineer | Gen 1 |
| php_engineer.md | `agent_type` | engineer | Gen 2/3 (underscore variant) |
| php-engineer.md | `type` | engineer | Gen 1 |
| product_owner.md | `agent_type` | product | Gen 2/3 (underscore variant) |
| product-owner.md | `type` | product | Gen 1 |
| project-organizer.md | `type` | ops | Gen 1 |
| prompt-engineer.md | `type` | analysis | Gen 1 |
| python-engineer.md | `type` | engineer | Gen 1 |
| qa-agent.md | `agent_type` | qa | Gen 2/3 (-agent variant) |
| qa.md | `type` | qa | Gen 1 |
| react_engineer.md | `agent_type` | engineer | Gen 2/3 (underscore variant) |
| react-engineer.md | `type` | engineer | Gen 1 |
| real_user.md | `agent_type` | qa | Gen 2/3 (underscore variant) |
| real-user.md | `type` | qa | Gen 1 |
| refactoring-engineer.md | `type` | refactoring | Gen 1 |
| research-agent.md | `agent_type` | research | Gen 2/3 (-agent variant) |
| research.md | `type` | research | Gen 1 |
| ruby_engineer.md | `agent_type` | engineer | Gen 2/3 (underscore variant) |
| ruby-engineer.md | `type` | engineer | Gen 1 |
| rust_engineer.md | `agent_type` | engineer | Gen 2/3 (underscore variant) |
| rust-engineer.md | `type` | engineer | Gen 1 |
| security-agent.md | `agent_type` | security | Gen 2/3 (-agent variant) |
| security.md | `type` | security | Gen 1 |
| svelte_engineer.md | `agent_type` | engineer | Gen 2/3 (underscore variant) |
| svelte-engineer.md | `type` | engineer | Gen 1 |
| tauri_engineer.md | `agent_type` | engineer | Gen 2/3 (underscore variant) |
| tauri-engineer.md | `type` | engineer | Gen 1 |
| ticketing.md | `type` | documentation | Gen 1 |
| tmux-agent.md | `type` | ops | Gen 1 |
| typescript-engineer.md | `type` | engineer | Gen 1 |
| vercel-ops-agent.md | `agent_type` | ops | Gen 2/3 (-agent variant) |
| vercel-ops.md | `type` | ops | Gen 1 |
| version-control.md | `type` | ops | Gen 1 |
| visual_basic_engineer.md | `agent_type` | engineer | Gen 2/3 (underscore variant) |
| visual-basic-engineer.md | `type` | engineer | Gen 1 |
| web-qa-agent.md | `agent_type` | qa | Gen 2/3 (-agent variant) |
| web-qa.md | `type` | qa | Gen 1 |
| web-ui-engineer.md | `agent_type` | engineer | Gen 2/3 (-agent variant) |
| web-ui.md | `type` | engineer | Gen 1 |

### Generation Heuristic

- **Gen 1**: Uses `type:` field (original format)
- **Gen 2/3**: Uses `agent_type:` field (newer format)
- **Underscore variant**: Files with `_` in name (e.g., `dart_engineer.md`) -- parallel to hyphenated Gen 1 counterpart
- **-agent variant**: Files with `-agent` suffix (e.g., `ops-agent.md`) -- parallel to bare Gen 1 counterpart

### Anomaly

`memory-manager-agent.md` has the `-agent` suffix naming pattern typical of Gen 2/3 files, but uses the `type:` field (Gen 1 format). Value: `memory_manager`.

---

## 3. Known Bug Documentation

### Crash Bug: `agent_management_service.py` line 444

**File**: `src/claude_mpm/services/agents/management/agent_management_service.py`

**Code at line 444**:

```python
metadata = AgentMetadata(
    type=AgentType(post.metadata.get("type", "core")),
    ...
)
```

**The `AgentType` enum** (from `src/claude_mpm/models/agent_definition.py`):

```python
class AgentType(str, Enum):
    CORE = "core"
    PROJECT = "project"
    CUSTOM = "custom"
    SYSTEM = "system"
    SPECIALIZED = "specialized"
```

**Bug**: `AgentType(value)` raises `ValueError` for any value not in `{core, project, custom, system, specialized}`. The vast majority of agent files use values like `engineer`, `ops`, `qa`, `research`, `documentation`, `security`, `product`, `analysis`, `content`, `refactoring`, `imagemagick`, `memory_manager`, `claude-mpm` -- none of which are valid enum members.

**Impact**: Loading any of the 45 out of 48 `type:` files with non-enum-compatible values will crash. The 27 `agent_type:` files are also affected because the parser reads `post.metadata.get("type", "core")` -- it looks for the `type` key, NOT `agent_type`. For `agent_type:` files, `type` is not present in frontmatter, so it defaults to `"core"`, which happens to be valid. This means Gen 2/3 files accidentally avoid the crash by virtue of not having a `type` key.

**Dual bug**:
1. The enum cannot represent real agent role values (engineer, ops, qa, etc.)
2. The parser only reads `type`, not `agent_type`, so the newer field name is silently ignored

**Resolution**: Scheduled for Phase 2 of the migration plan.

---

## 4. Hardcoded Agent Name References

### Location 1: `agent_check.py` (lines 156-161)

**File**: `src/claude_mpm/services/diagnostics/checks/agent_check.py`

```python
# Check for required core agents
core_agents = [
    "research-agent.md",
    "engineer.md",
    "qa-agent.md",
    "documentation-agent.md",
]
```

**Purpose**: Diagnostics check that validates core agents are deployed.

**Hardcoded names**: `research-agent.md`, `engineer.md`, `qa-agent.md`, `documentation-agent.md`

---

### Location 2: `git_source_sync_service.py` (lines 759-771)

**File**: `src/claude_mpm/services/agents/sources/git_source_sync_service.py`

```python
# Fallback to known agent list if API fails
logger.debug("Using fallback agent list")
return [
    "research-agent.md",
    "engineer.md",
    "qa-agent.md",
    "documentation-agent.md",
    "web-qa-agent.md",
    "security.md",
    "ops.md",
    "ticketing.md",
    "product_owner.md",
    "version_control.md",
    "project_organizer.md",
]
```

**Purpose**: Fallback agent list when GitHub API is unavailable.

**Hardcoded names**: 11 agent filenames. Note mixed naming conventions: some use `-agent` suffix, some use `_` (underscores), some are bare names.

**Issue**: `version_control.md` and `project_organizer.md` do not exist in the current `.claude/agents/` directory. The actual files are `version-control.md` and `project-organizer.md` (hyphens, not underscores). This is a pre-existing bug.

---

### Location 3: `todo_task_tools.py` (lines 50-59)

**File**: `src/claude_mpm/services/framework_claude_md_generator/section_generators/todo_task_tools.py`

```python
**Required format (Claude Code expects these exact values from deployed agent YAML names):**
- `subagent_type="research-agent"` - For investigation and analysis
- `subagent_type="engineer"` - For coding and implementation
- `subagent_type="qa-agent"` - For testing and quality assurance
- `subagent_type="documentation-agent"` - For docs and guides
- `subagent_type="security-agent"` - For security assessments
- `subagent_type="ops-agent"` - For deployment and infrastructure
- `subagent_type="version-control"` - For git and version management
- `subagent_type="data-engineer"` - For data processing and APIs
- `subagent_type="pm"` - For project management coordination
- `subagent_type="test_integration"` - For integration testing
```

**Purpose**: PM delegation matrix -- defines which agent names the PM agent can use when delegating tasks via the Task tool.

**Hardcoded names**: 10 agent identifiers used as `subagent_type` values. Note: this is content in a generated CLAUDE.md section, not Python logic, but it establishes the canonical delegation names.

---

## 5. Branch Strategy

```
Branch: agenttype-enums (current, all work here)
Strategy: Per-phase commits with clear commit messages

  Phase 0: Tests and baseline (this commit)
    - Integration tests for field consistency
    - This baseline snapshot document
    - Branch strategy documentation

  Phase 1: Archive cleanup
    - Remove or archive deprecated agent file variants

  Phase 2: Bug fix
    - Fix AgentType enum crash at agent_management_service.py:444
    - Make parser handle both `type` and `agent_type` fields

  Phase 3: Field standardization
    - Standardize on `agent_type` across all agent files

  Phase 4: Frontmatter migration
    - Migrate remaining `type:` fields to `agent_type:`

  Phase 5: Verification
    - Run integration tests to confirm migration
    - Verify all agents load without errors
```

**Simplified from original plan**: The original Phase 6 implementation plan proposed per-phase sub-branches. This has been simplified to per-phase commits on a single branch (`agenttype-enums`) since this is a single-contributor workflow.

---

## 6. Corrections from Devil's Advocate Review

### Correction 1: Actual file counts

The Phase 6 implementation plan stated "48 `type:` + 27 `agent_type:`". The actual verified counts are:

- **48 files** using `type:` in frontmatter (confirmed, matches plan)
- **27 files** using `agent_type:` in frontmatter (confirmed, matches plan)
- **75 total** agent files

The plan's stated count of "48+27" is correct. The earlier review suggesting "49 `type:`" was incorrect; 48 is the accurate number.

### Correction 2: Baseline grep command needs frontmatter-aware extraction

A naive `grep -c 'type:' .claude/agents/*.md` would match:
- Both `type:` and `agent_type:` (since `agent_type` contains `type`)
- Content-body occurrences (e.g., documentation mentioning "type:")
- YAML values that happen to contain "type:"

The correct approach uses frontmatter-aware parsing: extract only content between the first two `---` markers, then match `^type:` or `^agent_type:` at the start of a line. This baseline document used that approach via:

```bash
awk '/^---$/{n++;next} n==1{print} n==2{exit}' "$file"
```

### Correction 3: Phase 0 cannot verify agent_management_service loading

The crash bug at line 444 means that calling `_parse_agent_markdown()` on most Gen 1 agent files will raise `ValueError`. Phase 0 tests should verify the CURRENT (broken) state, not expect successful loading. The loading verification is deferred to Phase 5, after the bug fix in Phase 2.

### Correction 4: Per-phase sub-branches simplified to per-phase commits

The original plan proposed creating sub-branches like `agenttype-enums/phase-1`, `agenttype-enums/phase-2`, etc. For a single-contributor workflow, this adds unnecessary complexity. Simplified to per-phase commits on the single `agenttype-enums` branch with clear conventional commit messages (e.g., `fix: resolve AgentType enum crash for Phase 2`).

### Pre-existing Bug: Stale filenames in git_source_sync_service.py

The fallback agent list at `git_source_sync_service.py:769-771` references `version_control.md` and `project_organizer.md` (with underscores), but the actual filenames are `version-control.md` and `project-organizer.md` (with hyphens). This is a pre-existing bug unrelated to the `type`/`agent_type` migration but discovered during baseline analysis.

---

*Generated by: Research agent (Phase 0.2 baseline capture)*
*Method: Frontmatter-aware parsing of all 75 `.claude/agents/*.md` files*
*Source code inspection of 4 key files for bug and hardcoded reference documentation*
