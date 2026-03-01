# Implementation Plan: Fix Tests Nuking Agents

**Date**: 2026-03-01
**Branch**: `tests_nuke_agents`

---

## Phase 1: Test Isolation Fix (COMPLETED)

### What Was Done
Patched 8 test call sites across 3 files to mock `_review_project_agents`, preventing
the real review/archive chain from touching `.claude/agents/`.

### Status: ✅ Applied and Verified

---

## Phase 2: Production Code Fix — Thread `project_path` (COMPLETED)

### Problem
`_review_project_agents()` and `_archive_agents()` hardcode `Path.cwd()` instead of
accepting/using the `project_path` parameter.

### Changes Required

**File: `src/claude_mpm/cli/commands/auto_configure.py`**

#### 2a. Update `_review_project_agents()` signature and body

```python
# BEFORE (line 1136):
def _review_project_agents(self, agent_preview) -> Optional[dict]:
    ...
    project_agents_dir = Path.cwd() / ".claude" / "agents"   # line 1173

# AFTER:
def _review_project_agents(self, agent_preview, project_path: Path) -> Optional[dict]:
    ...
    project_agents_dir = project_path / ".claude" / "agents"
```

#### 2b. Update `_archive_agents()` signature and body

```python
# BEFORE (line 1179):
def _archive_agents(self, agents_to_archive: list[dict]) -> dict:
    ...
    project_agents_dir = Path.cwd() / ".claude" / "agents"   # line 1190

# AFTER:
def _archive_agents(self, agents_to_archive: list[dict], project_path: Path) -> dict:
    ...
    project_agents_dir = project_path / ".claude" / "agents"
```

#### 2c. Update all call sites in `_run_full_configuration()` and `_run_preview()`

There are **4 call sites** for `_review_project_agents` (lines 348, 350, 425, 427)
and **1 call site** for `_archive_agents` (line 476) that need `project_path` passed.

```python
# BEFORE:
agent_review_results = self._review_project_agents(agent_preview)
archive_result = self._archive_agents(agents_to_archive)

# AFTER:
agent_review_results = self._review_project_agents(agent_preview, project_path)
archive_result = self._archive_agents(agents_to_archive, project_path)
```

#### 2d. Update test mocks to match new signatures

The 8 test sites from Phase 1 mock `_review_project_agents` with `return_value=None`,
which doesn't depend on the signature. However, any tests that call the method
directly or verify its arguments would need updating.

### Estimated Scope
- 1 source file changed (~10 lines)
- 0-3 test files adjusted (verify mock compatibility)

---

### Status: ✅ Applied and Verified

---

## Phase 3: Recovery of Archived Agents (COMPLETED MANUALLY)

### Steps

1. **Inventory**: List all files in `.claude/agents/unused/`
2. **Deduplicate**: For each unique agent name, identify the latest timestamped copy
3. **Restore**: Move the latest copy back to `.claude/agents/{name}.md`
4. **Cleanup**: Remove `.claude/agents/unused/` directory entirely
5. **Verify**: Confirm agent count matches expected (~48)

### Recovery Script (proposed)

```bash
#!/bin/bash
# Restore latest version of each archived agent
UNUSED_DIR=".claude/agents/unused"
AGENTS_DIR=".claude/agents"

for agent_file in $(ls "$UNUSED_DIR"/*.md 2>/dev/null | sort -r); do
  # Extract base name (strip _YYYYMMDD_HHMMSS.md suffix)
  base_name=$(echo "$(basename "$agent_file")" | sed 's/_[0-9]\{8\}_[0-9]\{6\}\.md$//')
  target="$AGENTS_DIR/${base_name}.md"

  if [ ! -f "$target" ]; then
    cp "$agent_file" "$target"
    echo "Restored: $base_name"
  fi
done

echo "Done. Agent count: $(ls "$AGENTS_DIR"/*.md | wc -l)"
```

### Decision: Restore or Ignore?
Since the currently deployed 48 agents are the correct set (they survived because
they are either custom or matched the mock recommendation), the archived copies are
**older duplicates of already-present agents**. Unless some agents were lost entirely
and not re-deployed, cleanup is sufficient.

**Recommendation**: Simply delete `.claude/agents/unused/` — verify no unique agent
names exist only in `unused/` that are missing from the active directory.

---

## Phase 4: Structural Prevention (Guard Rails) (COMPLETED)

### 4a. Pytest Safety Fixture (IMPLEMENTED)

Add an `autouse` fixture in `conftest.py` that protects `.claude/agents/` from modification:

```python
@pytest.fixture(autouse=True)
def protect_real_agents(monkeypatch, request):
    """Prevent any test from modifying the real .claude/agents/ directory.

    This fixture intercepts shutil.move and shutil.rmtree to block operations
    targeting the real project agents directory. Tests that need to exercise
    archive/move logic should use tmp_path.
    """
    real_agents_dir = str(Path.cwd() / ".claude" / "agents")

    original_move = shutil.move
    original_rmtree = shutil.rmtree

    def guarded_move(src, dst, *args, **kwargs):
        src_str, dst_str = str(src), str(dst)
        if real_agents_dir in src_str or real_agents_dir in dst_str:
            raise RuntimeError(
                f"TEST SAFETY: Blocked shutil.move touching real agents dir.\n"
                f"  src={src_str}\n  dst={dst_str}\n"
                f"  Use tmp_path for filesystem tests."
            )
        return original_move(src, dst, *args, **kwargs)

    def guarded_rmtree(path, *args, **kwargs):
        if real_agents_dir in str(path):
            raise RuntimeError(
                f"TEST SAFETY: Blocked shutil.rmtree on real agents dir: {path}"
            )
        return original_rmtree(path, *args, **kwargs)

    monkeypatch.setattr(shutil, "move", guarded_move)
    monkeypatch.setattr(shutil, "rmtree", guarded_rmtree)
```

### 4b. CI Agent Count Assertion (OPTIONAL)

Add a pre/post test hook or a dedicated test that asserts agent count stability:

```python
def test_agent_directory_not_modified():
    """Canary test: verify tests don't modify real agent directory."""
    agents_dir = Path.cwd() / ".claude" / "agents"
    unused_dir = agents_dir / "unused"

    # No files should have been archived during this test session
    if unused_dir.exists():
        recent = [f for f in unused_dir.iterdir()
                  if f.stat().st_mtime > time.time() - 300]  # last 5 min
        assert len(recent) == 0, (
            f"Tests archived {len(recent)} agents during this session! "
            f"Files: {[f.name for f in recent]}"
        )
```

---

## Devil's Advocate Analysis

### Challenge 1: "The Phase 1 test fix is just patching over the symptom"

**Argument**: Mocking `_review_project_agents` in each test is a whack-a-mole approach. Any new test that calls `command.run()` with `yes=True, preview=False` will have the same problem. The next developer won't know to add the mock.

**Assessment**: **Valid concern.** This is why Phase 4a (the autouse safety fixture) is essential, not optional. The fixture acts as a catch-all that prevents ANY test from touching real agents, regardless of whether the test author remembers to add the mock. The Phase 1 fix is necessary (tests need to not break things *today*), but it's not sufficient alone.

**Counterpoint**: The mock approach *is* correct at the individual test level because these tests aren't testing the review/archive functionality — they're testing configuration flow, sync/async boundaries, and skill deployment. Mocking out an unrelated side effect is proper test design, not avoidance.

### Challenge 2: "The Phase 2 production fix might break real `--project-path` usage"

**Argument**: Nobody has ever used `--project-path` pointing to a different directory. Changing the method signatures might break other callers we haven't found, or the threading of `project_path` through `_run_preview()` might have its own issues since `_run_preview()` also calls `_review_project_agents()`.

**Assessment**: **Partially valid.** The risk is low because:
- The function signatures are private (`_` prefix), so no external callers exist
- The parameter is already available in the calling method — we're just connecting the plumbing
- But: we should add a dedicated test for the `--project-path` flow to prove it works

**Mitigation**: Add a test that creates a temp project with agents, runs configure with `project_path=tmp_path`, and verifies only the tmp agents are reviewed.

### Challenge 3: "The autouse fixture in Phase 4a is too aggressive"

**Argument**: An autouse fixture that intercepts `shutil.move` globally could have unintended side effects on tests that legitimately need to move files. It also adds overhead to every single test.

**Assessment**: **Valid.** The fixture as written intercepts ALL shutil.move calls, not just agent-related ones. Better approach:

- Make the guard more targeted: only block moves where source or dest matches the pattern `*/.claude/agents/*` AND the path is not under a `tmp_path`
- Or: instead of monkeypatching shutil globally, patch only the import used by `agent_review_service.py`
- Or: use a lighter approach — just verify post-test state rather than intercepting calls

**Revised recommendation**: Replace the `shutil.move` interception with a simpler state check:

```python
@pytest.fixture(autouse=True)
def verify_agents_untouched():
    """Verify no agent files were modified during the test."""
    agents_dir = Path.cwd() / ".claude" / "agents"
    before = set(f.name for f in agents_dir.glob("*.md")) if agents_dir.exists() else set()
    yield
    after = set(f.name for f in agents_dir.glob("*.md")) if agents_dir.exists() else set()
    removed = before - after
    assert not removed, f"TEST BUG: Real agents were removed during test: {removed}"
```

This is less intrusive (no monkeypatch of stdlib), catches the problem, and doesn't interfere with legitimate file operations.

**Counter-counterpoint**: The state-check approach detects the damage but doesn't prevent it. If a test archives 40 agents, the assertion fires, but the files are already moved. For a development machine, the loud failure is likely sufficient. For CI, you'd want the `shutil.move` interception to prevent file mutation entirely.

### Challenge 4: "Why not just run tests in an isolated directory / Docker container?"

**Argument**: The real fix is test isolation at the process level — run pytest in a temp directory or container so it can't touch the project's `.claude/agents/` at all.

**Assessment**: **Theoretically ideal, practically impractical.**
- Tests need the source tree to import from
- Many tests use relative paths, `Path.cwd()`, and project fixtures
- Docker adds 10-30s overhead per test run
- `tmp_path` isolation per-test IS the pytest way; the bug is that some tests don't use it

**Verdict**: Fixing the tests to use proper isolation (Phase 1 + Phase 2) is the right approach. The autouse guard (Phase 4) is the safety net.

### Challenge 5: "Is the test fix over-mocking? Are we losing coverage?"

**Argument**: By mocking `_review_project_agents`, we're no longer testing the review→archive flow at all. What if the review logic has bugs?

**Assessment**: **Correct — but those 8 tests were never MEANT to test review/archive.** They test:
- Configuration flow with skip confirmation
- Sync/async boundary crossing
- Skill deployment workflows

The review/archive logic should have its OWN tests that:
1. Create a temp agents directory with known agents
2. Call `_review_project_agents()` with controlled inputs
3. Verify categorization is correct
4. Call `_archive_agents()` and verify files moved within temp dir

**Action**: Check if `AgentReviewService` has dedicated unit tests. If not, add them in Phase 2.

### Challenge 6: "What about preview mode (`_run_preview`) — it also calls `_review_project_agents`"

**Argument**: The preview path (lines 348-350) also calls `_review_project_agents()` with the same `Path.cwd()` bug. Even though preview doesn't archive, it still reads the real directory and could cause issues (performance, exceptions if dir doesn't exist in CI).

**Assessment**: **Valid but lower severity.** Preview only reads, doesn't mutate. But it should still be fixed in Phase 2 for correctness and to avoid confusion when `project_path` differs from `cwd`.

---

## Recommended Implementation Order

| Priority | Phase | Effort | Risk | Status |
|----------|-------|--------|------|--------|
| P0 | Phase 1: Test mocks | ✅ Complete | None | ✅ Done |
| P0 | Phase 3: Recovery / cleanup of unused/ | 5 min | Low | ✅ Done (manual) |
| P1 | Phase 4: Autouse safety fixture | 30 min | Low | ✅ Done |
| P1 | Phase 2: Production `project_path` fix | 1 hr | Low | ✅ Done |

### All phases complete.

### Devil's Advocate Verification Results (2026-03-01)
1. **Mock removal test**: Removed `_review_project_agents` mock, ran with `project_path=/tmp/test-nonexistent-project` — zero agents removed. Phase 2 fix works independently.
2. **Fixture detection test**: Simulated agent removal — fixture correctly detects and would fail the test.
3. **Full suite**: 6981 passed, 759 skipped, 13 pre-existing failures (unrelated). Agent count stable at 48 throughout.
4. **Unused directory**: 0 files (Phase 3 cleanup was manual).

---

## Files Involved

### Already Modified (Phase 1)
- `tests/cli/commands/test_auto_configure.py`
- `tests/services/config_api/test_autoconfig_defaults.py`
- `tests/services/config_api/test_autoconfig_skill_deployment.py`

### To Modify (Phases 2-4)
- `src/claude_mpm/cli/commands/auto_configure.py` (thread project_path)
- `tests/conftest.py` (autouse safety fixture)
- `tests/services/agents/test_agent_review_service.py` (new — dedicated unit tests)

### To Clean Up (Phase 3)
- `.claude/agents/unused/` (339 files → delete after verification)
