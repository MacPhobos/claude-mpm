# Agent Naming Standardization: Phased Implementation Plan v7

**Date**: 2026-03-04
**Branch**: agenttype-enums
**Prerequisite**: analysis-v6 (unified analysis + empirical test)

---

## Design Decisions (Settled)

| Question | Decision | Rationale |
|----------|----------|-----------|
| Q1: subagent_type resolution | `name:` field (PROVEN) | Empirical test: stem rejected, name accepted |
| Q2: Canonical format | **Hyphens** | Matches `agent_registry.py`, `skill_to_agent_mapping.yaml`, web conventions |
| Q3: `-agent` suffix | **Do NOT add** when normalizing | Keep `normalize_deployment_filename()` stripping behavior. Don't touch existing `-agent` files this phase |
| Q4: Memory file naming | **Leave as-is** | Not named after agent IDs |
| Q5: `name:` field values | **NEVER CHANGE** | Empirical: changing breaks PM delegation with no fallback |
| Q7: nestjs-engineer invisible | **Defer** | YAML parse failure, fix in separate PR |
| Q8: Duplicate `name:` values | **Defer** | 5 collision pairs, fix in separate PR |
| Q9: Case sensitivity | **Leave as-is** | No enforcement, any format works |

### What Changes vs What Stays

| Element | Changes? | Current → Target |
|---------|----------|------------------|
| Filenames (`.claude/agents/`) | **YES** | `golang_engineer.md` → `golang-engineer.md` |
| `agent_id` frontmatter | **YES** | `golang_engineer` → `golang-engineer` |
| `agent_capabilities.yaml` keys | **YES** | `golang_engineer:` → `golang-engineer:` |
| Normalization canonical | **YES** | Underscore → Hyphen |
| `name:` frontmatter | **NO** | `Golang Engineer` stays |
| `agent_type:` frontmatter | **NO** | `engineer` stays |
| Hook checks | **NO** | Check `agent_type`, not filenames |
| `tool_access_control.py` | **NO** | Checks `agent_type`, not filenames |
| Memory files | **NO** | Named after display names |

---

## Phase 1: Fix Pre-existing Bugs

**Goal**: Fix things that are already broken. No rename. Safe to commit independently.
**Risk**: LOW — fixes existing bugs without changing any naming conventions.

### 1.1 Fix `scripts/bump_agent_versions.py`

**Problem**: Hardcoded list of agent names (mixed underscore/hyphen) targeting `.json` files that DON'T EXIST. Hardcoded path to `/Users/masa/...`. Script is completely non-functional.

**File**: `scripts/bump_agent_versions.py`

**Fix**: Rewrite to use dynamic filesystem discovery:
```python
AGENTS_DIR = Path(__file__).parent.parent / "src" / "claude_mpm" / "agents" / "templates"

def discover_agents(agents_dir: Path) -> list[str]:
    """Discover agent template files dynamically."""
    return [f.stem for f in agents_dir.glob("*.json") if f.is_file()]
```

**Note**: Since no `.json` files exist in the templates directory, this script may be entirely dead code. Consider deprecating or removing it.

### 1.2 Fix `todo_task_tools.py` — Wrong `subagent_type` Values

**Problem**: Claims `subagent_type="research-agent"` is correct. Empirical test proves the actual valid value is `"Research"` (the `name:` field). All values in this file are WRONG.

**File**: `src/claude_mpm/services/framework_claude_md_generator/section_generators/todo_task_tools.py`

**Fix**: Replace ALL `subagent_type` values with actual `name:` field values from deployed agents:

| Current (WRONG) | Correct (`name:` field) |
|-----------------|------------------------|
| `"research-agent"` | `"Research"` |
| `"engineer"` | `"Engineer"` |
| `"qa-agent"` | `"QA"` |
| `"documentation-agent"` | `"Documentation Agent"` |
| `"security-agent"` | `"Security"` |
| `"ops-agent"` | `"Ops"` |
| `"version-control"` | `"Version Control"` |
| `"data-engineer"` | `"Data Engineer"` |
| `"pm"` | Keep `"pm"` (unclear — verify) |

Also fix the ❌ "WRONG" examples and ✅ "correct" examples to match actual behavior.

### 1.3 Fix `content_formatter.py` Fallback Capabilities

**Problem**: Same issue as 1.2 — fallback capabilities list uses wrong `subagent_type` values.

**File**: `src/claude_mpm/core/framework/formatters/content_formatter.py` (lines 262-278)

**Fix**: Replace all parenthesized IDs with actual `name:` field values:
```
- **Engineer** (`Engineer`): Code implementation...
- **Research** (`Research`): Investigation and analysis
- **QA** (`QA`): Testing and quality assurance
...
```

### 1.4 Fix `capability_generator.py` Fallback Capabilities

**File**: `src/claude_mpm/core/framework/formatters/capability_generator.py` (lines 351-367)

**Fix**: Same as 1.3 — update fallback list to use `name:` field values.

### 1.5 Dead Code Cleanup: `templates/__init__.py`

**Problem**: `AGENT_TEMPLATES` dict references files like `documentation_agent.md`, `engineer_agent.md` etc. that DON'T EXIST in the templates directory. `get_template_path()`, `load_template()`, `get_available_templates()` always return None/empty.

**Files**:
- `src/claude_mpm/agents/templates/__init__.py`
- `src/claude_mpm/agents/agent_loader.py` (uses these)
- `src/claude_mpm/agents/__init__.py` (re-exports)

**Fix**: Mark as deprecated with warnings, or remove if no callers depend on return values. Check `agent_loader.py` usage first.

### Phase 1 Verification
```bash
make test  # Full test suite should pass
# Manually verify: content_formatter fallback shows correct name: values
# Manually verify: todo_task_tools generates correct subagent_type values
```

---

## Phase 2: Unify Normalization to Hyphen-Canonical

**Goal**: Make the normalization system produce hyphens consistently while still accepting underscore input.
**Risk**: MEDIUM — changes internal normalization output. Tests will need updating.
**Dependency**: None (can be done independently of Phase 1).

### 2.1 Update `agent_name_normalizer.py`

**File**: `src/claude_mpm/core/agent_name_normalizer.py`

**Changes**:

a) **`normalize()` method** (line ~262): Change to produce hyphens:
```python
# BEFORE: cleaned = cleaned.replace("-", "_").replace(" ", "_")
# AFTER:  cleaned = cleaned.replace("_", "-").replace(" ", "-")
```

b) **`CANONICAL_NAMES` dict keys**: Update from underscore to hyphen:
```python
# BEFORE: "version_control": "Version Control"
# AFTER:  "version-control": "Version Control"
```

c) **`ALIASES` dict target values**: Update to point to hyphen keys:
```python
# BEFORE: "version control": "version_control"
# AFTER:  "version control": "version-control"
```

d) **`to_key()` method** (line ~321): Update to produce hyphens:
```python
# BEFORE: return normalized.lower().replace(" ", "_")
# AFTER:  return normalized.lower().replace(" ", "-")
```

e) **`to_task_format()` / `from_task_format()`**: Since canonical IS now hyphen format, `to_task_format()` becomes a no-op (or just `return self.to_key()`). `from_task_format()` can accept hyphens directly.

### 2.2 Verify `agent_registry.py` is Already Correct

**File**: `src/claude_mpm/core/agent_registry.py`

**Already uses hyphen-canonical** via `normalize_agent_id()` (line ~594):
```python
normalized = normalized.replace("_", "-")
```

**No changes needed.** Just verify `AGENT_ALIASES` dict values are already hyphen format.

### 2.3 Update `tool_access_control.py` Normalization

**File**: `src/claude_mpm/core/tool_access_control.py`

**Line 74 normalization**: Currently converts to underscores:
```python
agent_type = agent_type.lower().replace(" ", "_").replace("-", "_")
```

**Change to hyphens**:
```python
agent_type = agent_type.lower().replace(" ", "-").replace("_", "-")
```

**Update AGENT_RESTRICTIONS dict keys** (lines 44-55):
```python
# BEFORE: "version_control": AGENT_TOOLS, "data_engineer": AGENT_TOOLS
# AFTER:  "version-control": AGENT_TOOLS, "data-engineer": AGENT_TOOLS
```

### 2.4 Update `agent_session_manager.py` Dict Keys

**File**: `src/claude_mpm/core/agent_session_manager.py` (lines 189-194)

**Update initialization_prompts dict keys**:
```python
# BEFORE: "data_engineer": "You are the Data Engineer Agent..."
# AFTER:  "data-engineer": "You are the Data Engineer Agent..."
```

### 2.5 Update Test Files

**Files**:
- `tests/test_agent_name_normalization.py`
- `tests/test_agent_name_formats.py`
- `tests/test_agent_name_consistency.py`
- Any other test files with hardcoded underscore assertions

**Fix**: Update expected output values from underscore to hyphen canonical:
```python
# BEFORE: ("version_control", "Version Control")
# AFTER:  ("version-control", "Version Control")
```

### Phase 2 Verification
```bash
make test  # Tests pass with updated assertions
# Verify: normalize("version_control") → "version-control"
# Verify: normalize("python-engineer") → "python-engineer" (idempotent)
# Verify: to_key("Python Engineer") → "python-engineer"
```

---

## Phase 3: Rename Files + Update Config

**Goal**: Rename the 14 underscore-named files to hyphen format. Update config to match.
**Risk**: HIGH — must be atomic with Phase 4. DO NOT commit without Phase 4.
**Dependency**: Phase 2 must be complete (normalization produces hyphens).

### 3.1 Rename Deployed Agent Files

**Directory**: `.claude/agents/`

**14 files to rename** (underscore → hyphen):

| Current Filename | New Filename | `name:` Field (UNCHANGED) |
|-----------------|-------------|--------------------------|
| `dart_engineer.md` | `dart-engineer.md` | `Dart Engineer` |
| `golang_engineer.md` | `golang-engineer.md` | `Golang Engineer` |
| `java_engineer.md` | `java-engineer.md` | `Java Engineer` |
| `nestjs_engineer.md` | `nestjs-engineer.md` | `nestjs-engineer` |
| `nextjs_engineer.md` | `nextjs-engineer.md` | `Nextjs Engineer` |
| `php_engineer.md` | `php-engineer.md` | `Php Engineer` |
| `product_owner.md` | `product-owner.md` | `Product Owner` |
| `react_engineer.md` | `react-engineer.md` | `React Engineer` |
| `real_user.md` | `real-user.md` | `real-user` |
| `ruby_engineer.md` | `ruby-engineer.md` | `Ruby Engineer` |
| `rust_engineer.md` | `rust-engineer.md` | `Rust Engineer` |
| `svelte_engineer.md` | `svelte-engineer.md` | `Svelte Engineer` |
| `tauri_engineer.md` | `tauri-engineer.md` | `Tauri Engineer` |
| `visual_basic_engineer.md` | `visual-basic-engineer.md` | `Visual Basic Engineer` |

**Files NOT touched this phase** (deferred to Q8):
- All `-agent` suffix files (`research-agent.md`, `qa-agent.md`, etc.)
- Their bare-name counterparts (`research.md`, `qa.md`, etc.)
- Collision pairs resolution

### 3.2 Update Frontmatter `agent_id` Values

For each renamed file, update the `agent_id:` frontmatter value to match the new filename stem:

```yaml
# BEFORE (in golang_engineer.md):
agent_id: golang_engineer

# AFTER (in golang-engineer.md):
agent_id: golang-engineer
```

**CRITICAL**: Do NOT change `name:` values. Do NOT change `agent_type:` values.

### 3.3 Update `agent_capabilities.yaml`

**File**: `src/claude_mpm/config/agent_capabilities.yaml`

**Rename ALL outer keys** from underscore to hyphen. Update `agent_id` inner values to match:

```yaml
# BEFORE:
golang_engineer:
  name: "Golang Engineer"
  agent_id: "golang_engineer"

# AFTER:
golang-engineer:
  name: "Golang Engineer"
  agent_id: "golang-engineer"
```

**Full list of keys to rename**:
- `python_engineer` → `python-engineer`
- `typescript_engineer` → `typescript-engineer`
- `nextjs_engineer` → `nextjs-engineer`
- `golang_engineer` → `golang-engineer`
- `java_engineer` → `java-engineer`
- `rust_engineer` → `rust-engineer`
- `php_engineer` → `php-engineer`
- `ruby_engineer` → `ruby-engineer`
- `svelte_engineer` → `svelte-engineer`
- `react_engineer` → `react-engineer`
- `dart_engineer` → `dart-engineer`
- `javascript_engineer` → `javascript-engineer`
- `visual_basic_engineer` → `visual-basic-engineer`
- `tauri_engineer` → `tauri-engineer`
- `product_owner` → `product-owner`
- `vercel_ops_agent` → `vercel-ops`
- `gcp_ops_agent` → `gcp-ops`
- `local_ops_agent` → `local-ops`
- `digitalocean_ops_agent` → `digitalocean-ops`
- `version_control` → `version-control`
- `data_engineer` → `data-engineer`
- `web_qa` → `web-qa`
- `api_qa` → `api-qa`
- Keys that are ALREADY hyphen or bare: leave unchanged

### 3.4 Update `agents_metadata.py` Dict Keys

**File**: `src/claude_mpm/agents/agents_metadata.py`

**Update `ALL_AGENT_CONFIGS` dict keys** to hyphen format:
```python
# BEFORE: "version_control": VERSION_CONTROL_CONFIG
# AFTER:  "version-control": VERSION_CONTROL_CONFIG
```

### Phase 3 Verification
```bash
# Check no underscore-named .md files remain (except -agent suffix files, deferred)
ls .claude/agents/*_*.md 2>/dev/null  # Should be empty

# Check agent_capabilities.yaml has no underscore keys
grep -E '^[a-z]+_[a-z]+' src/claude_mpm/config/agent_capabilities.yaml  # Should be empty

# Check frontmatter agent_id values are hyphenated
grep 'agent_id:' .claude/agents/*.md | grep '_'  # Should be empty (except existing non-renamed)
```

---

## Phase 4: Fix Stem-Using Code Paths

**Goal**: Ensure all code that extracts `agent_file.stem` normalizes it before use.
**Risk**: MEDIUM — code changes to multiple deployment files.
**Dependency**: MUST be committed WITH Phase 3 (atomic).

### 4.1 Fix `agent_capabilities_service.py`

**File**: `src/claude_mpm/services/agent_capabilities_service.py`

**Line ~224**: Add normalization after stem extraction:
```python
# BEFORE:
agent_id = agent_file.stem

# AFTER:
raw_stem = agent_file.stem
agent_id = raw_stem.lower().replace("_", "-")
if agent_id.endswith("-agent"):
    agent_id = agent_id[:-6]
```

This ensures YAML lookup uses hyphen-format keys matching the updated `agent_capabilities.yaml`.

### 4.2 Fix `ensure_agent_id_in_frontmatter()` — Add `update_existing` Parameter

**File**: `src/claude_mpm/services/agents/deployment_utils.py` (lines 83-132)

**Problem**: Currently skips files that already have `agent_id` field:
```python
if isinstance(parsed, dict) and "agent_id" in parsed:
    return content  # Does NOT update existing agent_id
```

**Fix**: Add `update_existing` parameter:
```python
def ensure_agent_id_in_frontmatter(
    content: str, filename: str, *, update_existing: bool = False
) -> str:
    ...
    if isinstance(parsed, dict) and "agent_id" in parsed:
        if not update_existing:
            return content
        # Update existing agent_id to match normalized filename
        old_id = parsed["agent_id"]
        if old_id != derived_agent_id:
            content = content.replace(
                f"agent_id: {old_id}",
                f"agent_id: {derived_agent_id}"
            )
        return content
```

**Update callers**: `deploy_agent_file()` should pass `update_existing=True` during this migration (or always, to auto-fix stale IDs).

### 4.3 Fix Remaining Deployment Paths

These paths extract `agent_file.stem` without normalization. Add `normalize_deployment_filename()` calls or inline normalization.

**Files and lines** (from exploration):

| File | Line | Current Code | Fix |
|------|------|-------------|-----|
| `single_agent_deployer.py` | 68 | `agent_name = template_file.stem` | Add: `agent_name = template_file.stem.lower().replace("_", "-")` |
| `async_agent_deployment.py` | 264 | `data["_agent_name"] = file_path.stem` | Normalize stem |
| `agent_deployment_context.py` | 43, 73 | `self.agent_name = self.template_file.stem` | Normalize stem |
| `agent_deployment.py` | 478 | `agent_name = template_file_path.stem` | Normalize stem |
| `agent_management_service.py` | 97 | `file_path = target_dir / f"{name}.md"` | Normalize name |
| `deployment_reconciler.py` | 295, 308 | `agent_id = agent_file.stem` | Normalize stem |

**Pattern**: Create a shared helper or use `normalize_deployment_filename()` stem extraction:
```python
def normalize_stem(stem: str) -> str:
    """Normalize agent name stem to hyphen-canonical format."""
    normalized = stem.lower().replace("_", "-")
    if normalized.endswith("-agent"):
        normalized = normalized[:-6]
    return normalized
```

### 4.4 Fix `templates/__init__.py` Dict Keys (if not removed in Phase 1)

If `AGENT_TEMPLATES` was not removed in Phase 1.5:

```python
# BEFORE: "web_qa": "web_qa_agent.md"
# AFTER:  "web-qa": "web-qa-agent.md"  (or whatever the actual filename is)
```

### Phase 4 Verification
```bash
make test  # Full test suite

# Verify deployment pipeline:
# 1. Deploy a test agent with underscore filename
# 2. Verify it deploys with hyphen filename
# 3. Verify old underscore file is cleaned up
```

---

## Phase 5: Verification & Documentation

**Goal**: End-to-end verification and documentation updates.
**Risk**: LOW — read-only verification + documentation.

### 5.1 Full Test Suite

```bash
make test  # All tests pass
```

### 5.2 Empirical Delegation Test

Repeat the empirical test from analysis-v6 to confirm PM delegation still works:

```
Agent(subagent_type="Golang Engineer") → Should succeed
Agent(subagent_type="golang-engineer") → Should fail (expected — stem not used)
Agent(subagent_type="Research") → Should succeed
```

### 5.3 Verify No Duplicate Files

```bash
# Check for underscore-named files that should have been renamed
ls .claude/agents/ | grep '_' | sort
# Expected: only files NOT in the rename list (deferred Q8 items)

# Check for orphaned files
ls .claude/agents/ | wc -l  # Should match pre-rename count (same files, new names)
```

### 5.4 Update PM_INSTRUCTIONS.md

**File**: `src/claude_mpm/agents/PM_INSTRUCTIONS.md`

Standardize all agent name references. Currently uses mixed formats:
- `local-ops` (hyphen, no suffix) — keep, but note actual `subagent_type` is `Local Ops`
- `web-qa-agent` (hyphen + suffix) — update to match `name:` field if different
- `engineer` (bare) — keep, but note actual `subagent_type` is `Engineer`

This is a documentation consistency pass, not a functional change.

### 5.5 Update WORKFLOW.md

**File**: `src/claude_mpm/agents/WORKFLOW.md`

Same consistency pass as PM_INSTRUCTIONS.md.

### Phase 5 Verification
```bash
make test  # Final pass
# Manual: Start a new PM session and verify agent capabilities display correctly
# Manual: Delegate to 2-3 agents and verify they load correctly
```

---

## Files Modified Per Phase

### Phase 1 (5 files)
- `scripts/bump_agent_versions.py`
- `src/claude_mpm/services/framework_claude_md_generator/section_generators/todo_task_tools.py`
- `src/claude_mpm/core/framework/formatters/content_formatter.py`
- `src/claude_mpm/core/framework/formatters/capability_generator.py`
- `src/claude_mpm/agents/templates/__init__.py` (deprecation)

### Phase 2 (5-8 files)
- `src/claude_mpm/core/agent_name_normalizer.py`
- `src/claude_mpm/core/tool_access_control.py`
- `src/claude_mpm/core/agent_session_manager.py`
- `tests/test_agent_name_normalization.py`
- `tests/test_agent_name_formats.py`
- `tests/test_agent_name_consistency.py`
- (possibly other test files with hardcoded assertions)

### Phase 3 (16+ files)
- 14 files in `.claude/agents/` (rename + frontmatter update)
- `src/claude_mpm/config/agent_capabilities.yaml`
- `src/claude_mpm/agents/agents_metadata.py`

### Phase 4 (7 files)
- `src/claude_mpm/services/agent_capabilities_service.py`
- `src/claude_mpm/services/agents/deployment_utils.py`
- `src/claude_mpm/services/agents/deployment/single_agent_deployer.py`
- `src/claude_mpm/services/agents/deployment/async_agent_deployment.py`
- `src/claude_mpm/services/agents/deployment/agent_deployment_context.py`
- `src/claude_mpm/services/agents/deployment/agent_deployment.py`
- `src/claude_mpm/services/agents/deployment/agent_management_service.py`

### Phase 5 (2-3 files)
- `src/claude_mpm/agents/PM_INSTRUCTIONS.md`
- `src/claude_mpm/agents/WORKFLOW.md`
- Test verification (no file changes)

**Total**: ~35-40 files across all phases

---

## Commit Strategy

| Phase | Commit | Can Ship Independently? |
|-------|--------|------------------------|
| Phase 1 | `fix: correct pre-existing agent naming bugs` | ✅ YES |
| Phase 2 | `refactor: unify normalization to hyphen-canonical` | ✅ YES (with test updates) |
| Phase 3+4 | `feat: rename agent files to hyphen format` | ❌ MUST be atomic |
| Phase 5 | `docs: update PM documentation for naming consistency` | ✅ YES |

---

## Deferred Items (Separate PRs)

| Item | Why Deferred | Tracking |
|------|-------------|----------|
| Q7: Fix `nestjs-engineer` YAML parsing | Isolated fix, different root cause | Separate PR |
| Q8: Resolve 5 collision pairs (`-agent` suffix duplicates) | Requires decision on which version to keep per pair | Separate PR after this rename |
| Q9: Case sensitivity standardization | No functional impact, low priority | Backlog |
| Remote cache update | `bobmatnyc/claude-mpm-agents` repo needs same renames | Separate PR to agents repo |
| User migration command | `claude-mpm agents normalize` for user deployments | Feature request |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Phase 3+4 partial application | Single atomic commit; CI must pass before merge |
| Breaking PM delegation | `name:` fields NEVER change; empirical test in Phase 5 |
| Test failures from hardcoded names | Update test assertions in Phase 2 |
| User scripts with hardcoded names | Document in release notes; provide migration guide |
| Deployment recreates underscore files | `normalize_deployment_filename()` already handles this |
| Remote cache sync recreates old files | `deploy_agent_file()` normalizes; `cleanup_legacy=True` removes old |

---

## Success Criteria

1. All 14 underscore-named files renamed to hyphen format
2. No underscore-format keys in `agent_capabilities.yaml`
3. `agent_name_normalizer.py` produces hyphen canonical output
4. `agent_registry.py` and `agent_name_normalizer.py` agree on canonical format
5. All deployment paths normalize stems before use
6. `todo_task_tools.py` and `content_formatter.py` use correct `name:` field values
7. Full test suite passes
8. PM delegation empirical test passes (unchanged behavior)
9. No duplicate agent files in `.claude/agents/`
