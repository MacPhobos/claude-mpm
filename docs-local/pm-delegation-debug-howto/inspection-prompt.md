# PM Delegation Inspection Prompt

Paste the following into a separate Claude Code session to inspect PM operation.

---

```
Inspect the claude-mpm PM delegation pipeline to verify correct operation. Do ALL of the following steps and report findings:

1. **System Prompt Log** - Read the most recent system prompt log:
   - Run: ls -t .claude-mpm/logs/prompts/system_prompt_*.md | head -1
   - Read that file and report:
     a) Total size in bytes
     b) Whether "Available Agent Capabilities" section exists
     c) How many agents are listed in the capabilities section (count the ### headers)
     d) Whether these key sections exist: "Workflow Instructions", "Memory Instructions", "Current PM Memories", "Context-Aware Agent Selection", "Temporal & User Context"
     e) List the first 5 agent IDs found in the capabilities section

2. **Deployed Agents** - Check what agents are actually deployed:
   - Run: ls .claude/agents/*.md 2>/dev/null | wc -l
   - Run: ls .claude/agents/*.md 2>/dev/null | head -20
   - Compare count against the number listed in the system prompt capabilities section from step 1

3. **Deployed Skills** - Check what skills are deployed:
   - Run: ls .claude/skills/*.md 2>/dev/null | wc -l
   - Run: ls .claude/skills/*.md 2>/dev/null | head -10

4. **Hook Configuration** - Verify hooks are configured:
   - Read .claude/settings.local.json
   - Report which hook types are configured (PreToolUse, PostToolUse, UserPromptSubmit, SubagentStop, SessionStart, Stop)
   - Verify the hook command scripts exist (check if the paths in the config are valid files)

5. **Startup Log** - Read the most recent startup log:
   - Run: ls -t .claude-mpm/logs/startup/startup-*.log | head -1
   - Read that file and report any ERROR or WARNING lines
   - Report whether framework loading succeeded

6. **Hook Debug Log** - Check if hook debug logging is active:
   - Run: cat /tmp/claude-mpm-hook.log 2>/dev/null | tail -20
   - If the file exists, report the most recent events
   - If it doesn't exist, note that CLAUDE_MPM_HOOK_DEBUG is not enabled

7. **Event Log** - Check for delegation anti-patterns:
   - Run: cat .claude-mpm/event_log.json 2>/dev/null | python3 -m json.tool 2>/dev/null | head -30
   - Report any pending events

8. **Prompt Integrity Check** - In the system prompt log from step 1:
   - grep for "Circuit Breaker" - report if circuit breaker rules are present
   - grep for "DELEGATION" - report if delegation rules are present
   - grep for "Available Agent Capabilities" and count lines until next "##" header to see full agent list
   - Check that the prompt ends with temporal context (date, user info)

Present findings in a structured report with PASS/WARN/FAIL for each check.
```
