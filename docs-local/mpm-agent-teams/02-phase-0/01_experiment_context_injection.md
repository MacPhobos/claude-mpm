# Experiment 1: Teammate Context Injection PoC

**Blocker:** B1 — Teammate Context Gap
**Effort:** 2-3 days
**Dependencies:** None
**Priority:** CRITICAL — gates all other work

---

## Hypothesis

MPM can inject behavioral protocols into teammates via the `PreToolUse` hook on the Agent tool, causing teammates to follow MPM verification and quality standards at acceptable token cost (< 3,500 tokens per spawn, < 15% of teammate context window).

---

## Background

### The Problem
When the PM (team lead) spawns teammates via the Agent tool with `team_name`, Claude Code launches new processes. MPM controls the initial Claude Code launch (via `--system-prompt-file`) but has **no control** over subsequent teammate launches. Teammates receive:
- Their agent definition from `.claude/agents/{subagent_type}.md` (which includes BASE_AGENT.md)
- The project's CLAUDE.md
- Team tools (SendMessage, TaskList, etc.)

Teammates do **not** receive:
- PM_INSTRUCTIONS.md (74KB, too large to inject)
- Circuit breaker enforcement instructions
- PM verification gate requirements
- Team-specific behavioral constraints

### The Injection Point
`PreToolUse` fires before any tool execution. MPM's hook handler already intercepts it and can return modified `tool_input` back to Claude Code (`hook_handler.py:559-564`). When `tool_name == "Agent"`, we can modify the `prompt` field before Claude Code spawns the teammate.

### What Teammates Already Have
Agent files deployed to `.claude/agents/` already contain BASE_AGENT.md (baked in at deploy time). This provides:
- Git workflow standards
- Self-action imperative
- Verification before completion
- Output format standards

**The gap is team-specific behavioral constraints**, not general agent behavior.

---

## Approach: Three Injection Methods to Test

### Method A: PreToolUse Prompt Injection (Recommended)

**Mechanism:** Hook intercepts Agent tool calls and prepends a "Teammate Protocol" block to the `prompt` parameter.

**Implementation sketch:**
```python
# In hook_handler.py or new teammate_context_injector.py

TEAMMATE_PROTOCOL = """
## MPM Teammate Protocol

You are operating as a teammate in an MPM-managed Agent Teams session.

### Behavioral Requirements
1. COMPLETE your assigned task fully — do not delegate sideways to other teammates
2. VERIFY before claiming done — provide specific evidence (file paths, test output, HTTP responses)
3. REPORT all file changes — list every file created, modified, or deleted
4. Do NOT instruct the user to run commands — execute them yourself
5. When sending results to team lead, include:
   - What was done (specific actions taken)
   - Evidence of completion (test results, file paths, verification output)
   - Any issues encountered or concerns

### Forbidden Actions
- Do NOT claim work is "done" or "working" without evidence
- Do NOT use phrases: "should work", "appears to be working", "looks correct"
- Do NOT delegate your task to another teammate via SendMessage
- Do NOT make changes outside your assigned scope without team lead approval

### Communication Protocol
- Report completion to team lead via SendMessage with evidence
- If blocked, message team lead immediately with specific blocker
- If you discover work outside your scope, create a TaskCreate for it — don't do it yourself
"""

def handle_pretooluse(self, event):
    tool_name = event.get("tool_name")
    tool_input = event.get("tool_input", {})

    if tool_name == "Agent" and tool_input.get("team_name"):
        # This is a teammate spawn — inject protocol
        original_prompt = tool_input.get("prompt", "")
        tool_input["prompt"] = TEAMMATE_PROTOCOL + "\n\n---\n\n" + original_prompt
        return {"tool_input": tool_input}

    return None  # No modification for non-team Agent calls
```

**Token cost:** ~500 tokens for the protocol block
**Pros:** Dynamic, per-session, no file changes, reversible, can include session context
**Cons:** Adds to PM context window (prompt is visible in PM's turn)

### Method B: Deploy-Time Agent File Augmentation

**Mechanism:** During `claude-mpm agents deploy`, append a "Teammate Protocol" section to each agent file in `.claude/agents/`.

**Implementation sketch:**
```python
# In agent_template_builder.py, after BASE_AGENT.md composition

if self.config.get("agent_teams_enabled"):
    teammate_protocol = self._load_teammate_protocol()
    content_parts.append(teammate_protocol)
```

**Token cost:** ~500 tokens per agent file (permanent)
**Pros:** No runtime overhead, no PM context impact, always present
**Cons:** Static (can't include session context), requires redeploy to update, affects ALL agent invocations (not just team spawns)

### Method C: Hybrid (Recommended Final Approach)

**Mechanism:** Deploy-time adds persistent behavioral rules; PreToolUse adds session-specific context.

```
Deploy-time (in agent file):
  - Teammate behavioral protocol (verification, evidence, reporting)
  - Always present, no runtime cost

PreToolUse (at spawn time):
  - Team session context (team name, PM's current task, shared constraints)
  - Only added for team_name Agent calls
```

**Token cost:** ~500 deploy-time + ~200 runtime = ~700 total
**Pros:** Best of both — persistent rules + dynamic context
**Cons:** Two injection points to maintain

---

## Test Protocol

### Test 1: Baseline Behavior (No Injection)

**Purpose:** Measure teammate behavior without any injection to establish a baseline.

**Steps:**
1. Enable Agent Teams: `export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
2. Start MPM session as team lead
3. Spawn 3 teammates (Research, Engineer, QA) via Agent tool with `team_name`
4. Assign each a task that requires:
   - File creation/modification
   - Verification of results
   - Reporting back to team lead
5. Record for each teammate:
   - Did it provide evidence of completion? (Y/N)
   - Did it use forbidden phrases ("should work", etc.)? (Y/N)
   - Did it report file changes? (Y/N)
   - Did it attempt to delegate to other teammates? (Y/N)
   - Did it instruct the user to run commands? (Y/N)

**Expected result:** Teammates will have SOME good behavior (from BASE_AGENT.md in their agent file) but will lack team-specific constraints.

### Test 2: PreToolUse Injection (Method A)

**Purpose:** Measure behavioral improvement from prompt injection.

**Steps:**
1. Implement PreToolUse hook modification (see implementation sketch above)
2. Repeat Test 1 with identical tasks and teammates
3. Record same metrics
4. Compare compliance rates

**Success criteria:**
- Evidence provision rate improves by > 30% over baseline
- Forbidden phrase usage drops by > 50%
- File change reporting improves by > 30%
- Sideways delegation attempts drop to near zero

### Test 3: Token Cost Measurement

**Purpose:** Measure the actual token overhead of injection.

**Steps:**
1. Record PM context window usage before spawning teammates (tokens used)
2. Spawn 3 teammates with Method A injection
3. Record PM context window usage after spawning
4. Calculate: overhead per teammate = (after - before - task_description_tokens) / 3

**Success criteria:**
- Per-teammate overhead < 3,500 tokens
- Total overhead for 3 teammates < 15% of PM's available context

### Test 4: Deploy-Time Injection (Method B)

**Purpose:** Validate that persistent agent file modification works.

**Steps:**
1. Modify agent template builder to append teammate protocol
2. Run `claude-mpm agents deploy` to rebuild agent files
3. Verify protocol appears in `.claude/agents/research.md` (etc.)
4. Repeat Test 1 tasks — verify compliance WITHOUT PreToolUse hook active
5. Verify non-team agent invocations are unaffected (protocol should be ignored when not in team context)

**Success criteria:**
- Compliance rates similar to Test 2
- Non-team invocations show no behavioral regression

### Test 5: Context Window Relief Measurement

**Purpose:** Validate that Agent Teams reduces PM context consumption vs Task tool.

**Steps:**
1. Run a standard 3-agent workflow via Task tool (current model):
   - Research -> Engineer -> QA (sequential)
   - Record PM context usage after each delegation
2. Run the same workflow via Agent Teams:
   - 3 teammates, results via SendMessage
   - Record PM context usage after each message received
3. Compare total PM context consumed

**Success criteria:**
- Agent Teams PM context usage < 70% of Task tool PM context usage
- PM can sustain longer sessions before context saturation

---

## Implementation Plan

### Day 1: Infrastructure

1. **Create `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py`**
   - `TeammateContextInjector` class
   - `TEAMMATE_PROTOCOL` constant (the behavioral block)
   - `inject_context(tool_input: dict) -> dict` method
   - Feature-flagged via `CLAUDE_MPM_AGENT_TEAMS_CONTEXT_INJECTION=1`

2. **Modify `hook_handler.py`**
   - In PreToolUse handler: if `tool_name == "Agent"` and `tool_input.team_name`, call injector
   - Return modified `tool_input` with protocol prepended to `prompt`

3. **Write unit tests**
   - `tests/hooks/test_teammate_context_injector.py`
   - Test injection when team_name present
   - Test NO injection when team_name absent
   - Test injection content correctness
   - Test feature flag toggle

### Day 2: Live Testing

4. **Run Tests 1-3** (baseline, injection, token measurement)
   - Requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`
   - Record all metrics in `docs-local/mpm-agent-teams/02-phase-0/results/exp1_results.md`

5. **Iterate on TEAMMATE_PROTOCOL content**
   - If compliance is low: add more specific instructions
   - If token cost is high: trim non-critical sections
   - Target: maximum compliance at minimum token cost

### Day 3: Deploy-Time & Comparison

6. **Implement Method B** (deploy-time injection)
   - Modify `agent_template_builder.py`
   - Test with `claude-mpm agents deploy`
   - Run Test 4

7. **Run Test 5** (context window comparison)
   - Same-task comparison between Task tool and Agent Teams
   - Record results

8. **Write results document**
   - `docs-local/mpm-agent-teams/02-phase-0/results/exp1_results.md`
   - Include: all metrics, compliance rates, token costs, recommendation

---

## Success Criteria Summary

| Criterion | Threshold | Measurement |
|-----------|-----------|-------------|
| Teammate compliance with evidence requirements | > 80% | Test 2 vs Test 1 |
| Forbidden phrase elimination | > 90% reduction | Test 2 vs Test 1 |
| File change reporting | > 80% | Test 2 |
| Token overhead per teammate | < 3,500 tokens | Test 3 |
| Total token overhead (3 teammates) | < 15% of PM context | Test 3 |
| Non-team invocation regression | 0% | Test 4 |
| PM context relief vs Task tool | > 30% reduction | Test 5 |

---

## Failure Modes and Mitigations

| Failure Mode | Detection | Mitigation |
|-------------|-----------|------------|
| LLM ignores injected protocol | Test 2 compliance < 50% | Escalate: stronger language, more explicit rules, consider code enforcement |
| Token cost exceeds budget | Test 3 > 3,500/teammate | Trim protocol to absolute minimum (evidence + reporting only) |
| PreToolUse hook doesn't fire for Agent tool | Test 2 injection not present | Fall back to Method B (deploy-time only) |
| Deploy-time injection causes regression | Test 4 non-team regression | Gate injection behind `## Agent Teams Protocol` header that teammates recognize |
| Context window relief not measurable | Test 5 < 10% difference | Investigate: are SendMessage results as large as Task tool results? |

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/claude_mpm/hooks/claude_hooks/teammate_context_injector.py` | CREATE | Context injection logic |
| `src/claude_mpm/hooks/claude_hooks/hook_handler.py` | MODIFY | Wire PreToolUse to injector |
| `src/claude_mpm/services/agents/deployment/agent_template_builder.py` | MODIFY | Deploy-time injection (Method B) |
| `tests/hooks/test_teammate_context_injector.py` | CREATE | Unit tests |
| `tests/integration/test_teammate_injection_integration.py` | CREATE | Integration tests |
| `docs-local/mpm-agent-teams/02-phase-0/results/exp1_results.md` | CREATE | Test results |
