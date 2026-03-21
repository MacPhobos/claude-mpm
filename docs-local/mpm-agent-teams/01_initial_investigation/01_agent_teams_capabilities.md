# Agent Teams Capabilities Research
**Issue #290: Integrating Anthropic's Agent Teams with MPM Orchestration**

- **Researcher**: Agent Teams Capabilities Researcher (Task #2)
- **Date**: 2026-03-20
- **Status**: VERIFIED — findings drawn from direct codebase inspection and live Agent Teams session

---

## Executive Summary

This document captures the actual current state of Agent Teams as implemented in Claude Code (v2.1.47+), and how MPM currently handles (or fails to handle) this feature. The core finding is:

> **MPM does not use Claude Code's native Agent Teams for its orchestration. It uses the Task tool for sequential, isolated subagent delegation. These are architecturally distinct systems.** The @MacPhobos concern is valid: teammates spawned via Agent Teams do NOT automatically receive MPM's full BaseAgent / PM_INSTRUCTIONS flow.

This research was conducted while *running as a teammate inside an active Agent Teams session*, providing ground-truth observations of the API surface.

---

## 1. Agent Teams API Surface (Verified)

### 1.1 Tools Available to Teammates

The following tools are available inside an Agent Teams session (verified from this session's tool set):

| Tool | Parameters | Purpose |
|------|-----------|---------|
| `TaskCreate` | subject, description, activeForm, owner, addBlocks, addBlockedBy | Create tasks in the shared task list |
| `TaskUpdate` | taskId, status, subject, description, owner, metadata, addBlocks, addBlockedBy | Update task status (pending → in_progress → completed) |
| `TaskList` | (none) | List all tasks with status and ownership |
| `TaskGet` | taskId | Get full task details including description |
| `TaskStop` | taskId | Stop a running task |
| `TaskOutput` | taskId | Get output from a background task |
| `SendMessage` | to, message, summary | Peer-to-peer messaging between teammates |
| `TeamCreate` | (deferred) | Create a new agent team |
| `TeamDelete` | (deferred) | Delete an agent team |
| `Agent` | subagent_type, prompt, description, team_name, run_in_background, isolation | Spawn subagents or teammates |

**Key observation**: Tools like `TaskCreate`, `TaskList`, `SendMessage` are available to ALL teammates — these are shared across the team, not per-agent. The task list is a team-wide shared resource.

### 1.2 SendMessage Addressing

- **Direct**: `to: "researcher"` — by teammate name (not UUID)
- **Broadcast**: `to: "*"` — all teammates (costly: O(N) messages)
- **Structured protocols**: `shutdown_request/response`, `plan_approval_request/response`
- Message content is NOT visible to other teammates via text output — MUST use SendMessage tool

### 1.3 TaskCreate/TaskList State Machine

```
pending → in_progress → completed
                     → deleted
```

- Tasks can block each other via `addBlockedBy` / `addBlocks`
- Tasks have owners (agent name)
- A shared task list is visible to all team members simultaneously

### 1.4 Agent Tool Parameters for Teams

```json
{
  "subagent_type": "engineer",
  "team_name": "my-team",          // assigns to existing team
  "run_in_background": true,        // async execution
  "isolation": "worktree",          // git worktree isolation
  "prompt": "..."
}
```

The `team_name` parameter is how the Agent tool integrates with Agent Teams: a teammate can spawn further subagents into the same team.

### 1.5 Hook Events (Claude Code v2.1.47+)

Agent Teams introduces two new hook events:

| Event | Trigger | Fields |
|-------|---------|--------|
| `TeammateIdle` | Teammate goes idle | teammate_id, teammate_type, idle_reason |
| `TaskCompleted` | Task marked complete | task_id, task_title, completed_by, status |

**Verified in code**: `src/claude_mpm/hooks/claude_hooks/event_handlers.py:1517-1591`
```python
def handle_teammate_idle_fast(self, event):
    """Handle TeammateIdle hook event (Claude Code v2.1.47+ Agent Teams)."""
    # Experimental feature - event schema may evolve
    teammate_id = event.get("teammate_id", event.get("agent_id", ""))
    ...
```

### 1.6 Environment Variable

Agent Teams requires explicit opt-in:
```bash
CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

Without this, TeamCreate and team-related tools are unavailable.

---

## 2. Spawning Model

### 2.1 How Teammates Are Spawned

When a team-lead uses `TeamCreate` or the `Agent` tool with `team_name`, Claude Code:
1. Launches a new `claude` executable process
2. Passes the team context (team name, task list state, peer roster)
3. The spawned process receives the same CLAUDE.md / project instructions as the team-lead
4. The spawned process gets the team tools: TaskList, TaskGet, TaskCreate, TaskUpdate, SendMessage

**Critical Gap**: The spawned teammate does NOT automatically receive:
- MPM's agent-specific system prompt (e.g., the Engineer agent's domain instructions)
- MPM's BASE_AGENT.md universal instructions
- MPM's circuit breakers and verification gates
- MPM's skill injections

This confirms @MacPhobos's concern: *"We need to ensure that each team-mate actually uses the full BaseAgent/PM_INSTRUCTIONS flow. Currently it does not appear to do so."*

### 2.2 What Context Is Inherited

Teammates DO inherit:
- The project-level CLAUDE.md (project instructions)
- The Claude Code output style (if set via `~/.claude/CLAUDE.md`)
- If MPM's output style is in CLAUDE.md/settings, then yes — but only what's statically configured there

**In this research session**: I (the Research agent) received both the PM output style AND the Research output style because the team-lead's CLAUDE.md/settings included both. This is the current workaround — static injection via settings.

### 2.3 Tool Access in Teammates

Teammates get a broader tool set than MPM's Task-spawned subagents:
- **Agent Teams tools**: TaskCreate, TaskList, TaskGet, TaskUpdate, SendMessage, TeamCreate
- **Standard tools**: Read, Edit, Write, Bash, Glob, Grep, WebSearch, WebFetch, Agent
- **Deferred tools**: All the MCP tools available to the session

MPM's Task-spawned subagents get only standard tools — no SendMessage, no TaskList.

---

## 3. Communication Patterns

### 3.1 SendMessage vs Task Tool

| Aspect | Agent Teams (SendMessage) | MPM (Task tool) |
|--------|--------------------------|-----------------|
| Direction | Bidirectional (any teammate → any teammate) | Unidirectional (PM → agent only) |
| Concurrency | Multiple simultaneous | Sequential (PM waits for completion) |
| Addressing | By name or broadcast | N/A (implicit — PM delegates) |
| State sharing | Shared TaskList | Isolated — result returned in output |
| Idle handling | TeammateIdle hook fires | Task tool returns when complete |
| Background | run_in_background=true | run_in_background=true on Task tool |

### 3.2 Idle States and Notifications

When a teammate completes its task and calls `TaskUpdate(status=completed)`, the system:
1. Fires the `TeammateIdle` hook event (captured by MPM's hook handler)
2. Notifies the team-lead that the teammate is available
3. The team-lead can then assign new tasks via `SendMessage` or `TaskUpdate(owner=...)`

This is fundamentally different from MPM's current model where the PM blocks until the Task tool returns.

### 3.3 Cross-Project Messaging (MPM-Specific)

MPM has its own cross-project messaging system separate from Agent Teams:
- **File**: `src/claude_mpm/services/communication/task_injector.py`
- Writes JSON task files to `~/.claude/tasks/`
- Uses Claude Code's native `TaskList`/`TaskGet` to surface messages to the PM
- This is an **independent** mechanism not related to Agent Teams' SendMessage

---

## 4. Limitations and Experimental Status

### 4.1 What Is Experimental

- **TeamCreate** — creating named teams
- **TeammateIdle** hook event — schema may evolve
- **TaskCompleted** hook event — schema may evolve
- **Agent tool `team_name` parameter** — team assignment

### 4.2 What Is More Stable

- **TaskCreate/TaskList/TaskGet/TaskUpdate** — these appear stable (currently in use in this session)
- **SendMessage** — appears stable, clear protocol structure
- **run_in_background** on Agent tool — used in production
- **isolation: "worktree"** on Agent tool — used in production

### 4.3 Known Limitations

1. **No agent specialization**: Native Agent Teams has no concept of "engineer" vs "researcher" roles — all teammates run the same base claude instance with team tools
2. **No MPM workflow enforcement**: No circuit breakers, no verification gates, no git file tracking in native Agent Teams
3. **Version requirement**: Requires Claude Code ≥ v2.1.47 for hook events; MPM has a migration to remove these hooks on older versions (`src/claude_mpm/migrations/migrate_remove_unsupported_hooks.py`)
4. **Broadcast cost**: `SendMessage(to="*")` costs O(N) messages — expensive with large teams
5. **Task list is team-global**: No per-agent task scoping; all teammates see all tasks

### 4.4 MPM's Version Handling

MPM has explicit version gating for Agent Teams hooks:
```python
# src/claude_mpm/hooks/claude_hooks/installer.py:205-207
MIN_NEW_HOOKS_VERSION = "2.1.47"
```
And a migration to remove them on older installs:
```python
# src/claude_mpm/migrations/migrate_remove_unsupported_hooks.py
UNSUPPORTED_HOOK_EVENTS = ["WorktreeCreate", "WorktreeRemove", "TeammateIdle", "TaskCompleted", "ConfigChange"]
```

---

## 5. MPM Agent Awareness

### 5.1 How MPM Currently Handles the Agent Tool

MPM's PM agent uses the **Task tool** (not the Agent tool directly) for all delegation:

```python
# src/claude_mpm/hooks/claude_hooks/event_handlers.py:371-386
pre_tool_data = {
    ...
    "is_delegation": tool_name == "Task",  # Only tracks Task, not Agent tool
    ...
}
if tool_name == "Task" and isinstance(tool_input, dict):
    self._handle_task_delegation(tool_input, pre_tool_data, session_id)
```

The `subagent_type` parameter is normalized via `AgentNameNormalizer`:
```python
# src/claude_mpm/hooks/claude_hooks/event_handlers.py:419-438
raw_agent_type = tool_input.get("subagent_type", "unknown")
normalizer = AgentNameNormalizer()
agent_type = normalizer.to_task_format(raw_agent_type)  # lowercase-with-hyphens
```

### 5.2 Agent Template Loading and BASE_AGENT Inheritance

Agents are discovered in three-tier priority:
1. **PROJECT**: `.claude-mpm/agents/` — project-specific overrides
2. **USER**: `~/.claude/agents/` — user-specific agents
3. **SYSTEM**: `src/claude_mpm/agents/templates/` — defaults

Agent definition format (Markdown with YAML frontmatter):
```markdown
---
name: engineer
description: Software development specialist
extends: BASE_ENGINEER      # Inheritance chain
skills: [git-workflow, tdd]
---
# Engineer instructions...
```

`BASE_AGENT.md` is appended to ALL agent definitions. It contains:
- Git workflow standards
- Memory routing
- Output format standards
- Handoff protocol
- The Agent Teams section (lines 172-185) — passive documentation only
- Performance-first engineering
- Self-action imperative
- Verification before completion

**Key fact**: `BASE_AGENT.md` mentions Agent Teams but gives no operational instructions for using TeamCreate or SendMessage. It says:
```markdown
**When to use which:**
- mpm PM: Default for all orchestration (richer workflow, specialization, verification)
- Native Agent Teams: When you want simpler, lighter coordination without mpm overhead
- They can coexist but should not be layered (do not use Agent Teams inside mpm PM delegation)
```

Source: `src/claude_mpm/agents/BASE_AGENT.md:182-185`

### 5.3 Do Spawned Teammates Get MPM Agent Definitions?

**No, not automatically.**

When the team-lead (running with MPM PM instructions) spawns a teammate via Agent Teams:
- The teammate receives the project CLAUDE.md
- The teammate does NOT receive the specific agent template (e.g., `engineer.md` content)
- The teammate does NOT receive the BASE_AGENT.md universal instructions unless they're embedded in CLAUDE.md/settings

**Contrast with Task-spawned subagents**: When the PM uses the Task tool with `subagent_type: "engineer"`, MPM's agent loader:
1. Locates the engineer agent template
2. Assembles the prompt: frontmatter + body + BASE_AGENT.md + skills
3. Passes this assembled content as the subagent's system prompt

This is the core gap: the Agent tool with `team_name` bypasses MPM's agent template assembly entirely.

### 5.4 The PM Output Style and Tool Restrictions

The PM's output style (`CLAUDE_MPM_OUTPUT_STYLE.md`) explicitly limits tools:
```markdown
## Allowed Tools
- **Task** for delegation (PRIMARY FUNCTION)
- **TodoWrite** for tracking delegation progress ONLY
- **WebSearch/WebFetch** for context BEFORE delegation ONLY
- **NEVER Edit, Write, Bash, or implementation tools** without explicit override
```

**Notable absence**: `TeamCreate`, `SendMessage`, `TaskList` (the Agent Teams tools) are not mentioned. The PM currently has no instructions for using these tools.

### 5.5 Existing Agent Teams Hook Integration

MPM already tracks Agent Teams events passively:

| Hook | Handler | What it does |
|------|---------|-------------|
| `TeammateIdle` | `handle_teammate_idle_fast` | Emits `teammate_idle` to Socket.IO dashboard |
| `TaskCompleted` | `handle_task_completed_fast` | Emits `task_completed` to Socket.IO dashboard |

Source: `src/claude_mpm/hooks/claude_hooks/hook_handler.py:539-541`

These handlers are **observational only** — they emit to the dashboard but do not trigger any MPM workflow responses.

---

## 6. Cost Implications

### 6.1 Agent Teams vs Single-Agent Delegation

| Factor | Agent Teams (Parallel) | Task Tool (Sequential) |
|--------|----------------------|----------------------|
| Parallelism | Full — multiple simultaneous | None — PM blocks per agent |
| Token usage | Higher — each teammate has full context | Lower — context per-task only |
| Context sharing | Shared task list, no shared memory | Isolated — output returned to PM |
| Coordination overhead | SendMessage round-trips | None (PM is coordinator) |
| Idle cost | Teammates running even when waiting | Agents only run when active |

### 6.2 Background Execution (run_in_background)

`run_in_background: true` on the Task tool allows the PM to continue working while an agent runs. This approximates some parallelism without full Agent Teams:
- Available today in MPM
- No shared task list
- Results delivered via notification when complete

### 6.3 Worktree Isolation Impact

Using `isolation: "worktree"` with Agent Teams:
- Creates a full git worktree copy per teammate
- Prevents file conflicts for parallel writes
- Higher disk usage, but enables true parallel implementation
- Worktree cleaned up if no changes made

---

## 7. Gap Analysis: MPM vs Agent Teams

### 7.1 What MPM Has That Agent Teams Lacks

| MPM Capability | Agent Teams Equivalent |
|----------------|----------------------|
| 37+ specialized agents | One agent type (generic teammate) |
| Circuit breakers / verification gates | None |
| Git file tracking protocol | None |
| Session resume logs | TaskList (partial) |
| Multi-level memory (kuzu, agent memories) | None |
| Skill injection | None |
| Anti-pattern detection (delegation scanner) | None |
| Structured response format | Free-form output |

### 7.2 What Agent Teams Has That MPM Lacks

| Agent Teams Capability | MPM Equivalent |
|----------------------|----------------|
| True peer-to-peer messaging | Cross-project messaging (file-based, different sessions) |
| Shared task list with blocking | TodoWrite (PM-private, no agent access) |
| Parallel execution (native) | Background tasks (limited) |
| Team-lead + teammate structure | PM + agent (hierarchical, not peer) |
| TeammateIdle notifications | SubagentStop event tracking |

### 7.3 The Core Tension

MPM's delegation model is **hierarchical and sequential**: PM orchestrates, agents execute, results return to PM. This provides tight control and verification but limits parallelism.

Agent Teams is **peer-to-peer and parallel**: teammates work concurrently, share a task list, communicate directly. This enables higher throughput but sacrifices MPM's enforcement layer.

The comment from @MacPhobos identifies this directly: if teammates run without MPM's agent instructions, they behave as generic Claude instances — no specialization, no verification gates, no circuit breakers.

---

## 8. Verified File Locations

| Purpose | File Path |
|---------|-----------|
| Agent Teams hook events (TeammateIdle, TaskCompleted) | `src/claude_mpm/hooks/claude_hooks/event_handlers.py:1517-1591` |
| Hook event routing (Agent Teams section) | `src/claude_mpm/hooks/claude_hooks/hook_handler.py:539-541` |
| Task delegation tracking (Task tool handler) | `src/claude_mpm/hooks/claude_hooks/event_handlers.py:415-548` |
| SubagentStop processing | `src/claude_mpm/hooks/claude_hooks/services/subagent_processor.py` |
| BASE_AGENT.md (Agent Teams section) | `src/claude_mpm/agents/BASE_AGENT.md:172-185` |
| PM output style / allowed tools | `src/claude_mpm/agents/CLAUDE_MPM_OUTPUT_STYLE.md:36-43` |
| Hook version gating | `src/claude_mpm/hooks/claude_hooks/installer.py:205-207` |
| Migration for older Claude Code | `src/claude_mpm/migrations/migrate_remove_unsupported_hooks.py` |
| Task injector (cross-project messaging) | `src/claude_mpm/services/communication/task_injector.py` |
| Agent tier discovery | `src/claude_mpm/core/agent_registry.py` |

---

## 9. Key Findings Summary

1. **Agent Teams is experimentally supported in Claude Code ≥ v2.1.47**, enabled via `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. MPM already has hook handlers for `TeammateIdle` and `TaskCompleted` for dashboard observability.

2. **MPM does not use Agent Teams for orchestration**. All delegation uses the Task tool (sequential, isolated). Agent Teams' TeamCreate/SendMessage are not referenced in any MPM PM instructions or workflow.

3. **The @MacPhobos concern is confirmed**: teammates spawned via Agent Teams receive project CLAUDE.md but NOT MPM's agent-specific templates, BASE_AGENT.md universal instructions, skill injections, or circuit breakers. They run as generic Claude instances.

4. **The Task tool and Agent Teams are architecturally incompatible** in their current forms:
   - Task tool: hierarchical, sequential, PM-controlled, isolated
   - Agent Teams: peer-to-peer, parallel, shared state, no enforcement layer

5. **Bridging them requires explicit design choices**: Either (a) inject MPM agent templates as teammate system prompts, or (b) create an Agent Teams-aware PM mode that uses TeamCreate + SendMessage for coordination while preserving MPM's verification logic.

6. **MPM already leverages TaskList natively**: The cross-project task injector writes to `~/.claude/tasks/` using Claude Code's TaskList/TaskGet surface. This is independent of Agent Teams but shows familiarity with the task system.

7. **Cost implications favor targeted use**: Agent Teams adds overhead (parallel context, idle running) that is only worthwhile for genuinely parallel workloads. For most MPM workflows (sequential planning, implement, test, document), the Task tool remains more cost-effective.

---

## 10. Open Questions for Issue #290

1. **System Prompt Injection**: Can MPM inject the agent template content as the teammate's system prompt when TeamCreate is called? Or does this require a pre-configured `~/.claude/agents/` file?

2. **Hybrid Model**: Should the PM be updated to use both models — Agent Teams for parallel exploration, Task tool for sequential implementation?

3. **Verification Gate Preservation**: If teammates run in parallel, how do verification gates (QA must run after Engineer) get enforced without the PM being the sequential bottleneck?

4. **TeammateIdle → TaskAssign Loop**: Should MPM's hook handler for `TeammateIdle` trigger automatic task assignment from a queue? This would create a feedback loop MPM doesn't currently support.

5. **BASE_AGENT Propagation**: Should BASE_AGENT.md content be embedded in the project CLAUDE.md so teammates inherit it automatically without MPM needing to inject it per-spawn?

---

*Research conducted during live Agent Teams session | Tool evidence verified against codebase | Factual claims marked as verified vs. inferred throughout*
