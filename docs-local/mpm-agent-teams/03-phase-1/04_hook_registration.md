# Hook Registration: TeammateIdle and TaskCompleted

**Phase:** 1
**Status:** Implementation spec
**Problem:** Python handlers exist but hooks are NOT registered in `settings.local.json`
**Root cause:** `installer.py` conditionally registers these hooks only when `supports_new_hooks()` returns True (Claude Code >= 2.1.47). Current `settings.local.json` was likely written before v2.1.47 was available or the installer was run before the version check passed.

---

## 1. Current State

### Handlers (exist, working)

| Handler | File | Line | Event Type |
|---------|------|------|-----------|
| `handle_teammate_idle_fast` | `event_handlers.py` | 1570 | TeammateIdle |
| `handle_task_completed_fast` | `event_handlers.py` | 1620 | TaskCompleted |

Both handlers are wired in the `hook_handler.py` dispatch table (lines 540-541):
```python
"TeammateIdle": self.event_handlers.handle_teammate_idle_fast,
"TaskCompleted": self.event_handlers.handle_task_completed_fast,
```

### Registration (MISSING)

Current `settings.local.json` hooks section:
- `PreToolUse` — registered
- `PostToolUse` — registered
- `Stop` — registered
- `SubagentStop` — registered
- `SessionStart` — registered
- `UserPromptSubmit` — registered
- `TeammateIdle` — **NOT registered**
- `TaskCompleted` — **NOT registered**
- `WorktreeCreate` — **NOT registered**
- `WorktreeRemove` — **NOT registered**
- `ConfigChange` — **NOT registered**

### Installer Logic (already correct)

`installer.py` lines 850-877 already handle registration of these hooks:

```python
new_hook_events_simple = [
    "WorktreeCreate",
    "WorktreeRemove",
    "TeammateIdle",
    "TaskCompleted",
]
new_hook_events_matcher = ["ConfigChange"]

if self.supports_new_hooks():
    for event_type in new_hook_events_simple:
        existing = settings["hooks"].get(event_type, [])
        settings["hooks"][event_type] = merge_hooks_for_event(
            existing, hook_command, use_matcher=False
        )
```

**The code is correct.** The issue is that `settings.local.json` was generated before Claude Code v2.1.47 was available, so `supports_new_hooks()` returned False and the hooks were not written. A re-run of `claude-mpm agents deploy` (which calls `install_hooks()`) on Claude Code >= 2.1.47 will add them.

---

## 2. Fix: Re-run Hook Installation

### Option A: User action (simplest)

```bash
claude-mpm agents deploy
```

This calls `HookInstaller.install_hooks()` → `_update_claude_settings()` → detects v2.1.47+ → registers all 5 new hook events. **No code change needed.**

### Option B: Add to Phase 1 implementation checklist

The Phase 1 engineer should run `claude-mpm agents deploy` after making code changes, which naturally re-writes `settings.local.json` with all supported hooks.

### Verification After Registration

After deploy, `settings.local.json` should contain:

```json
{
  "hooks": {
    "PreToolUse": [...],
    "PostToolUse": [...],
    "Stop": [...],
    "SubagentStop": [...],
    "SessionStart": [...],
    "UserPromptSubmit": [...],
    "TeammateIdle": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "<hook-script-path>"
          }
        ]
      }
    ],
    "TaskCompleted": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "<hook-script-path>"
          }
        ]
      }
    ],
    "WorktreeCreate": [...],
    "WorktreeRemove": [...],
    "ConfigChange": [...]
  }
}
```

---

## 3. Handler Enhancements

The existing handlers do logging + dashboard emission. Phase 1 enhancements are minimal — the handlers already do what's needed for dashboard visibility.

### TeammateIdle Handler (line 1570)

**Current behavior:**
1. Validation logging (to be converted per `01_context_injection_production.md` Section 3)
2. Extract teammate_id, teammate_type, idle_reason
3. Emit `teammate_idle` SocketIO event to dashboard

**Phase 1 additions:**
None. The handler is sufficient for dashboard integration. Team lead notification is handled by Claude Code's native Agent Teams messaging (SendMessage), not by hook events.

**Future (Phase 2+):** Optionally emit a structured idle-reason to help PM decide whether to reassign or wait.

### TaskCompleted Handler (line 1620)

**Current behavior:**
1. Validation logging (to be converted per `01_context_injection_production.md` Section 3)
2. Extract task_id, task_title, completed_by, completion_status
3. Emit `task_completed` SocketIO event to dashboard

**Phase 1 additions:**
None. Task tracking in Agent Teams is handled by Claude Code's native task system. The hook provides dashboard visibility, which is its sole purpose.

**Future (Phase 2+):** Cross-reference task_id with PM's delegation tracking to auto-mark PM todos as completed.

---

## 4. Testing

### Test: Hook Registration

Add to `tests/test_hook_installer.py`:

```python
def test_new_hooks_registered_on_v2_1_47(tmp_path, monkeypatch):
    """TeammateIdle and TaskCompleted registered when version supports them."""
    installer = HookInstaller()
    installer.claude_dir = tmp_path / ".claude"
    installer.claude_dir.mkdir()
    installer.settings_file = installer.claude_dir / "settings.local.json"
    installer.settings_file.write_text("{}")

    # Mock version to return 2.1.47+
    monkeypatch.setattr(installer, "get_claude_version", lambda: "2.1.50")
    monkeypatch.setattr(installer, "get_hook_command", lambda: "/path/to/hook.sh")

    installer._update_claude_settings("/path/to/hook.sh")

    import json
    settings = json.loads(installer.settings_file.read_text())

    assert "TeammateIdle" in settings["hooks"]
    assert "TaskCompleted" in settings["hooks"]
    assert "WorktreeCreate" in settings["hooks"]
    assert "WorktreeRemove" in settings["hooks"]
    assert "ConfigChange" in settings["hooks"]

def test_new_hooks_not_registered_on_old_version(tmp_path, monkeypatch):
    """TeammateIdle and TaskCompleted NOT registered on Claude Code < 2.1.47."""
    installer = HookInstaller()
    installer.claude_dir = tmp_path / ".claude"
    installer.claude_dir.mkdir()
    installer.settings_file = installer.claude_dir / "settings.local.json"
    installer.settings_file.write_text("{}")

    monkeypatch.setattr(installer, "get_claude_version", lambda: "2.1.30")
    monkeypatch.setattr(installer, "get_hook_command", lambda: "/path/to/hook.sh")

    installer._update_claude_settings("/path/to/hook.sh")

    import json
    settings = json.loads(installer.settings_file.read_text())

    assert "TeammateIdle" not in settings["hooks"]
    assert "TaskCompleted" not in settings["hooks"]
```

### Test: Handler Dispatch

Add to `tests/hooks/claude_hooks/test_hook_handler_integration.py`:

```python
def test_teammate_idle_dispatches(hook_handler):
    """TeammateIdle events route to the correct handler."""
    event = {
        "type": "TeammateIdle",
        "session_id": "test-session",
        "teammate_id": "researcher-1",
        "teammate_type": "Research",
        "reason": "waiting_for_input",
    }
    # Should not raise
    hook_handler._route_event(event)

def test_task_completed_dispatches(hook_handler):
    """TaskCompleted events route to the correct handler."""
    event = {
        "type": "TaskCompleted",
        "session_id": "test-session",
        "task_id": "task-1",
        "task_title": "Research auth patterns",
        "completed_by": "researcher-1",
        "status": "completed",
    }
    hook_handler._route_event(event)
```

### Test: Dashboard Emission

Add to `tests/hooks/test_agent_teams_validation_logging.py` (renamed or supplemented):

```python
def test_teammate_idle_emits_socketio(mock_hook_handler, event_handlers):
    """TeammateIdle handler emits teammate_idle event to dashboard."""
    event = {
        "session_id": "s1",
        "cwd": "/tmp",
        "teammate_id": "r1",
        "teammate_type": "Research",
        "reason": "idle",
    }
    event_handlers.handle_teammate_idle_fast(event)

    mock_hook_handler._emit_socketio_event.assert_called_once()
    call_args = mock_hook_handler._emit_socketio_event.call_args
    assert call_args[0][1] == "teammate_idle"
    assert call_args[0][2]["teammate_id"] == "r1"

def test_task_completed_emits_socketio(mock_hook_handler, event_handlers):
    """TaskCompleted handler emits task_completed event to dashboard."""
    event = {
        "session_id": "s1",
        "cwd": "/tmp",
        "task_id": "t1",
        "task_title": "Research auth",
        "completed_by": "r1",
        "status": "completed",
    }
    event_handlers.handle_task_completed_fast(event)

    mock_hook_handler._emit_socketio_event.assert_called_once()
    call_args = mock_hook_handler._emit_socketio_event.call_args
    assert call_args[0][1] == "task_completed"
    assert call_args[0][2]["task_id"] == "t1"
```

---

## 5. Implementation Checklist

| Step | Action | Effort |
|------|--------|--------|
| 1 | Run `claude-mpm agents deploy` to register missing hooks | 1 min |
| 2 | Verify `settings.local.json` contains TeammateIdle + TaskCompleted | 1 min |
| 3 | Convert `_validation_log()` calls per doc 01 Section 3 | 30 min |
| 4 | Add registration unit tests (Section 4 above) | 30 min |
| 5 | Add handler dispatch tests | 20 min |
| 6 | Add dashboard emission tests | 20 min |
| 7 | Run full test suite: `make test` | 5 min |

**Total estimated effort:** ~2 hours

---

## 6. Risk: Hook Event Schema Stability

Per the handler docstrings, these are experimental events and the schema may evolve. Current mitigation:

- Handlers use `.get()` with fallback keys (e.g., `event.get("teammate_id", event.get("agent_id", ""))`)
- All fields have defaults — no KeyError possible
- Dashboard emission uses a normalized data dict — frontend doesn't parse raw events
- If Claude Code changes the schema, handlers gracefully degrade (empty fields, not crashes)

No additional schema stability work needed for Phase 1. If Anthropic publishes a formal schema for Agent Teams events, update the handlers to match.
