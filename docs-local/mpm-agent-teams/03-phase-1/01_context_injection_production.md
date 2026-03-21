# Context Injection: Production Readiness

**Phase:** 1
**Status:** Implementation spec
**Depends on:** Phase 0 TeammateContextInjector (validated, 18/18 tests pass)

---

## 1. Activation Mechanism

### Problem

Phase 0 required manually prefixing the hook command in `settings.local.json` with `CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION=1`. This is fragile — `claude-mpm agents deploy` calls `HookInstaller.install_hooks()` which regenerates `settings.local.json` and drops the env var prefix.

### Options Evaluated

| Option | Mechanism | Survives deploy? | User action? | Complexity |
|--------|-----------|:---:|:---:|:---:|
| A: Auto-detect `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` | Read Anthropic's env var at injection decision time | Yes | None | Low |
| B: Add env var to hook installer | Prefix hook command in `_update_claude_settings()` | Yes | None | Medium |
| C: Config file flag | Read `.claude-mpm/configuration.yaml` | Yes | Manual config | Medium |

### Recommendation: Option A (auto-detect)

**Rationale:**

1. **Zero friction.** If the user has already set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (required by Claude Code to enable Agent Teams), injection activates automatically. No second flag needed.
2. **Survives deploy.** No hook command modification required — the check happens at runtime in Python, not in `settings.local.json`.
3. **Correct lifecycle.** When Anthropic graduates Agent Teams from experimental, the env var goes away and we update the check. The activation condition tracks the feature's actual availability.
4. **No breaking change.** The existing `CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION` env var becomes a manual override (force-enable/disable), not the primary activation path.

### Implementation

**File:** `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py`

Change the `__init__` method (lines 57-69):

```python
def __init__(self, enabled: bool | None = None) -> None:
    if enabled is not None:
        self._enabled = enabled
    else:
        # Manual override takes precedence
        manual = os.environ.get("CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION")
        if manual is not None:
            self._enabled = manual == "1"
        else:
            # Auto-detect: enable when Agent Teams is active
            self._enabled = (
                os.environ.get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "0") == "1"
            )
```

**Precedence chain:**
1. Constructor `enabled` param (tests)
2. `CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION=1|0` (manual override)
3. `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (auto-detect)
4. Default: disabled

### Tests to Add

In `tests/hooks/test_teammate_context_injector.py`:

```python
def test_auto_detect_agent_teams_env(monkeypatch):
    """Injection enables automatically when Agent Teams env var is set."""
    monkeypatch.delenv("CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION", raising=False)
    monkeypatch.setenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "1")
    injector = TeammateContextInjector()
    assert injector.is_enabled()

def test_manual_override_disables(monkeypatch):
    """Manual override can disable even when Agent Teams is active."""
    monkeypatch.setenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", "1")
    monkeypatch.setenv("CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION", "0")
    injector = TeammateContextInjector()
    assert not injector.is_enabled()

def test_no_env_vars_disabled(monkeypatch):
    """Injection disabled when no env vars are set."""
    monkeypatch.delenv("CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION", raising=False)
    monkeypatch.delenv("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", raising=False)
    injector = TeammateContextInjector()
    assert not injector.is_enabled()
```

---

## 2. Teammate Protocol Synchronization

### Problem

Two copies of the teammate protocol exist:

1. **`teammate_context_injector.py:20-43`** — `TEAMMATE_PROTOCOL` constant (injected at runtime)
2. **`TEAM_CIRCUIT_BREAKER_PROTOCOL.md` Section 3** — `TEAMMATE_PROTOCOL_BLOCK` (definitive spec)

These already differ. The injector version is a condensed rewrite (~340 tokens); the protocol doc version is the full 5-rule block (~421 tokens). Both are within the 500-token budget.

### Decision: CB Protocol Doc is Source of Truth

The `TEAM_CIRCUIT_BREAKER_PROTOCOL.md` Section 3 `TEAMMATE_PROTOCOL_BLOCK` is the **canonical text**. Rationale:

1. The protocol doc was written with explicit CB mapping (Rule 1→CB#3, Rule 2→CB#4, etc.)
2. The protocol doc includes the token measurement appendix
3. Changes to CB enforcement should start in the protocol doc, not in Python code

### Implementation

**File:** `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py`

Replace the current `TEAMMATE_PROTOCOL` constant (lines 20-43) with the exact `TEAMMATE_PROTOCOL_BLOCK` from `TEAM_CIRCUIT_BREAKER_PROTOCOL.md` Section 3 (the Python constant on lines 256-281 of that doc).

Add a sync-check comment at the top:

```python
# SYNC: This block must match TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 3.
# Source of truth: docs-local/mpm-agent-teams/02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md
# Last synced: 2026-03-20 (Phase 1 production)
# Token budget: ~421 tokens (max 500)
TEAMMATE_PROTOCOL = """\
## MPM Teammate Protocol
...
"""
```

### Sync Enforcement

Add a unit test that verifies the constant matches the doc:

```python
def test_protocol_matches_source_of_truth():
    """TEAMMATE_PROTOCOL must match TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 3."""
    from claude_mpm.hooks.claude_hooks.teammate_context_injector import TEAMMATE_PROTOCOL

    doc_path = Path(__file__).parent.parent.parent / (
        "docs-local/mpm-agent-teams/02-phase-0/TEAM_CIRCUIT_BREAKER_PROTOCOL.md"
    )
    if not doc_path.exists():
        pytest.skip("Protocol doc not in this checkout")

    content = doc_path.read_text()
    # Extract the Python constant block from the doc
    start = content.index('TEAMMATE_PROTOCOL_BLOCK = """')
    end = content.index('"""', start + len('TEAMMATE_PROTOCOL_BLOCK = """')) + 3
    doc_block = content[start:end]
    # eval to get the string value
    doc_value = eval(doc_block.split(" = ", 1)[1])  # nosec

    assert TEAMMATE_PROTOCOL.strip() == doc_value.strip(), (
        "TEAMMATE_PROTOCOL is out of sync with TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 3. "
        "Update the Python constant to match the doc."
    )
```

---

## 3. Production Logging

### Current State

Phase 0 validation logging writes to `/tmp/claude-mpm-agent-teams-validation.log` via `_validation_log()` (event_handlers.py line ~73). This is always-on, unbounded, and `/tmp`-resident.

### Production Logging Design

| Concern | Decision | Rationale |
|---------|----------|-----------|
| **Where** | MPM's existing `_log()` helper (writes to `_hook_handler.log_file`) | Single log destination; already rotated by hook_handler |
| **Level** | INFO for injection events; DEBUG for field extraction | Injection is a significant event worth tracking; field details are debug noise |
| **Validation logging** | Remove `/tmp/` writes; convert to DEBUG-level `_log()` calls | Phase 0 validation is complete; `/tmp/` writes have no rotation and leak disk |
| **Performance** | Zero-cost when DEBUG=false (existing `if DEBUG:` guards) | Injection adds ~0.1ms for string concat; logging adds ~0.5ms only when enabled |

### Implementation

**File:** `src/claude_mpm/hooks/claude_hooks/event_handlers.py`

1. **Remove `_validation_log()` function** (lines ~73-93) and its `/tmp/` file handle.

2. **Convert all `_validation_log()` calls** to `_log()` calls guarded by `if DEBUG:`:

   ```python
   # Before (Phase 0):
   _validation_log(f"[AGENT_TEAMS_VALIDATION] PreToolUse intercepted...")

   # After (Phase 1):
   if DEBUG:
       _log(f"[AGENT_TEAMS] PreToolUse intercepted...")
   ```

3. **Keep the INFO-level injection log** in `handle_pre_tool_fast` (already exists at line ~462):
   ```python
   _log(f"TeammateContextInjector: Injected protocol for Agent Teams spawn ...")
   ```
   This fires only when injection actually occurs (team_name present + enabled), so it's low-volume.

4. **Keep INFO-level logs** in `handle_teammate_idle_fast` (line ~1613) and `handle_task_completed_fast` (line ~1665) — these are dashboard-relevant events.

### Files Changed

| File | Change |
|------|--------|
| `event_handlers.py` | Remove `_validation_log()`, convert 6 calls to `if DEBUG: _log()` |
| `test_agent_teams_validation_logging.py` | Update tests to check `_log()` instead of `/tmp/` file |

---

## 4. Feature Flag Lifecycle

### Current: Experimental (Phase 1)

- Context injection activates when `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` is detected
- Manual override available via `CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION`
- Injection is prompt-only — no code enforcement of CB compliance

### Graduation Criteria (exit experimental)

Context injection becomes default (always-on for all sessions) when **all three** conditions are met:

1. **Anthropic graduates Agent Teams.** The `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` env var is no longer required. At that point, any Claude Code session might use Agent Teams.

2. **Phase 1 CB compliance metrics pass.** Per TEAM_CIRCUIT_BREAKER_PROTOCOL.md Section 7: CB#3 evidence compliance >= 70%, peer delegation resistance >= 70% across at least 20 teammate spawns.

3. **No performance regression.** PreToolUse hook latency with injection does not exceed 50ms p95 (current baseline: ~15ms for fast hook, ~450ms for full Python hook — injection adds negligible overhead to the Python path).

### Graduation Implementation

When criteria are met, change `TeammateContextInjector.__init__` to:

```python
# Post-graduation: always enabled, no env var check
# The should_inject() method still checks for team_name in tool_input,
# so non-team Agent tool calls are unaffected.
self._enabled = True
```

The `should_inject()` method's `"team_name" in tool_input` check provides the runtime guard — injection only fires for Agent Teams spawns regardless of the feature flag state.
