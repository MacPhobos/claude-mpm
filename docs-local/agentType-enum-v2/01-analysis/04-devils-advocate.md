# Devil's Advocate Analysis v2: Challenging the Agent Naming Proposals

**Date**: 2026-03-05
**Branch**: `agenttype-enums`
**Analyst**: Devil's Advocate (Research Agent)
**Methodology**: Evidence-based contrarian analysis — challenge every assumption, find what the team missed
**Context**: v8 Phases 1-4 already implemented; this analysis evaluates both completed and proposed changes

---

## Executive Summary

After thorough investigation of the codebase, prior research (v5 risk assessment, v6 devil's advocate, v8 correction plan), and the current state of deployed agents, I find **3 VALID CONCERNS**, **2 OVERBLOWN risks**, and **2 areas NEEDING MORE DATA**. The most critical finding: **two parallel normalization systems (`AgentNameNormalizer` and `AGENT_NAME_MAP`) have divergent display names**, creating a ticking time bomb that none of the prior analyses fully addressed. Additionally, the proposals' biggest blind spot is that the actual root problem — inconsistent `name:` field values — lives in an upstream repo explicitly declared out of scope.

---

## Challenge 1: Is `name:` Actually the Resolution Mechanism?

### Claim Being Challenged

Prior research (v8 plan) states: "PM delegates via `Agent(subagent_type="<value>")`. The `subagent_type` parameter is matched against the `name:` frontmatter field of deployed agent `.md` files in `.claude/agents/`."

### Counter-Evidence Found

**CONFIRMED: `name:` IS the resolution key.** I verified this independently by examining the Agent tool's available `subagent_type` values visible in the runtime system prompt. The list includes:

| `subagent_type` Value | Matches `name:` field? | Agent File |
|---|---|---|
| `Research` | YES | `research.md` → `name: Research` |
| `Engineer` | YES | `engineer.md` → `name: Engineer` |
| `ticketing_agent` | YES (underscore!) | `ticketing.md` → `name: ticketing_agent` |
| `aws_ops_agent` | YES (underscore!) | `aws-ops.md` → `name: aws_ops_agent` |
| `mpm_agent_manager` | YES (underscore!) | `mpm-agent-manager.md` → `name: mpm_agent_manager` |
| `nestjs-engineer` | YES (kebab!) | `nestjs-engineer.md` → `name: nestjs-engineer` |
| `real-user` | YES (kebab!) | `real-user.md` → `name: real-user` |
| `Google Cloud Ops` | YES (space!) | `gcp-ops.md` → `name: Google Cloud Ops` |
| `Clerk Operations` | YES | `clerk-ops.md` → `name: Clerk Operations` |
| `Documentation Agent` | YES | `documentation.md` → `name: Documentation Agent` |

Every single `subagent_type` in the runtime exactly matches the `name:` frontmatter field. Claude Code uses the `name:` field, NOT the filename stem.

**However**, this creates a critical implication the team hasn't addressed: **the `name:` field values are wildly inconsistent across agents**, and since they come from the upstream Git repo, they are explicitly OUT OF SCOPE for this project. The PM must use exact `name:` values including:
- Underscored names: `ticketing_agent`, `aws_ops_agent`, `mpm_agent_manager`, `mpm_skills_manager`
- Kebab-case names: `nestjs-engineer`, `real-user`
- Title Case with spaces: `Golang Engineer`, `Local Ops`, `Google Cloud Ops`
- Inconsistent casing: `Php Engineer` (not `PHP`), `Nextjs Engineer` (not `NextJS`), `Imagemagick` (not `ImageMagick`)

**The filename standardization effort addresses a SECONDARY identifier**, not the primary one.

### Does filename stem serve as fallback?

No evidence of fallback. From `system_context.py:19-33`, the system tells PM to use lowercase format, but this is claude-mpm's system context injection, not Claude Code's native resolution:

```python
# system_context.py:31-36
"IMPORTANT: The Task tool accepts both naming formats:
- Capitalized format: 'Research', 'Engineer', 'QA', 'Version Control', 'Data Engineer'
- Lowercase format: 'research', 'engineer', 'qa', 'version-control', 'data-engineer'"
```

But per v8 findings, this is WRONG — `Agent(subagent_type="golang-engineer")` **fails** while `Agent(subagent_type="Golang Engineer")` succeeds. The system context is providing incorrect guidance.

### Verdict: **VALID CONCERN**

The `name:` field IS the resolution key (confirmed). But the proposals focus on filename standardization while the actual resolution key (`name:`) has inconsistent values that are OUT OF SCOPE. This is addressing a symptom, not the disease.

---

## Challenge 2: Risk of `type:` → `agent_type:` Rename

### Claim Being Challenged

The proposal suggests standardizing from `type:` to `agent_type:` in agent frontmatter.

### Counter-Evidence Found

**This rename has ALREADY HAPPENED.** All 48 deployed agents in `.claude/agents/` use `agent_type:` (line 7 in every file). No agent uses bare `type:`. Evidence from grep:

```
.claude/agents/engineer.md:7:agent_type: engineer
.claude/agents/research.md:7:agent_type: research
.claude/agents/qa.md:7:agent_type: qa
... (all 48 agents)
```

The only reference to `type:` (without `agent_` prefix) is in example templates within `mpm-agent-manager.md:1247`:
```
type: engineer|ops|research|qa|security|docs
```

**Is `type:` a Claude Code standard field?** No evidence that Claude Code reads or interprets the `type:` or `agent_type:` field. The Claude Code standard frontmatter fields are `name:`, `description:`, and optionally `tools:`. The `agent_type:` field is a claude-mpm-specific extension used for categorization within MPM's agent system.

The agent frontmatter schema (`src/claude_mpm/config/schemas/agent_frontmatter_schema.json`) defines the expected fields with `additionalProperties: true`, meaning extra fields don't break anything. The required fields are: `name`, `description`, `version`, `model`.

### Verdict: **OVERBLOWN**

This rename is already complete. No risk remains. The only cleanup needed is the example template in `mpm-agent-manager.md` that still shows the old `type:` format, and that's cosmetic.

---

## Challenge 3: Archive Removal Risks

### Claim Being Challenged

Proposal #4 suggests removing archive templates from `src/claude_mpm/agents/templates/archive/`.

### Counter-Evidence Found

**The archive directory does NOT exist.** Glob search for `src/claude_mpm/agents/templates/archive/**/*` returns no files. The directory has already been removed (or never existed at this path).

However, a DIFFERENT archive concept exists:

1. **`.claude/agents/unused/`** — Used for archiving/deactivating agents during deployment:
   - `tests/conftest.py:527`: `"archive": project / ".claude" / "agents" / "unused"`
   - `tests/conftest.py:149`: "Checks both agents/ (for removals) and agents/unused/ (for archives)"
   - Test safety fixtures guard against accidental archival of live agents

2. **`.claude-mpm/inbox/.archive/`** — Message archiving (unrelated to agents):
   - `src/claude_mpm/migrations/migrate_messages_to_db.py:84`

3. **`_archive/` at project root** — General project archive containing historical documents

No tests reference `src/claude_mpm/agents/templates/archive/`. No migration code depends on it.

### Verdict: **OVERBLOWN**

The proposed archive directory doesn't exist. The actual archive mechanisms (`.claude/agents/unused/`) serve a different purpose (runtime agent deactivation) and should NOT be removed — they're actively tested and used by the deployment pipeline.

---

## Challenge 4: Separator Standardization Risks (`_` → `-` in Filenames)

### Claim Being Challenged

Proposal #1 suggests standardizing filenames to use `-` separators instead of `_`.

### Counter-Evidence Found

**This rename has ALREADY HAPPENED (mostly).** All 48 current files in `.claude/agents/` already use hyphens:

```
aws-ops.md, clerk-ops.md, code-analyzer.md, content-agent.md,
data-engineer.md, data-scientist.md, digitalocean-ops.md,
engineer.md, golang-engineer.md, ... (all hyphens)
```

No underscore-named agent files remain in `.claude/agents/`. The v8 Phase 1-4 commits already addressed this.

**BUT — the `name:` field values still use underscores in 5 agents:**

| Filename (hyphen) | `name:` Field (MISMATCH) |
|---|---|
| `ticketing.md` | `ticketing_agent` |
| `aws-ops.md` | `aws_ops_agent` |
| `mpm-agent-manager.md` | `mpm_agent_manager` |
| `mpm-skills-manager.md` | `mpm_skills_manager` |
| `nestjs-engineer.md` | `nestjs-engineer` (kebab, not Title Case) |
| `real-user.md` | `real-user` (kebab, not Title Case) |

Since `name:` is the resolution key and these values come from the upstream repo, this creates a permanent mismatch: **filenames use hyphens but PM must use underscores for 4 agents**.

### The Dual Normalization System Problem (CRITICAL FINDING)

Two separate normalization systems exist with DIVERGENT display names:

| Agent | `name:` Field (actual) | `AGENT_NAME_MAP` (registry) | `CANONICAL_NAMES` (normalizer) |
|---|---|---|---|
| ticketing | `ticketing_agent` | `ticketing_agent` | `Ticketing` |
| code-analyzer | `Code Analysis` | `Code Analysis` | `Code Analyzer` |
| gcp-ops | `Google Cloud Ops` | `Google Cloud Ops` | `GCP Ops` |
| clerk-ops | `Clerk Operations` | `Clerk Operations` | `Clerk Ops` |
| real-user | `real-user` | `real-user` | `Real User` |
| mpm-agent-manager | `mpm_agent_manager` | `mpm_agent_manager` | `MPM Agent Manager` |
| mpm-skills-manager | `mpm_skills_manager` | `mpm_skills_manager` | `MPM Skills Manager` |
| javascript-engineer | `Javascript Engineer` | `Javascript Engineer` | `JavaScript Engineer` |
| typescript-engineer | `Typescript Engineer` | `Typescript Engineer` | `TypeScript Engineer` |
| nestjs-engineer | `nestjs-engineer` | `nestjs-engineer` | `NestJS Engineer` |

**`AGENT_NAME_MAP` (in `agent_name_registry.py`) matches the actual `name:` fields.**
**`CANONICAL_NAMES` (in `agent_name_normalizer.py`) does NOT match — it uses "prettier" display names.**

This means:
- Code using `AgentNameNormalizer.normalize("ticketing")` gets `"Ticketing"` (WRONG for delegation)
- Code using `get_agent_name("ticketing")` gets `"ticketing_agent"` (CORRECT for delegation)
- Code using `AgentNameNormalizer.normalize("gcp-ops")` gets `"GCP Ops"` (WRONG for delegation)
- Code using `get_agent_name("gcp-ops")` gets `"Google Cloud Ops"` (CORRECT for delegation)

The `AgentNameNormalizer` is used for TODO prefixes, display, and color coding. If any code path uses it for delegation (e.g., converting TodoWrite agent names back to `subagent_type`), it will produce wrong values for at least 10 agents.

**Evidence of usage conflict** (`agent_name_normalizer.py:282-283`):
```python
# Normalizer converts underscores to hyphens
cleaned = cleaned.replace("_", "-").replace(" ", "-")
```

And then looks up in `CANONICAL_NAMES` which has the "pretty" (but wrong-for-delegation) names. The `to_task_format()` method produces lowercase-hyphenated versions of the CANONICAL (wrong) names.

### Git History Impact

Renaming files complicates `git blame` and `git log --follow`. For 48 agents that were already renamed, this history disruption has already occurred. No additional risk from future renames.

### Verdict: **VALID CONCERN**

Filename standardization is complete but exposed a deeper problem: two parallel name registries (`AGENT_NAME_MAP` vs `CANONICAL_NAMES`) that disagree on 10+ agent display names. Only `AGENT_NAME_MAP` matches actual `name:` field values. The `AgentNameNormalizer.CANONICAL_NAMES` is a ticking time bomb for any code path that uses it for delegation-related logic.

---

## Challenge 5: Is Duplication Actually Harmful?

### Claim Being Challenged

Proposal #5 suggests eliminating duplicate agents deployed under different filenames.

### Counter-Evidence Found

**Current state**: The v8 correction plan identified that the `AGENT_NAME_MAP` in `agent_name_registry.py:100-115` includes legacy `-agent` suffix variants for backward compatibility:

```python
# Legacy -agent suffix variants (backward compatibility)
"research-agent": "Research",
"qa-agent": "QA",
"documentation-agent": "Documentation Agent",
"ops-agent": "Ops",
"security-agent": "Security",
"web-qa-agent": "Web QA",
"api-qa-agent": "API QA",
"local-ops-agent": "Local Ops",
"vercel-ops-agent": "Vercel Ops",
"gcp-ops-agent": "Google Cloud Ops",
"digitalocean-ops-agent": "DigitalOcean Ops",
"javascript-engineer-agent": "Javascript Engineer",
"web-ui-engineer": "Web UI",
"ticketing-agent": "ticketing_agent",
```

However, looking at the actual deployed files in `.claude/agents/`, there are NO duplicate files with `-agent` suffixes (the old duplicates have been cleaned up). The legacy entries exist only in the `AGENT_NAME_MAP` as a compatibility shim.

**Evidence of actual failures?** The `toolchain_detector.py` CORE_AGENTS list previously used `-agent` suffixed names that matched NO deployed files:

```python
# toolchain_detector.py (BEFORE v8 Phase 4 fix):
CORE_AGENTS = [
    "engineer",
    "qa-agent",            # NO FILE "qa-agent.md" existed
    "memory-manager-agent",
    "local-ops-agent",     # NO FILE
    "research-agent",      # NO FILE
    "documentation-agent", # NO FILE
    "security-agent",      # NO FILE
]
```

This was a real, confirmed failure — 5 of 7 CORE_AGENTS entries referenced non-existent files. This was fixed in v8 Phase 4 (commit `663bdaaf`).

**Cost/benefit of deduplication**: The legacy entries in `AGENT_NAME_MAP` serve backward compatibility. Removing them could break code that still references agents by old names. The overhead is minimal (14 extra dict entries).

### Verdict: **NEEDS MORE DATA**

File-level duplication is already resolved. The remaining "duplication" is backward-compatibility entries in `AGENT_NAME_MAP`. The question is: does any code still reference agents by `-agent` suffixed names? A comprehensive grep for each legacy name would answer this definitively. The `toolchain_detector.py` issue was real and already fixed, but there may be other references lurking in configuration or documentation.

---

## Challenge 6: Single Source of Truth from Git Repositories

### Claim Being Challenged

Proposal #6 suggests git repositories should be the single source of truth for agent definitions.

### Counter-Evidence Found

**The architecture already enforces this.** Agent definitions flow:

```
claude-mpm-agents repo (upstream)
    → ~/.claude-mpm/cache/agents/ (local cache)
        → .claude/agents/ (deployed, git-tracked in project)
```

The `AGENT_NAME_MAP` in `agent_name_registry.py` is a HARDCODED COPY of data from the upstream repo. It's explicitly documented as such (`agent_name_registry.py:1-8`):

> "This module provides the canonical mapping between agent filename stems and their `name:` frontmatter field values as declared in the deployed `.md` agent files."

**The real problem**: There are now THREE sources of agent identity:

1. **Upstream repo** (`claude-mpm-agents`): Defines `name:` field values — the ACTUAL source of truth
2. **`AGENT_NAME_MAP`** (`agent_name_registry.py`): Hardcoded copy — can go stale
3. **`CANONICAL_NAMES`** (`agent_name_normalizer.py`): Different hardcoded copy — ALREADY stale for 10+ agents

The extraction script (`scripts/extract_agent_names.sh` per v8 plan) can detect drift between sources 1 and 2, but no mechanism detects drift between sources 2 and 3.

**Alternative approach: dynamic resolution**

Instead of hardcoded maps, could we read `name:` fields dynamically at startup?

```python
# Conceptual: read deployed agents and build map dynamically
def build_agent_map(agents_dir: Path) -> dict[str, str]:
    agent_map = {}
    for agent_file in agents_dir.glob("*.md"):
        frontmatter = parse_frontmatter(agent_file)
        agent_map[agent_file.stem] = frontmatter.get("name", agent_file.stem)
    return agent_map
```

This would eliminate staleness entirely but adds startup cost and requires `.claude/agents/` to always be available.

### Verdict: **VALID CONCERN**

Having three divergent identity systems is worse than having one imperfect one. The `AGENT_NAME_MAP` was the right solution (v8 Phase 2), but `CANONICAL_NAMES` was not updated to match and now actively provides wrong values. The "single source of truth" goal is undermined by having TWO hardcoded registries.

---

## Challenge 7: Alternative Approaches

### Claim Being Challenged

The proposals assume renaming/standardizing is the right approach. Are there better alternatives?

### Alternatives Evaluated

#### 7a: Resolution Mapping Layer (Instead of Renaming)

**Concept**: Keep filenames as-is, add a mapping layer that translates any input format to the correct `name:` value.

**Assessment**: This is EXACTLY what `AGENT_NAME_MAP` + `AgentNameNormalizer` already do. The problem is they disagree. Adding a THIRD mapping layer would make things worse. The right fix is consolidating the existing two.

**Verdict**: Already implemented (partially). Consolidation needed, not more layers.

#### 7b: Agent Aliasing (Multiple Names → Same Agent)

**Concept**: Allow agents to register multiple aliases so that `"local-ops"`, `"Local Ops"`, and `"local_ops"` all resolve to the same agent.

**Assessment**: The `AgentNameNormalizer.ALIASES` dict already does this with 80+ entries. The problem isn't lack of aliasing — it's that the aliases resolve to wrong canonical values for some agents.

**Verdict**: Already implemented. Fix the canonical values, don't add more aliases.

#### 7c: Fix Claude Code's Resolution (Not Our Naming)

**Concept**: Make Claude Code's agent resolution case-insensitive and separator-agnostic.

**Assessment**: Claude Code is an external platform we don't control. Even if we could lobby for fuzzy matching, it would create ambiguity (does `"ops"` match `Ops`, `Local Ops`, `Vercel Ops`, `Google Cloud Ops`, or `DigitalOcean Ops`?). Exact matching is actually the RIGHT behavior — we just need to provide the exact right values.

**Verdict**: Not actionable. The fix is in our data, not their platform.

#### 7d: Fix the Upstream `name:` Field Values

**Concept**: Standardize all `name:` values in the `claude-mpm-agents` repo to use consistent Title Case format.

**Assessment**: This is the ACTUAL root cause fix. Currently declared out of scope, but it's the only change that would resolve:
- `ticketing_agent` → `Ticketing Agent` (or just `Ticketing`)
- `aws_ops_agent` → `AWS Ops`
- `mpm_agent_manager` → `MPM Agent Manager`
- `mpm_skills_manager` → `MPM Skills Manager`
- `nestjs-engineer` → `NestJS Engineer`
- `real-user` → `Real User`

**Verdict**: RECOMMENDED as the highest-impact change. Declaring it "out of scope" is a process decision, not a technical one. The 6 non-conforming `name:` values are the root cause of most naming confusion.

---

## Risk Matrix

| # | Challenge | Severity | Likelihood | Verdict |
|---|---|---|---|---|
| 1 | `name:` IS resolution key, but `name:` values are inconsistent | HIGH | CERTAIN | **VALID CONCERN** |
| 2 | `type:` → `agent_type:` rename risk | LOW | N/A (done) | **OVERBLOWN** |
| 3 | Archive removal risk | LOW | N/A (doesn't exist) | **OVERBLOWN** |
| 4 | Separator standardization — dual normalization divergence | **CRITICAL** | CERTAIN | **VALID CONCERN** |
| 5 | Duplication harm — legacy compatibility entries | MEDIUM | UNKNOWN | **NEEDS MORE DATA** |
| 6 | Single source of truth — three identity systems | HIGH | CERTAIN | **VALID CONCERN** |
| 7a | Alternative: mapping layer | N/A | N/A | Already implemented |
| 7b | Alternative: aliasing | N/A | N/A | Already implemented |
| 7c | Alternative: fix Claude Code | N/A | NOT ACTIONABLE | Out of our control |
| 7d | Alternative: fix upstream `name:` values | HIGH IMPACT | ACTIONABLE | **RECOMMENDED** |

---

## Critical Finding: The `AgentNameNormalizer` vs `AGENT_NAME_MAP` Divergence

This is the most important finding in this analysis and was NOT addressed by any prior research.

### The Problem

Two modules provide agent name resolution with DIFFERENT outputs for the same input:

**File**: `src/claude_mpm/core/agent_name_normalizer.py` (472 lines)
**File**: `src/claude_mpm/core/agent_name_registry.py` (167 lines)

```python
# agent_name_normalizer.py — used for TODO prefixes, display, colors
AgentNameNormalizer.normalize("gcp-ops")     → "GCP Ops"        # WRONG for delegation
AgentNameNormalizer.normalize("ticketing")   → "Ticketing"      # WRONG for delegation
AgentNameNormalizer.normalize("nestjs-engineer") → "NestJS Engineer" # WRONG for delegation

# agent_name_registry.py — used for PM delegation resolution
get_agent_name("gcp-ops")     → "Google Cloud Ops"   # CORRECT (matches name: field)
get_agent_name("ticketing")   → "ticketing_agent"    # CORRECT (matches name: field)
get_agent_name("nestjs-engineer") → "nestjs-engineer" # CORRECT (matches name: field)
```

### Impact

- **10 agents** have divergent names between the two systems
- Any code path using `AgentNameNormalizer` for delegation will silently fail
- `to_task_format()` in normalizer produces wrong `subagent_type` values for affected agents
- TODO prefixes show "pretty" names that differ from actual delegation names

### Recommendation

**Option A (Minimal)**: Update `CANONICAL_NAMES` in `AgentNameNormalizer` to match `AGENT_NAME_MAP` values exactly. Accept "ugly" display names like `ticketing_agent` in TODO prefixes.

**Option B (Merge)**: Merge the two systems into one authoritative module. Use `AGENT_NAME_MAP` as the source, add display formatting as a separate concern.

**Option C (Fix Upstream + Merge)**: Fix the 6 non-conforming `name:` values in the upstream repo to use Title Case, then merge the two systems. This makes Option B trivial because all names would be human-readable.

---

## Recommendations

### Immediate (This PR)

1. **MUST**: Reconcile `AgentNameNormalizer.CANONICAL_NAMES` with `AGENT_NAME_MAP` — currently 10 agents have divergent names. This is a latent bug.

2. **SHOULD**: Add a test that asserts `CANONICAL_NAMES` and `AGENT_NAME_MAP` produce consistent values for all agents. This prevents future drift.

3. **SHOULD**: Fix `system_context.py:31-36` — it incorrectly tells PM that lowercase format works. It doesn't for most agents (only single-word ones like `research`, `engineer`, `qa` work in lowercase).

### Near-Term (Next Sprint)

4. **SHOULD**: Fix the 6 non-conforming `name:` values in the upstream `claude-mpm-agents` repo. This resolves the root cause and simplifies everything downstream.

5. **CONSIDER**: Merge `AgentNameNormalizer` and `agent_name_registry` into a single module with clear separation between "delegation name" (must match `name:` field exactly) and "display name" (for human-readable output).

### Not Recommended

6. **DO NOT**: Add more normalization layers or alias systems. The problem is too many maps, not too few.

7. **DO NOT**: Make Claude Code resolution fuzzy. Exact matching is correct; fix the data instead.

---

## Evidence File Index

| Finding | Primary Evidence |
|---------|-----------------|
| `name:` is resolution key | Agent tool `subagent_type` values match `name:` fields exactly |
| Dual normalization divergence | `agent_name_normalizer.py:21-75` vs `agent_name_registry.py:43-116` |
| `agent_type:` rename complete | `grep "^agent_type:" .claude/agents/*.md` — all 48 use `agent_type:` |
| Archive dir doesn't exist | `glob src/claude_mpm/agents/templates/archive/**/*` returns empty |
| Filename standardization complete | All `.claude/agents/*.md` files use hyphens |
| `system_context.py` incorrect | `src/claude_mpm/core/system_context.py:31-36` claims lowercase works |
| Legacy `-agent` suffix entries | `agent_name_registry.py:100-115` — 14 backward-compat entries |
| Non-conforming `name:` values | `ticketing.md`, `aws-ops.md`, `mpm-agent-manager.md`, `mpm-skills-manager.md`, `nestjs-engineer.md`, `real-user.md` |
| v8 Phases 1-4 implemented | Commits `e2c9e59c`, `6ff9727c`, `f392f54e`, `663bdaaf` |
| `toolchain_detector.py` was broken | v8 current-state-audit: 5 of 7 CORE_AGENTS referenced non-existent files |
| `ticketing.md` wrong `agent_type` | `.claude/agents/ticketing.md:7: agent_type: documentation` (should be `ticketing`) |
| Schema allows extra fields | `agent_frontmatter_schema.json:127: "additionalProperties": true` |
| Schema name pattern violated | `agent_frontmatter_schema.json:17: "pattern": "^[a-z][a-z0-9_-]*$"` — requires lowercase, but agents use Title Case |
| Archive deliberately deleted | Commit `bb9923cb`: "feat: implement Phase 4 -- delete templates/archive directory" (39 JSON files) |
| Dedup infrastructure exists | `agents_cleanup.py:76`: `_find_duplicate_agents_by_content()` + `_find_agent_suffix_duplicates()` |
| Agent files test-protected | `tests/conftest.py:141-186`: `verify_agents_untouched` autouse fixture guards against accidental modification |
| `todo_task_tools.py` teaches PM | Line 47: "Valid subagent_type values (must match deployed agent YAML `name:` field values)" |
| Historical duplication fixed | CHANGELOG line 991: "startup: prevent duplicate agent deployment after sync" + 3 more entries |
| PM skill contradicts itself | `SKILL.md:37-51` uses mixed formats: `engineer` (lowercase) alongside `Research` (Title Case) |

---

## Appendix A: Supplementary Agent Research Findings

### Frontmatter Schema Name Pattern Violation

The `agent_frontmatter_schema.json` (line 17) defines:
```json
"name": {
  "type": "string",
  "pattern": "^[a-z][a-z0-9_-]*$",
  "description": "Agent identifier (kebab-case or snake_case)"
}
```

This pattern **requires lowercase** — but the majority of deployed agents use Title Case names like `Research`, `Engineer`, `Documentation Agent`, `Google Cloud Ops`. The `frontmatter_validator.py` (line 227) would attempt to "fix" these names to lowercase with underscores if validation were enforced strictly.

**Implication**: The schema is wrong (not the agents). If someone enforces schema validation, it would break every agent with a Title Case `name:` field.

### Archive Deletion Was Deliberate and Well-Documented

The `src/claude_mpm/agents/templates/archive/` directory was removed through a 4-commit cleanup:
1. `67f21f09`: Original JSON-to-Markdown migration
2. `08a5905e`: Clean up obsolete JSON template references
3. `b0a7f9c7`: Remove all references to templates/archive directory
4. `bb9923cb`: Delete templates/archive directory (39 JSON files removed)

A separate `tests/archive/` directory exists but is excluded from pytest collection via `pyproject.toml:328`.

### Historical Duplication Impact Was Cosmetic, Not Functional

Per `docs/_archive/2025-12-implementation/agent-count-discrepancy-2025-12-15.md`: "Even with inflated counts, agents deploy correctly (duplicates are overwritten or skipped)." The system has robust mitigation: dedup in git sync (`git_source_manager.py:402`), a dedicated cleanup command (`agents_cleanup.py`), and content-hash comparison.

### PM Skill Document Contains Contradictory `subagent_type` Guidance

The `/mpm` skill (`SKILL.md:37-55`) shows `subagent_type` values in mixed formats:
- `subagent_type="engineer"` (lowercase — works because `name: Engineer` and Claude Code may be case-insensitive for single words)
- `subagent_type="Research"` (Title Case — correct, matches `name: Research`)
- `subagent_type="version-control"` (kebab — WRONG per empirical evidence, should be `"Version Control"`)

This contradicts `todo_task_tools.py:60` which explicitly states: "Claude Code's Task tool requires exact agent names as defined in the deployed agent YAML frontmatter `name:` field."
