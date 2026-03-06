# Code Reference: PM Delegation Pipeline

## Source Files and Their Roles

### Prompt Assembly Pipeline

| File | Role | Key Functions |
|------|------|---------------|
| `src/claude_mpm/core/framework_loader.py` | Main orchestrator for prompt assembly | `get_framework_instructions()`, `_format_full_framework()`, `_generate_agent_capabilities_section()`, `_log_system_prompt()` |
| `src/claude_mpm/core/framework/formatters/content_formatter.py` | Formats the assembled prompt sections | `format_full_framework()`, `format_minimal_framework()` |
| `src/claude_mpm/core/framework/formatters/capability_generator.py` | Generates "Available Agent Capabilities" section | `generate_capabilities_section()`, `parse_agent_metadata()` |
| `src/claude_mpm/core/framework/loaders/instruction_loader.py` | Loads PM_INSTRUCTIONS.md, WORKFLOW.md, MEMORY.md | `load_all_instructions()` |
| `src/claude_mpm/core/framework/formatters/context_generator.py` | Generates temporal/user context | `generate_temporal_user_context()` |
| `src/claude_mpm/services/system_instructions_service.py` | Service layer for loading instructions | `load_system_instructions()`, `create_system_prompt()` |

### Hook System (Runtime Event Processing)

| File | Role | Key Functions |
|------|------|---------------|
| `src/claude_mpm/hooks/claude_hooks/hook_handler.py` | Main hook entry point; reads stdin events | `handle()`, `_route_event()`, `_emit_hook_execution_event()` |
| `src/claude_mpm/hooks/claude_hooks/event_handlers.py` | Individual event type handlers | `handle_user_prompt_fast()`, `handle_pre_tool_fast()`, `handle_subagent_stop_fast()` |
| `src/claude_mpm/hooks/claude_hooks/services/state_manager.py` | Tracks delegation state | `track_delegation()`, `get_delegation_agent_type()` |
| `src/claude_mpm/hooks/claude_hooks/services/duplicate_detector.py` | Deduplicates hook events | `is_duplicate()` |
| `.claude/settings.local.json` | Hook configuration for Claude Code | Defines which hooks fire and what scripts handle them |

### Logging Infrastructure

| File | Role | Key Functions |
|------|------|---------------|
| `src/claude_mpm/core/log_manager.py` | Unified log management with async writing | `log_prompt()`, `setup_logging()`, `cleanup_old_logs()` |
| `src/claude_mpm/core/logging_config.py` | Logger factory and configuration | `get_logger()`, `configure_logging()`, `log_operation()` |
| `src/claude_mpm/core/logger.py` | Base logger with JSON formatter | `get_logger()`, `setup_logging()` |
| `src/claude_mpm/cli/startup_logging.py` | Startup log capture | `setup_startup_logging()`, `get_latest_startup_log()` |

### Diagnostics

| File | Role | Key Functions |
|------|------|---------------|
| `src/claude_mpm/services/diagnostics/checks/agent_check.py` | Agent health diagnostics | `_check_deployed_agents()`, `_check_agent_versions()`, `_validate_agents()` |
| `src/claude_mpm/services/diagnostics/checks/instructions_check.py` | Instruction file diagnostics | `_check_claude_md_placement()`, `_check_duplicates()`, `_check_conflicts()` |
| `src/claude_mpm/cli/commands/debug.py` | CLI debug commands | `debug_agents()`, `debug_hooks()`, `debug_services()`, `debug_socketio()` |

### Anti-Pattern Detection

| File | Role | Key Functions |
|------|------|---------------|
| `src/claude_mpm/services/delegation_detector.py` | Detects delegation anti-patterns in PM output | `detect_user_delegation()`, `format_as_autotodo()` |
| `src/claude_mpm/services/event_log.py` | Persistent event storage | `append_event()`, `list_events()`, `get_stats()` |

### Agent/Skill Deployment

| File | Role | Key Functions |
|------|------|---------------|
| `src/claude_mpm/services/agents/agent_selection_service.py` | Agent selection strategies | `deploy_minimal_configuration()`, `deploy_auto_configure()` |
| `src/claude_mpm/services/agents/toolchain_detector.py` | Detects project toolchain | `detect_toolchain()`, `recommend_agents()` |
| `src/claude_mpm/services/dynamic_skills_generator.py` | Generates dynamic selection skills | `generate_agent_selection_skill()`, `generate_tool_selection_skill()` |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CLAUDE_MPM_HOOK_DEBUG` | `false` | Enable hook debug logging to `/tmp/claude-mpm-hook.log` |
| `CLAUDE_MPM_SKIP_CLEANUP` | `0` | Skip log cleanup on startup |
| `CLAUDE_SESSION_ID` | (set by Claude) | Session identifier used in prompt logs |

---

## Log File Locations

| Log Type | Path Pattern | Retention |
|----------|-------------|-----------|
| System prompts | `.claude-mpm/logs/prompts/system_prompt_*.md` | 7 days |
| Startup logs | `.claude-mpm/logs/startup/startup-*.log` | 48 hours |
| MPM logs | `.claude-mpm/logs/mpm/mpm_*.log` | 48 hours |
| Session logs | `.claude-mpm/logs/sessions/` | 7 days |
| Hook debug | `/tmp/claude-mpm-hook.log` | Manual cleanup |
| Event log | `.claude-mpm/event_log.json` | Manual cleanup |

---

## Hook Configuration

The hooks are configured in `.claude/settings.local.json`:

```json
{
  "hooks": {
    "PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "...claude-hook-handler.sh"}]}],
    "PostToolUse": [{"matcher": "*", "hooks": [...]}],
    "UserPromptSubmit": [{"matcher": "*", "hooks": [...]}],
    "SubagentStop": [{"matcher": "*", "hooks": [...]}],
    "SessionStart": [{"matcher": "*", "hooks": [...]}],
    "Stop": [{"matcher": "*", "hooks": [...]}]
  }
}
```

All hooks route through the same handler script, which invokes `hook_handler.py`. The handler reads the event from stdin, routes to the appropriate `EventHandlers` method, and outputs `{"continue": true}` to stdout.

---

## Prompt Assembly Order

The final system prompt is assembled in this exact order by `ContentFormatter.format_full_framework()`:

```
1. PM_INSTRUCTIONS.md content (core PM behavior)
2. [Optional] Custom INSTRUCTIONS.md (project-level overrides)
3. WORKFLOW.md (5-phase workflow, QA gates)
4. MEMORY.md (memory system configuration)
5. PM Memories from .claude-mpm/memories/PM.md
6. Agent Capabilities Section (auto-generated from deployed agents)
7. Context-Aware Agent Selection guidance
8. Temporal & User Context (date, user, system)
9. BASE_PM.md (base framework requirements)
10. [Optional] Output Style (for Claude < 1.0.83)
```

Each section is separated and labeled with markdown headers. The LLM reads this entire prompt as its system instructions and makes delegation decisions based on the content.
