# Correction Plan v8: PM Agent Reference Alignment

**Date**: 2026-03-05
**Branch**: agenttype-enums
**Prerequisite**: Phase 5 complete (all naming standardization done)
**Scope constraint**: Modifications to agent/skill definitions retrieved from Git repos are OUT OF SCOPE.

---

## Context

### System Architecture

claude-mpm requires network connectivity (built on Claude Code). Agent and skill definitions live in external Git repositories (`claude-mpm-agents`, `claude-mpm-skills`), cached locally at `~/.claude-mpm/cache/agents/`. Deployment copies cached agents to `.claude/agents/` in the project directory.

### How PM Delegation Works (Empirically Proven)

PM delegates via `Agent(subagent_type="<value>")`. The `subagent_type` parameter is matched against the `name:` frontmatter field of deployed agent `.md` files in `.claude/agents/`.

- `Agent(subagent_type="Golang Engineer")` -- **succeeds** (matches `name: Golang Engineer`)
- `Agent(subagent_type="golang-engineer")` -- **fails** (no agent has `name: golang-engineer` except nestjs-engineer)

### What We Found

PM_INSTRUCTIONS.md — the PM's runtime system prompt — references agents using **filename stems** (e.g., `local-ops`, `web-qa-agent`) instead of their `name:` field values (e.g., `Local Ops`, `Web QA`). Additionally, several agents referenced by PM are not deployed locally.

---

## Problem Inventory

### P1: PM References Agents by Wrong Identifiers

PM_INSTRUCTIONS.md uses filename stems or ad-hoc names. Since `subagent_type` resolves against `name:`, these references likely cause delegation failures.

| PM Says | Occurrences | Agent File | Actual `name:` Field | Deployed? | Correct Reference |
|---------|------------|------------|---------------------|-----------|-------------------|
| `local-ops` | 18 | `local-ops.md` | `Local Ops` | **NO** | `Local Ops` |
| `web-qa-agent` | 8 | `web-qa.md` | `Web QA` | YES | `Web QA` |
| `api-qa-agent` | 2 | `api-qa.md` | `API QA` | **NO** | `API QA` |
| `vercel-ops` | 2 | `vercel-ops.md` | `Vercel Ops` | **NO** | `Vercel Ops` |
| `gcp-ops` | 2 | `gcp-ops.md` | `Google Cloud Ops` | **NO** | `Google Cloud Ops` |
| `clerk-ops` | 2 | `clerk-ops.md` | `Clerk Operations` | YES | `Clerk Operations` |
| `version-control` | 2 | `version-control.md` | `Version Control` | YES | `Version Control` |
| `security` | 1 | `security.md` | `Security` | **NO** | `Security` |
| `ticketing-agent` | 1 | `ticketing.md` | `ticketing_agent` | YES | `ticketing_agent` |

**Note on `name:` field anomalies**: Several agents have non-standard `name:` values (e.g., `aws_ops_agent`, `ticketing_agent`, `mpm_agent_manager`, `nestjs-engineer`, `real-user`). These are defined in the external Git repo and are **out of scope** for this plan. PM must reference these agents using their actual `name:` values, even if the format is inconsistent.

### P2: 8 Agents in Cache But Not Deployed

These agents exist in `~/.claude-mpm/cache/agents/` but are missing from `.claude/agents/`:

| Agent | `name:` Field | Has `author:` | Has `version:` | PM References It? |
|-------|--------------|--------------|----------------|-------------------|
| `local-ops.md` | `Local Ops` | NO | YES | **YES (18x)** |
| `api-qa.md` | `API QA` | YES | YES | **YES (2x)** |
| `security.md` | `Security` | YES | YES | **YES (1x)** |
| `vercel-ops.md` | `Vercel Ops` | YES | YES | **YES (2x)** |
| `gcp-ops.md` | `Google Cloud Ops` | YES | YES | **YES (2x)** |
| `digitalocean-ops.md` | `DigitalOcean Ops` | YES | YES | NO |
| `javascript-engineer.md` | `Javascript Engineer` | YES | YES | NO |
| `web-ui.md` | `Web UI` | YES | YES | NO |

**Root Cause**: NOT a code bug. The deployment pipeline (`_discover_cached_agents()` in `git_source_sync_service.py`) correctly recurses the cache using `rglob("*.md")`. These agents were likely added to the remote repo after the last `claude-mpm agents deploy` was run and committed.

**Fix**: Run deployment, commit results. No code change needed for this specific issue.

### P3: Inconsistent CORE_AGENTS Lists

Two different hardcoded CORE_AGENTS lists exist with conflicting contents and formats:

| File | Purpose | Contents |
|------|---------|----------|
| `framework_agent_loader.py:35` | Framework loading fallback | `["engineer", "research", "qa", "documentation", "ops", "ticketing"]` |
| `toolchain_detector.py:162` | Auto-configuration "always include" | `["engineer", "qa-agent", "memory-manager-agent", "local-ops-agent", "research-agent", "documentation-agent", "security-agent"]` |

**Issues**:
- `toolchain_detector.py` uses `-agent` suffixed names that match NEITHER filenames NOR `name:` fields
- Different agents included: `ticketing` vs `memory-manager-agent`, `local-ops-agent`, `security-agent`
- No single source of truth

### P4: `enums.py` Stale Enum Value

`src/claude_mpm/core/enums.py:433`: `VERSION_CONTROL = "version_control"` — underscore format doesn't match hyphen-canonical.

### P5: `templates/__init__.py` Dead Code

`src/claude_mpm/agents/templates/__init__.py` references non-existent `.json` template files (e.g., `version_control_agent.md`, `data_engineer_agent.md`). All functions return None/empty. Identified in Phase 1 but not removed.

### P6: WORKFLOW.md QA Routing Uses Stem Identifiers

`src/claude_mpm/agents/WORKFLOW.md` QA routing section references agents as `api-qa` and `web-qa` (filename stems, already fixed to hyphens in Phase 5) instead of `name:` field values `API QA` and `Web QA`.

---

## Out of Scope

| Item | Reason |
|------|--------|
| Changing `name:` fields in agent .md files | Definitions from Git repo -- out of scope |
| Fixing `name:` anomalies (`aws_ops_agent`, `ticketing_agent`, etc.) | Same -- agent definitions from Git repo |
| Remote cache repo renames | Separate repo (`bobmatnyc/claude-mpm-agents`) |
| nestjs-engineer YAML parse failure | Separate PR (Q7 from v7 plan) |
| Duplicate `-agent` suffix collision pairs | Separate PR (Q8 from v7 plan) |

---

## Phased Implementation Plan

### Phase 1: Deploy Missing Agents

**Goal**: Get the 8 cached agents deployed to `.claude/agents/` so PM can actually find them.
**Risk**: LOW -- standard deployment operation, no code changes.
**Files modified**: `.claude/agents/` (8 new files)

#### 1.1 Run Agent Deployment

**CRITICAL**: When running claude-mpm you must use '.venv/bin/claude-mpm' to ensure you're running the latest local code with all fixes. Running a globally installed version will not reflect recent changes. 

```bash
# Verify cache has all agents
find ~/.claude-mpm/cache/agents -name "*.md" ! -name "BASE*" ! -name "README*" | wc -l
# Expected: 45+ agents

# Run deployment
.venv/bin/claude-mpm agents deploy --force-sync

# Verify new agents appeared
ls .claude/agents/ | wc -l
# Expected: 48 (40 existing + 8 new)
```

#### 1.2 Verify All PM-Referenced Agents Are Deployed

```bash
# These MUST exist after deployment:
for agent in local-ops api-qa security vercel-ops gcp-ops; do
  ls .claude/agents/${agent}.md 2>/dev/null && echo "OK: ${agent}" || echo "MISSING: ${agent}"
done
```

#### 1.3 If Deployment Doesn't Deploy All Agents

If `claude-mpm agents deploy` still doesn't deploy all cached agents, there's a discovery or filtering bug. Investigate:

1. Check `filter_non_mpm_agents` setting — `local-ops.md` lacks `author:` field, might be filtered
2. Check `excluded_agents` config — should be empty (`[]`)
3. Check `_discover_cached_agents()` output — does it find all 45+ paths?
4. If `local-ops.md` is filtered due to missing `author:` field, the fix is in the deployment filter logic (add fallback for agents from known MPM repos), not in the agent file itself.

#### Phase 1 Verification

```bash
ls .claude/agents/ | wc -l        # Should be 48
ls .claude/agents/local-ops.md    # Must exist
ls .claude/agents/api-qa.md       # Must exist
ls .claude/agents/security.md     # Must exist
```

---

### Phase 2: Build Authoritative Name Map

**Goal**: Create a single source of truth mapping agent identifiers to their actual `name:` field values.
**Risk**: LOW -- read-only analysis + new constant file.
**Files modified**: 1 new file

#### 2.1 Create Agent Name Registry Constant

Create a module that reads deployed agents and provides the canonical mapping.

**File**: `src/claude_mpm/core/agent_name_registry.py` (NEW)

```python
"""
Authoritative mapping of agent identifiers to their frontmatter name: field values.

This is the SINGLE SOURCE OF TRUTH for how PM should reference agents.
The name: field is what subagent_type resolves against at runtime.

Generated from deployed agents in .claude/agents/ via:
    grep '^name:' .claude/agents/*.md

IMPORTANT: name: values come from the claude-mpm-agents Git repository
and must NOT be modified here. If a name: value is wrong, fix it upstream.
"""

# Map: filename stem -> actual name: field value
# PM must use these VALUES (not the keys) when delegating.
AGENT_NAME_MAP: dict[str, str] = {
    # Core agents
    "engineer": "Engineer",
    "research": "Research",
    "qa": "QA",
    "documentation": "Documentation Agent",
    "ops": "Ops",
    "security": "Security",
    "version-control": "Version Control",
    "data-engineer": "Data Engineer",
    "ticketing": "ticketing_agent",
    # ... (complete from deployed agents)

    # Ops platform agents
    "local-ops": "Local Ops",
    "vercel-ops": "Vercel Ops",
    "gcp-ops": "Google Cloud Ops",
    "clerk-ops": "Clerk Operations",
    "aws-ops": "aws_ops_agent",
    "digitalocean-ops": "DigitalOcean Ops",

    # QA agents
    "web-qa": "Web QA",
    "api-qa": "API QA",
    "real-user": "real-user",

    # ... (remaining agents)
}

# Reverse map: name: value -> filename stem (for lookups)
NAME_TO_STEM: dict[str, str] = {v: k for k, v in AGENT_NAME_MAP.items()}


def get_agent_name(stem: str) -> str:
    """Get the name: field value for an agent, given its filename stem.

    This is what PM should use as subagent_type.
    """
    return AGENT_NAME_MAP.get(stem, stem)


def get_agent_stem(name: str) -> str:
    """Get the filename stem for an agent, given its name: field value."""
    return NAME_TO_STEM.get(name, name)
```

#### 2.2 Write Extraction Script

Create a script that regenerates the map from deployed agents:

```bash
#!/usr/bin/env bash
# scripts/extract_agent_names.sh
# Regenerates AGENT_NAME_MAP from deployed agents
for f in .claude/agents/*.md; do
  stem=$(basename "$f" .md)
  name=$(grep '^name:' "$f" | head -1 | sed 's/name: *//')
  echo "    \"$stem\": \"$name\","
done
```

#### Phase 2 Verification

```bash
# Run extraction script and compare with constant
./scripts/extract_agent_names.sh | sort > /tmp/extracted.txt
grep '":' src/claude_mpm/core/agent_name_registry.py | sort > /tmp/coded.txt
diff /tmp/extracted.txt /tmp/coded.txt  # Should be empty
```

---

### Phase 3: Fix PM_INSTRUCTIONS.md Agent References

**Goal**: Replace all filename-stem agent references with correct `name:` field values.
**Risk**: MEDIUM -- changes PM runtime behavior. Must be exact.
**Files modified**: 2 (`PM_INSTRUCTIONS.md`, `WORKFLOW.md`)
**Dependency**: Phase 1 (agents deployed), Phase 2 (name map available)

#### 3.1 Audit All Agent References in PM_INSTRUCTIONS.md

Systematically find and categorize every agent reference:

```bash
# Find all agent references (look for bold, backtick, and quoted agent names)
grep -nE '(local-ops|web-qa-agent|api-qa-agent|vercel-ops|gcp-ops|clerk-ops|security-agent|ticketing-agent|version-control)' \
  src/claude_mpm/agents/PM_INSTRUCTIONS.md
```

#### 3.2 Replacement Rules

Each reference falls into one of these categories:

**A. Descriptive text (PM guidance)**:
References telling PM which agent to use. These should use the `name:` field since PM will pass it as `subagent_type`.

```
# BEFORE:
delegate to **local-ops**
delegate to **web-qa-agent** for browser verification

# AFTER:
delegate to **Local Ops**
delegate to **Web QA** for browser verification
```

**B. YAML/code examples**:
Examples showing Task delegation format. The `agent:` value must be the `name:` field.

```yaml
# BEFORE:
  agent: "local-ops"

# AFTER:
  agent: "Local Ops"
```

**C. Routing tables**:
Tables mapping triggers to agents.

```
# BEFORE:
| localhost, PM2, npm | **local-ops** | Local development |

# AFTER:
| localhost, PM2, npm | **Local Ops** | Local development |
```

**D. Parenthetical identifiers**:
Agent descriptions with IDs in parens.

```
# BEFORE:
| **Ops** (local-ops) | ...
| **QA** (web-qa-agent, api-qa-agent) | ...

# AFTER:
| **Ops** (`Local Ops`) | ...
| **QA** (`Web QA`, `API QA`) | ...
```

#### 3.3 Complete Replacement Map

| Current Reference | Replace With | Rationale |
|-------------------|-------------|-----------|
| `local-ops` | `Local Ops` | name: field of local-ops.md |
| `web-qa-agent` | `Web QA` | name: field of web-qa.md |
| `api-qa-agent` | `API QA` | name: field of api-qa.md |
| `vercel-ops` | `Vercel Ops` | name: field of vercel-ops.md |
| `gcp-ops` | `Google Cloud Ops` | name: field of gcp-ops.md |
| `clerk-ops` | `Clerk Operations` | name: field of clerk-ops.md |
| `ticketing-agent` | `ticketing_agent` | name: field of ticketing.md (NOTE: underscore, from repo) |
| `security-agent` | `Security` | name: field of security.md |
| `version-control` (when used as delegation target) | `Version Control` | name: field of version-control.md |

**Context-sensitive replacements**: Some occurrences of these terms are in descriptive text, not delegation targets. For example, "version-control agent" in a sentence describing capabilities should still become "Version Control agent" to be consistent, but does not require exact matching.

#### 3.4 Fix WORKFLOW.md

Same replacements for the QA routing section:

```python
# BEFORE:
if "API" in implementation: use api-qa
elif "UI" in implementation: use web-qa

# AFTER:
if "API" in implementation: use API QA
elif "UI" in implementation: use Web QA
```

#### Phase 3 Verification

```bash
# No filename-stem agent references should remain as delegation targets
grep -c 'local-ops\|web-qa-agent\|api-qa-agent\|vercel-ops\|gcp-ops\|clerk-ops' \
  src/claude_mpm/agents/PM_INSTRUCTIONS.md
# Expected: 0

# Correct name: values should appear
grep -c 'Local Ops\|Web QA\|API QA\|Vercel Ops\|Google Cloud Ops\|Clerk Operations' \
  src/claude_mpm/agents/PM_INSTRUCTIONS.md
# Expected: >= 30

# Spot-check: YAML example should use name: value
grep 'agent:' src/claude_mpm/agents/PM_INSTRUCTIONS.md
# Should show: agent: "Local Ops" (not agent: "local-ops")
```

---

### Phase 4: Fix Source Code Hardcoded Agent Lists

**Goal**: Align hardcoded agent lists in source code with actual deployed agents.
**Risk**: MEDIUM -- changes runtime behavior of framework loading and auto-configuration.
**Files modified**: 3-4 files
**Dependency**: Phase 2 (name map available)

#### 4.1 Fix `toolchain_detector.py` CORE_AGENTS

**File**: `src/claude_mpm/services/agents/toolchain_detector.py` (line ~162)

**Problem**: Uses `-agent` suffixed names that match neither filenames nor `name:` fields:
```python
# CURRENT (WRONG):
CORE_AGENTS = [
    "engineer",
    "qa-agent",           # No file "qa-agent.md" exists
    "memory-manager-agent",
    "local-ops-agent",    # No file "local-ops-agent.md" exists
    "research-agent",     # No file "research-agent.md" exists
    "documentation-agent",
    "security-agent",     # No file "security-agent.md" exists
]
```

**Question**: What format does this list need? It's used in `recommended.update(self.CORE_AGENTS)` — check what `recommended` contains and how it's consumed downstream.

**Investigation needed**:
1. Trace `recommended` set from `toolchain_detector.py` through to deployment
2. Determine if these values are used as filenames, agent_ids, or name: fields
3. Fix to match whatever format the consumer expects

**Likely fix** (if values are filename stems):
```python
CORE_AGENTS = [
    "engineer",
    "qa",
    "memory-manager-agent",
    "local-ops",
    "research",
    "documentation",
    "security",
]
```

#### 4.2 Align `framework_agent_loader.py` CORE_AGENTS

**File**: `src/claude_mpm/services/agents/loading/framework_agent_loader.py` (line ~35)

**Current**:
```python
CORE_AGENTS = ["engineer", "research", "qa", "documentation", "ops", "ticketing"]
```

**Decision needed**: Should this list match `toolchain_detector.py`? They serve different purposes:
- `framework_agent_loader.py`: Fallback for framework loading
- `toolchain_detector.py`: "Always include" during auto-configuration

**Recommendation**: Both should reference the same core set, using filename stems (since that's how files are discovered). Differences in purpose can be handled by the calling code, not duplicate lists.

#### 4.3 Fix `git_source_sync_service.py` Fallback List

**File**: `src/claude_mpm/services/agents/sources/git_source_sync_service.py` (line ~759)

The fallback agent list is used when the GitHub API is unavailable. It should list the core agents by their actual filenames in the repository.

**Current** (partially fixed in Phase 5):
```python
[
    "research-agent.md",      # Actual file: research.md (in repo, -agent suffix)
    "engineer.md",
    "qa-agent.md",            # Actual file: qa.md (in repo, -agent suffix)
    "documentation-agent.md", # Actual file: documentation.md (in repo, -agent suffix)
    "web-qa-agent.md",        # Actual file: web-qa.md (in repo, -agent suffix)
    "security.md",
    "ops.md",
    "ticketing.md",
    "product-owner.md",
    "version-control.md",
    "project-organizer.md",
]
```

**Problem**: Some entries use `-agent` suffixed names but the actual repo files don't have that suffix. Need to verify against the actual repo structure.

**Verification**:
```bash
find ~/.claude-mpm/cache/agents -name "*.md" ! -name "BASE*" ! -name "README*" -exec basename {} \; | sort
```

**Fix**: Update to match actual filenames in the repository.

#### 4.4 Fix `enums.py` VERSION_CONTROL Value

**File**: `src/claude_mpm/core/enums.py` (line ~433)

```python
# BEFORE:
VERSION_CONTROL = "version_control"

# AFTER:
VERSION_CONTROL = "version-control"
```

**Prerequisite**: Grep all usages of `AgentType.VERSION_CONTROL` to ensure no comparisons break:
```bash
grep -rn "VERSION_CONTROL" src/claude_mpm/ --include="*.py" | grep -v __pycache__
```

#### Phase 4 Verification

```bash
make test  # Full test suite

# Verify CORE_AGENTS lists reference actual files:
for agent in $(python3 -c "
from src.claude_mpm.services.agents.toolchain_detector import ToolchainDetector
print('\n'.join(ToolchainDetector.CORE_AGENTS))
"); do
  ls .claude/agents/${agent}.md 2>/dev/null || echo "MISSING: ${agent}.md"
done
```

---

### Phase 5: Clean Up Dead Code

**Goal**: Remove non-functional code that causes confusion.
**Risk**: LOW -- removing code that provably does nothing.
**Files modified**: 1-3 files

#### 5.1 Remove `templates/__init__.py` Dead Code

**File**: `src/claude_mpm/agents/templates/__init__.py`

The `AGENT_TEMPLATES` dict, `AGENT_NICKNAMES` dict, `get_template_path()`, `load_template()`, and `get_available_templates()` all reference non-existent `.json` files and always return None/empty.

**Steps**:
1. Verify no callers depend on non-None return values:
   ```bash
   grep -rn "get_template_path\|load_template\|get_available_templates\|AGENT_TEMPLATES\|AGENT_NICKNAMES" \
     src/claude_mpm/ --include="*.py" | grep -v templates/__init__
   ```
2. If callers exist, verify they handle None/empty gracefully
3. Remove dead code or replace with deprecation warnings

#### 5.2 Remove Unused Variables in `agents_metadata.py`

If any metadata references are orphaned by earlier phases, clean them up.

#### Phase 5 Verification

```bash
make test  # Full test suite
python3 -c "from claude_mpm.agents.templates import get_template_path; print(get_template_path('engineer'))"
# Should print deprecation warning or None
```

---

### Phase 6: End-to-End Verification

**Goal**: Verify the complete PM delegation chain works.
**Risk**: LOW -- read-only verification.
**Files modified**: 0

#### 6.1 Full Test Suite

```bash
make test  # All naming tests pass, no new regressions
```

#### 6.2 Empirical Delegation Test

Start a new PM session and test:

```
# These should all succeed (using name: field values):
Agent(subagent_type="Local Ops")        # Was: "local-ops" (broken)
Agent(subagent_type="Web QA")           # Was: "web-qa-agent" (broken)
Agent(subagent_type="API QA")           # Was: "api-qa-agent" (broken)
Agent(subagent_type="Security")         # Was: "security" (maybe worked, maybe not)
Agent(subagent_type="Vercel Ops")       # Was: "vercel-ops" (broken)
Agent(subagent_type="Google Cloud Ops") # Was: "gcp-ops" (broken)
Agent(subagent_type="Clerk Operations") # Was: "clerk-ops" (broken)
Agent(subagent_type="ticketing_agent")  # Was: "ticketing-agent" (broken)
```

#### 6.3 Verify PM_INSTRUCTIONS.md Consistency

```bash
# No filename-stem delegation targets remain
grep -cE '(delegate to|agent:).*\b(local-ops|web-qa-agent|api-qa-agent|gcp-ops|vercel-ops|clerk-ops)\b' \
  src/claude_mpm/agents/PM_INSTRUCTIONS.md
# Expected: 0
```

#### 6.4 Verify Agent Capabilities Section

The PM's "Available Agent Capabilities" section (generated at runtime) should list all deployed agents. Verify:
1. All 48 agents appear
2. Each shows correct `name:` value
3. No duplicates

---

## Files Modified Per Phase

### Phase 1 (0 code files)
- `.claude/agents/` (8 new deployed agent files -- from cache, not modified)

### Phase 2 (1-2 new files)
- `src/claude_mpm/core/agent_name_registry.py` (NEW)
- `scripts/extract_agent_names.sh` (NEW)

### Phase 3 (2 files)
- `src/claude_mpm/agents/PM_INSTRUCTIONS.md`
- `src/claude_mpm/agents/WORKFLOW.md`

### Phase 4 (3-4 files)
- `src/claude_mpm/services/agents/toolchain_detector.py`
- `src/claude_mpm/services/agents/loading/framework_agent_loader.py`
- `src/claude_mpm/services/agents/sources/git_source_sync_service.py`
- `src/claude_mpm/core/enums.py`

### Phase 5 (1-3 files)
- `src/claude_mpm/agents/templates/__init__.py`
- `src/claude_mpm/agents/agents_metadata.py` (if cleanup needed)

### Phase 6 (0 files)
- Verification only

**Total**: ~10-15 files

---

## Commit Strategy

| Phase | Commit Message | Can Ship Independently? |
|-------|---------------|------------------------|
| Phase 1 | `chore: deploy missing cached agents` | YES |
| Phase 2 | `feat: add authoritative agent name registry` | YES |
| Phase 3 | `fix: PM references agents by name: field values` | YES (after Phase 1) |
| Phase 4 | `fix: align hardcoded agent lists with deployed agents` | YES |
| Phase 5 | `chore: remove dead template code` | YES |
| Phase 6 | No commit (verification only) | N/A |

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| PM behavior changes after PM_INSTRUCTIONS.md update | References change from non-working (stem) to working (name:) -- strictly an improvement |
| Wrong `name:` value used in PM_INSTRUCTIONS.md | Phase 2 creates authoritative map from actual deployed agents; Phase 3 uses only values from that map |
| Deployment doesn't deploy all cached agents | Phase 1.3 has investigation steps for filter_non_mpm_agents and missing author: field |
| CORE_AGENTS list change breaks auto-configuration | Phase 4 traces usage before changing; full test suite validates |
| `name:` field values change in upstream repo | Out of scope; extraction script (Phase 2.2) can re-generate map when needed |
| Removing dead code breaks something | Phase 5 verifies no callers depend on non-None returns before removing |

---

## Success Criteria

1. All PM-referenced agents are deployed in `.claude/agents/`
2. PM_INSTRUCTIONS.md uses only `name:` field values when referencing agents
3. WORKFLOW.md uses only `name:` field values
4. Single authoritative agent name map exists in source code
5. CORE_AGENTS lists reference actual deployed agent files
6. `enums.py` uses hyphen-canonical format
7. Dead template code removed
8. Full test suite passes (no regressions)
9. Empirical delegation test passes for all PM-referenced agents

---

## Devil's Advocate Review

### Challenge 1: "PM might be smart enough to resolve stem to name:"

**Rebuttal**: Empirical evidence from analysis-v6 proves otherwise. `Agent(subagent_type="golang-engineer")` **fails** while `Agent(subagent_type="Golang Engineer")` succeeds. The matching is exact, not fuzzy. Even if Claude sometimes resolves it through the available agent list in the system prompt, this is unreliable and wastes inference tokens on resolution attempts.

### Challenge 2: "Creating agent_name_registry.py is over-engineering"

**Rebuttal**: Without it, PM_INSTRUCTIONS.md references will drift again as agents are added/renamed upstream. The registry provides:
- A single grep-able source of truth
- An extraction script to detect drift
- Import-able constants for source code that needs agent names

**Counter-counter**: The registry is a hardcoded copy of data that lives in `.claude/agents/*.md` files. It could go stale. The extraction script mitigates this, but it's a manual process.

**Verdict**: Include it, but keep it minimal. The extraction script is the real value -- it can be run as a CI check.

### Challenge 3: "Phase 1 deploys agents but they might get cleaned up on next deployment"

**Rebuttal**: `.claude/agents/` files are git-tracked. Once committed, they persist across deployments unless explicitly removed. The deployment pipeline adds/updates agents but doesn't remove manually-committed ones. The risk is if a future `claude-mpm agents deploy` with `--clean` flag removes agents not found in the current template source.

**Mitigation**: Verify deployment behavior. If `--clean` or reconciliation removes agents, the fix is ensuring the deployment source includes all cached agents.

### Challenge 4: "Changing CORE_AGENTS in toolchain_detector.py might break auto-configure"

**Rebuttal**: The current values (`qa-agent`, `local-ops-agent`, `research-agent`, etc.) don't match ANY real files. They're already broken. Fixing them to match actual filenames can only improve the situation.

**Evidence**: `ls .claude/agents/qa-agent.md` returns "not found". `ls .claude/agents/local-ops-agent.md` returns "not found". These CORE_AGENTS values have never worked.

### Challenge 5: "Some name: values are ugly (aws_ops_agent, ticketing_agent) -- should we normalize them?"

**Rebuttal**: Out of scope per constraints. These values come from the Git repo. PM must reference them as-is. Changing them would require modifying agent definitions, which is explicitly excluded. The ugliness is cosmetic; functional correctness requires exact matching.

### Challenge 6: "Why not just make subagent_type resolution fuzzy/normalized?"

**Rebuttal**: subagent_type resolution is a Claude Code platform behavior, not something claude-mpm controls. Even if we could change it, fuzzy matching creates ambiguity (e.g., does "ops" match "Ops", "Local Ops", or "DigitalOcean Ops"?). Exact matching with correct values is more reliable.

### Challenge 7: "The fallback list in git_source_sync_service.py uses repo filenames -- but repo files might have -agent suffix"

**Rebuttal**: Valid concern. The fallback list (Phase 4.3) needs to match actual filenames IN THE REPOSITORY, not in `.claude/agents/`. These may differ because deployment strips `-agent` suffix. Need to verify:
```bash
find ~/.claude-mpm/cache/agents -name "*.md" ! -name "BASE*" ! -name "README*" -exec basename {} \;
```
If repo has `research.md` (not `research-agent.md`), the fallback should use `research.md`.

### Challenge 8: "local-ops.md lacks author: field -- filter_non_mpm_agents will reject it"

**Rebuttal**: Investigation shows other deployed agents (research.md, code-analyzer.md, real-user.md, etc.) also lack `author:` fields but ARE deployed. So the filter either isn't active or doesn't block deployment in practice. However, this IS a potential issue if `filter_non_mpm_agents: true` is enforced more strictly in future versions.

**Mitigation**: Phase 1.3 includes investigation steps. If the filter blocks local-ops.md, the fix is either:
1. Adjust filter to accept agents from known MPM cache directories (code change, in scope)
2. Or disable the filter for cache-sourced agents (code change, in scope)
NOT: add author: to local-ops.md (agent definition change, out of scope)
