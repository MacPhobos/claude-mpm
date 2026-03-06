# Claude Code Agent Name Resolution Mechanics

**Date**: 2026-03-05
**Branch**: agenttype-enums
**Status**: Research complete

---

## 1. The Resolution Chain: How Claude Code Matches `subagent_type` to Agent Files

### 1.1 Overview

When a PM (or any agent) delegates work via the `Agent` tool (or `Task` tool, which wraps it), Claude Code resolves the `subagent_type` parameter against the `name:` frontmatter field of deployed `.md` agent files in `.claude/agents/`.

The resolution chain is:

```
PM_INSTRUCTIONS.md text
  -> Model interprets "delegate to **Local Ops**"
    -> Model calls Agent(subagent_type="Local Ops")
      -> Claude Code scans .claude/agents/*.md
        -> Matches name: frontmatter field
          -> .claude/agents/local-ops.md has name: "Local Ops"
            -> Agent spawned with local-ops.md as system prompt
```

### 1.2 Evidence: `subagent_type` Matches Against `name:` Field

From the implementation plan (empirically proven):

- `Agent(subagent_type="Golang Engineer")` -- **succeeds** (matches `name: Golang Engineer` in `.claude/agents/golang-engineer.md`)
- `Agent(subagent_type="golang-engineer")` -- **fails** (no agent has `name: golang-engineer`)

This confirms:
1. **Matching is exact** against the `name:` field value
2. **Matching is NOT against** the filename stem
3. **No fuzzy matching** is performed (no normalization, no case-folding, no hyphen-to-space conversion)

### 1.3 What the Agent Tool Description Shows

The Agent tool's description text lists available agents by their `name:` field values. For example, in this session:

```
Research: Memory-efficient codebase analysis...
Local Ops: Local operations specialist...
Web QA: Progressive 6-phase web testing...
```

These are the exact `name:` field values from the deployed `.claude/agents/*.md` files. The model uses this listing to know what values are valid for `subagent_type`.

### 1.4 The Two-Source Problem

The PM's knowledge of available agents comes from TWO sources:

| Source | What it contains | When it's consulted |
|--------|-----------------|-------------------|
| **Agent tool description** | Lists agents by `name:` field, dynamically generated from deployed `.claude/agents/*.md` files | Every time the model considers using the Agent tool |
| **PM_INSTRUCTIONS.md** (system prompt) | Static text telling PM which agent to delegate to for which task | Read once at PM session start |

**CRITICAL INSIGHT**: If PM_INSTRUCTIONS.md says "delegate to **local-ops**" but the Agent tool shows agents listed as "Local Ops", the model must bridge the gap. Sometimes it will succeed (if it can infer "local-ops" -> "Local Ops"), sometimes it will fail. This is unreliable and wastes inference tokens on resolution attempts.

**The fix is trivial**: Make PM_INSTRUCTIONS.md use the same identifiers that appear in the Agent tool listing -- i.e., the `name:` field values.

---

## 2. How PM_INSTRUCTIONS.md References Become Agent Delegations

### 2.1 The Model's Interpretation Pipeline

When the PM model reads PM_INSTRUCTIONS.md and encounters a delegation instruction like:

```
- User: "Start the app on localhost" -> Delegate to **Local Ops**
```

The model:
1. Parses the instruction: "I should delegate this to the Local Ops agent"
2. Looks at the Agent tool's available agents listing
3. Finds a matching entry (exact `name:` field)
4. Calls `Agent(subagent_type="Local Ops")`

### 2.2 When PM_INSTRUCTIONS.md Uses Filename Stems (Current State)

Currently, many references in PM_INSTRUCTIONS.md use filename stems:

```
- DELEGATE to local-ops
- DELEGATE to web-qa-agent
- DELEGATE to api-qa-agent
```

The model must then:
1. Parse "local-ops" from the instruction
2. Look at the Agent tool listing (which shows "Local Ops")
3. **Attempt to infer** that "local-ops" means "Local Ops"
4. Call `Agent(subagent_type="Local Ops")` -- IF the inference succeeds

This inference step is:
- **Not guaranteed** to succeed
- **Model-dependent** (Opus may handle it differently than Sonnet)
- **Token-wasteful** (inference cycles spent on resolution rather than task planning)
- **Sometimes wrong** (the model might pass `subagent_type="local-ops"` literally, which fails)

### 2.3 The Agent Capabilities Section (Generated at Runtime)

The `AgentCapabilitiesGenerator` (in `src/claude_mpm/services/agents/management/agent_capabilities_generator.py`) generates a section injected into the PM prompt. This section uses a **mixed format**:

```
- **Local Ops** (`local-ops`): Local operations specialist...
```

The template line:
```jinja2
- **{{ cap.name }}** (`{{ cap.id }}`): {{ cap.capability_text }}
```

Where:
- `cap.name` = The cleaned `name:` field (with " Agent" stripped, hyphens to spaces)
- `cap.id` = The agent ID (filename stem)

This provides the PM with BOTH the display name and the ID. However, the template instruction says:

```
Use the agent ID in parentheses when delegating tasks via the Task tool.
```

**PROBLEM**: This instruction tells the PM to use the `id` (filename stem) for delegation. But `subagent_type` resolves against `name:`, not `id`. This creates a contradiction:
- The template says "use `local-ops`"
- But `Agent(subagent_type="local-ops")` fails
- While `Agent(subagent_type="Local Ops")` succeeds

### 2.4 Fix Needed in Agent Capabilities Generator

The template instruction on line 177 currently says:
```
Use the agent ID in parentheses when delegating tasks via the Task tool.
```

This should be changed to instruct the PM to use the **name** (bold text), not the ID:
```
Use the agent name in bold when delegating tasks via the Task/Agent tool.
```

---

## 3. The Task Tool vs Agent Tool

### 3.1 How claude-mpm Routes Delegation

In claude-mpm, the PM typically delegates via the **Task tool** rather than the raw Agent tool. The Task tool wraps the Agent tool and adds tracking, context injection, and other orchestration features.

When PM uses the Task tool, it specifies:
```yaml
agent: "Local Ops"
task: "Start dev server"
```

The `agent` field is passed as `subagent_type` to the underlying Agent tool. Therefore, the same `name:` field matching applies.

### 3.2 Current PM_INSTRUCTIONS.md Task Tool Examples

The PM_INSTRUCTIONS.md already contains an example that uses the `name:` field correctly:

```yaml
Task:
  agent: "Local Ops"
  task: "Start dev server and verify it's running"
```

This is correct -- "Local Ops" matches the `name:` field in `local-ops.md`.

However, other parts of PM_INSTRUCTIONS.md are inconsistent, using filename stems in prose:
```
DELEGATE to local-ops
Delegate to **web-qa-agent** for browser verification
```

---

## 4. Summary of Resolution Mechanics

| Step | Component | What Happens |
|------|-----------|-------------|
| 1 | PM reads system prompt | PM_INSTRUCTIONS.md + generated capabilities section loaded |
| 2 | User makes request | PM decides which agent to delegate to |
| 3 | PM references agent | Extracts agent identifier from instructions or capabilities list |
| 4 | PM calls Task/Agent tool | Passes identifier as `subagent_type` (Task tool) or `agent` parameter |
| 5 | Claude Code resolves | Scans `.claude/agents/*.md`, matches `name:` frontmatter field |
| 6 | Agent spawned | Matching `.md` file loaded as system prompt for subagent |

### Key Takeaways

1. **`subagent_type` must exactly match the `name:` frontmatter field** -- this is the authoritative resolution mechanism
2. **Filename stems do NOT work** as `subagent_type` values (empirically proven)
3. **The model CAN sometimes bridge the gap** between stem format and name format, but this is unreliable
4. **PM_INSTRUCTIONS.md MUST use `name:` field values** for all agent references that will become delegation targets
5. **The Agent Capabilities Generator currently gives contradictory advice** -- it shows the name but tells PM to use the ID
6. **The YAML examples in PM_INSTRUCTIONS.md already use `name:` format** (`agent: "Local Ops"`) -- the prose just needs to catch up
