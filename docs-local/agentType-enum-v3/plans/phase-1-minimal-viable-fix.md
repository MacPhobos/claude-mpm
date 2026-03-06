# Phase 1: Minimal Viable Fix (MVF)

**Goal**: Fix ALL active delegation failures and critical latent bugs in a single PR.
**Effort**: ~2-3 hours
**Risk**: LOW
**Branch**: `fix/agent-naming-mvf` off `main`
**PR Target**: `main`

---

## Prerequisites

Before starting, verify these assumptions (run on `main`):

```bash
# 1. .claude/agents/ is empty on main (agents deployed at runtime)
ls .claude/agents/ 2>/dev/null | wc -l  # Should be 0

# 2. agent_name_registry.py does NOT exist on main
ls src/claude_mpm/services/agents/agent_name_registry.py 2>/dev/null  # Should not exist

# 3. agents_metadata.py does NOT exist on main
ls src/claude_mpm/core/agents_metadata.py 2>/dev/null  # Should not exist

# 4. Archive directory EXISTS on main
ls src/claude_mpm/agents/templates/archive/*.json | wc -l  # Should be ~39

# 5. CANONICAL_NAMES is in agent_name_normalizer.py, NOT agents_metadata.py
grep -l "CANONICAL_NAMES" src/claude_mpm/core/agent_name_normalizer.py  # Should match

# 6. agent_frontmatter_schema.json does NOT exist on main
find src/ -name "agent_frontmatter_schema.json" 2>/dev/null  # Should be empty
```

---

## Change 1: Fix `agents deploy` Command (Cherry-Pick)

**Source**: Branch commit `e2c9e59c`
**Problem**: `agents deploy` CLI calls `sync_repository()` on wrong object
**Impact**: The CLI deploy command literally doesn't work

### File: `src/claude_mpm/cli/commands/agents.py`

**Lines ~627-632** (the `deploy` subcommand handler):

The issue is on line 632: `sync_result = git_sync.sync_repository(force=force)` — the `git_sync` object (a `GitSourceSyncService`) calls `sync_repository()` which expects `(repo_config, force)` parameters, but is being called with just `(force=force)`.

**Fix**: Cherry-pick commit `e2c9e59c` which corrects the method call to use the proper sync method with the right parameters.

```bash
git cherry-pick e2c9e59c
```

**Verification**:
```bash
# Ensure the deploy command no longer errors
claude-mpm agents deploy --help  # Should not crash
make test  # Run full suite
```

---

## Change 2: Create Agent Name Registry (Cherry-Pick)

**Source**: Branch commit `6ff9727c`
**Problem**: No centralized mapping from agent_id to `name:` field values
**Impact**: Multiple competing hardcoded lists diverge from reality

### New File: `src/claude_mpm/services/agents/agent_name_registry.py`

This is a NEW file that provides the authoritative mapping from `agent_id` → `name:` frontmatter field value. It does NOT exist on main.

```bash
git cherry-pick 6ff9727c
```

**Post cherry-pick verification**:
```bash
# File should exist
ls src/claude_mpm/services/agents/agent_name_registry.py

# Verify the mapping matches actual deployed agent name: values
# (Will be validated by drift-detection test in Change 8)
make test
```

---

## Change 3: Fix PM_INSTRUCTIONS.md and WORKFLOW.md Agent References (Cherry-Pick)

**Source**: Branch commit `f392f54e`
**Problem**: PM references agents by filename stems instead of `name:` field values
**Impact**: PM may send wrong `subagent_type` values, causing delegation failures

### Files Modified:
- `src/claude_mpm/agents/PM_INSTRUCTIONS.md`
- `src/claude_mpm/agents/WORKFLOW.md`

```bash
git cherry-pick f392f54e
```

**Post cherry-pick verification**:
```bash
# Verify no lowercase agent references remain in PM instructions
# (Except in code examples/format descriptions)
grep -n "subagent_type.*\"research\"\|subagent_type.*\"engineer\"\|subagent_type.*\"qa\"" \
  src/claude_mpm/agents/PM_INSTRUCTIONS.md || echo "Clean"

make test
```

**IMPORTANT**: The cherry-pick only fixes PM_INSTRUCTIONS.md and WORKFLOW.md partially.
See Change 10 below for the FULL PM prompt audit that catches remaining issues.

---

## Change 4: Fix CLAUDE_MPM_OUTPUT_STYLE.md Broken References

**Problem**: Two broken agent references in the output style guide
**Impact**: PM delegation fails when triggered by output style guidance

### File: `src/claude_mpm/agents/CLAUDE_MPM_OUTPUT_STYLE.md`

**Line 23**: `local-ops` should be `Local Ops`
```
BEFORE: - Run commands (curl/lsof) → STOP! Delegate to local-ops
AFTER:  - Run commands (curl/lsof) → STOP! Delegate to Local Ops
```

**Line 75**: `Documentation` should be `Documentation Agent`
```
BEFORE: - ❌ `[PM] Update CLAUDE.md` → Delegate to Documentation
AFTER:  - ❌ `[PM] Update CLAUDE.md` → Delegate to Documentation Agent
```

**Implementation**:
```python
# Exact edits needed:
# Line 23: Replace "local-ops" with "Local Ops" (in delegation context only)
# Line 75: Replace "Documentation" with "Documentation Agent"
```

**Verification**:
```bash
# Verify the name: values match actual deployed agents
# Local Ops → name: "Local Ops" in local-ops.md cache file
# Documentation Agent → name: "Documentation Agent" in documentation.md cache file
grep -r "^name:" ~/.claude-mpm/cache/agents/local-ops.md 2>/dev/null
grep -r "^name:" ~/.claude-mpm/cache/agents/documentation.md 2>/dev/null

make test
```

**Guard Rail**: Search for ALL occurrences of `local-ops` and `Documentation` in the file before editing to avoid unintended changes.

---

## Change 5: Fix system_context.py Incorrect Lowercase Guidance

**Problem**: `system_context.py` tells PM that lowercase format works (`"research"`, `"version-control"`)
**Impact**: PM sends wrong `subagent_type` format — Claude Code resolves from `name:` field which is Title Case

### File: `src/claude_mpm/core/system_context.py`

**Lines 19-40** (the `get_system_context()` return string):

Replace the entire agent list and format guidance with correct `name:` field values.

**BEFORE** (lines 19-40):
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
automatically normalize them to lowercase-hyphenated format for the Task tool.

Work efficiently and delegate appropriately to subagents when needed."""
```

**AFTER**:
```python
"""You have access to native subagents via the Task tool with subagent_type parameter.

IMPORTANT: subagent_type MUST match the agent's exact `name:` frontmatter field value.
These are case-sensitive. Examples of correct values:
- "Research" (not "research")
- "Engineer" (not "engineer")
- "QA" (not "qa")
- "Documentation Agent" (not "documentation")
- "Local Ops" (not "local-ops")
- "Version Control" (not "version-control")
- "Data Engineer" (not "data-engineer")
- "Security" (not "security")

Use these agents by calling: Task(description="task description", subagent_type="Research")

Work efficiently and delegate appropriately to subagents when needed."""
```

**Verification**:
```bash
# Verify no lowercase agent names remain in the guidance (except as "not" examples)
grep -n "subagent_type" src/claude_mpm/core/system_context.py

make test
```

**Guard Rail**: This is a string change only. No import changes. No function signature changes.

---

## Change 6: Reconcile CANONICAL_NAMES with Actual `name:` Field Values

**Problem**: `CANONICAL_NAMES` in `agent_name_normalizer.py` produces wrong names for 10 agents
**Impact**: Any code using `AgentNameNormalizer` for delegation-adjacent logic gets wrong names

### File: `src/claude_mpm/core/agent_name_normalizer.py`

**The `CANONICAL_NAMES` dict** (starts ~line 22) needs these 10 corrections:

| Key | Current (WRONG) | Correct (`name:` value) |
|-----|-----------------|------------------------|
| `"documentation"` | `"Documentation"` | `"Documentation Agent"` |
| `"ops"` | `"Ops"` | `"Ops"` (keep — matches upstream) |
| `"ticketing"` | `"Ticketing"` | `"ticketing_agent"` |
| `"tmux"` | `"Tmux"` | `"Tmux Agent"` |
| `"content"` | `"Content"` | `"Content Optimization"` |
| `"web_ui"` | `"Web UI"` | `"Web UI"` (keep — matches upstream) |
| `"tavily_research"` | `"Research"` | Remove (alias, not a real agent) |

**Additionally, add missing agents**:
```python
"nestjs_engineer": "nestjs-engineer",  # Non-conforming upstream name
"aws_ops": "aws_ops_agent",  # Non-conforming upstream name
"mpm_agent_manager": "mpm_agent_manager",  # Non-conforming upstream name
"mpm_skills_manager": "mpm_skills_manager",  # Non-conforming upstream name
"real_user": "real-user",  # Non-conforming upstream name
"data_scientist": "Data Scientist",
"digitalocean_ops": "Digitalocean Ops",
"visual_basic_engineer": "Visual Basic Engineer",
```

**Key Principle**: The 6 non-conforming upstream `name:` values (snake_case and kebab-case) MUST be preserved exactly. These are set in the upstream `claude-mpm-agents` git repository and we do NOT modify them.

The non-conforming values are:
1. `ticketing_agent` (snake_case)
2. `aws_ops_agent` (snake_case)
3. `mpm_agent_manager` (snake_case)
4. `mpm_skills_manager` (snake_case)
5. `nestjs-engineer` (kebab-case)
6. `real-user` (kebab-case)

**Verification**:
```bash
# Verify all CANONICAL_NAMES values match actual deployed name: fields
# Cross-reference with cache:
for f in ~/.claude-mpm/cache/agents/*.md; do
  name=$(grep "^name:" "$f" | head -1 | sed 's/^name: *//' | tr -d '"')
  echo "$(basename $f .md) → $name"
done

make test
```

---

## Change 7: Delete `templates/archive/` Directory

**Problem**: 39 dead JSON templates in archive create confusion and test complexity
**Impact**: Dead code only — no runtime consumers (verified by searching for `archive` imports)

### Directory: `src/claude_mpm/agents/templates/archive/`

**Pre-deletion verification** (MANDATORY):
```bash
# Verify no code imports from archive
grep -rn "templates/archive\|templates.archive" src/claude_mpm/ --include="*.py" | grep -v __pycache__
# Should return 0 results

# Verify local_template_manager.py doesn't reference archive
grep -n "archive" src/claude_mpm/services/agents/loading/local_template_manager.py
# Should return 0 results

# Verify no recursive glob (rglob) discovers archive JSON files
grep -rn "rglob.*json\|glob.*\*\*.*json" src/claude_mpm/ --include="*.py" | grep -v __pycache__
# Should return 0 results for templates-related code
```

**WHY archive is safe to delete** (proven by code analysis on main):
1. `AgentDiscoveryService.list_available_agents()` uses `self.templates_dir.glob("*.md")` — flat glob, `.md` only. Archive contains `.json` files, so they are NOT discovered.
2. `AgentDiscoveryService.get_filtered_templates()` delegates to `list_available_agents()` — same `.md` glob constraint.
3. `multi_source_deployment_service.py` uses `AgentDiscoveryService` for all 4 tiers — same `.md` glob constraint.
4. `SingleAgentDeployer` receives `template_file` from the discovery service — it never discovers files itself.
5. `agent_template_builder.py` CAN read `.json` files (line 365), but it only receives paths from the deployer, which only receives paths from discovery (`.md` only).
6. No code uses `rglob` or `**/*.json` patterns on the templates directory.
7. Conclusion: archive `.json` files have zero discovery path. Deletion is safe.

**Deletion**:
```bash
git rm -r src/claude_mpm/agents/templates/archive/
```

**Also clean up any references**:
```bash
# Search for any remaining archive references
grep -rn "archive" src/claude_mpm/agents/ --include="*.py" --include="*.json" --include="*.md"
# Clean up any found references
```

**Verification**:
```bash
# Ensure no import errors
python -c "import claude_mpm"

make test
```

---

## Change 8: Add Drift-Detection Test

**Problem**: Hardcoded name maps go stale over time (proven by CANONICAL_NAMES divergence)
**Impact**: Prevents future regressions

### New File: `tests/test_agent_name_drift.py`

```python
"""Test that agent name mappings stay in sync with deployed agents.

This test reads all .md files from the agent cache and verifies
that CANONICAL_NAMES and the agent_name_registry both match
the actual name: frontmatter field values.
"""

import re
from pathlib import Path

import pytest
import yaml

from claude_mpm.core.agent_name_normalizer import AgentNameNormalizer


def _get_cached_agents():
    """Read all cached agent files and extract name: field values."""
    cache_dir = Path.home() / ".claude-mpm" / "cache" / "agents"
    if not cache_dir.exists():
        pytest.skip("Agent cache not available")

    agents = {}
    for md_file in sorted(cache_dir.glob("*.md")):
        content = md_file.read_text()
        # Extract YAML frontmatter
        match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1))
                if isinstance(frontmatter, dict) and "name" in frontmatter:
                    agents[md_file.stem] = frontmatter["name"]
            except yaml.YAMLError:
                pass
    return agents


class TestCanonicalNamesDrift:
    """Verify CANONICAL_NAMES matches reality."""

    def test_canonical_names_match_deployed(self):
        """Every CANONICAL_NAMES entry must match actual name: field."""
        cached = _get_cached_agents()
        if not cached:
            pytest.skip("No cached agents found")

        mismatches = []
        for key, canonical_value in AgentNameNormalizer.CANONICAL_NAMES.items():
            # Convert underscore key to dash for filename lookup
            filename_key = key.replace("_", "-")
            if filename_key in cached:
                actual_name = cached[filename_key]
                if canonical_value != actual_name:
                    mismatches.append(
                        f"  {key}: CANONICAL='{canonical_value}' vs ACTUAL='{actual_name}'"
                    )

        assert not mismatches, (
            f"CANONICAL_NAMES drift detected ({len(mismatches)} mismatches):\n"
            + "\n".join(mismatches)
        )

    def test_no_unknown_canonical_entries(self):
        """CANONICAL_NAMES should not have entries for non-existent agents."""
        cached = _get_cached_agents()
        if not cached:
            pytest.skip("No cached agents found")

        # Build set of all valid agent keys (both dash and underscore variants)
        valid_keys = set()
        for stem in cached:
            valid_keys.add(stem)
            valid_keys.add(stem.replace("-", "_"))

        # Known aliases that don't map 1:1 to files
        known_aliases = {"tavily_research", "architect", "pm"}

        unknown = []
        for key in AgentNameNormalizer.CANONICAL_NAMES:
            if key not in valid_keys and key not in known_aliases:
                unknown.append(key)

        assert not unknown, (
            f"CANONICAL_NAMES has entries for non-existent agents: {unknown}"
        )
```

**Verification**:
```bash
uv run pytest tests/test_agent_name_drift.py -v
make test
```

---

## Change 9: Fix `agent_frontmatter_schema.json` Name Pattern (if exists)

**Problem**: Schema requires lowercase `name` pattern `^[a-z][a-z0-9_-]*` but agents use Title Case
**Impact**: Schema enforcement would break all agents
**Condition**: Only apply if this file exists on main

### File: `src/claude_mpm/agents/agent_frontmatter_schema.json` (if present)

**Pre-check**:
```bash
find src/ -name "agent_frontmatter_schema.json" 2>/dev/null
```

If NOT found on main: Skip this change entirely (the file was created on the branch).

If found: Update the `name` pattern to allow Title Case, snake_case, and kebab-case:
```json
"name": {
  "type": "string",
  "description": "Human-readable display name for the agent",
  "pattern": "^[A-Za-z][A-Za-z0-9_ -]*$"
}
```

**Verification**:
```bash
# If file exists, validate JSON is still valid
python -c "import json; json.load(open('src/claude_mpm/agents/agent_frontmatter_schema.json'))"
make test
```

---

## Change 10: Full PM Prompt Audit (AMENDMENT — addresses incomplete audit)

**Problem**: Cherry-pick (Change 3) only fixes PM_INSTRUCTIONS.md and some WORKFLOW.md references. At least 6 additional files contain wrong agent references using filename stems instead of `name:` field values. These files are loaded into PM context and directly affect delegation behavior.

**Impact**: PM may use `local-ops-agent`, `version-control`, `api-qa`, etc. as `subagent_type` values — all will fail Claude Code resolution.

### Discovery command:
```bash
# Find ALL wrong agent references across PM prompt files
grep -rn "local-ops\|version-control\|api-qa\|web-qa\|local.ops.agent" \
  src/claude_mpm/agents/ --include="*.md" | grep -v archive | grep -v "name:"
```

### Files and fixes:

**A. `src/claude_mpm/agents/WORKFLOW.md`** (residual issues after cherry-pick):

| Line | Wrong | Correct |
|------|-------|---------|
| 38 | `api-qa (APIs), web-qa (UI), qa (general)` | `API QA (APIs), Web QA (UI), QA (general)` |
| 43 | `use api_qa` | `use "API QA"` |
| 44 | `use web_qa` | `use "Web QA"` |
| 45 | `use qa` | `use "QA"` |
| 111 | `local-ops` | `Local Ops` |
| 113 | `local-ops agent` | `Local Ops` |
| 115 | `local-ops agent` | `Local Ops` |

**B. `src/claude_mpm/agents/templates/pm-examples.md`**:

Replace ALL occurrences of `local-ops-agent` with `Local Ops` (~10 occurrences on lines 39, 245, 252, 253, 271, 272, 286, 299, 302, 306).

**C. `src/claude_mpm/agents/templates/pr-workflow-examples.md`**:

Replace ALL occurrences of `version-control` with `Version Control` (~8 occurrences on lines 5, 29, 30, 36, 37, 87, 88, 99, 100, 112).

**D. `src/claude_mpm/agents/templates/circuit-breakers.md`**:

| Line | Wrong | Correct |
|------|-------|---------|
| 58 | `Research agent` | `Research` |
| 63 | `Research agent` | `Research` |

**E. `src/claude_mpm/agents/BASE_AGENT.md`**:

| Line | Wrong | Correct |
|------|-------|---------|
| 78 | `Documentation` | `Documentation Agent` |

**F. `src/claude_mpm/agents/templates/README.md`**:

| Line | Wrong | Correct |
|------|-------|---------|
| 154 | `local-ops-agent` | `Local Ops` |

### Verification:
```bash
# After all fixes, this should return ZERO results:
grep -rn "local-ops-agent\|local-ops\b\|version-control\b\|api-qa\b\|web-qa\b" \
  src/claude_mpm/agents/ --include="*.md" | grep -v archive | grep -v "name:" | grep -v "\.md:.*#"
# Exceptions: Markdown headers/anchors may contain hyphens — review manually

make test
```

**Guard Rail**: Each file must be reviewed to ensure references in code EXAMPLES (which show format, not delegation) are distinguished from references that PM uses for actual delegation. Only fix the delegation-relevant references.

---

## Commit Strategy

All 10 changes in a SINGLE commit (or 3 cherry-picks + 1 fresh commit):

```bash
# On main branch:
git checkout main
git checkout -b fix/agent-naming-mvf

# Cherry-picks (3 clean commits from agenttype-enums branch)
git cherry-pick e2c9e59c   # agents deploy fix
git cherry-pick 6ff9727c   # agent_name_registry.py
git cherry-pick f392f54e   # PM_INSTRUCTIONS.md + WORKFLOW.md fixes

# Fresh changes (Changes 4-9)
# ... apply edits ...
git add -A
git commit -m "fix: reconcile agent naming across PM prompts, normalizer, and output style

- Fix CLAUDE_MPM_OUTPUT_STYLE.md broken agent references (local-ops→Local Ops, Documentation→Documentation Agent)
- Fix system_context.py incorrect lowercase guidance (must use exact name: field values)
- Reconcile CANONICAL_NAMES with actual deployed name: values (10 corrections)
- Delete templates/archive/ (39 dead JSON files, no runtime consumers)
- Add drift-detection test to prevent future CANONICAL_NAMES divergence
- Fix agent_frontmatter_schema.json name pattern if present
- Full PM prompt audit: fix 6+ files with wrong agent references (WORKFLOW.md residuals,
  pm-examples.md, pr-workflow-examples.md, circuit-breakers.md, BASE_AGENT.md, README.md)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Full Test Verification

```bash
# 1. Run full test suite
make test

# 2. Run drift detection specifically
uv run pytest tests/test_agent_name_drift.py -v

# 3. Manual delegation smoke test (if possible)
# Deploy agents locally and verify PM can delegate to:
# - "Research" (standard Title Case)
# - "Local Ops" (two words)
# - "Documentation Agent" (with Agent suffix)
# - "ticketing_agent" (non-conforming snake_case)
# - "nestjs-engineer" (non-conforming kebab-case)
```

---

## Rollback Strategy

Each cherry-pick is independently revertable:
```bash
git revert <cherry-pick-commit-hash>
```

The fresh commit is also a single atomic revert:
```bash
git revert <fresh-commit-hash>
```

If the entire PR needs reverting:
```bash
git revert --no-commit <merge-commit-hash>
```

No database migrations. No infrastructure changes. Pure code/text changes. Zero rollback risk.

---

## Success Criteria

1. `agents deploy` CLI command works without errors
2. `CANONICAL_NAMES` values match actual `name:` frontmatter for ALL entries
3. `system_context.py` gives PM correct agent name format guidance
4. `CLAUDE_MPM_OUTPUT_STYLE.md` references correct agent `name:` values
5. `templates/archive/` directory removed
6. Drift-detection test passes and catches future mismatches
7. `make test` passes with no regressions
8. PM can successfully delegate to agents with correct `subagent_type` values
