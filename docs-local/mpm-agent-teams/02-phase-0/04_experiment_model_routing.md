# Experiment 4: Model Routing & Context Window Validation

**Validation:** V2 (Model Routing) + V3 (Context Window Relief)
**Effort:** 1 day
**Dependencies:** Experiment 1 (needs working Agent Teams session)
**Priority:** HIGH — validates primary motivation for integration

---

## Hypothesis

1. Per-teammate model selection via the Agent tool's `model` parameter works reliably in Agent Teams, enabling cost-optimized team compositions.
2. Agent Teams measurably reduces PM (team lead) context window consumption compared to the Task tool model, enabling longer and more complex sessions.

---

## Part A: Per-Teammate Model Routing

### Background

MPM's current model routing table (PM_INSTRUCTIONS.md):

| Agent Type | Default Model | Cost Ratio |
|------------|--------------|------------|
| Engineer | sonnet | 1.0x |
| Research | sonnet | 1.0x |
| QA | sonnet | 1.0x |
| Ops | haiku | ~0.3x |
| Documentation | haiku | ~0.3x |
| Code Analysis | sonnet | 1.0x |

In Agent Teams, each teammate's model is set via the `model` parameter on the Agent tool call. The agent file's frontmatter `model` field provides a default. The Agent tool `model` overrides the file default.

### Test Protocol

#### Test A1: Model Override Verification

**Purpose:** Confirm that the Agent tool `model` parameter actually controls teammate model.

**Steps:**
1. Deploy research agent with `model: sonnet` in frontmatter
2. Spawn teammate: `Agent(subagent_type="research", model="haiku", team_name="test", prompt="...")`
3. Verify teammate runs on Haiku (check response characteristics / self-identification)
4. Repeat with `model="opus"` — verify Opus characteristics

**Pass criteria:** Teammate model matches Agent tool `model` parameter, overriding file default.

#### Test A2: Mixed-Model Team Composition

**Purpose:** Validate a realistic mixed-model team.

**Steps:**
1. Create a team with:
   - Team lead: Opus (inherited from session)
   - Research teammate: Sonnet (`model: "sonnet"`)
   - Engineer teammate: Sonnet (`model: "sonnet"`)
   - Ops teammate: Haiku (`model: "haiku"`)
2. Assign each a task appropriate to their role
3. Verify:
   - All teammates complete their tasks successfully
   - Haiku teammate handles ops task adequately (start server, check process)
   - Sonnet teammates handle complex tasks (code analysis, implementation)
   - No model-related failures

**Pass criteria:** All teammates complete tasks. Haiku adequate for ops. No quality regression from mixed models.

#### Test A3: Cost Estimation

**Purpose:** Estimate cost savings from mixed-model teams.

**Steps:**
1. Run a standard 3-agent workflow (Research -> Engineer -> QA) with all Sonnet teammates
2. Run the same workflow with optimized routing (Research: Sonnet, Engineer: Sonnet, QA: Sonnet, with future Ops tasks on Haiku)
3. Record token usage per teammate (input + output)
4. Calculate cost using published pricing:
   - Opus: $15/$75 per 1M tokens (input/output)
   - Sonnet: $3/$15 per 1M tokens
   - Haiku: $0.25/$1.25 per 1M tokens

**Pass criteria:** Mixed-model team achieves >= 20% cost reduction vs uniform Sonnet for workflows including ops/documentation tasks.

---

## Part B: Context Window Relief

### Background

**The problem:** In MPM's current Task tool model, every agent's results return into the PM's context window. For a typical multi-phase workflow:

```
PM Context Growth (Task tool model):
  Start:                          ~20K tokens (PM instructions + project context)
  After Research returns:         +5-15K tokens (research findings in PM context)
  After Engineer returns:         +3-10K tokens (implementation summary in PM context)
  After QA returns:               +2-5K tokens (test results in PM context)
  Total PM context consumed:      30-50K tokens
```

With Agent Teams, teammates operate in independent context windows. The PM receives only SendMessage summaries:

```
PM Context Growth (Agent Teams model):
  Start:                          ~20K tokens (PM instructions + project context)
  After Research teammate msg:    +1-3K tokens (targeted summary via SendMessage)
  After Engineer teammate msg:    +1-2K tokens (targeted summary via SendMessage)
  After QA teammate msg:          +0.5-1K tokens (targeted summary via SendMessage)
  Total PM context consumed:      23-26K tokens
```

**Predicted savings:** 30-50% reduction in PM context consumption.

### Test Protocol

#### Test B1: Task Tool Baseline

**Purpose:** Measure PM context consumption for a standard 3-phase workflow via Task tool.

**Steps:**
1. Start a fresh MPM session (no Agent Teams)
2. Execute a standard workflow:
   - Research: "Analyze the agent deployment pipeline" (Task tool)
   - Engineer: "Add a logging statement to agent_template_builder.py" (Task tool)
   - QA: "Verify the logging statement works" (Task tool)
3. After each delegation completes, note:
   - Approximate conversation length (messages/turns)
   - How verbose the returned result is
   - Whether PM context feels "full" (subjective but informative)

**Note:** Exact token counting may require Claude Code API instrumentation. If not available, use conversation length as a proxy.

#### Test B2: Agent Teams Comparison

**Purpose:** Measure PM context consumption for the same workflow via Agent Teams.

**Steps:**
1. Start a fresh MPM session with Agent Teams enabled
2. Execute the same workflow as Test B1 but via teammates:
   - Research teammate: same task
   - Engineer teammate: same task
   - QA teammate: same task
3. Instruct each teammate (via Teammate Protocol): "Send a concise summary of results to team lead. Include key findings and evidence only."
4. After each teammate message, note same metrics as B1

**Pass criteria:** PM context consumption is measurably lower than B1.

#### Test B3: Sustained Session Test

**Purpose:** Validate that Agent Teams enables longer PM sessions before context saturation.

**Steps:**
1. **Task tool session:** Execute 5 sequential delegations (Research x2, Engineer x2, QA x1)
   - Note when PM responses start losing context or quality
2. **Agent Teams session:** Execute same 5 tasks via teammates
   - Note when PM responses start losing context or quality
3. Compare: At what delegation count does each model show degradation?

**Pass criteria:** Agent Teams session sustains 30%+ more delegations before quality degradation.

#### Test B4: Message Size Control

**Purpose:** Validate that teammate SendMessage responses are more concise than Task tool returns.

**Steps:**
1. Assign identical tasks to:
   - A Task tool subagent (standard MPM delegation)
   - An Agent Teams teammate (with Teammate Protocol instructing concise reporting)
2. Measure approximate size of returned results
3. Compare verbosity

**Pass criteria:** Teammate SendMessage results are 50%+ smaller than Task tool returns.

---

## Implementation Plan

### Morning: Model Routing Tests (3 hours)

1. **Setup:** Enable Agent Teams, deploy agents, verify environment
2. **Run Tests A1-A2:** Model override and mixed-model team
3. **Run Test A3:** Cost estimation comparison
4. **Document:** Model routing results

### Afternoon: Context Window Tests (4 hours)

4. **Run Test B1:** Task tool baseline (standard MPM session)
5. **Run Test B2:** Agent Teams comparison (same tasks)
6. **Run Test B3:** Sustained session comparison (5 delegations each)
7. **Run Test B4:** Message size comparison
8. **Document:** Context window results

### End of Day: Write Results

9. Write results to `docs-local/mpm-agent-teams/02-phase-0/results/exp4_results.md`
10. Include: measurements, comparisons, cost analysis, recommendation

---

## Success Criteria Summary

| Criterion | Threshold | Test |
|-----------|-----------|------|
| Model override works per-teammate | 100% | A1 |
| Mixed-model team completes tasks | 100% | A2 |
| Haiku adequate for ops/docs tasks | No quality failures | A2 |
| Cost reduction with mixed models | >= 20% for ops-heavy workflows | A3 |
| PM context reduction vs Task tool | >= 30% | B2 vs B1 |
| Session sustainability improvement | >= 30% more delegations | B3 |
| Teammate message conciseness | >= 50% smaller than Task returns | B4 |

---

## Failure Modes

| Failure Mode | Impact | Mitigation |
|-------------|--------|------------|
| Model parameter ignored for teammates | No cost optimization | Check if frontmatter model is locked; try without frontmatter |
| Haiku too weak for ops tasks | Can't use cheapest model | Route only Documentation to Haiku; keep Ops on Sonnet |
| Context savings < 10% | Primary motivation invalidated | Investigate: are SendMessage results as verbose as Task returns? Add stronger conciseness instructions. |
| Teammate messages too terse (missing evidence) | Verification quality drops | Balance: concise summary + required evidence fields (from CB#3 protocol) |
| Session sustainability improvement not measurable | Hard to prove value | Use longer benchmark (10 delegations) or measure via token counting API if available |
