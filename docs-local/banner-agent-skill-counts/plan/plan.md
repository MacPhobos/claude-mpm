# Plan: Fix Startup Banner Agent/Skill Counts

## Context

The startup banner in `src/claude_mpm/cli/startup_display.py` displays inaccurate agent and skill counts because each counting function looks at only one scope — and they don't even look at the *same* scope:

| What | Function | Scope it checks | What it misses |
|------|----------|----------------|----------------|
| Agents: 48 | `_count_deployed_agents()` | **Project only** (`.claude/agents/`) | 7 user-level agents at `~/.claude/agents/` |
| Skills: 62 | `_count_mpm_skills()` | **User only** (`~/.claude/skills/`) | 189 project-level skills at `.claude/skills/` |

### Additional issues discovered during research

1. **Source repo counted as skills**: `~/.claude/skills/claude-mpm/` is a git clone (source repo, 160 nested SKILL.md files) — not deployed skills. It must be excluded.
2. **Case sensitivity**: 166 of 189 project skills use `skill.md` (lowercase), only 23 use `SKILL.md`. Current code checks only `SKILL.md` — works on macOS (case-insensitive) but would break on Linux.

## Files Modified

| File | Changes |
|------|---------|
| `src/claude_mpm/cli/startup_display.py` | Replace counting functions, add formatter, update banner layout |
| `tests/test_startup_display.py` | Add tests for new functions, update banner assertions |

## Implementation Steps

### Step 1: Replace `_count_mpm_skills()` and `_count_deployed_agents()` with `_count_scope_assets()`
- Unified function that counts both agents and skills for either "project" or "user" scope
- Excludes git source repos (dirs containing `.git`)
- Supports both `SKILL.md` and `skill.md` for Linux portability

### Step 2: Add `_format_scope_counts()` helper
- Progressive truncation: full → abbreviated → minimal
- Handles zero counts, singular forms

### Step 3: Modify `display_startup_banner()` layout
- Model gets its own line (was combined with counts)
- Two new scope lines replace old combined count
- CWD shifts from line 11 → 13
- Right panel unchanged, total lines still 16

### Step 4: Add tests
- `TestCountScopeAssets` (7 tests)
- `TestFormatScopeCounts` (6 tests)
- Updated banner integration test

### Step 5: Run tests and verify
