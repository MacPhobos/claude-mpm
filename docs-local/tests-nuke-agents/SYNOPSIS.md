# Bug Synopsis: `make tests` Deletes Deployed Agents

**Date**: 2026-03-01
**Severity**: Critical (data loss)
**Branch**: `tests_nuke_agents`
**Affected versions**: Unknown start — present (5.9.41)

---

## 1. Problem Statement

Running `make tests` (i.e. `uv run pytest tests/`) **deletes the majority of deployed agents** from the project's `.claude/agents/` directory. A project starting with ~50 deployed agents is left with only ~7 after a single test run.

The agents are not truly deleted — they are **archived** (moved) to `.claude/agents/unused/` with timestamps appended to their filenames. As of discovery, **339 archived agent files** had accumulated in that directory from multiple test runs, representing **48 unique agent names**.

---

## 2. Root Cause

### The Bug Chain

```
Test calls command.run(args) with yes=True, preview=False
  → AutoConfigureCommand._run_full_configuration()
    → self._review_project_agents(agent_preview)
      → Path.cwd() / ".claude" / "agents"   ← BUG: ignores project_path parameter
      → AgentReviewService.review_project_agents()
        → Categorizes agents not in mock recommendations as "unused"
    → self._archive_agents(agents_to_archive)
      → Path.cwd() / ".claude" / "agents"   ← BUG: same hardcoded path
      → AgentReviewService.archive_agents()
        → shutil.move() each "unused" agent to .claude/agents/unused/
```

### Two Distinct Bugs

**Bug A — Test isolation failure (immediate cause)**:
8 test cases across 3 files invoke `command.run(args)` with `yes=True` (skip confirmation) and `preview=False` (full execution mode), which triggers the real `_review_project_agents()` → `_archive_agents()` chain against the live filesystem.

| File | Offending Tests |
|------|-----------------|
| `tests/cli/commands/test_auto_configure.py` | `test_run_full_with_skip_confirmation` |
| `tests/services/config_api/test_autoconfig_defaults.py` | 3 tests crossing sync/async boundary |
| `tests/services/config_api/test_autoconfig_skill_deployment.py` | 4 full-workflow integration tests |

**Bug B — Production code parameter shadowing (latent cause)**:
Both `_review_project_agents()` and `_archive_agents()` in `auto_configure.py` **hardcode `Path.cwd()`** instead of using the `project_path` parameter that is already threaded through `run()` → `_run_full_configuration()`. The parameter exists in the calling method's signature but is never passed down.

```python
# Line 1173 — ignores project_path
project_agents_dir = Path.cwd() / ".claude" / "agents"

# Line 1190 — same pattern
project_agents_dir = Path.cwd() / ".claude" / "agents"
```

### Why Only ~7 Agents Survive

The mock `agent_preview.recommendations` in test fixtures typically contains only 1-3 agents (e.g., `"python-engineer"`). The review service categorizes every other managed agent as "unused" and archives it. Custom agents survive because the review service skips agents not in the managed set. So:

- **Survive**: Custom agents + the 1-3 mock-recommended agents
- **Archived**: All other managed agents (~40-45 of ~50)

---

## 3. Impact Assessment

| Dimension | Impact |
|-----------|--------|
| **Data loss** | Reversible (shutil.move, not delete), but disruptive |
| **Developer workflow** | Must re-deploy agents after every test run |
| **CI/CD** | Any CI that runs tests from within a project with deployed agents would lose them |
| **Stealth factor** | HIGH — no error, no warning, no output indicating agents were moved |
| **Accumulation** | 339 files accumulated silently in unused/ across multiple runs |

---

## 4. Applied Fix (Test Isolation — Bug A)

The Research agent applied targeted mocks across all 8 call sites:

```python
with patch.object(command, "_review_project_agents", return_value=None):
    result = command.run(args)
```

This prevents the real review/archive chain from executing during tests while still allowing the rest of `command.run()` to exercise its logic.

### Files Modified
- `tests/cli/commands/test_auto_configure.py` (+19/-12 lines)
- `tests/services/config_api/test_autoconfig_defaults.py` (+24/-6 lines)
- `tests/services/config_api/test_autoconfig_skill_deployment.py` (+25/-4 lines)

### Verification
- Full test suite: 6980 passed, 759 skipped, 15 pre-existing failures (unrelated)
- Agent count stable at 48 throughout test run
- No new files appear in `.claude/agents/unused/`

---

## 5. Remaining Work (Bug B — Production Code)

The production code in `auto_configure.py` still hardcodes `Path.cwd()` in both methods. This means that even in real usage, if a user runs `claude-mpm configure --project-path /other/project`, the review/archive would operate on `cwd()` instead of `/other/project`.

This requires a separate fix: thread `project_path` through to `_review_project_agents()` and `_archive_agents()`.

---

## 6. Recovery

339 archived agent files in `.claude/agents/unused/` need to be:
1. Deduplicated (keep only latest timestamp per agent name)
2. Restored to `.claude/agents/`
3. The `unused/` directory cleaned up
