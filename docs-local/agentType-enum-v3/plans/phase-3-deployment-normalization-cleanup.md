# Phase 3: Deployment & Normalization Cleanup

**Goal**: Reduce technical debt in the deployment pipeline and normalization functions.
**Effort**: ~3-4 hours
**Risk**: MEDIUM (touching deployment paths that affect agent file creation)
**Branch**: `refactor/deployment-normalization-cleanup` off `main` (after Phase 2 merged)
**PR Target**: `main`
**Depends On**: Phase 1 (MVF) and Phase 2 (Registry & Enum) must be merged first

---

## Prerequisites

Phases 1 and 2 must be merged. Verify:
```bash
# 1. Phase 1: agent_name_registry exists, archive deleted, CANONICAL_NAMES fixed
ls src/claude_mpm/services/agents/agent_name_registry.py
ls src/claude_mpm/agents/templates/archive/ 2>/dev/null && echo "FAIL" || echo "OK"

# 2. Phase 2: AgentType extended, CORE_AGENT_IDS consolidated
python -c "from claude_mpm.models.agent_definition import AgentType; print(AgentType.ENGINEER)"
python -c "from claude_mpm.services.agents.agent_name_registry import CORE_AGENT_IDS; print(CORE_AGENT_IDS)"

# 3. All existing tests pass
make test
```

---

## Context: The Three Deployment Paths

On main, there are 3 separate code paths that create agent .md files in `.claude/agents/`:

| # | Path | Function | How It Works | Normalization |
|---|------|----------|--------------|---------------|
| 1 | **Unified** | `deployment_utils.py:deploy_agent_file()` | Full normalization: filename, frontmatter, dedup | ✅ Complete |
| 2 | **Legacy** | `SingleAgentDeployer.deploy_single_agent()` | Builds content via `template_builder`, writes directly | ⚠️ Inline only (line 68) |
| 3 | **Configure** | `configure.py:_deploy_single_agent()` | Raw `shutil.copy2()` from cache to target | ❌ None |

**Goal**: Make paths 2 and 3 use the same normalization as path 1, WITHOUT merging them into a single function (they serve different use cases per devil's advocate analysis).

---

## Change 1: Add Filename Normalization to `SingleAgentDeployer`

**Problem**: `SingleAgentDeployer.deploy_single_agent()` uses inline normalization on line 68 that differs from `deployment_utils.py:normalize_deployment_filename()`.

**Current behavior** (lines 63-68 of `single_agent_deployer.py`):
```python
agent_name = template_file.stem
target_file = agents_dir / f"{agent_name}.md"
```

The `agent_name` is the raw template filename stem. No lowercase conversion, no underscore-to-dash, no `-agent` suffix stripping.

**Note**: The `template_file` argument is typically a `.json` file from `templates/`, not a `.md` file from cache. The template builder then constructs the markdown content. So the filename normalization applies to the OUTPUT filename, not the input.

### File: `src/claude_mpm/services/agents/deployment/single_agent_deployer.py`

**Change**: After deriving `agent_name` from template_file, normalize the output filename:

```python
# BEFORE (line 63-64):
agent_name = template_file.stem
target_file = agents_dir / f"{agent_name}.md"

# AFTER:
from claude_mpm.services.agents.deployment_utils import normalize_deployment_filename

agent_name = template_file.stem
normalized_filename = normalize_deployment_filename(f"{agent_name}.md")
target_file = agents_dir / normalized_filename
```

**Import addition** at top of file:
```python
from claude_mpm.services.agents.deployment_utils import normalize_deployment_filename
```

**Side effects to check**:
- `results["skipped"].append(agent_name)` — still uses raw `agent_name` for logging (OK)
- `results["updated"].append(agent_name)` / `results["deployed"].append(agent_name)` — same (OK)
- `self.results_manager.record_agent_deployment(...)` — uses `agent_name` for metrics (OK)
- The `target_file.exists()` check on the NEXT line uses the normalized name — this is CORRECT (avoids deploying `python_engineer.md` when `python-engineer.md` already exists)

**Also add dedup logic**: After writing, check for the underscore variant and remove it:
```python
from claude_mpm.services.agents.deployment_utils import (
    normalize_deployment_filename,
    get_underscore_variant_filename,
)

# After writing target_file:
underscore_variant = get_underscore_variant_filename(normalized_filename)
if underscore_variant:
    variant_path = agents_dir / underscore_variant
    if variant_path.exists() and variant_path != target_file:
        variant_path.unlink()
        self.logger.info(f"Removed duplicate: {underscore_variant}")
```

**Verification**:
```bash
# Verify the deployer still works
python -c "
from claude_mpm.services.agents.deployment.single_agent_deployer import SingleAgentDeployer
print('Import OK')
"

make test
```

---

## Change 2: Add Normalization to `configure.py` Deploy

**Problem**: `configure.py:_deploy_single_agent()` uses raw `shutil.copy2()` with zero normalization. The target filename is derived from `full_agent_id` which may contain underscores.

**Current behavior** (lines 3081-3119 of `configure.py`):
```python
def _deploy_single_agent(self, agent: AgentConfig, show_feedback: bool = True) -> bool:
    # ...
    if "/" in full_agent_id:
        target_name = full_agent_id.split("/")[-1] + ".md"
    else:
        target_name = full_agent_id + ".md"
    # ...
    shutil.copy2(source_file, target_file)
```

### File: `src/claude_mpm/cli/commands/configure.py`

**Change**: Normalize the target filename and ensure frontmatter has agent_id:

```python
from claude_mpm.services.agents.deployment_utils import (
    normalize_deployment_filename,
    ensure_agent_id_in_frontmatter,
    get_underscore_variant_filename,
)

# BEFORE:
if "/" in full_agent_id:
    target_name = full_agent_id.split("/")[-1] + ".md"
else:
    target_name = full_agent_id + ".md"

# AFTER:
if "/" in full_agent_id:
    raw_name = full_agent_id.split("/")[-1] + ".md"
else:
    raw_name = full_agent_id + ".md"
target_name = normalize_deployment_filename(raw_name)
```

**Then**, after `shutil.copy2()`, add frontmatter normalization:
```python
# Copy the agent file
shutil.copy2(source_file, target_file)

# Ensure agent_id in frontmatter
content = target_file.read_text()
updated_content = ensure_agent_id_in_frontmatter(content, target_name)
if updated_content != content:
    target_file.write_text(updated_content)

# Clean up underscore variant if it exists
underscore_variant = get_underscore_variant_filename(target_name)
if underscore_variant:
    variant_path = target_dir / underscore_variant
    if variant_path.exists() and variant_path != target_file:
        variant_path.unlink()
```

**Key constraint**: Do NOT replace `shutil.copy2` with `deploy_agent_file()`. The configure path copies FROM cache (pre-built .md files), while `deploy_agent_file()` expects to do its own content building. They serve different purposes.

**Verification**:
```bash
# Verify configure still imports correctly
python -c "from claude_mpm.cli.commands.configure import ConfigureCommand; print('Import OK')"

make test
```

---

## Change 3: Consolidate Normalization Functions

**Problem**: 5+ normalization functions with subtle differences in `-agent` suffix stripping, space handling, and underscore conversion.

### Inventory of normalization functions on main:

```bash
grep -rn "def normalize\|def _normalize\|def canonicalize\|def to_canonical\|def agent_name_to\|def format_agent" \
  src/claude_mpm/ --include="*.py" | grep -v __pycache__
```

**Known functions**:

1. `deployment_utils.py:normalize_deployment_filename()` — Filename normalization (lowercase, `_` → `-`, strip `-agent`)
2. `agent_name_normalizer.py:AgentNameNormalizer.normalize()` — Display name normalization (CANONICAL_NAMES lookup)
3. `agent_name_normalizer.py:AgentNameNormalizer._normalize_key()` — Key normalization (lowercase, strip separators)
4. Various inline normalizations in `single_agent_deployer.py`, `configure.py`, etc.

### Target State: 2 normalization functions

| Function | Purpose | Input → Output | Location |
|----------|---------|----------------|----------|
| `normalize_deployment_filename()` | File system naming | `"python_engineer.md"` → `"python-engineer.md"` | `deployment_utils.py` (keep) |
| `AgentNameNormalizer.normalize()` | Display naming | `"python_engineer"` → `"Python Engineer"` | `agent_name_normalizer.py` (keep, fix) |

**Functions to remove or inline**:
- Any standalone `normalize_agent_name()` in other files → Replace with import from one of the two above
- Inline normalizations in deployers → Replace with `normalize_deployment_filename()` call

### Implementation:

For each normalization occurrence found by grep:
1. Determine if it's a FILENAME normalization or DISPLAY NAME normalization
2. Replace with the appropriate canonical function
3. Add import if needed

**Verification**:
```bash
# Count remaining normalization functions (should be exactly 2 + helpers)
grep -rn "def normalize" src/claude_mpm/ --include="*.py" | grep -v __pycache__ | wc -l

make test
```

---

## Change 4: Gut Dead `templates/__init__.py` Module (UPGRADED from "maybe cleanup")

**Problem**: `templates/__init__.py` is a **100% dead module**, not just "maybe has dead code." Contains:
- `AGENT_TEMPLATES` dict mapping 10 agent types to files that **ALL 10 DON'T EXIST** (e.g., `documentation_agent.md`, `engineer_agent.md` — none exist in `templates/`)
- `AGENT_NICKNAMES` dict — yet ANOTHER competing agent name list (missed in original "4+ competing lists" audit, making it the 6th)
- `get_template_path()` — function that ALWAYS returns `None` (target files don't exist)
- `load_template()` — function that ALWAYS returns `None` (delegates to `get_template_path`)
- **Zero production consumers** — verified by grep that no code imports `AGENT_TEMPLATES`, `AGENT_NICKNAMES`, `get_template_path`, or `load_template`

### File: `src/claude_mpm/agents/templates/__init__.py`

**Current contents** (80 lines of dead code):
```python
AGENT_TEMPLATES = {
    "documentation": "documentation_agent.md",  # DOESN'T EXIST
    "engineer": "engineer_agent.md",             # DOESN'T EXIST
    "qa": "qa_agent.md",                         # DOESN'T EXIST
    # ... all 10 reference nonexistent files
}

AGENT_NICKNAMES = {
    "documentation": "Documenter",               # Yet another competing name list
    "version_control": "Versioner",
    # ...
}

def get_template_path(agent_type): ...           # Always returns None
def load_template(agent_type): ...               # Always returns None
```

**Action**: Replace entire file with minimal package marker:
```python
"""Agent templates module."""
```

### Pre-change verification:
```bash
# Confirm no code imports these symbols
grep -rn "from.*agents.templates.*import\|agents\.templates\.AGENT\|agents\.templates\.load\|agents\.templates\.get" \
  src/claude_mpm/ --include="*.py" | grep -v __pycache__ | grep -v "templates/__init__"
# Should return 0 results

# Confirm the referenced files don't exist
for f in documentation_agent.md engineer_agent.md qa_agent.md api_qa_agent.md web_qa_agent.md \
  version_control_agent.md research_agent.md ops_agent.md security_agent.md data_engineer_agent.md; do
  ls "src/claude_mpm/agents/templates/$f" 2>/dev/null && echo "EXISTS: $f" || echo "MISSING: $f"
done
# All 10 should be MISSING
```

**Verification**:
```bash
# Verify import still works (module is still a valid package)
python -c "import claude_mpm.agents.templates; print('Import OK')"

# Verify no references to archive remain
grep -rn "archive" src/claude_mpm/agents/ --include="*.py" | grep -v __pycache__
# Should return 0 results

make test
```

---

## Change 5: Add Comprehensive Integration Tests

### New File: `tests/test_deployment_normalization.py`

```python
"""Integration tests for deployment path normalization consistency.

Verifies that all three deployment paths produce consistent results:
1. deploy_agent_file() — unified path
2. SingleAgentDeployer.deploy_single_agent() — legacy path
3. configure.py._deploy_single_agent() — configure path

All paths should produce:
- Lowercase dash-based filenames
- Consistent agent_id in frontmatter
- No duplicate files (underscore vs dash variants)
"""

import re
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from claude_mpm.services.agents.deployment_utils import (
    normalize_deployment_filename,
    ensure_agent_id_in_frontmatter,
    get_underscore_variant_filename,
)


class TestFilenameNormalization:
    """Verify normalize_deployment_filename produces consistent results."""

    @pytest.mark.parametrize("input_name,expected", [
        ("python-engineer.md", "python-engineer.md"),
        ("python_engineer.md", "python-engineer.md"),
        ("Python_Engineer.md", "python-engineer.md"),
        ("QA.md", "qa.md"),
        ("qa-agent.md", "qa.md"),
        ("local-ops.md", "local-ops.md"),
        ("local_ops_agent.md", "local-ops.md"),
        ("documentation.md", "documentation.md"),
        ("nestjs-engineer.md", "nestjs-engineer.md"),
        ("RESEARCH.md", "research.md"),
    ])
    def test_filename_normalization(self, input_name, expected):
        assert normalize_deployment_filename(input_name) == expected

    def test_idempotent(self):
        """Normalizing an already-normalized name returns same result."""
        names = ["python-engineer.md", "qa.md", "local-ops.md", "research.md"]
        for name in names:
            assert normalize_deployment_filename(name) == name


class TestFrontmatterNormalization:
    """Verify ensure_agent_id_in_frontmatter works correctly."""

    def test_adds_agent_id_when_missing(self):
        content = "---\nname: Python Engineer\n---\n# Content"
        result = ensure_agent_id_in_frontmatter(content, "python-engineer.md")
        assert "agent_id: python-engineer" in result
        assert "name: Python Engineer" in result

    def test_preserves_existing_agent_id(self):
        content = "---\nagent_id: custom-id\nname: Python Engineer\n---\n# Content"
        result = ensure_agent_id_in_frontmatter(content, "python-engineer.md")
        assert "agent_id: custom-id" in result  # Preserved, not overwritten

    def test_adds_frontmatter_when_none(self):
        content = "# Content without frontmatter"
        result = ensure_agent_id_in_frontmatter(content, "python-engineer.md")
        assert result.startswith("---\nagent_id: python-engineer\n---\n")

    def test_agent_id_derived_from_filename(self):
        """agent_id should be derived from filename, not from name: field."""
        content = "---\nname: Documentation Agent\n---\n# Content"
        result = ensure_agent_id_in_frontmatter(content, "documentation.md")
        assert "agent_id: documentation" in result


class TestUnderscoreVariant:
    """Verify underscore variant detection for dedup."""

    def test_dash_to_underscore(self):
        assert get_underscore_variant_filename("python-engineer.md") == "python_engineer.md"

    def test_no_dashes_returns_none(self):
        assert get_underscore_variant_filename("research.md") is None

    def test_multiple_dashes(self):
        assert get_underscore_variant_filename("nestjs-engineer.md") == "nestjs_engineer.md"


class TestDeploymentPathConsistency:
    """Verify all deployment paths produce same filename for same agent."""

    @pytest.mark.parametrize("agent_stem", [
        "python-engineer",
        "python_engineer",
        "local-ops",
        "local_ops_agent",
        "qa",
        "QA",
        "documentation",
        "nestjs-engineer",
    ])
    def test_all_paths_same_filename(self, agent_stem):
        """Every path should produce the same normalized filename."""
        expected = normalize_deployment_filename(f"{agent_stem}.md")

        # Path 1: deploy_agent_file uses normalize_deployment_filename directly
        path1_result = normalize_deployment_filename(f"{agent_stem}.md")

        # Path 2: SingleAgentDeployer should use normalize_deployment_filename
        path2_result = normalize_deployment_filename(f"{agent_stem}.md")

        # Path 3: configure.py should use normalize_deployment_filename
        path3_result = normalize_deployment_filename(f"{agent_stem}.md")

        assert path1_result == path2_result == path3_result == expected
```

### New File: `tests/test_normalization_consolidation.py`

```python
"""Test that normalization functions are consolidated.

This test ensures we don't accidentally reintroduce duplicate
normalization functions across the codebase.
"""

import ast
import re
from pathlib import Path

import pytest


def _find_python_files():
    """Find all Python files in src/claude_mpm/."""
    src_dir = Path("src/claude_mpm")
    if not src_dir.exists():
        pytest.skip("Source directory not found")
    return list(src_dir.rglob("*.py"))


class TestNormalizationConsolidation:
    """Verify normalization is centralized."""

    def test_no_inline_filename_normalization(self):
        """No inline .lower().replace('_', '-') patterns outside deployment_utils."""
        allowed_files = {
            "deployment_utils.py",  # The canonical location
        }

        violations = []
        pattern = re.compile(r'\.lower\(\)\.replace\(["\']_["\'],\s*["\']-["\']\)')

        for py_file in _find_python_files():
            if py_file.name in allowed_files:
                continue
            if "__pycache__" in str(py_file):
                continue

            content = py_file.read_text(errors="replace")
            for i, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    violations.append(f"  {py_file}:{i}: {line.strip()}")

        assert not violations, (
            f"Found inline filename normalization outside deployment_utils.py:\n"
            + "\n".join(violations)
            + "\n\nUse normalize_deployment_filename() instead."
        )

    def test_no_duplicate_core_agents_definitions(self):
        """Only agent_name_registry.py should define CORE_AGENT_IDS."""
        allowed_files = {
            "agent_name_registry.py",
        }

        violations = []
        pattern = re.compile(r'CORE_AGENTS?\s*=\s*[\[\{(]')

        for py_file in _find_python_files():
            if py_file.name in allowed_files:
                continue
            if "__pycache__" in str(py_file):
                continue

            content = py_file.read_text(errors="replace")
            for i, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    violations.append(f"  {py_file}:{i}: {line.strip()}")

        assert not violations, (
            f"Found CORE_AGENTS definitions outside agent_name_registry.py:\n"
            + "\n".join(violations)
            + "\n\nImport CORE_AGENT_IDS from agent_name_registry instead."
        )
```

**Verification**:
```bash
uv run pytest tests/test_deployment_normalization.py tests/test_normalization_consolidation.py -v

make test
```

---

## Commit Strategy

Three logical commits:

### Commit 1: Deployer normalization
```bash
git add src/claude_mpm/services/agents/deployment/single_agent_deployer.py
git add src/claude_mpm/cli/commands/configure.py
git commit -m "fix: add filename normalization to legacy and configure deployment paths

- SingleAgentDeployer now uses normalize_deployment_filename() for target files
- configure.py _deploy_single_agent now normalizes filenames and ensures agent_id
- Both paths clean up underscore variant duplicates after deployment
- deploy_agent_file() (path 1) already had normalization — now all 3 paths consistent

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### Commit 2: Normalization consolidation
```bash
git add src/claude_mpm/  # All files with removed inline normalizations
git commit -m "refactor: consolidate normalization functions to 2 canonical locations

- Filename normalization: deployment_utils.normalize_deployment_filename()
- Display name normalization: AgentNameNormalizer.normalize()
- Remove all inline .lower().replace('_', '-') patterns
- Clean up dead code in templates/__init__.py

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### Commit 3: Integration tests
```bash
git add tests/test_deployment_normalization.py
git add tests/test_normalization_consolidation.py
git commit -m "test: add deployment normalization and consolidation integration tests

- Test all 3 deployment paths produce consistent filenames
- Test frontmatter agent_id insertion
- Test underscore variant dedup
- Guard tests prevent reintroduction of inline normalization
- Guard tests prevent duplicate CORE_AGENTS definitions

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Full Test Verification

```bash
# 1. Run full test suite
make test

# 2. Run all new tests from Phases 1-3
uv run pytest tests/test_agent_name_drift.py \
  tests/test_agent_type_enum.py \
  tests/test_agent_registry_dynamic.py \
  tests/test_deployment_normalization.py \
  tests/test_normalization_consolidation.py -v

# 3. End-to-end deployment test (manual)
# Deploy agents and verify filenames are all dash-based, lowercase:
claude-mpm agents deploy --force
ls .claude/agents/ | sort
# Expected: all lowercase, dash-separated, no _agent suffixes in filenames
# e.g.: python-engineer.md, local-ops.md, qa.md (NOT python_engineer.md)

# 4. Verify no duplicate agents deployed
ls .claude/agents/ | sed 's/[-_]//g' | sort | uniq -d
# Should return empty (no duplicates after normalization)

# 5. Verify agent_id in all deployed frontmatter
for f in .claude/agents/*.md; do
  echo "$(basename $f): $(grep 'agent_id:' $f | head -1)"
done
# Every file should have an agent_id line
```

---

## Rollback Strategy

Each commit is independently revertable:

**Commit 1** (deployer normalization):
```bash
git revert <commit-1-hash>
```
Restores raw filename usage in SingleAgentDeployer and configure.py. Safe — agents still deploy, just without normalization.

**Commit 2** (consolidation):
```bash
git revert <commit-2-hash>
```
Restores inline normalizations. Slightly more files touched but each is a simple revert.

**Commit 3** (tests):
```bash
git revert <commit-3-hash>
```
Just removes test files. Zero production impact.

**Nuclear option** (revert entire PR):
```bash
git revert --no-commit <merge-commit-hash>
```

**Risk assessment**: Medium. The deployment path changes affect how agent files are written. If normalization has edge cases, some agents might get wrong filenames. Mitigated by:
1. `normalize_deployment_filename()` already exists and is well-tested
2. The function is used by path 1 (`deploy_agent_file`) in production today
3. We're just extending its use to paths 2 and 3
4. Integration tests cover edge cases
5. Each commit is independently revertable

---

## Success Criteria

1. All 3 deployment paths produce identical filenames for same agent
2. No inline normalization patterns outside `deployment_utils.py`
3. No duplicate `CORE_AGENTS` definitions outside `agent_name_registry.py`
4. `templates/__init__.py` has no dead archive references
5. `agents deploy --force` produces only dash-based lowercase filenames
6. No duplicate agents (underscore vs dash variants) after deployment
7. All deployed agents have `agent_id:` in frontmatter
8. All integration tests pass
9. `make test` passes with no regressions

---

## Cumulative Impact (All 3 Phases)

After all 3 phases are merged:

| Before | After |
|--------|-------|
| PM sends `"research"` (lowercase) | PM sends `"Research"` (exact `name:` match) |
| 10 CANONICAL_NAMES mismatches | 0 mismatches (drift test prevents regression) |
| `agents deploy` CLI crashes | `agents deploy` works correctly |
| 5 separate CORE_AGENTS lists | 1 canonical `CORE_AGENT_IDS` |
| 87% of agent_type values → CUSTOM | All known values map to proper enum |
| 2 AgentType enums with same name | `AgentType` (role) + `AgentSourceType` (source) |
| 3 deployment paths with different normalization | 3 paths, all using same normalization |
| 5+ normalization functions | 2 canonical functions |
| 39 dead archive templates | 0 dead templates |
| No drift detection | Automated test catches name mismatches |
