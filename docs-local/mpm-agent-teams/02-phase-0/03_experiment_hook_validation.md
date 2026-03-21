# Experiment 3: Hook System Validation

**Validation:** V1 — TeammateIdle/TaskCompleted hooks actually fire
**Effort:** 1 day
**Dependencies:** Experiment 1 (needs a working Agent Teams session with context injection)
**Priority:** HIGH — foundational for Phase 1 observability

---

## Hypothesis

MPM's existing hook handlers for `TeammateIdle` and `TaskCompleted` (written speculatively for Claude Code v2.1.47) will correctly fire and capture useful data during a real Agent Teams session.

---

## Background

### What's Already Wired
MPM has handlers for two Agent Teams hook events:

```python
# hook_handler.py:539-542
"TeammateIdle": self.event_handlers.handle_teammate_idle_fast,
"TaskCompleted": self.event_handlers.handle_task_completed_fast,
```

These handlers extract event data and emit to the Socket.IO dashboard, but:
- They were written speculatively — never validated against real Agent Teams sessions
- Event field names use fallback patterns (`event.get("teammate_id", event.get("agent_id", ""))`)
- The actual event schema from Claude Code may differ from what MPM expects

### What's NOT Wired
- No handler for teammate spawn events (SubagentStart is synthetic/internal only)
- No handler for SendMessage events between teammates
- No enforcement logic — handlers are observe-only

---

## Test Protocol

### Test 1: TeammateIdle Event Validation

**Purpose:** Confirm `TeammateIdle` fires when a teammate goes idle, and MPM correctly captures event data.

**Steps:**
1. Start MPM with Socket.IO dashboard enabled
2. Enable Agent Teams: `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
3. Start a team session with PM as team lead
4. Spawn a Research teammate with a simple task ("List files in src/")
5. Wait for teammate to complete and go idle
6. Check:
   - Did `TeammateIdle` handler fire? (check MPM logs)
   - What fields were in the event? (log the raw event)
   - Did `teammate_id` resolve correctly?
   - Did `teammate_type` resolve correctly?
   - Did Socket.IO dashboard receive the `teammate_idle` emission?

**Instrumentation needed:**
```python
# Temporary logging in handle_teammate_idle_fast
def handle_teammate_idle_fast(self, event):
    import json
    logger.info(f"[PHASE0-VALIDATION] TeammateIdle raw event: {json.dumps(event, indent=2)}")
    # ... existing handler code
```

**Expected fields (from current handler code):**
```json
{
  "teammate_id": "...",       // or "agent_id"
  "teammate_type": "...",     // or "agent_type"
  "reason": "...",            // or "idle_reason"
  "session_id": "...",
  "working_directory": "..."
}
```

### Test 2: TaskCompleted Event Validation

**Purpose:** Confirm `TaskCompleted` fires when a teammate marks a task complete via TaskUpdate.

**Steps:**
1. Same session as Test 1
2. Spawn a teammate and assign it a task via TaskCreate
3. Teammate works and calls TaskUpdate(status="completed")
4. Check:
   - Did `TaskCompleted` handler fire?
   - What fields were in the event?
   - Did `task_id`, `task_title`, `completed_by` resolve correctly?
   - Did Socket.IO dashboard receive the `task_completed` emission?

**Expected fields:**
```json
{
  "task_id": "...",
  "task_title": "...",        // or "title"
  "completed_by": "...",      // or "agent_id"
  "status": "completed"
}
```

### Test 3: Multiple Teammate Events

**Purpose:** Validate that events from multiple teammates are correctly distinguished.

**Steps:**
1. Spawn 3 teammates (Research, Engineer, QA)
2. Assign each a different task
3. Let all 3 complete
4. Verify:
   - 3 separate TeammateIdle events received
   - Each has correct `teammate_id` (distinguishable)
   - Each has correct `teammate_type` (research, engineer, qa)
   - 3 separate TaskCompleted events received
   - Each references correct `task_id`

### Test 4: Event Timing and Ordering

**Purpose:** Understand the timing relationship between events.

**Steps:**
1. Spawn a single teammate
2. Record timestamps of:
   - Agent tool call initiated (PreToolUse)
   - Agent tool call completed (PostToolUse)
   - TaskCompleted event received
   - TeammateIdle event received
3. Document the ordering: Do events arrive in a predictable sequence?

**Expected order:** PreToolUse -> PostToolUse -> [teammate works] -> TaskCompleted -> TeammateIdle

### Test 5: PreToolUse Interception for Agent Tool

**Purpose:** Confirm that PreToolUse fires for Agent tool calls and can return modified input.

**Steps:**
1. Add temporary logging to PreToolUse handler for Agent tool calls
2. Spawn a teammate
3. Verify:
   - PreToolUse fires with `tool_name: "Agent"`
   - `tool_input` contains `prompt`, `subagent_type`, `team_name`
   - Modified `tool_input` is accepted by Claude Code (prompt modification takes effect)
   - Teammate receives the modified prompt

**This is the most critical test for Experiment 1 viability.** If PreToolUse cannot modify Agent tool input, Method A context injection fails.

---

## Event Schema Documentation

After all tests, document the actual event schemas observed:

```markdown
# Agent Teams Hook Event Schemas (Observed)

## TeammateIdle
Fires when: [observed trigger]
Fields:
  - [field]: [type] — [description]
  - ...

## TaskCompleted
Fires when: [observed trigger]
Fields:
  - [field]: [type] — [description]
  - ...

## PreToolUse (Agent tool)
Fires when: [observed trigger]
Available fields:
  - tool_name: "Agent"
  - tool_input: {prompt, subagent_type, team_name, model, ...}
Can modify: [yes/no, which fields]
```

---

## Implementation Plan

### Setup (30 min)
1. Add detailed logging to `handle_teammate_idle_fast` and `handle_task_completed_fast`
2. Add logging to PreToolUse handler for `tool_name == "Agent"`
3. Ensure Socket.IO dashboard is accessible for event monitoring

### Testing (3-4 hours)
4. Run Tests 1-5 sequentially in a single Agent Teams session
5. Capture all logs and event data

### Documentation (2 hours)
6. Write actual event schemas based on observations
7. Document any discrepancies between expected and actual behavior
8. Note any handler fixes needed (field name mismatches, etc.)
9. Write results to `docs-local/mpm-agent-teams/02-phase-0/results/exp3_results.md`

---

## Success Criteria

| Criterion | Threshold |
|-----------|-----------|
| TeammateIdle fires | Yes, for every teammate that goes idle |
| TaskCompleted fires | Yes, for every TaskUpdate(completed) |
| Event fields resolve correctly | All primary fields (id, type, status) |
| Multiple teammates distinguished | Each has unique id |
| PreToolUse intercepts Agent tool | Yes, with modifiable tool_input |
| Event ordering is predictable | Consistent across 3+ runs |

---

## Failure Modes

| Failure Mode | Impact | Mitigation |
|-------------|--------|------------|
| TeammateIdle doesn't fire | Phase 1 loses teammate monitoring | Fall back to PostToolUse on Agent tool for completion detection |
| TaskCompleted doesn't fire | Phase 1 loses task tracking | Use TaskList polling from team lead instead |
| Field names don't match handler expectations | Events silently drop data | Fix field extraction in handlers (quick patch) |
| PreToolUse can't modify Agent tool input | Method A injection fails | Fall back to Method B (deploy-time only) |
| Events fire but Socket.IO emission fails | Dashboard blind to teams | Fix Socket.IO integration (separate issue) |

---

## Artifacts

| Artifact | Purpose |
|----------|---------|
| `results/exp3_results.md` | Test results and observations |
| `results/exp3_event_schemas.md` | Actual event schemas documented |
| Handler fixes (if needed) | Code patches for field name mismatches |
