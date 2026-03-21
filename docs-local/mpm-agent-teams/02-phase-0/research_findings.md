# Phase 0 Research Findings: Agent Teams Integration

**Date**: 2026-03-20
**Researcher**: Research Agent
**Purpose**: Technical due diligence for Phase 0 PoC — validate critical blockers before Agent Teams integration work begins
**GitHub Issue**: #290

---

## Summary of Key Findings

1. **There is NO pre-spawn hook from Claude Code** — `SubagentStart` is MPM-synthetic, not a real CC hook. `PreToolUse` on the Agent tool call IS available as a pre-spawn intercept.
2. **Assembled PM instructions are ~74KB** — already file-based due to Linux ARG_MAX; teammates receive agent file content directly (no PM instructions).
3. **BASE_AGENT.md is 15KB / ~3,800 tokens** — appendable to teammate prompts but each such call inflates PM's accumulated context window significantly.
4. **Deployed agent files are ~59KB each** — they already contain BASE_AGENT.md content (appended during template build). Teammates get this via `.claude/agents/` resolution.
5. **Circuit breakers are PM-only behavioral instructions** — they are conceptual protocols in PM_INSTRUCTIONS.md, NOT enforced by code. Peer-to-peer messaging bypasses them entirely.
6. **No existing tests for teammate context injection** — test infrastructure is pytest-based with hooks integration tests available as patterns.

---

## Area 1: Agent Deployment Pipeline

**Files investigated:**
- `src/claude_mpm/services/agents/deployment/processors/agent_processor.py`
- `src/claude_mpm/services/agents/deployment/agent_template_builder.py`
- `src/claude_mpm/services/agents/deployment/pipeline/steps/agent_processing_step.py`

### Pipeline Steps

```
Template file (.md or .json)
    ↓
AgentTemplateBuilder.build_agent_markdown()   [agent_template_builder.py:331]
    ↓ _parse_markdown_template() — parse YAML frontmatter + markdown body
    ↓ normalize tools, model, description
    ↓ _discover_base_agent_templates() — walk directory tree upward for BASE-AGENT.md files
    ↓ Compose: agent_specific_instructions + local BASE + parent BASE + root BASE
    ↓ Fallback: _load_base_agent_instructions(agent_type) → legacy BASE_{TYPE}.md
    ↓ Join with "\n\n---\n\n" separator
    ↓ Append memory update instructions if not present
    ↓ Prepend YAML frontmatter
    ↓
AgentProcessor._deploy_agent_content()   [processors/agent_processor.py:199]
    ↓
target_file.write_text(content)  →  .claude/agents/{agent-name}.md
```

### BASE_AGENT.md Prepending (agent_template_builder.py:622-653)

```python
# Compose hierarchical BASE-AGENT.md templates
content_parts = [agent_specific_instructions]

# Discover BASE-AGENT.md files in directory hierarchy (closest → farthest)
base_templates = self._discover_base_agent_templates(template_path)

for base_template_path in base_templates:
    base_content = base_template_path.read_text(encoding="utf-8")
    content_parts.append(base_content)

# Fallback to legacy BASE_{TYPE}.md if no hierarchical templates found
if len(content_parts) == 1:
    legacy_base_instructions = self._load_base_agent_instructions(agent_type)
    if legacy_base_instructions:
        content_parts.append(legacy_base_instructions)

# Join with separator
content = "\n\n---\n\n".join(content_parts)
```

**Key: BASE_AGENT.md is baked into the deployed file at deploy time, NOT at agent invocation time.** The deployed `.claude/agents/research.md` already contains BASE_AGENT.md content.

### Output Format

```markdown
---
name: research
description: "..."
model: sonnet
agent_type: research
version: "5.0.0"
skills:
- dspy
- langchain
---

[agent-specific instructions markdown]

---

[BASE_AGENT.md content]

---

## Memory Updates
...
```

### Implications for Phase 0

- **The pipeline CAN be modified** to produce teammate-ready agent files: inject circuit-breaker lite or PM verification context as an additional content part before the final join.
- **However, injection happens at deploy time**, not at spawn time — so any teammate-specific context injected here applies to ALL calls, not just teammates in an Agent Teams session.
- **Opportunistic injection**: A "teammate mode" flag could trigger a different set of BASE templates that include lightweight PM verification context and circuit breaker reminders.

---

## Area 2: BASE_AGENT.md Content and Size

**File**: `src/claude_mpm/agents/BASE_AGENT.md`

### Stats
- **Lines**: 420
- **Bytes**: 15,108
- **Estimated tokens**: ~3,800 (at 4 chars/token)

### Sections

| Section | Lines | Purpose | Critical for Teammates? |
|---------|-------|---------|------------------------|
| Git Workflow Standards | ~30 | Commit message formats | LOW |
| Memory Routing | ~15 | Memory system keywords | MEDIUM |
| Output Format Standards | ~30 | Markdown structure | MEDIUM |
| Handoff Protocol | ~20 | Agent handoff patterns | HIGH |
| Proactive Code Quality Improvements | ~30 | Search-before-implement, mimic patterns | MEDIUM |
| Minimalism Principle | ~30 | Fewer lines is better | HIGH |
| Claude Code Native Capabilities | ~45 | Agent tool, worktree, Agent Teams docs | HIGH |
| Performance-First Engineering | ~40 | Algorithm choice, avoid N+1 | MEDIUM |
| Agent Responsibilities | ~20 | What agents DO/DON'T do | HIGH |
| SELF-ACTION IMPERATIVE | ~40 | Agents execute, don't delegate to users | **CRITICAL** |
| Credential Testing Policy | ~25 | API key validation policy | LOW |
| VERIFICATION BEFORE COMPLETION | ~60 | Evidence required before claiming done | **CRITICAL** |
| Quality Standards | ~20 | Requirements for all work | HIGH |
| Communication Standards | ~15 | Tone and style | LOW |

### BASE_AGENT_LITE.md Feasibility

A "BASE_AGENT_LITE.md" for teammate injection could include:
- Agent Responsibilities (critical guardrails)
- SELF-ACTION IMPERATIVE (agents do work, don't delegate to users)
- VERIFICATION BEFORE COMPLETION (evidence requirement)
- Claude Code Native Capabilities (Agent Teams section — so teammates understand the team structure)
- Minimalism Principle

**Estimated lite size**: ~8,000 bytes / ~2,000 tokens — a 47% reduction.

The critical sections are about behavioral integrity (execute work, verify before claiming done), not tooling or git workflows.

---

## Area 3: PM_INSTRUCTIONS.md Generation

**Key files:**
- `src/claude_mpm/agents/PM_INSTRUCTIONS.md` — source instructions
- `src/claude_mpm/core/framework_loader.py:318` — `get_framework_instructions()`
- `src/claude_mpm/services/instructions/instruction_cache_service.py` — cache service
- `src/claude_mpm/core/interactive_session.py:401` — `_build_claude_command()`

### Assembly Components

From `InstructionCacheService` docstring (`instruction_cache_service.py:8`):
> "BASE_PM + PM_INSTRUCTIONS + WORKFLOW + capabilities + temporal context"

From `SystemInstructionsService`:
- FrameworkLoader assembles: INSTRUCTIONS.md, WORKFLOW.md, MEMORY.md, actual PM memories from `.claude-mpm/memories/PM.md`, Agent capabilities, BASE_PM.md

### Sizes

| Component | Bytes | Lines |
|-----------|-------|-------|
| PM_INSTRUCTIONS.md (source) | 47,802 | 1,155 |
| circuit-breakers.md (template) | 49,569 | 1,400 |
| BASE_AGENT.md | 15,108 | 420 |
| **Assembled PM_INSTRUCTIONS.md** (cached) | **73,876** | **1,659** |

**The assembled instructions are ~74KB / ~18,500 tokens.**

### Launch Mechanism (`interactive_session.py:438-504`)

```python
system_prompt = self.runner._create_system_prompt()

# Try file-based first (preferred, avoids Linux ARG_MAX)
cache_service = InstructionCacheService(project_root=project_root)
cache_result = cache_service.update_cache(instruction_content=system_prompt)

if cache_result.get("updated"):
    cmd.extend(["--system-prompt-file", str(cache_file)])  # line 490
else:
    cmd.extend(["--append-system-prompt", system_prompt])   # line 499
```

**Key**: PM instructions go via `--system-prompt-file` or `--append-system-prompt`, NOT `--system`. This is `--append-system-prompt`, meaning it supplements Claude Code's own system prompt rather than replacing it.

### The Teammate Context Gap

When PM spawns a teammate via the Agent tool:
- Claude Code resolves the agent definition from `.claude/agents/{subagent_type}.md`
- That file is the teammate's system prompt — already ~59KB for research agent
- MPM's PM_INSTRUCTIONS.md is **NOT** passed to teammates
- PM's circuit breakers, skills, and PM verification chains are **NOT** active in teammates

### Implications for Phase 0

- MPM has a well-understood injection point: the `.claude/agents/*.md` file
- A "teammate mode" overlay would be appended to the agent file content at deploy time OR injected via the `prompt` parameter at spawn time
- The PM's assembled instructions at 74KB are too large to inject verbatim into teammate prompts — selective extraction is required

---

## Area 4: Circuit Breaker Definitions

**Files:**
- `src/claude_mpm/agents/templates/circuit-breakers.md` (full definitions)
- `src/claude_mpm/agents/PM_INSTRUCTIONS.md:990-1030` (summary table)

### Complete List (from PM_INSTRUCTIONS.md table)

| # | Name | Trigger | Who Enforces |
|---|------|---------|-------------|
| 1 | Large Implementation | PM using Edit/Write > 5 lines | PM-only |
| 2 | Deep Investigation | PM reading > 3 files / architectural analysis | PM-only |
| 3 | Unverified Assertions | PM claiming status without evidence | PM-only |
| 4 | File Tracking | PM marking complete without git tracking | PM-only |
| 5 | Delegation Chain | PM claiming completion without full workflow | PM-only |
| 6 | Forbidden Tool Usage | PM using mcp-ticketer/browser MCP directly | PM-only |
| 7 | Verification Commands | PM using curl/lsof/ps/wget/nc | PM-only |
| 8 | QA Verification Gate | PM claiming done without QA for multi-component changes | PM-only |
| 9 | User Delegation | PM instructing user to run commands | PM-only |
| 10 | Delegation Failure Limit | >3 delegations to same agent without success | PM-only |

Additional in circuit-breakers.md:
- **#8 Skills Management** — PM doing skill ops directly (should be in mpm-skills-manager)

### Enforcement Mechanism

**CRITICAL FINDING**: Circuit breakers are behavioral instructions in PM's system prompt, NOT code-enforced mechanisms. They work by instructing the LLM to detect and self-correct violations. There is no Python code that blocks tool calls based on these rules.

This means:
- **Peer-to-peer messaging (SendMessage) between teammates completely bypasses ALL circuit breakers**
- A teammate could instruct another teammate to implement directly, bypassing the PM delegation chain
- No hook intercepts SendMessage content to enforce PM verification

### Which Circuit Breakers Could Be Embedded in Teammate Prompts?

For Phase 0, the relevant circuit breakers to consider for teammates:
- CB #3 (Unverified Assertions) — agents should not claim "done" without evidence
- CB #9 (User Delegation) — agents should execute, not delegate back to users

**NOT applicable to teammates** (these are PM orchestration rules):
- CB #1, #2, #5, #6, #7, #8 — these govern PM delegation behavior
- CB #4 — file tracking is PM's QA responsibility
- CB #10 — failure limit is PM orchestration

### Implications for Phase 0

The circuit breaker integrity concern is **valid and confirmed**. Since circuit breakers are LLM behavioral prompts (not code), peer-to-peer messaging in an Agent Teams session could:
1. Have teammate A ask teammate B to implement something without PM verification
2. Have teammates accumulate state without PM oversight
3. Bypass the Research → Implementation → QA pipeline

A minimal guardrail for teammates would be a condensed "teammate protocol" section that emphasizes:
- Always complete work and return results (don't delegate sideways)
- Evidence-based completion claims
- Report all file changes

---

## Area 5: .claude/agents/ Format

**Sample file**: `.claude/agents/research.md` (59,200 bytes, 1,253 lines)

### Format Structure

```markdown
---
name: Research                    ← Matches subagent_type in Agent tool call
description: "..."                ← How Claude decides when to use this agent
version: 5.0.0
schema_version: 1.3.0
agent_id: research-agent
agent_type: research
resource_tier: high
tags:
- research
- memory-efficient
...
capabilities:
  memory_limit: 4096
  cpu_limit: 80
  network_access: true
skills:
- dspy
- langchain
...
---

[Full agent instructions — agent-specific + BASE_AGENT.md]
```

### How Claude Code Resolves Agents

When the Agent tool is called with `subagent_type: "research"`:
1. Claude Code looks for `research.md` in `.claude/agents/` (project-level first)
2. Falls back to `~/.claude/agents/research.md` (user-level)
3. The agent's `name` field (case-insensitive, lowercase) must match the `subagent_type`
4. **The entire file content becomes the teammate's system prompt**

**IMPORTANT**: The `name` field in frontmatter must match kebab-case `subagent_type`. Underscores cause silent failures (`agent_template_builder.py:462-472`):
```python
# CRITICAL: NO underscores allowed - they cause silent failures!
if not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", claude_code_name):
    raise ValueError(...)
```

### Deployed Agents in This Repo

49 agent files in `.claude/agents/` including: documentation, engineer, research, qa, web-qa, api-qa, local-ops, ops, version-control, ticketing, security, python-engineer, typescript-engineer, golang-engineer, rust-engineer, java-engineer, javascript-engineer, ruby-engineer, php-engineer, react-engineer, nextjs-engineer, svelte-engineer, web-ui-engineer, tauri-engineer, data-engineer, data-scientist, dart-engineer, imagemagick, prompt-engineer, refactoring-engineer, agentic-coder-optimizer, clerk-ops, digitalocean-ops, gcp-ops, vercel-ops, project-organizer, tmux, mpm-agent-manager, mpm-skills-manager, memory-manager, product-owner, real-user, code-analyzer, content, aws-ops, nestjs-engineer, visual-basic-engineer, phoenix-engineer.

### Implications for Phase 0

- **Injection point is clear**: modifying the deployed `.md` file adds context to every teammate invocation with that `subagent_type`
- **Agent file already contains BASE_AGENT.md** — no need to inject it separately
- A "teammate context" section injected at deploy time is the cleanest approach for persistent context
- For session-specific context (e.g., "you are part of a team working on TICKET-123"), injection must happen in the Agent tool `prompt` parameter

---

## Area 6: Hook System for Agent Teams Events

**Files:**
- `src/claude_mpm/hooks/claude_hooks/event_handlers.py:1517-1591`
- `src/claude_mpm/hooks/claude_hooks/hook_handler.py:539-542`

### TeammateIdle Handler (event_handlers.py:1517-1551)

```python
def handle_teammate_idle_fast(self, event):
    """Handle TeammateIdle hook event (Claude Code v2.1.47+ Agent Teams)."""
    teammate_id = event.get("teammate_id", event.get("agent_id", ""))
    teammate_type = event.get("teammate_type", event.get("agent_type", "unknown"))
    idle_reason = event.get("reason", event.get("idle_reason", "unknown"))

    teammate_idle_data = {
        "session_id": session_id,
        "working_directory": working_dir,
        "teammate_id": teammate_id,
        "teammate_type": teammate_type,
        "idle_reason": idle_reason,
        "timestamp": ...,
        "hook_event_name": "TeammateIdle",
    }
    self.hook_handler._emit_socketio_event("", "teammate_idle", teammate_idle_data)
```

### TaskCompleted Handler (event_handlers.py:1553-1591)

```python
def handle_task_completed_fast(self, event):
    """Handle TaskCompleted hook event (Claude Code v2.1.47+ Agent Teams)."""
    task_id = event.get("task_id", "")
    task_title = event.get("task_title", event.get("title", ""))
    completed_by = event.get("completed_by", event.get("agent_id", ""))
    completion_status = event.get("status", "completed")
    # → emits socketio "task_completed" event
```

### Registration (hook_handler.py:539-542)

```python
# Agent Teams events (experimental in Claude Code v2.1.47+)
"TeammateIdle": self.event_handlers.handle_teammate_idle_fast,
"TaskCompleted": self.event_handlers.handle_task_completed_fast,
```

### CRITICAL: No Pre-Spawn Hook from Claude Code

From `hook_handler.py:526-532`:
```python
# NOTE: SubagentStart is NOT a registered Claude Code hook event.
# It is a synthetic event synthesized internally by claude-mpm based
# on patterns detected in SubagentStop events (to reconstruct the
# start of a subagent lifecycle). It will never fire from Claude Code
# itself, but the handler exists in the dispatch dict to allow
# internal code paths to emit it via _route_event if needed.
"SubagentStart": self.event_handlers.handle_subagent_start_fast,
```

**CONFIRMED: There is no `AgentSpawn` or pre-spawn hook from Claude Code.**

### The PreToolUse Opportunity

`PreToolUse` fires before ANY tool execution, including the Agent tool. This IS available and IS a real CC hook. MPM already uses it (`hook_handler.py:521`).

A `PreToolUse` handler that:
1. Detects `tool_name == "Agent"`
2. Reads `tool_input.subagent_type`
3. Injects additional context into `tool_input.prompt`

...would work as a **runtime teammate context injection mechanism**. This approach does not require modifying deployed agent files.

### Available Data in Agent Teams Events

| Event | Data Available | Use for Phase 0? |
|-------|---------------|-----------------|
| `TeammateIdle` | teammate_id, type, idle_reason | Monitor, not inject |
| `TaskCompleted` | task_id, title, completed_by, status | Track completion |
| `PreToolUse` (Agent tool) | tool_name, tool_input (prompt, subagent_type, model) | **INJECT CONTEXT HERE** |
| `PostToolUse` | tool output, success/failure | Track results |

### Implications for Phase 0

**Two injection approaches are viable:**
1. **Deploy-time**: Modify agent files in `.claude/agents/` to include teammate protocols (permanent, for all sessions)
2. **Runtime via PreToolUse**: Modify `tool_input.prompt` before the Agent tool executes (dynamic, per-session)

PreToolUse-based injection is the **lower-risk Phase 0 approach** because:
- No permanent file modification
- Can inject session-specific context (team session ID, shared constraints)
- Reversible without redeploying agents
- PreToolUse already returns modified input to Claude Code (line 559: `if (hook_type == "PreToolUse" and result is not None)`)

---

## Area 7: Agent Tool Parameters

**Reference**: `src/claude_mpm/agents/BASE_AGENT.md:142-186` (Claude Code Native Capabilities section)

### Parameters

```json
{
  "subagent_type": "research",     // Maps to .claude/agents/research.md name field
  "isolation": "worktree",         // Optional: creates isolated git worktree
  "prompt": "...",                 // Task description + any injected context
  "run_in_background": true,       // Optional: async execution
  "model": "sonnet"                // Optional: per-teammate model override
}
```

### prompt vs Agent Definition Relationship

From BASE_AGENT.md and the system architecture:
- The agent definition in `.claude/agents/` becomes the **system prompt** for the teammate
- The `prompt` parameter becomes the **user message** / task
- They do NOT conflict — the definition provides identity and instructions, prompt provides the task
- **Context injection into `prompt` works**: additional instructions in the prompt supplement the agent definition

### model Parameter

- YES, `model` controls model per-teammate
- PM's routing table (`PM_INSTRUCTIONS.md:495-503`): Engineer/Research → `sonnet`, Ops → `haiku`
- User preferences override

### Maximum Prompt Size

No explicit limit found in codebase. Practical ceiling:
- Claude's context window is 200K tokens
- Agent definition file is already ~15K tokens (59KB)
- Reasonable remaining context for prompt: ~180K tokens
- **Injection budget**: comfortably 2,000-5,000 tokens for teammate protocol overhead

### Implications for Phase 0

- Inject via `prompt` parameter: lightweight, safe, no file changes needed
- The `PreToolUse` hook already has access to `tool_input` and can modify `prompt`
- A 2,000-token "teammate protocol" block is well within limits

---

## Area 8: Existing Test Infrastructure

**Test framework**: pytest with `uv run pytest`
**Parallelization**: `-n auto` for full suite, `-p no:xdist` for debugging (per CLAUDE.md)

### Relevant Test Files

| File | Content | Relevance to Phase 0 |
|------|---------|---------------------|
| `tests/integration/test_hook_handler_integration.py` | Real component hook integration | Pattern for hook testing |
| `tests/hooks/test_subagent_start_fix.py` | SubagentStart event handling | Pattern for agent event tests |
| `tests/hooks/test_auto_pause_handler.py` | Auto-pause hook testing | Hook testing pattern |
| `tests/integration/test_native_agents_integration.py` | Native --agents flag | Agent command building |
| `tests/integration/agents/test_agent_id_fix.py` | Agent ID handling | Agent deployment testing |
| `tests/eval/agents/` | Agent behavior evaluation | Behavioral testing patterns |
| `tests/eval/metrics/` | Metrics for agent quality | Quality measurement patterns |

### Test Patterns Found

```python
# Integration test pattern (from test_hook_handler_integration.py)
@patch("src.claude_mpm.hooks.claude_hooks.hook_handler.ConnectionManagerService")
@pytest.mark.integration
def test_complete_event_flow_session_start(self, ...):
    # Uses real StateManager + DuplicateDetector
    # Patches external services

# Agent test pattern (from test_native_agents_integration.py)
def test_interactive_session_build_command_with_native_agents(self):
    runner = ClaudeRunner(use_native_agents=True)
    session = InteractiveSession(runner)
    cmd = session._build_claude_command()
    assert "--agents" in cmd
```

### No Existing Tests for Teammate Context Injection

Confirmed: there are no existing tests for:
- Agent tool `prompt` modification via PreToolUse
- Teammate protocol injection
- Agent Teams hook events (TeammateIdle, TaskCompleted)

### How to Test Teammate Context Injection

**Unit test approach**:
```python
# Test that PreToolUse hook modifies Agent tool prompt
def test_pretooluse_injects_teammate_context():
    handler = ClaudeHookHandler(...)
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Agent",
        "tool_input": {"subagent_type": "research", "prompt": "investigate X"}
    }
    result = handler.handle_event(event)
    assert "teammate protocol" in result["tool_input"]["prompt"]
```

**Integration test approach**: Simulate a full PreToolUse→Agent tool call cycle with real hook handler.

---

## Area 9: Model Selection in Current MPM

**Reference**: `src/claude_mpm/agents/PM_INSTRUCTIONS.md:465-535`

### Model Routing Table

| Agent Type | Default Model | Rationale |
|------------|--------------|-----------|
| Engineer (all languages) | `sonnet` | Excellent code at 60% Opus cost |
| Research | `sonnet` | Pattern analysis is structured |
| QA (all types) | `sonnet` | Test writing follows patterns |
| Security | `sonnet` | Known attack patterns |
| Code Analysis | `sonnet` | Strong analytical capability |
| PM (self) | Inherits session model | User chose it |
| Ops (all types) | `haiku` | Deployment commands are deterministic |
| Documentation Agent | `haiku` | Writing from existing code is structured |

### How Model is Passed to Subagents

From `PM_INSTRUCTIONS.md:526-535`:
```
PM delegates with model:
PM: [Delegates to engineer with model: "sonnet"]
PM: [Delegates to QA with model: "sonnet"]
PM: [Delegates to ops with model: "haiku"]
```

The `model` field in the Agent tool call overrides the agent file's `model` frontmatter field.

### Agent Teams Model Behavior

- The Agent tool `model` parameter IS respected for teammates
- If not specified in the Agent tool call, the agent file's `model` frontmatter is used
- If neither specifies model, Claude Code inherits the parent session model

### Implications for Phase 0

For Phase 0 PoC:
- Model routing works today via the Agent tool `model` parameter
- The `model` field in deployed agent files provides a sensible default
- No changes needed to model routing for Phase 0

---

## Area 10: Context Window Sizes

### Token Budget Analysis

| Component | Bytes | ~Tokens (÷4) | Notes |
|-----------|-------|--------------|-------|
| BASE_AGENT.md | 15,108 | ~3,777 | Already in all deployed agents |
| PM_INSTRUCTIONS.md source | 47,802 | ~11,951 | PM system prompt only |
| circuit-breakers.md | 49,569 | ~12,392 | Referenced in PM_INSTRUCTIONS |
| **Assembled PM_INSTRUCTIONS.md** | **73,876** | **~18,469** | What PM actually receives |
| research.md (deployed) | 59,200 | ~14,800 | What research teammate receives |
| BASE_AGENT_LITE.md (proposed) | ~8,000 | ~2,000 | Estimated for critical sections only |

### Why 450KB Was Mentioned in InstructionCacheService

From `instruction_cache_service.py:5`:
> "Linux systems have ARG_MAX limits (~128-256KB) that prevent passing assembled PM instructions (~450KB) via CLI arguments"

The 450KB figure may be from an older version or includes additional runtime context. Current cached file is 73,876 bytes. Either way, the design already uses file-based loading.

### Teammate Context Window Budget

When a teammate is spawned:
- System prompt = agent definition file (~59KB = ~14,800 tokens)
- Additional context from `prompt` parameter = task description
- Claude's 200K token context window leaves ~185K tokens for conversation

**Injection budget at spawn time**: The `prompt` parameter can safely carry:
- BASE_AGENT_LITE.md equivalent: ~2,000 tokens
- Circuit breaker mini-rules (3-5 key CBs): ~500 tokens
- Team session context (PM instructions excerpt, team ID): ~1,000 tokens
- **Total overhead per teammate spawn**: ~3,500 tokens

This is **well within limits** but adds to PM's accumulated context window across multiple delegations.

### PM Context Window Degradation Risk

When PM spawns N teammates with injected context:
- Each Agent tool result returns to PM's context
- If each result includes the injected prompt echoed back, PM context grows by ~3,500 tokens × N teammates
- For a typical session with 5-10 agent delegations: 17,500 - 35,000 additional tokens
- Against PM's 200K context: manageable but non-negligible

**Recommendation**: Keep teammate injected context to a minimum — focus on critical behavioral rules only, not full BASE_AGENT.md.

---

## Critical Findings for Phase 0 Planning

### Blocker 1: Teammate Context Gap — Assessment

**Severity**: CONFIRMED BLOCKER
**Mechanism**: Clear injection points exist
**Best approach**: PreToolUse hook modifying Agent tool `prompt` parameter
**Alternative**: Deploy-time agent file modification

The PreToolUse approach is lower-risk for Phase 0 because:
1. No permanent file modification
2. Session-specific context can be injected (team ID, task context)
3. PreToolUse already returns modified input (hook_handler.py:559-564)
4. Can be toggled via environment variable without affecting normal MPM operation

### Blocker 2: Circuit Breaker Integrity — Assessment

**Severity**: CONFIRMED BLOCKER
**Root cause**: Circuit breakers are LLM behavioral prompts, NOT code enforcement
**Peer-to-peer risk**: Real — SendMessage between teammates bypasses all PM oversight

**What's needed for Phase 0 PoC**:
- Instrument PreToolUse for Agent tool calls (to detect when teammates spawn sub-agents)
- Instrument PostToolUse for SendMessage calls (to log/monitor peer-to-peer)
- Verify that TeammateIdle/TaskCompleted hooks actually fire in a real Agent Teams session
- Test whether injecting a "report back to PM" constraint in teammate prompt reduces unauthorized delegation

### Surprises and Concerns

1. **SubagentStart is synthetic** — expected it to be a real CC hook. Phase 0 must use PreToolUse for pre-spawn interception.

2. **Agent files are already 59KB** — adding another 2KB of "teammate protocol" is relatively small overhead but the files are complex. Consider whether injection into `prompt` vs file modification is cleaner.

3. **Circuit breakers are purely prompt-based** — there's no code fallback. If an LLM ignores the instructions (especially in peer-to-peer messages), MPM has no mechanism to enforce them. Phase 0 needs to assess LLM compliance rate empirically.

4. **TeammateIdle/TaskCompleted handlers are stub-level** — they receive events and emit to socketio but take no enforcement action. There's room to add enforcement logic here.

5. **PreToolUse already returns modified input** — this is the key enabler. The infrastructure for runtime injection already exists and is used by MPM for other purposes. The Phase 0 work may be smaller than anticipated.

6. **No tests for Agent Teams events exist** — the handlers were written speculatively in v2.1.47 but never validated against real Agent Teams sessions. Phase 0 must include this validation as a primary goal.

---

## Appendix: File Paths Quick Reference

| Purpose | Path |
|---------|------|
| BASE_AGENT.md source | `src/claude_mpm/agents/BASE_AGENT.md` |
| PM_INSTRUCTIONS.md source | `src/claude_mpm/agents/PM_INSTRUCTIONS.md` |
| circuit-breakers.md | `src/claude_mpm/agents/templates/circuit-breakers.md` |
| Assembled PM instructions cache | `.claude-mpm/PM_INSTRUCTIONS.md` |
| Deployed agent files | `.claude/agents/*.md` |
| Agent template builder | `src/claude_mpm/services/agents/deployment/agent_template_builder.py` |
| Agent processor | `src/claude_mpm/services/agents/deployment/processors/agent_processor.py` |
| Hook handler dispatch | `src/claude_mpm/hooks/claude_hooks/hook_handler.py:518-542` |
| TeammateIdle handler | `src/claude_mpm/hooks/claude_hooks/event_handlers.py:1517` |
| TaskCompleted handler | `src/claude_mpm/hooks/claude_hooks/event_handlers.py:1553` |
| Claude launch command builder | `src/claude_mpm/core/interactive_session.py:401` |
| Instruction cache service | `src/claude_mpm/services/instructions/instruction_cache_service.py` |
| Hook integration tests | `tests/integration/test_hook_handler_integration.py` |
| SubagentStart hook tests | `tests/hooks/test_subagent_start_fix.py` |
