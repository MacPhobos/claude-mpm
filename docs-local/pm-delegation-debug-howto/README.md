# PM Delegation Debug & Traceability Guide

## Purpose

When modifying PM prompt files (e.g., `src/claude_mpm/agents/PM_INSTRUCTIONS.md`, `WORKFLOW.md`, `MEMORY.md`), you need to verify that Claude Code correctly delegates to the intended agents and skills. This guide documents every debug channel and verification technique available in claude-mpm.

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [The System Prompt Pipeline](#2-the-system-prompt-pipeline)
3. [Debug Channel 1: System Prompt Logs](#3-debug-channel-1-system-prompt-logs)
4. [Debug Channel 2: Hook Debug Logging](#4-debug-channel-2-hook-debug-logging)
5. [Debug Channel 3: Startup Logs](#5-debug-channel-3-startup-logs)
6. [Debug Channel 4: CLI Debug Commands](#6-debug-channel-4-cli-debug-commands)
7. [Debug Channel 5: Diagnostics (Doctor)](#7-debug-channel-5-diagnostics-doctor)
8. [Debug Channel 6: Event Log](#8-debug-channel-6-event-log)
9. [Debug Channel 7: SocketIO Event Monitor](#9-debug-channel-7-socketio-event-monitor)
10. [Debug Channel 8: Delegation Detector](#10-debug-channel-8-delegation-detector)
11. [Practical Verification Workflows](#11-practical-verification-workflows)
12. [Gaps and Limitations](#12-gaps-and-limitations)

---

## 1. Architecture Overview

Claude-mpm injects PM behavior into Claude Code through a **system prompt suffix** mechanism. The chain is:

```
PM_INSTRUCTIONS.md (source)
        |
        v
FrameworkLoader (loads + assembles)
        |
        v
ContentFormatter (formats sections)
        |
        v
CapabilityGenerator (discovers deployed agents)
        |
        v
SystemInstructionsService (serves to Claude Code)
        |
        v
Claude Code's system_prompt_suffix (injected via hooks)
        |
        v
Claude Code LLM (receives full system prompt)
        |
        v
Agent delegation decisions (by the LLM)
```

**Key insight**: Claude-mpm does NOT programmatically control which agent gets delegated to. The PM prompt **instructs** the LLM to delegate, and the LLM makes the routing decision based on the prompt text. This means:

- There is no "delegation router" in code that you can step through
- Agent selection happens inside the LLM based on prompt content
- Verification must focus on (a) what prompt was injected, and (b) what the LLM actually did

### Files That Affect PM Behavior

| File | Location | What It Controls |
|------|----------|-----------------|
| `PM_INSTRUCTIONS.md` | `src/claude_mpm/agents/` | Core PM behavior, circuit breakers, delegation rules |
| `WORKFLOW.md` | `src/claude_mpm/agents/` | 5-phase workflow, QA gates, verification protocols |
| `MEMORY.md` | `src/claude_mpm/agents/` | Memory system, static memory management |
| `BASE_PM.md` | `src/claude_mpm/agents/` | Base framework requirements (appended after INSTRUCTIONS) |
| Agent templates | `src/claude_mpm/agents/templates/*.json` | Agent metadata, routing keywords, memory routing |
| Deployed agents | `.claude/agents/*.md` | What agents are available for delegation |
| Deployed skills | `.claude/skills/*.md` | What skills are available for invocation |

---

## 2. The System Prompt Pipeline

### How the prompt gets assembled

The `FrameworkLoader` class (`src/claude_mpm/core/framework_loader.py`) orchestrates assembly:

1. **`InstructionLoader.load_all_instructions()`** - Loads PM_INSTRUCTIONS.md, WORKFLOW.md, MEMORY.md
2. **`MemoryManager.load_memories()`** - Loads PM.md from `.claude-mpm/memories/`
3. **`AgentLoader.load_agents_directory()`** - Discovers agent definitions
4. **`ContentFormatter.format_full_framework()`** - Assembles the final prompt:
   - INSTRUCTIONS.md content (stripped of metadata comments)
   - Custom INSTRUCTIONS.md if present (project-level overrides)
   - WORKFLOW.md content
   - MEMORY.md content
   - Actual PM memories from `.claude-mpm/memories/PM.md`
   - **Agent capabilities section** (dynamically generated from deployed agents)
   - **Temporal/user context** (date, user, system info)
   - BASE_PM.md content
   - Output style (for older Claude Code versions)

### Agent Capabilities Discovery

The `CapabilityGenerator` (`src/claude_mpm/core/framework/formatters/capability_generator.py`) builds the "Available Agent Capabilities" section by:

1. Scanning `.claude/agents/*.md` for deployed agent files
2. Parsing YAML frontmatter from each agent file
3. Loading routing metadata from JSON templates (`src/claude_mpm/agents/templates/*.json`)
4. Generating a formatted section listing each agent with:
   - Display name and ID (used in Task tool delegation)
   - Description
   - Routing keywords, paths, priority
   - Memory routing info
   - Authority, model, tools

**This is the section the LLM reads to decide which agent to delegate to.**

---

## 3. Debug Channel 1: System Prompt Logs

### What it captures

Every time `FrameworkLoader.get_framework_instructions()` is called, it logs the complete assembled system prompt to disk via the `LogManager`.

### Where to find them

```
.claude-mpm/logs/prompts/system_prompt_YYYYMMDD_HHMMSS_mmm.md
```

### How to use

```bash
# Find the most recent system prompt log
ls -lt .claude-mpm/logs/prompts/system_prompt_*.md | head -5

# Read the latest one
cat "$(ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1)"

# Search for specific agent mentions in the prompt
grep -n "python-engineer\|Engineer\|Research" "$(ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1)"

# Verify a specific agent appears in capabilities section
grep -A5 "Available Agent Capabilities" "$(ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1)"

# Check total prompt size (important for context window limits)
wc -c "$(ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1)"
```

### What to look for after modifying PM files

1. **Agent capabilities section** - Does it list the agents you expect?
2. **Routing keywords** - Are the routing hints correct for each agent?
3. **Workflow instructions** - Are your workflow changes reflected?
4. **Memory instructions** - Are memory configurations present?
5. **Prompt size** - Is the total prompt within reasonable bounds (~60-70KB)?
6. **Section ordering** - Instructions -> Workflow -> Memory -> Memories -> Capabilities -> Context -> BASE_PM

### Code path

```
FrameworkLoader.get_framework_instructions()
  -> FrameworkLoader._log_system_prompt()
    -> LogManager.log_prompt("system_prompt", instructions, metadata)
      -> writes to .claude-mpm/logs/prompts/
```

Source: `src/claude_mpm/core/framework_loader.py:480-523`

### Retention

System prompt logs are retained for **7 days** (168 hours) by default. Configurable via `logging.prompt_retention_hours` in configuration.

---

## 4. Debug Channel 2: Hook Debug Logging

### What it captures

The hook handler processes every Claude Code event (UserPromptSubmit, PreToolUse, PostToolUse, SubagentStop, etc.) and can log detailed event data.

### How to enable

```bash
export CLAUDE_MPM_HOOK_DEBUG=true
```

### Where to find logs

```
/tmp/claude-mpm-hook.log
```

### What gets logged

When `CLAUDE_MPM_HOOK_DEBUG=true`:

- Every hook event received (type, keys, session_id)
- Event routing decisions
- Delegation tracking (which agent was delegated to)
- Duplicate event detection
- Subagent start/stop events
- Hook execution timing
- Error details

### How to use

```bash
# Enable debug mode
export CLAUDE_MPM_HOOK_DEBUG=true

# Start a Claude Code session, perform some actions, then:
tail -f /tmp/claude-mpm-hook.log

# Filter for delegation-related events
grep -i "delegation\|subagent\|agent_type" /tmp/claude-mpm-hook.log

# Filter for tool usage events (shows what PM is calling)
grep "PreToolUse\|PostToolUse" /tmp/claude-mpm-hook.log

# See subagent lifecycle (agent delegation and completion)
grep "SubagentStart\|SubagentStop" /tmp/claude-mpm-hook.log
```

### Key events for delegation tracing

| Event | What It Tells You |
|-------|------------------|
| `UserPromptSubmit` | User's prompt was received; shows prompt preview |
| `PreToolUse` with `tool_name=Task` | PM is about to delegate to an agent |
| `SubagentStart` | A subagent (delegated agent) has started |
| `SubagentStop` | A subagent has completed; shows agent_type and reason |
| `PostToolUse` | Tool call completed; shows exit_code |

### Code path

```
hook_handler.py main()
  -> ClaudeHookHandler.handle()
    -> _route_event()
      -> EventHandlers.handle_pre_tool_fast()  # for PreToolUse
      -> EventHandlers.handle_subagent_stop_fast()  # for SubagentStop
    -> _emit_hook_execution_event()  # structured event emitted
```

Source: `src/claude_mpm/hooks/claude_hooks/hook_handler.py:123-139`

### Important caveat

Hook debug logging is **intentionally suppressed by default** because ANY output to stderr from a hook is interpreted by Claude Code as a hook error. All debug output goes to the file, never stderr.

---

## 5. Debug Channel 3: Startup Logs

### What it captures

Comprehensive startup information including framework loading, agent discovery, MCP server status, and memory usage.

### Where to find them

```
.claude-mpm/logs/startup/startup-YYYY-MM-DD-HH-MM-SS.log
```

### How to use

```bash
# Read the most recent startup log
cat "$(ls -t .claude-mpm/logs/startup/startup-*.log | head -1)"

# Check what agents were discovered during startup
grep -i "agent\|deploy\|capabilit" "$(ls -t .claude-mpm/logs/startup/startup-*.log | head -1)"

# Check framework loading
grep -i "framework\|instruction\|loaded" "$(ls -t .claude-mpm/logs/startup/startup-*.log | head -1)"
```

### What it captures relevant to delegation

- Framework version loaded
- Number of agents discovered
- Agent capability cache status
- MCP server configuration
- Memory loading status
- API key validation

### Code path

```
startup_logging.py:setup_startup_logging()
  -> Adds file handler to claude_mpm logger
  -> All subsequent log calls captured
```

Source: `src/claude_mpm/cli/startup_logging.py:480-562`

---

## 6. Debug Channel 4: CLI Debug Commands

### Available commands

```bash
# Debug deployed agents
claude-mpm debug agents --deployed

# Trace a specific agent
claude-mpm debug agents --trace <agent-name>

# Debug agent memory
claude-mpm debug agents --memory

# Debug hooks
claude-mpm debug hooks

# Debug services
claude-mpm debug services --list
claude-mpm debug services --status
claude-mpm debug services --dependencies
claude-mpm debug services --trace <service-name>

# Debug cache
claude-mpm debug cache

# Debug SocketIO events (live monitor)
claude-mpm debug socketio
claude-mpm debug socketio --raw
claude-mpm debug socketio --filter-types hook_execution

# Debug performance
claude-mpm debug performance
```

### Most useful for PM delegation debugging

```bash
# See what agents are deployed and available
claude-mpm debug agents --deployed

# This shows:
# - Agent file paths
# - File sizes
# - Modification dates
# - Locations (project vs user level)
```

Source: `src/claude_mpm/cli/commands/debug.py`

---

## 7. Debug Channel 5: Diagnostics (Doctor)

### What it checks

The `claude-mpm doctor` command runs comprehensive diagnostics including agent health:

```bash
claude-mpm doctor
claude-mpm doctor --verbose
```

### Agent-specific checks

- **Deployed Agents**: Counts deployed agents, checks for missing core agents
- **Agent Versions**: Checks if agents are up-to-date vs cached versions
- **Agent Validation**: Validates agent file structure (Identity section, minimum size)
- **Common Issues**: Checks for duplicates, permission issues

### Instructions checks

- **CLAUDE.md Placement**: Verifies CLAUDE.md is in project root only
- **Duplicate Content**: Detects duplicated paragraphs across instruction files
- **Conflicting Directives**: Finds PM role definitions, delegation rules, etc. in multiple files
- **Agent Definitions**: Finds agents defined in multiple places
- **Separation of Concerns**: Ensures MPM content isn't in CLAUDE.md and vice versa

### How to use for PM debugging

```bash
# Run full diagnostics
claude-mpm doctor --verbose

# Look specifically at agent and instructions results
claude-mpm doctor --verbose 2>&1 | grep -A5 "Agent\|Instructions"
```

Source: `src/claude_mpm/services/diagnostics/checks/agent_check.py` and `instructions_check.py`

---

## 8. Debug Channel 6: Event Log

### What it captures

Persistent JSON event log for system events including delegation anti-patterns detected.

### Where to find it

```
.claude-mpm/event_log.json
```

### How to use

```bash
# View the event log
cat .claude-mpm/event_log.json | python3 -m json.tool

# Filter for delegation-related events
python3 -c "
import json
events = json.load(open('.claude-mpm/event_log.json'))
for e in events:
    if 'delegation' in e.get('event_type', '').lower():
        print(json.dumps(e, indent=2))
"
```

Source: `src/claude_mpm/services/event_log.py`

---

## 9. Debug Channel 7: SocketIO Event Monitor

### What it captures

Real-time event stream of all hook executions, including delegation events, tool usage, and subagent lifecycle.

### How to use

```bash
# Start live event monitor
claude-mpm debug socketio --pretty

# Filter for hook execution events only
claude-mpm debug socketio --filter-types hook_execution

# Save events to file for analysis
claude-mpm debug socketio --output /tmp/events.json

# Raw event format
claude-mpm debug socketio --raw
```

### What to watch for

The hook handler emits structured `hook_execution` events that include:
- `hook_name`: Event type (PreToolUse, SubagentStop, etc.)
- `tool_name`: For PreToolUse/PostToolUse - which tool was called
- `agent_type`: For SubagentStop - which agent completed
- `duration_ms`: How long the hook took
- `prompt_preview`: First 100 chars of user prompt
- `result_summary`: Human-readable summary

### Prerequisites

Requires the SocketIO monitor server to be running:
```bash
claude-mpm monitor start
```

Source: `src/claude_mpm/hooks/claude_hooks/hook_handler.py:620-685`

---

## 10. Debug Channel 8: Delegation Detector

### What it captures

Detects anti-patterns in PM output where the PM instructs the user to do something manually instead of delegating.

### Patterns detected

- "Make sure to X" -> Should delegate verification
- "You'll need to run X" -> Should delegate execution
- "Please run X" -> Should delegate execution
- "Remember to X" -> Should delegate task
- "Don't forget to X" -> Should delegate task
- "You should/can/could X" -> Suggested delegation

### How it works

The `DelegationDetector` scans PM output text and returns structured detections:

```python
from claude_mpm.services.delegation_detector import get_delegation_detector

detector = get_delegation_detector()
detections = detector.detect_user_delegation(pm_output_text)
for d in detections:
    print(f"Anti-pattern: {d['pattern_type']}")
    print(f"Original: {d['original_text']}")
    print(f"Should be: {d['suggested_todo']}")
```

### Integration with hooks

The delegation detector is loaded lazily in the event handlers and can scan PM responses during hook processing.

Source: `src/claude_mpm/services/delegation_detector.py`

---

## 11. Practical Verification Workflows

### Workflow A: Verify PM instructions changes are applied

After modifying `PM_INSTRUCTIONS.md`:

```bash
# 1. Clear caches to force reload
claude-mpm cache clear  # if available, or delete .claude-mpm/cache/

# 2. Start a new Claude Code session
claude

# 3. Check the generated system prompt
ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1 | xargs cat | head -100

# 4. Search for your specific changes
grep -n "your_new_text" "$(ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1)"
```

### Workflow B: Verify agent routing

```bash
# 1. Check deployed agents
claude-mpm debug agents --deployed

# 2. Verify agent appears in system prompt capabilities section
grep -A3 "python-engineer\|rust-engineer\|YOUR_AGENT" \
  "$(ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1)"

# 3. Check routing keywords in template
cat src/claude_mpm/agents/templates/your-agent.json | python3 -m json.tool | grep -A10 routing

# 4. Enable hook debug and test
export CLAUDE_MPM_HOOK_DEBUG=true
# Start Claude session, ask it to do something that should route to your agent
# Then check:
grep "SubagentStart\|SubagentStop\|Task" /tmp/claude-mpm-hook.log
```

### Workflow C: Verify skill loading

```bash
# 1. Check deployed skills
ls .claude/skills/

# 2. Verify skill appears in system prompt
grep "your-skill-name" "$(ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1)"

# 3. Skills are referenced via the Skill tool in Claude Code
# The PM prompt section "PM Skills System" lists available skills
grep -A20 "PM Skills System" "$(ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1)"
```

### Workflow D: End-to-end delegation trace

```bash
# 1. Enable all debug channels
export CLAUDE_MPM_HOOK_DEBUG=true

# 2. Start Claude Code
claude

# 3. Submit a prompt that should trigger specific delegation
# e.g., "Implement a new API endpoint"

# 4. After the session, trace the full flow:

# a) What prompt was injected?
cat "$(ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1)" | wc -c
# Should see ~60-70KB of PM instructions

# b) What hook events occurred?
cat /tmp/claude-mpm-hook.log | grep -E "Processing hook|tool_name|agent_type"

# c) Was delegation attempted?
cat /tmp/claude-mpm-hook.log | grep -i "PreToolUse.*Task\|SubagentStart"

# d) What agent was selected?
cat /tmp/claude-mpm-hook.log | grep "SubagentStop" | tail -5

# e) Check startup log for any issues
cat "$(ls -t .claude-mpm/logs/startup/startup-*.log | head -1)" | grep -i "error\|warning\|agent"
```

### Workflow E: Compare prompts before and after changes

```bash
# 1. Before making changes, save the current prompt
cp "$(ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1)" /tmp/prompt-before.md

# 2. Make your changes to PM_INSTRUCTIONS.md

# 3. Start a new Claude Code session to generate a new prompt

# 4. Compare
diff /tmp/prompt-before.md "$(ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1)"
```

---

## 12. Gaps and Limitations

### What you CANNOT directly observe

1. **LLM's internal routing decision**: The LLM reads the PM prompt and decides which agent to delegate to. There is no code-level routing logic to step through. The "routing" happens inside the model's inference.

2. **Real-time prompt inspection**: You can only see the system prompt **after** it's been logged. There's no way to intercept it before it reaches Claude Code.

3. **Skill trigger evaluation**: Skills are loaded by Claude Code based on trigger conditions in their frontmatter. Whether a skill activates depends on Claude Code's internal matching, not claude-mpm code.

4. **Agent response content**: The hook system captures SubagentStart and SubagentStop events but does NOT capture the full content of what the subagent returns. You see that delegation happened, but not the full response.

5. **Claude Code's own system prompt**: Claude-mpm injects via `system_prompt_suffix`. Claude Code adds its own base system prompt before this. You only see the MPM-injected portion in the logs.

### What you CAN observe and verify

| Aspect | How to Verify | Debug Channel |
|--------|--------------|---------------|
| PM instructions content | Read system prompt logs | Prompt logs |
| Agent capabilities listed | Grep capabilities section | Prompt logs |
| Agent routing keywords | Check JSON templates | File inspection |
| Hook events fired | Enable CLAUDE_MPM_HOOK_DEBUG | Hook debug log |
| Delegation attempted | Check for Task PreToolUse | Hook debug log |
| Subagent lifecycle | SubagentStart/Stop events | Hook debug log |
| Agent deployment status | `claude-mpm debug agents` | CLI debug |
| Instructions conflicts | `claude-mpm doctor` | Diagnostics |
| Anti-pattern detection | DelegationDetector | Event log |
| Real-time events | SocketIO monitor | SocketIO debug |

### Recommended improvements

If deeper traceability is needed, consider:

1. **Agent selection logging**: Add logging in `event_handlers.py` when a Task tool call is detected, extracting the agent name from the tool parameters.

2. **Prompt diff tool**: A CLI command like `claude-mpm debug prompt-diff` that compares the current prompt against a baseline.

3. **Agent routing test harness**: A test that feeds sample prompts to the capability generator and verifies expected agents appear with correct routing metadata.

4. **Delegation audit log**: A structured log that captures every Task tool invocation with the agent name, task description, and outcome.

---

## Quick Reference Card

```
# See what prompt was injected
ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1 | xargs cat

# Enable hook debug logging
export CLAUDE_MPM_HOOK_DEBUG=true
tail -f /tmp/claude-mpm-hook.log

# Check deployed agents
claude-mpm debug agents --deployed

# Run diagnostics
claude-mpm doctor --verbose

# View event log
cat .claude-mpm/event_log.json | python3 -m json.tool

# Live event monitor
claude-mpm debug socketio --pretty

# Check startup log
cat "$(ls -t .claude-mpm/logs/startup/startup-*.log | head -1)"

# Search prompt for specific content
grep "SEARCH_TERM" "$(ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1)"
```
