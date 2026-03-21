# MPM Architecture Integration Analysis
## Issue #290: Integrating Anthropic's Agent Teams with MPM

**Author**: MPM Architecture Integration Analyst
**Date**: 2026-03-20
**Role**: Task #3 — MPM Architecture Deep-Dive
**Status**: Complete

---

## Executive Summary

This analysis examines MPM's architecture to identify concrete integration points, risks, and feasibility for the Agent Teams hybrid model proposed in Issue #290. The central finding is that **integrating Agent Teams creates a fundamental context gap**: teammates spawned by Claude Code's native mechanism do not receive MPM's BASE_AGENT.md, circuit breakers, or verification gate instructions. This gap — flagged by @MacPhobos — is not cosmetic; it undermines the correctness guarantees that MPM's entire architecture is built around.

The proposed hybrid model is architecturally sound in concept but requires solving this context gap before any other integration work is meaningful.

---

## 1. Current MPM Delegation Model

### 1.1 Architecture Overview

MPM uses a **strict hierarchical PM-centric orchestration model**:

```
User Request
     │
     ▼
┌─────────────────────────────────────────────────────┐
│                   PM Agent                          │
│  • Orchestration only (no implementation)           │
│  • Circuit breaker enforcement (13 breakers)        │
│  • Evidence collection & verification               │
│  • File tracking protocol                           │
└─────────────┬───────────────────────────────────────┘
              │ Task(subagent_type="X")
              │
     ┌────────┼────────┐
     ▼        ▼        ▼
 Research  Engineer   QA      ... (49+ agent types)
     │        │        │
     └────────┴────────┘
              │
              ▼ Evidence returned
         PM Verifies → Reports Results
```

**Key structural properties:**
- PM is the **single orchestration point** — all delegation flows through it
- Agents are **domain-isolated** — each has specialized instructions and tool access
- Results must include **verifiable evidence** — forbidden phrases like "should work"
- Every implementation phase flows through a **QA verification gate** before completion
- The full workflow is **strictly sequential**: Research → Code Analysis → Implementation → QA → Documentation

### 1.2 How PM Delegates: The Task Tool Flow

When PM delegates, it calls the `Task` tool with `subagent_type`:

```python
Task(
    description="Fix authentication bug in login flow",
    subagent_type="Engineer",         # Maps to agent template
    isolation="worktree",             # Optional: parallel work isolation
    run_in_background=True            # Optional: async execution
)
```

The `subagent_type` is captured by MPM's hook system at multiple points:
- `hooks/claude_hooks/services/duplicate_detector.py:79` — deduplication
- `hooks/claude_hooks/hook_handler.py:612` — delegation tracking
- `hooks/claude_hooks/event_handlers.py` — event streaming to dashboard

**What happens after Task() is called:**
1. Claude Code receives the task with `subagent_type="Engineer"`
2. It looks up agent definition in `.claude/agents/` (PROJECT tier) or MPM's system tier
3. Agent template is loaded with BASE_AGENT.md prepended (if going through MPM's AgentLoader)
4. Agent executes with its specialized instructions

### 1.3 Agent Template Resolution: Three-Tier System

```
Agent ID Resolution:
                                   ┌─────────────────────────┐
Task(subagent_type="Research") ──► │   AgentLoader.get_agent  │
                                   └────────────┬────────────┘
                                                │
                         Priority cascade (first match wins):
                                                │
                    ┌───────────────────────────┼───────────────────────┐
                    ▼                           ▼                       ▼
         PROJECT TIER                    SYSTEM TIER             CACHE TIER
       .claude/agents/               src/claude_mpm/          ~/.claude-mpm/
                                   agents/templates/          cache/agents/
       (user overrides)             (built-in agents)        (GitHub cached)
```

**Critical detail**: The `AgentLoader` is a **Python-layer singleton**. It resolves templates when MPM orchestrates delegation. But when Agent Teams spawns teammates natively via the Claude Code executable, this Python layer is **bypassed entirely**.

### 1.4 How BASE_AGENT.md Gets Loaded

`BASE_AGENT.md` is universally prepended to all agent prompts:

```
src/claude_mpm/agents/BASE_AGENT.md (420 lines)
    ↓ prepended to
Each agent's specific instructions
    ↓ combined = full agent prompt
Agent executes with full instruction set
```

BASE_AGENT.md contains (per file:1-420):
- Git workflow standards (conventional commits, atomic changes)
- Memory routing protocol
- Output format standards
- Handoff protocol between agents
- **SELF-ACTION IMPERATIVE** — agents must execute work themselves
- **VERIFICATION BEFORE COMPLETION** — blocking rule, evidence required
- Agent Teams awareness (lines 172-185): "They can coexist but should not be layered"
- Performance-first engineering principles

---

## 2. The Teammate Context Gap (Critical Issue)

### 2.1 The Problem Statement

@MacPhobos identified: *"When a team-lead spins up team-mates, the team-mates are started using claude code executable. We need to ensure that each team-mate actually uses the full BaseAgent/PM_INSTRUCTIONS flow. Currently it does not appear to do so."*

This is architecturally confirmed by examining the two spawning paths:

```
PATH A: MPM Native Delegation (WORKING)
═══════════════════════════════════════
User → PM → Task(subagent_type="Research")
              │
              ▼ [Python AgentLoader]
         src/claude_mpm/agents/templates/research.md
              +
         BASE_AGENT.md (prepended)
              +
         Circuit breaker instructions
              +
         Memory routing rules
              ▼
         Agent has FULL MPM instruction set ✅


PATH B: Agent Teams Native Spawning (GAP)
══════════════════════════════════════════
Team Lead → TeamCreate/Agent spawn
              │
              ▼ [Claude Code executable, NOT Python]
         .claude/agents/ (if exists)
              OR
         Claude Code built-in defaults
              ▼
         Agent has PARTIAL or NO MPM instructions ❌
         Missing:
         - BASE_AGENT.md content
         - Circuit breakers
         - Verification gates
         - Memory routing rules
         - Evidence requirements
```

### 2.2 What's Already Wired (Partially)

MPM's hook handler **already handles Agent Teams events** (hook_handler.py:539-541):

```python
# Agent Teams events (experimental in Claude Code v2.1.47+)
"TeammateIdle": self.event_handlers.handle_teammate_idle_fast,
"TaskCompleted": self.event_handlers.handle_task_completed_fast,
```

And event_handlers.py:1517-1549 handles `TeammateIdle` by extracting:
- `teammate_id`
- `teammate_type`
- `idle_reason`

This means MPM's **observability layer is partially wired** for Agent Teams, but the **instruction injection layer is not**.

### 2.3 What's Missing for Full Integration

| Layer | Status | Gap |
|-------|--------|-----|
| Event capture (TeammateIdle, TaskCompleted) | ✅ Wired | None |
| Dashboard visibility of teammates | ✅ Partial | teammate_type tracking incomplete |
| BASE_AGENT.md injection into teammates | ❌ Missing | Path B spawning bypasses AgentLoader |
| Circuit breaker enforcement in teammates | ❌ Missing | Instructions never loaded |
| Memory routing for teammates | ❌ Missing | Agent-specific routing not configured |
| Verification gate for teammate outputs | ❌ Missing | PM can't enforce QA on peer-messaged results |

---

## 3. Circuit Breaker Compatibility with Agent Teams

### 3.1 Current Circuit Breaker Architecture

MPM enforces 13 circuit breakers via a 3-strike enforcement model. Key breakers relevant to Agent Teams:

| Breaker | Mechanism | Agent Teams Risk |
|---------|-----------|-----------------|
| CB#1: Large Implementation | PM using Edit/Write >5 lines | Team lead could bypass via peer-to-peer |
| CB#2: Deep Investigation | PM reading >3 files | Teammates could do this without PM oversight |
| CB#3: Unverified Assertions | PM claiming status without evidence | Teammates could report to team-lead without evidence |
| CB#5: Delegation Chain | PM claiming complete without full workflow | Team-based completion skips PM workflow |
| CB#8: QA Verification Gate | PM claiming complete without QA | Team-native QA bypass (see section 4) |

### 3.2 How Agent Teams Bypasses Circuit Breakers

**The fundamental problem**: Circuit breakers are **PM-centric instruction sets**. They work because:
1. PM receives CB instructions via PM_INSTRUCTIONS.md
2. PM *chooses* to delegate rather than implement
3. PM *requires* evidence before reporting completion
4. Agents receive BASE_AGENT.md with verification requirements

When Agent Teams introduces **peer-to-peer messaging** (SendMessage between teammates):
```
Team Lead                    Teammate A
    │                            │
    │ ◄── SendMessage("Done") ───┤  ← No PM oversight
    │                            │  ← No evidence requirement
    │                            │  ← No QA gate
    ▼                            │
Reports complete                 │  ← CB#8 never fires
    (bypassed QA gate)
```

### 3.3 Difficulty Rating: HARD

Retrofitting circuit breakers into an Agent Teams context requires:
1. Embedding CB instructions into every teammate's system prompt (solved by fixing context gap)
2. Defining what "PM oversight" means when team-lead IS a teammate
3. Preventing team-lead from accepting peer results without verification
4. Redefining the evidence chain for team-produced outputs

---

## 4. QA Gate Integration Analysis

### 4.1 Current QA Gate Architecture

```
Implementation Complete
         │
         ▼ [PM mandatory delegation]
   ┌─────────────────────┐
   │    QA Gate          │
   │  (BLOCKING)         │
   │                     │
   │ Routes to:          │
   │ • Web QA (UI)       │
   │ • API QA (backend)  │
   │ • Local Ops (infra) │
   └─────────┬───────────┘
             │ Evidence: actual HTTP responses, screenshots, logs
             ▼
   PM receives evidence → Claims completion
```

**Key constraint** (PM_INSTRUCTIONS.md:655-741): "No 'done/complete/ready/working/fixed' claims without QA evidence."

### 4.2 How Team-Based QA Would Work (Proposed)

The issue proposes: "Agent Teams results flow through existing verification gates." But this is problematic:

**Scenario A: PM delegates QA teammate**
```
Team Lead → Task(subagent_type="QA")
              │ [QA teammate executes]
              ▼
           QA sends results via SendMessage
              │
              ▼
Team Lead receives evidence
           (standard flow, works)
```
**Assessment**: This works if QA teammate has full MPM instructions (context gap solved). **Difficulty: MEDIUM**

**Scenario B: Parallel QA (Security + Performance + Functional)**
```
Team Lead spawns 3 QA agents simultaneously:
    ├─ Security QA
    ├─ Performance QA
    └─ Functional QA
         │
         ▼ All report via SendMessage concurrently
    Team Lead aggregates
```
**Problem**: PM_INSTRUCTIONS.md has no protocol for aggregating parallel QA results. Current model assumes sequential, single-QA-agent verification. Conflicting results (Security: FAIL, Functional: PASS) have no resolution protocol.
**Assessment**: Requires new aggregation protocol. **Difficulty: HARD**

**Scenario C: QA from non-PM-spawned teammates**
```
Team Agent (not PM-spawned) claims "QA complete"
    │
    ▼ PM has no visibility into what QA was run
PM cannot validate evidence chain
```
**Assessment**: Fundamentally breaks evidence-based verification model. **Difficulty: VERY HARD** (requires architectural change)

---

## 5. Memory System Analysis

### 5.1 Current Memory Architecture

MPM uses **three layers of memory**:

```
Layer 1: kuzu-memory (MCP, Graph DB)
─────────────────────────────────────
Purpose: PM context enhancement, project-wide knowledge
Access: PM calls mcp__kuzu-memory__kuzu_recall FIRST before delegating
Sharing: Project-scoped, single writer model (PM)
File: External MCP server

Layer 2: Agent Memories (flat files)
─────────────────────────────────────
Location: .claude-mpm/memories/{agent_name}.md
Format: Single-line facts in markdown sections
Limit: 80KB (~20k tokens) per file
Sharing: Per-agent-type, not shared between agent instances
Access: Read at agent start, written at completion

Layer 3: PM Memory
─────────────────────────────────────
Location: .claude-mpm/memories/PM_memories.md
Content: PM-specific decisions, preferences, patterns
Access: PM only
```

### 5.2 What "Team-Shared Context" Would Require

The issue proposes "Memory system supports team-shared context." Currently:

| Memory Need | Current Support | Gap |
|-------------|----------------|-----|
| Agent reads its own memory | ✅ Full support | None |
| PM reads project memory (kuzu) | ✅ Full support | None |
| Teammate A reads Teammate B's findings | ❌ Not supported | New shared memory layer needed |
| Team-level memory (ephemeral, session-scoped) | ❌ Not supported | No session-shared memory concept |
| Team lead reads all teammates' memories | ❌ Not supported | No aggregation mechanism |
| Memory written by teammate, read by PM | ⚠️ Indirect only | Agent writes to file, PM reads next session |

**The fundamental mismatch**: Agent memories are designed for **cross-session persistence** (learn today, recall next week). Agent Teams needs **within-session sharing** (Research A finds X, Engineer B needs X). These are different use cases with different latency and consistency requirements.

### 5.3 Session-Scoped Sharing Options

Three approaches for within-session memory sharing:

**Option A: File-based shared blackboard**
```
/tmp/session-{id}/shared-context.md
    ├─ Research findings (written by Research teammate)
    └─ Architecture decisions (read by Engineer teammate)
```
- Simple, no new infrastructure
- Race conditions if multiple writers
- No cleanup guarantees

**Option B: kuzu-memory as shared store**
- Extend PM's kuzu-memory calls to be available to all teammates
- Requires MCP server access in each teammate's tool set
- Consistent with existing pattern

**Option C: Team Lead as memory broker**
- All teammates report to team lead, which holds context
- Team lead re-includes context in each delegation
- No new infrastructure, but creates bottleneck

**Assessment**: Option C is lowest risk and consistent with existing PM-centric model. **Difficulty: MEDIUM**

---

## 6. Proposed Hybrid Model Assessment

### 6.1 Use Case 1: Research Phase — 3 Parallel Researchers

**Proposed**: 3 Research agents run in parallel to explore different aspects simultaneously.

**Current State**: Already possible with `isolation: "worktree"` + `run_in_background: true`:
```python
Task(subagent_type="Research", description="Auth patterns", run_in_background=True)
Task(subagent_type="Research", description="DB patterns", run_in_background=True)
Task(subagent_type="Research", description="API patterns", run_in_background=True)
```

**What Agent Teams adds**:
- Researchers can message each other to coordinate (avoid duplication)
- Team lead can synthesize findings in real-time rather than waiting for all 3

**What breaks**:
- If researchers communicate peer-to-peer, PM loses the research gate (CB#7)
- PM no longer validates research quality before implementation begins
- Synthesis quality depends on team-lead's instruction set (context gap)

**Net assessment**: LOW additional value vs HIGH risk. Current parallel Research via background tasks already achieves parallelism. Peer coordination benefit is marginal. **Skip unless context gap fully resolved.**

### 6.2 Use Case 2: Parallel QA — Security + Performance + Functional

**Proposed**: Three QA agents run simultaneously, each with domain expertise.

**What Agent Teams adds**:
- Saves time vs sequential QA
- Each specialist is deeper in their domain

**What breaks**:
- No protocol for conflicting QA results (Security: FAIL, Functional: PASS)
- PM_INSTRUCTIONS.md CB#8 (QA gate) expects single verification agent
- Evidence aggregation format undefined
- If any QA teammate lacks MPM instructions (context gap), evidence chain is incomplete

**Net assessment**: GENUINE VALUE for speed, but requires new aggregation protocol and conflict resolution rules. **MEDIUM value, HARD to implement correctly.**

### 6.3 Use Case 3: Complex Features — Frontend + Backend + Test Coordinating

**Proposed**: Three domain engineers work simultaneously, coordinating via peer messages.

**What Agent Teams adds**:
- True parallel implementation (not just parallel agents in isolated worktrees)
- Engineers can negotiate interfaces peer-to-peer rather than through PM
- Faster iteration on shared API contracts

**What breaks**:
- CB#1 (Implementation Detection) may fire if team-lead does any implementation work
- File tracking (CB#4 + CB#5) becomes complex with multiple agents modifying code
- Worktree isolation (`isolation: "worktree"`) is already available for the parallel case
- Merge conflicts when teammates in same worktree touch shared files
- PM loses visibility into inter-agent negotiations

**Net assessment**: HIGHEST complexity use case. Current worktree isolation already handles the "parallel engineers" case. The peer-negotiation benefit exists but is risky without PM oversight. **HIGH value potential, VERY HARD to implement safely.**

---

## 7. Migration Risk Assessment

### 7.1 Breaking Changes

| Pattern | Current Behavior | Agent Teams Impact | Risk Level |
|---------|-----------------|-------------------|------------|
| PM as sole orchestrator | All delegation through PM | Team lead can bypass PM | HIGH |
| Sequential QA gate | Single QA before completion | Multiple parallel QA with no aggregation | HIGH |
| Evidence chain | PM collects all evidence | Peer-to-peer results skip PM | HIGH |
| File tracking protocol | PM runs git tracking | Multiple agents may commit concurrently | MEDIUM |
| Memory isolation | Agent memories per-type | Teammates need cross-agent access | MEDIUM |
| Circuit breaker scope | PM-scoped enforcement | Peer messages bypass PM-layer CBs | HIGH |
| Research gate | PM validates before implementing | Parallel research may not pass through gate | MEDIUM |

### 7.2 What Would NOT Break

- Hook system observability (already handles TeammateIdle/TaskCompleted)
- Worktree isolation (independent of Agent Teams)
- Background execution model
- kuzu-memory as PM context tool
- Agent template resolution (if context gap solved)
- Individual agent capabilities and tools

### 7.3 Required Pre-Conditions for Safe Integration

Before any hybrid model integration:

**P0 — Must have before anything else:**
1. **Solve context gap**: Every teammate must receive BASE_AGENT.md + circuit breaker instructions
2. **Define PM role in teams**: Is team-lead a modified PM? A regular PM? Something new?
3. **QA aggregation protocol**: Define how parallel QA results are combined and conflicts resolved

**P1 — Required for production safety:**
4. **File tracking for parallel agents**: Extend git tracking protocol for multi-agent commits
5. **Memory sharing mechanism**: Session-scoped shared context (Option C recommended)
6. **Evidence chain for team outputs**: What constitutes valid evidence from a team vs individual agent

**P2 — Quality of life:**
7. **Dashboard extension**: teammate_type tracking is incomplete (event_handlers.py:1533)
8. **Cost model update**: PM_INSTRUCTIONS.md model selection table needs team scenarios

---

## 8. Specific Integration Points with Difficulty Ratings

### 8.1 Context Gap Resolution
**Files to modify**: Agent deployment pipeline (`services/agents/deployment/`), system context injection
**Approach**: When deploying agents to `.claude/agents/`, automatically prepend BASE_AGENT.md
**Difficulty**: MEDIUM
**Why not EASY**: Deployment pipeline has 4 steps (validation, configuration, agent_processing, target_directory) — BASE_AGENT.md injection must happen in `agent_processing_step.py` and be idempotent

### 8.2 Team Lead System Prompt
**Files to create**: `src/claude_mpm/agents/TEAM_LEAD_INSTRUCTIONS.md`
**Approach**: Modified PM instructions for team-lead role — what verification means when you ARE in the team
**Difficulty**: HARD
**Why**: Requires rethinking PM circuit breakers for peer context (CB#1, CB#2 fire differently when team-lead has teammates)

### 8.3 QA Aggregation Protocol
**Files to modify**: `PM_INSTRUCTIONS.md` (QA gate section), new `QA_AGGREGATION_PROTOCOL.md`
**Approach**: Define merge rules for parallel QA results; adopt fail-safe (any FAIL = team FAIL)
**Difficulty**: HARD
**Why**: Edge cases in conflicting results require domain judgment, not just rules

### 8.4 Hook Handler Extension for Teams
**Files to modify**: `hooks/claude_hooks/event_handlers.py` (handle_teammate_idle_fast)
**Current state**: `teammate_type` extracted but dashboard tracking incomplete
**Approach**: Emit full teammate context to dashboard; track which teammates are running MPM agents
**Difficulty**: EASY
**Code reference**: event_handlers.py:1517-1549

### 8.5 File Tracking for Parallel Commits
**Files to modify**: `templates/git-file-tracking.md`, PM_INSTRUCTIONS.md
**Approach**: Require all parallel agents to track files immediately, PM verifies consolidated `git status` before claiming completion
**Difficulty**: MEDIUM
**Why**: Git conflict resolution from parallel worktrees is already handled by worktree isolation; need protocol for non-worktree parallel commits

### 8.6 Session Memory Sharing
**Files to create**: `services/agents/memory/session_blackboard.py`
**Approach**: Lightweight shared dict (or file) scoped to session ID; team-lead writes context after each delegation; teammates read before starting
**Difficulty**: MEDIUM
**Why**: Not architecturally novel, but requires new data flow between agents

### 8.7 Circuit Breaker Adaptation for Teams
**Files to modify**: `templates/circuit-breakers.md`
**Approach**: Add "Team Context" exception clauses; CB#2 fires differently if team-lead delegated to research teammate vs doing research itself
**Difficulty**: HARD
**Why**: Circuit breakers are the core safety mechanism; changes risk degrading enforcement

---

## 9. Architecture Diagrams

### 9.1 Current State: Pure PM Hierarchy

```
                    ┌──────────────┐
                    │     USER     │
                    └──────┬───────┘
                           │ Task/Request
                           ▼
                    ┌──────────────┐
                    │      PM      │ ← All circuit breakers active
                    │  (Orchestr.) │ ← Collects all evidence
                    └──────┬───────┘ ← Single orchestration point
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │ Research │    │ Engineer │    │    QA    │
    │ (BASE)   │    │ (BASE+   │    │ (BASE+   │
    │          │    │  ENG)    │    │  VERIFY) │
    └────┬─────┘    └────┬─────┘    └────┬─────┘
         │               │               │
         └───────────────┴───────────────┘
                          │ Evidence
                          ▼
                    ┌──────────────┐
                    │      PM      │ ← Verifies, tracks files
                    └──────────────┘ ← Reports to user
```

### 9.2 Proposed Hybrid: PM as Team Lead

```
                    ┌──────────────┐
                    │     USER     │
                    └──────┬───────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │       Team Lead (PM)         │
            │  • Modified PM instructions  │
            │  • Team coordination role    │
            │  • Still collects evidence   │
            └──────┬───────────────────────┘
                   │ Peer messages + Task delegations
          ┌────────┼────────┐
          │        │        │
          ▼        ▼        ▼
    ┌──────────┐ ┌──┐ ┌──────────┐
    │ Research │ │R2│ │ Research │  ← Parallel researchers
    │ [NEEDS   │ │  │ │    3     │  ← Context gap here ⚠️
    │ BASE_AGT]│ │  │ │          │
    └────┬─────┘ └┬─┘ └────┬─────┘
         │        │         │
         └────────┴─────────┘
                  │ SendMessage results (peer-to-peer)
                  ▼
            Team Lead aggregates
                  │ Task(QA agents)
          ┌───────┼───────┐
          ▼       ▼       ▼
        Sec      Perf    Func   ← Parallel QA
        QA       QA      QA     ← Aggregation needed ⚠️
          └───────┴───────┘
                  │
            Team Lead → Report to User
```

### 9.3 Required Integration: Context Injection

```
Agent Deployment Pipeline (services/agents/deployment/)
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
validation_  configuration_   agent_processing_   ← Add BASE_AGENT.md
step.py      step.py          step.py                injection HERE
                                    │
                                    ▼
                             target_directory_
                             step.py
                                    │
                                    ▼
                           .claude/agents/
                          ├── research.md      ← Contains BASE_AGENT.md
                          ├── engineer.md      ← Contains BASE_AGENT.md
                          └── team-lead.md     ← Contains BASE_AGENT.md
                                                  + TEAM_LEAD_INSTRUCTIONS.md
```

---

## 10. Key Findings and Recommendations

### 10.1 Critical Findings

1. **The context gap is real and documented**: BASE_AGENT.md explicitly states (line 185): "They can coexist but should not be layered (do not use Agent Teams inside mpm PM delegation)." This was a deliberate design decision acknowledging the gap. Any integration must override this explicitly.

2. **MPM's hook system is partially wired for Agent Teams**: `TeammateIdle` and `TaskCompleted` events are already handled. The observability foundation exists.

3. **Worktree isolation already provides most parallelism benefits**: The main Agent Teams value proposition (parallel agents) is already available via `isolation: "worktree"` + `run_in_background: true`. The incremental value from Agent Teams is peer-to-peer coordination, not parallelism itself.

4. **The evidence chain is the hardest problem**: MPM's correctness guarantees are based on the PM collecting verifiable evidence. Peer-to-peer results fundamentally complicate this.

5. **QA gate aggregation has no existing protocol**: The 3-parallel-QA use case requires defining merge semantics that don't exist in PM_INSTRUCTIONS.md.

### 10.2 Recommendations

**If pursuing integration:**

1. **Start with context gap resolution only** (agent_processing_step.py modification) — this is prerequisite for everything else and relatively low-risk
2. **Define team-lead instructions as a new role** (not a modification of PM instructions) — create TEAM_LEAD_INSTRUCTIONS.md as a separate artifact
3. **Implement Option C memory sharing** (team-lead as broker) — lowest infrastructure risk
4. **Apply fail-safe QA aggregation** (any FAIL = team FAIL) — conservative but safe
5. **Pilot with Research parallelism only** — lowest risk use case, already partially supported

**If NOT pursuing integration yet:**
- Document the existing `run_in_background` + `isolation: "worktree"` pattern as the "MPM parallel agents" pattern
- Keep BASE_AGENT.md's "should not be layered" guidance as the official position
- Address context gap separately as a defensive measure (protect against accidental Agent Teams usage)

---

## 11. Code References

| Topic | File | Lines |
|-------|------|-------|
| BASE_AGENT.md Agent Teams note | `src/claude_mpm/agents/BASE_AGENT.md` | 172-185 |
| Circuit breaker definitions | `src/claude_mpm/agents/templates/circuit-breakers.md` | All |
| QA verification gate | `src/claude_mpm/agents/PM_INSTRUCTIONS.md` | 655-741 |
| Workflow pipeline | `src/claude_mpm/agents/WORKFLOW.md` | All |
| Agent loader (Python) | `src/claude_mpm/services/agents/loading/` | — |
| Deployment pipeline steps | `src/claude_mpm/services/agents/deployment/pipeline/steps/` | — |
| TeammateIdle hook handler | `src/claude_mpm/hooks/claude_hooks/event_handlers.py` | 1517-1549 |
| TaskCompleted + TeammateIdle events | `src/claude_mpm/hooks/claude_hooks/hook_handler.py` | 539-542 |
| subagent_type extraction | `src/claude_mpm/hooks/claude_hooks/services/duplicate_detector.py` | 77-81 |
| Memory protocol | `src/claude_mpm/agents/MEMORY.md` | All |
| Agent delegation table | `src/claude_mpm/agents/AGENT_DELEGATION.md` | All |

---

*Research captured in: `docs-local/mpm-agent-teams/01_initial_investigation/02_mpm_integration_analysis.md`*
*No ticketing context provided — file-based capture only.*
