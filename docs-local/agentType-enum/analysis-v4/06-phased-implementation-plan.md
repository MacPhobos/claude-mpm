# Phased Implementation Plan: Archive Removal

**Date**: 2026-03-03
**Based on**: Holistic Report (05-holistic-report.md) and four research analyses
**Approach**: Incremental phases with independent rollback and test criteria per phase
**Estimated effort**: 1 sprint (4-5 working days)
**Semver impact**: PATCH or MINOR (no breaking changes for consumers)

---

## Overview

```
Phase 0          Phase 1          Phase 2          Phase 3          Phase 4          Phase 5
Pre-flight  -->  Registry    -->  Dead Code   -->  References  -->  Delete      -->  Validate
Validation       Cleanup          Removal          Update           Archive          End-to-End
(no changes)     (1 file)         (5 files)        (4 files)        (git rm)         (testing)
   |                |                |                |                |                |
   v                v                v                v                v                v
 Baseline        Fewer            No behavior      Scripts          Archive          Full
 captured        phantom          change           updated          removed          confidence
                 agents           (was no-ops)                       cleanly
```

**Note**: Routing data migration (previously Phase 3) was removed after verification confirmed
the routing data in 5 archive JSONs was never loaded by any runtime code path — it is dead data.

Each phase is **independently deployable and reversible**.

---

## Phase 0: Pre-flight Validation (No Code Changes)

**Goal**: Establish baseline measurements before any modifications.
**Risk level**: NONE (read-only operations)
**Dependencies**: None

### Changes
None. This phase is purely observational.

### Actions

1. **Run full test suite and capture baseline**
   ```bash
   cd /Users/mac/workspace/claude-mpm-fork
   python -m pytest --tb=short -q 2>&1 | tee docs-local/agentType-enum/analysis-v4/phase0-test-baseline.txt
   ```

2. **Verify git cache is populated and functional**
   ```bash
   # Count cached agents
   find ~/.claude-mpm/cache/agents/ -name "*.md" -not -name "BASE-AGENT.md" -not -name "README.md" -not -name "CHANGELOG.md" | wc -l
   # Expected: 50+ agents

   # Verify cache is readable
   ls ~/.claude-mpm/cache/agents/bobmatnyc/claude-mpm-agents/agents/
   ```

3. **Document current agent count in `.claude/agents/`**
   ```bash
   ls .claude/agents/*.md 2>/dev/null | wc -l
   ```

4. **Snapshot archive contents for reference**
   ```bash
   # Create inventory of archive files
   ls -la src/claude_mpm/agents/templates/archive/*.json | awk '{print $NF}' > docs-local/agentType-enum/analysis-v4/phase0-archive-inventory.txt

   # Extract memory_routing data for comparison
   python3 -c "
   import json, pathlib
   archive = pathlib.Path('src/claude_mpm/agents/templates/archive')
   for f in sorted(archive.glob('*.json')):
       data = json.loads(f.read_text())
       mr = data.get('memory_routing', {})
       routing = data.get('routing', {})
       if mr or routing:
           print(f'{f.name}: memory_routing={bool(mr)}, routing={bool(routing)}')
   " > docs-local/agentType-enum/analysis-v4/phase0-routing-snapshot.txt
   ```

5. **Verify `UnifiedAgentRegistry` agent count (includes archive phantom entries)**
   ```bash
   python3 -c "
   from src.claude_mpm.core.unified_agent_registry import UnifiedAgentRegistry
   registry = UnifiedAgentRegistry()
   registry.discover_agents()
   print(f'Total agents in registry: {len(registry._agents)}')
   " 2>/dev/null || echo "Run via claude-mpm to test registry count"
   ```

### Test Criteria
- [ ] Full test suite passes (baseline captured)
- [ ] Git cache directory exists and contains 50+ `.md` files
- [ ] Archive inventory file created with 39 JSON files listed
- [ ] Routing snapshot captured for 5 agents with `routing` field

### Rollback
N/A — no changes made.

---

## Phase 1: Remove UnifiedAgentRegistry Archive Discovery

**Goal**: Stop `UnifiedAgentRegistry` from discovering 39 phantom JSON agents via `rglob`.
**Risk level**: LOW
**Dependencies**: Phase 0 complete

### Changes

| File | Line | Change |
|------|------|--------|
| `src/claude_mpm/core/unified_agent_registry.py` | ~256 | Add filter to exclude `archive/` subdirectory from `rglob("*")` results |

### Implementation

In `unified_agent_registry.py`, the `_discover_path()` method at line ~256:

**Current code** (01-pipeline-trace:223):
```python
for file_path in path.rglob("*"):
```

**Updated code**:
```python
for file_path in path.rglob("*"):
    # Skip legacy archive directory (JSON templates superseded by git-cached .md agents)
    if "archive" in file_path.parts:
        continue
```

### Test Criteria
- [ ] Full test suite passes
- [ ] `UnifiedAgentRegistry` agent count decreases by ~39 entries
- [ ] Agent listing (`claude-mpm agents list`) shows only git-cached agents
- [ ] No references to archive JSON files in registry output
- [ ] `claude-mpm configure` still works correctly (agents load from git cache)

### Rollback
Revert single file: `git checkout -- src/claude_mpm/core/unified_agent_registry.py`

---

## Phase 2: Clean Up Dead Code Paths

**Goal**: Remove 5 code paths that scan `templates/*.json` and find nothing.
**Risk level**: LOW (these are already no-ops that return empty results)
**Dependencies**: Phase 1 complete

### Changes

| # | File | Lines | Current Behavior | Action |
|---|------|-------|-----------------|--------|
| 2a | `src/claude_mpm/skills/skill_manager.py` | 28-37 | `_load_agent_mappings()` scans `templates/*.json`, finds 0 files, returns empty dict | Remove method body or replace with pass/noop comment |
| 2b | `src/claude_mpm/core/framework/formatters/capability_generator.py` | 294-335 | `load_memory_routing_from_template()` fallback searches `templates/*.json`, finds 0 files | Remove JSON fallback; `.md` frontmatter always provides `memory_routing` |
| 2c | `src/claude_mpm/core/framework/processors/template_processor.py` | 66 | `files("claude_mpm.agents.templates") / f"{agent_name}.json"` — finds 0 files | Remove JSON template loading path |
| 2d | `src/claude_mpm/cli/commands/agent_state_manager.py` | 141 | `templates_dir.glob("*.json")` — finds 0 files | Remove JSON listing iteration |
| 2e | `src/claude_mpm/services/native_agent_converter.py` | 284 | `templates_dir.glob("*.json")` — finds 0 files | Remove JSON scanning code |

### Implementation Details

#### 2a: SkillManager (skill_manager.py:28-37)

**Source**: 03-skill-mapping:188-203

**Current code**:
```python
def _load_agent_mappings(self):
    agent_templates_dir = Path(__file__).parent.parent / "agents" / "templates"
    for template_file in agent_templates_dir.glob("*.json"):
        # ... loads skills from JSON templates
```

**Action**: Remove the JSON scanning logic. Skills are resolved through:
1. `.md` frontmatter `skills:` arrays (primary)
2. `SkillsRegistry.get_skills_for_agent()` (secondary)

The archive JSON `skills` arrays were never loaded due to the path bug.

#### 2b: CapabilityGenerator (capability_generator.py:294-335)

**Source**: 03-skill-mapping:236-242

**Current code**:
```python
def load_memory_routing_from_template(self, agent_name):
    # Searches templates/*.json for memory_routing
    # This NEVER finds anything because JSONs are in archive/ subdirectory
```

**Action**: Remove the JSON fallback. Memory routing is always found in `.md` YAML frontmatter (Step 1 always succeeds per 03-skill-mapping:259-264).

#### 2c: TemplateProcessor (template_processor.py:66)

**Source**: 04-devils-advocate:50-55

**Current code**:
```python
templates_package = files("claude_mpm.agents.templates")
template_file = templates_package / f"{agent_name}.json"
```

**Action**: Remove JSON template loading. No `.json` files exist at the `templates/` root level.

#### 2d: AgentStateManager (agent_state_manager.py:141)

**Source**: 01-pipeline-trace:205-209

**Current code**:
```python
for template_file in sorted(self.templates_dir.glob("*.json")):
```

**Action**: Remove JSON listing. This loop body never executes.

#### 2e: NativeAgentConverter (native_agent_converter.py:284)

**Source**: 04-devils-advocate:292-295

**Current code**:
```python
json_files = list(templates_dir.glob("*.json"))
```

**Action**: Remove JSON scanning. This always returns an empty list.

### Test Criteria
- [ ] Full test suite passes
- [ ] No behavior change observable (these were already no-ops)
- [ ] `claude-mpm configure` works correctly
- [ ] `claude-mpm agents deploy` works correctly
- [ ] Memory routing still functions for all agents
- [ ] Skill binding still functions for all agents
- [ ] No new warnings or errors in logs

### Rollback
Revert the 5 files individually:
```bash
git checkout -- src/claude_mpm/skills/skill_manager.py
git checkout -- src/claude_mpm/core/framework/formatters/capability_generator.py
git checkout -- src/claude_mpm/core/framework/processors/template_processor.py
git checkout -- src/claude_mpm/cli/commands/agent_state_manager.py
git checkout -- src/claude_mpm/services/native_agent_converter.py
```

---

## Phase 3: Update References

**Goal**: Clean up all remaining references to archive directory.
**Risk level**: LOW
**Dependencies**: Phases 1-2 complete

### Changes

| # | File | Line | Change |
|---|------|------|--------|
| 3a | `scripts/delegation_matrix_poc.py` | 20 | Update path from archive to git cache |
| 3b | `scripts/migrate_json_to_markdown.py` | 593 | Remove `--archive` flag and related logic |
| 3c | `.secrets.baseline` | 226-270 | Remove 4 stale archive file entries |
| 3d | `pyproject.toml` | 209 | Remove `_archive` from ruff `exclude` list |
| 3e | `pyproject.toml` | 329 | Remove `archive` from pytest `norecursedirs` |

### Implementation Details

#### 3a: delegation_matrix_poc.py

**Source**: 01-pipeline-trace:176-179

**Current code**:
```python
templates_dir = Path(__file__).parent.parent / "src/claude_mpm/agents/templates/archive"
```

**Updated code**:
```python
# Use git-cached agents as the source of truth
cache_dir = Path.home() / ".claude-mpm" / "cache" / "agents" / "bobmatnyc" / "claude-mpm-agents" / "agents"
```

Also update file discovery from `glob("*.json")` to `rglob("*.md")` with appropriate frontmatter parsing.

#### 3b: migrate_json_to_markdown.py

**Source**: 01-pipeline-trace:179

Remove the `--archive` flag and any logic that moves files to `templates/archive/`. The migration is complete.

#### 3c: .secrets.baseline

Remove entries for:
- `archive/local_ops_agent.json` (04-devils-advocate:252)
- `archive/ops.json` (04-devils-advocate:253)
- `archive/security.json` (04-devils-advocate:254)
- `archive/typescript_engineer.json` (04-devils-advocate:255)

```bash
# After editing .secrets.baseline:
detect-secrets scan --update .secrets.baseline
```

#### 3d-3e: pyproject.toml

**Source**: 04-devils-advocate:209, 329

Remove `_archive` from ruff exclude list (line 209).
Remove `archive` from pytest norecursedirs (line 329).

### Test Criteria
- [ ] Full test suite passes
- [ ] `delegation_matrix_poc.py` runs against cache data (or gracefully handles missing cache)
- [ ] `detect-secrets scan` passes without stale entries
- [ ] `ruff check .` passes
- [ ] `pytest --collect-only` doesn't reference archive

### Rollback
Revert individual files:
```bash
git checkout -- scripts/delegation_matrix_poc.py scripts/migrate_json_to_markdown.py .secrets.baseline pyproject.toml
```

---

## Phase 4: Delete Archive Directory

**Goal**: Remove the archive directory from the repository.
**Risk level**: MEDIUM (irreversible file deletion, though git history preserves content)
**Dependencies**: Phases 1-3 complete and verified

### Changes

```bash
git rm -r src/claude_mpm/agents/templates/archive/
```

This removes:
- 39 JSON agent template files
- 1 README.md documenting the archive

### Pre-deletion Checklist

Before executing `git rm`:

- [ ] Phase 0 baseline tests all pass
- [ ] Phase 1 registry cleanup deployed and verified
- [ ] Phase 2 dead code removal deployed and verified
- [ ] Phase 3 reference updates deployed and verified
- [ ] Archive content snapshot saved (Phase 0)

### Test Criteria
- [ ] `git rm -r` succeeds without errors
- [ ] Full test suite passes
- [ ] `claude-mpm configure` works correctly
- [ ] `claude-mpm agents deploy` succeeds
- [ ] `claude-mpm agents list` shows correct agent set
- [ ] No `FileNotFoundError` or `ModuleNotFoundError` referencing archive
- [ ] No warnings about missing templates in logs
- [ ] `ruff check .` passes
- [ ] `detect-secrets scan` passes

### Rollback

If issues are discovered after deletion:
```bash
# Restore archive from git history
git checkout HEAD~1 -- src/claude_mpm/agents/templates/archive/
```

This restores all archive files from the commit before deletion.

---

## Phase 5: Post-Removal Validation

**Goal**: Comprehensive end-to-end validation that the system works correctly without archive.
**Risk level**: NONE (read-only validation)
**Dependencies**: Phase 4 complete

### Validation Checklist

#### 5.1 Core Functionality

- [ ] **`claude-mpm configure`**: Interactive agent selection works
  ```bash
  claude-mpm configure
  # Verify: Agent list loads, selection works, deployment succeeds
  ```

- [ ] **`claude-mpm agents deploy`**: Deploys all agents from cache
  ```bash
  claude-mpm agents deploy --force
  # Verify: All agents deployed to .claude/agents/
  ```

- [ ] **`claude-mpm agents list`**: Shows correct agent inventory
  ```bash
  claude-mpm agents list
  # Verify: 50+ agents listed, no phantom JSON entries
  ```

- [ ] **`claude-mpm agents sync`**: Sync from GitHub works
  ```bash
  claude-mpm agents sync --force
  # Verify: ETag-based sync completes successfully
  ```

#### 5.2 Skill-to-Agent Mappings

- [ ] Skills are correctly bound to agents via `.md` frontmatter
  ```bash
  claude-mpm skills list
  # Verify: Skills show correct agent associations
  ```

#### 5.3 Memory Routing

- [ ] Memory routing data is available for all agents
  ```bash
  # Verify memory_routing is parsed from .md frontmatter
  python3 -c "
  from pathlib import Path
  import yaml
  cache = Path.home() / '.claude-mpm/cache/agents/bobmatnyc/claude-mpm-agents/agents'
  for md in cache.rglob('*.md'):
      if md.name in ('BASE-AGENT.md', 'README.md', 'CHANGELOG.md'):
          continue
      content = md.read_text()
      if '---' in content:
          fm = content.split('---')[1]
          data = yaml.safe_load(fm)
          mr = data.get('memory_routing')
          if mr:
              print(f'{md.name}: memory_routing OK ({len(mr.get(\"keywords\", []))} keywords)')
  "
  ```

#### 5.4 Full Test Suite

- [ ] Compare test results with Phase 0 baseline
  ```bash
  python -m pytest --tb=short -q 2>&1 | tee docs-local/agentType-enum/analysis-v4/phase5-test-results.txt
  diff docs-local/agentType-enum/analysis-v4/phase0-test-baseline.txt docs-local/agentType-enum/analysis-v4/phase5-test-results.txt
  ```

#### 5.5 Runtime Validation

- [ ] No import errors when starting claude-mpm
- [ ] No `FileNotFoundError` in logs
- [ ] No warnings about missing templates
- [ ] Agent prompts load correctly during Claude Code sessions

### Rollback
If validation fails, restore archive and revert all changes:
```bash
git checkout HEAD~1 -- src/claude_mpm/agents/templates/archive/
# Then selectively revert phases as needed
```

---

## Summary: Phase Comparison

| Phase | Files Changed | Risk | Reversible | Behavior Change |
|-------|--------------|------|------------|-----------------|
| 0 | 0 | None | N/A | None |
| 1 | 1 | Low | Single file revert | Fewer phantom agents in registry |
| 2 | 5 | Low | Per-file revert | None (removing no-ops) |
| 3 | 4-5 | Low | Per-file revert | Script/config cleanup |
| 4 | -40 (deletion) | Medium | `git checkout HEAD~1` | Archive removed |
| 5 | 0 | None | N/A | None (validation only) |

**Total files modified in claude-mpm**: ~11 files changed + 40 files deleted
**Total PRs**: 3-4 (one per phase, phases 0 and 5 are non-code)

**Note**: Routing data migration was evaluated and deemed unnecessary — the routing data in
5 archive JSON files was confirmed as dead data never loaded by any runtime code path.

---

## Appendix: File Reference Quick-Lookup

| File (relative to src/claude_mpm/) | Phase | Action | Source |
|------------------------------------|-------|--------|--------|
| `core/unified_agent_registry.py:256` | 1 | Filter archive from rglob | 01-pipeline-trace:222-228 |
| `skills/skill_manager.py:28-37` | 2 | Remove dead JSON scan | 03-skill-mapping:188-203 |
| `core/framework/formatters/capability_generator.py:294-335` | 2 | Remove dead JSON fallback | 03-skill-mapping:236-242 |
| `core/framework/processors/template_processor.py:66` | 2 | Remove dead JSON loading | 04-devils-advocate:50-55 |
| `cli/commands/agent_state_manager.py:141` | 2 | Remove dead JSON listing | 01-pipeline-trace:205-209 |
| `services/native_agent_converter.py:284` | 2 | Remove dead JSON scanning | 04-devils-advocate:292-295 |
| `scripts/delegation_matrix_poc.py:20` | 3 | Update to use cache | 01-pipeline-trace:176-179 |
| `scripts/migrate_json_to_markdown.py:593` | 3 | Remove --archive flag | 01-pipeline-trace:179 |
| `.secrets.baseline:226-270` | 3 | Remove 4 stale entries | 04-devils-advocate:252-255 |
| `pyproject.toml:209,329` | 3 | Remove archive exclusions | 04-devils-advocate:209,329 |
| `agents/templates/archive/*` | 4 | git rm -r | All sources |
