# Devil's Advocate: How the Rename WILL Break Things

**Analysis Date**: 2026-03-04
**Branch**: `agenttype-enums`
**Analyst**: devils-advocate teammate
**Methodology**: Aggressive skepticism — assume the rename breaks things and find proof

---

## Executive Summary

The proposed rename of agent template files from `underscore_names.md` to `hyphen-names.md` introduces **8 confirmed or likely breaks** across multiple layers of the system. The breaks range from immediately fatal (scripts that will throw FileNotFoundError) to subtle (dictionary key mismatches that silently return wrong data). The core problem: agent names flow through at least 5 separate systems with different normalization assumptions, and the rename disrupts each one differently.

---

## Attack Vector 1: `scripts/bump_agent_versions.py` — CONFIRMED BREAK

**File**: `scripts/bump_agent_versions.py:10-42`

The version bumper hardcodes underscore filenames as strings to construct file paths:

```python
AGENTS_WITH_SKILLS = [
    "golang_engineer",        # Will fail after rename → golang-engineer.md
    "local_ops_agent",        # Will fail after rename → local-ops.md
    "python_engineer",        # Will fail after rename → python-engineer.md
    "react_engineer",
    "rust_engineer",
    "typescript_engineer",
    "vercel_ops_agent",
    "nextjs_engineer",
    ...
]
```

After the rename, `AGENTS_DIR / f"{agent_name}.json"` (or `.md`) won't resolve. The file no longer exists at the old path. **This script silently fails or crashes** depending on error handling.

**Additional irony**: The script ALREADY has the inconsistency baked in — it includes `"php-engineer"` and `"ruby-engineer"` with hyphens (lines 33-34) alongside `"golang_engineer"` with underscores. The rename was partially applied to this file, **creating the exact bug we're warning about**.

**Classification**: CONFIRMED BREAK — `FileNotFoundError` on any agent in the rename list.

---

## Attack Vector 2: `agent_capabilities_service.py` Raw Stem — CONFIRMED BREAK

**File**: `src/claude_mpm/services/agent_capabilities_service.py:224`

```python
agent_id = agent_file.stem  # NO NORMALIZATION
```

Then at line 248:
```python
discovered_agents[agent_id] = {
    "id": agent_id,
    ...
    "category": self._categorize_agent(agent_id, content),  # ← uses raw stem
}
```

If the deployed agent file is `golang-engineer.md` (after redeploy), then:
- `agent_id = "golang-engineer"` (hyphen, from stem)
- Stored in `discovered_agents["golang-engineer"]`
- But `agent_capabilities.yaml` has key `golang_engineer` (underscore)

The lookup `agent_capabilities["golang_engineer"]` will succeed, but `agent_capabilities["golang-engineer"]` will MISS. The capabilities service returns wrong/empty data for all renamed agents.

**Contrast with**: `unified_agent_registry.py:319` which DOES normalize:
```python
return name.lower().replace("-", "_").replace(" ", "_")
```

Two different discovery paths — one normalizes, one doesn't. Same agent, different IDs depending on which path is used.

**Classification**: CONFIRMED BREAK — Silent capability lookup failures. Agent gets wrong category, wrong metadata.

---

## Attack Vector 3: `agent_capabilities.yaml` Internal Inconsistency — CONFIRMED BREAK

**File**: `src/claude_mpm/config/agent_capabilities.yaml`

The YAML already has an internal inconsistency:

```yaml
php_engineer:           # outer key: underscore
  agent_id: "php-engineer"   # inner value: hyphen  ← ALREADY WRONG

ruby_engineer:          # outer key: underscore
  agent_id: "ruby-engineer"  # inner value: hyphen  ← ALREADY WRONG

python_engineer:        # outer key: underscore
  agent_id: "python_engineer"  # inner value: underscore ← CONSISTENT

golang_engineer:        # outer key: underscore
  agent_id: "golang_engineer"  # inner value: underscore ← CONSISTENT
```

The rename proposal requires deciding: do we rename the outer YAML keys too? If yes, code that does `yaml_data["golang_engineer"]` breaks (expects underscore key). If no, the YAML remains internally inconsistent — outer key says one thing, inner `agent_id` says another.

Any code that uses the YAML keys as agent IDs will be broken by a rename. Any code that reads `agent_id` from the YAML and uses it as a file path is already broken for `php_engineer` and `ruby_engineer`.

**Classification**: CONFIRMED BREAK — Internal YAML inconsistency will be AMPLIFIED by the rename, not resolved.

---

## Attack Vector 4: `tool_analysis.py` Exact String Matching — LIKELY BREAK

**File**: `src/claude_mpm/hooks/claude_hooks/tool_analysis.py:84-86`

```python
"is_pm_delegation": tool_input.get("subagent_type") == "pm",
"is_research_delegation": tool_input.get("subagent_type") == "research",
"is_engineer_delegation": tool_input.get("subagent_type") == "engineer",
```

These are EXACT string comparisons against `subagent_type` values. The `subagent_type` is what the PM passes when calling the Task tool.

**The break scenario**: If the PM is instructed to use `subagent_type: "local-ops"` (hyphen) after the rename, and code elsewhere ALSO reads `subagent_type` and checks `== "local_ops"` (underscore), the check fails silently. The dashboard incorrectly marks these delegations as NOT delegation-related.

The three checks cover only core agent types (`pm`, `research`, `engineer`) and NOT the specialized agents being renamed. But they demonstrate the pattern: whenever code checks `subagent_type` with exact string matching, a naming change silently breaks the check.

**Classification**: LIKELY BREAK — Depends on what `subagent_type` values the PM actually emits. If PM uses exact file stem as subagent_type, any check against the old underscore name fails.

---

## Attack Vector 5: `subagent_processor.py` Hardcoded `is_delegation_related` Check — LIKELY BREAK

**File**: `src/claude_mpm/hooks/claude_hooks/services/subagent_processor.py:351-352`

```python
"is_delegation_related": agent_type
    in ["research", "engineer", "pm", "ops", "qa", "documentation", "security"],
```

This hardcoded list covers only base agent types. But the issue is the same pattern: if `agent_type` is now derived from a renamed filename like `"local-ops"` instead of `"local_ops"`, and there are similar checks elsewhere in the hook pipeline, they SILENTLY return false.

The dashboard, event routing, and tracking all depend on `is_delegation_related`. If it's wrong, events get misclassified.

**Classification**: LIKELY BREAK — Affects monitoring/dashboard accuracy. Not immediately fatal but corrupts observability data.

---

## Attack Vector 6: `AgentNameNormalizer.CANONICAL_NAMES` — POTENTIAL BREAK

**File**: `src/claude_mpm/core/agent_name_normalizer.py:21-75`

The normalizer DOES handle hyphens (line 283):
```python
cleaned = cleaned.replace("-", "_").replace(" ", "_")
```

So `"golang-engineer"` normalizes to `"Golang Engineer"` correctly.

**BUT** — the normalizer is only called if code USES it. It is NOT called at the Claude Code level when resolving `subagent_type` to agent files. It is NOT called in `agent_capabilities_service.py`. It is NOT called in `bump_agent_versions.py`.

The normalizer is a partial fix that only works when explicitly invoked, and many code paths bypass it entirely.

**Classification**: POTENTIAL BREAK — The normalizer works, but it's not universally applied. Every code path that skips the normalizer becomes a break point after the rename.

---

## Attack Vector 7: Deployed `.claude/agents/` vs Template Source — LIKELY BREAK

**The Two-Phase Problem**:

The rename script (`scripts/rename_templates_to_dashes.sh`) renames **source templates** in:
```
src/claude_mpm/agents/templates/golang_engineer.md → golang-engineer.md
```

But the **deployed files** in `.claude/agents/` are NOT automatically renamed:
```
.claude/agents/golang_engineer.md  ← STILL EXISTS with old name
```

Evidence from inspecting `.claude/agents/` — right now the deployed directory has:
- Underscore files: `golang_engineer.md`, `java_engineer.md`, `ruby_engineer.md`, `php_engineer.md`, etc.
- Hyphen files: `local-ops-agent.md`, `python-engineer.md`, `typescript-engineer.md`, etc.

**This means after the rename but BEFORE redeploy**:
- Source templates: all hyphens
- Deployed `.claude/agents/`: mixed (old underscore + some already hyphen)

**After redeploy**: The deployment copies source templates to `.claude/agents/`. Now there will be DUPLICATE agents! `golang-engineer.md` AND `golang_engineer.md` both exist — two different registrations of the same agent with different IDs.

**Classification**: LIKELY BREAK — Duplicate agent files. The framework's precedence/discovery logic may pick the wrong one, or both fire, causing double-execution.

---

## Attack Vector 8: Backwards Compatibility — User Scripts/Configs — POTENTIAL BREAK

**Evidence from codebase**:
- `scripts/bump_agent_versions.py:7`: Hardcoded to absolute path `/Users/masa/Projects/claude-mpm/...` (different machine path!)
- `scripts/VERSION_BUMP_SUMMARY.md:90`: References a for-loop with both `golang_engineer` AND `php-engineer` — already broken

**User-facing breaks**:

1. **`claude-mpm agents deploy golang_engineer`** — If a user has this in a script, after rename they'd need to change to `golang-engineer` or `golang-engineer-agent` (whatever the new name is)

2. **Agent ID in `--id` argument**: The CLI parser says "lowercase, hyphens only" (`agent_manager_parser.py:74`), but users may already have scripts using underscore names

3. **PM prompt content**: The generated CLAUDE.md lists agents by name. If the PM's built-in instructions hardcode `"python_engineer"` somewhere, those hardcoded references break when the deployed agent file changes name.

4. **Memory files**: Agent memory files in `.claude-mpm/memories/` may be named after agent IDs (e.g., `golang_engineer.md`). After a rename that changes the agent's effective ID, memory lookups fail — the agent can no longer find its own memories.

**Classification**: POTENTIAL BREAK — No direct code evidence of user script breakage (it's external), but the pattern is clear. Memory file naming is a likely internal break.

---

## Attack Vector 9: `agent_capabilities.yaml` `local_ops_agent` — CONFIRMED BREAK

The rename script maps:
```
mv local_ops_agent.md local-ops.md
```

But `agent_capabilities.yaml` has entry:
```yaml
local_ops_agent:
  agent_id: "local_ops_agent"
  metadata:
    template_file: "local-ops.md"  # ← ALREADY references hyphen!
```

And `scripts/bump_agent_versions.py` references `"local_ops_agent"` (underscore, no `-agent` suffix).

After rename:
- YAML key: `local_ops_agent` (unchanged? Or also renamed?)
- Template file: `local-ops.md` ✓ (already consistent with rename target)
- `bump_agent_versions.py`: looks for `local_ops_agent` (old name) — **FAILS**

**Classification**: CONFIRMED BREAK — The inconsistency is already present; rename amplifies it.

---

## The Meta-Problem: Pre-Existing Inconsistency

The codebase **already has mixed naming conventions** right now, before any rename:

| Location | Convention | Examples |
|----------|-----------|---------|
| `.claude/agents/` deployed files | MIXED | `golang_engineer.md` AND `python-engineer.md` |
| `agent_capabilities.yaml` outer keys | Underscore | `golang_engineer`, `python_engineer` |
| `agent_capabilities.yaml` `agent_id` values | Mixed | `"python_engineer"` but `"php-engineer"` |
| `AgentNameNormalizer.ALIASES` | Underscore keys | `"golang_engineer"`, `"python_engineer"` |
| `AgentNameNormalizer.CANONICAL_NAMES` | Underscore keys | `"golang_engineer"`, `"local_ops"` |
| `bump_agent_versions.py` | MIXED | `"golang_engineer"` AND `"php-engineer"` |
| PM skill templates | MIXED | `python-engineer`, `local-ops` (hyphens in docs) |

The rename doesn't solve this inconsistency — it creates a new inconsistency while the old one still exists. **You'd need to update ALL of these simultaneously, and there's no atomic operation for that.**

---

## Risk Matrix

| Break | Severity | Detectability | How to Trigger |
|-------|----------|--------------|----------------|
| `bump_agent_versions.py` file path | HIGH | Easy (FileNotFoundError) | Run version bumper script |
| `agent_capabilities_service.py` stem mismatch | HIGH | Silent (wrong data) | Any agent listing/capabilities query after redeploy |
| YAML internal inconsistency | MEDIUM | Silent | Agent auto-configuration feature |
| `tool_analysis.py` exact matches | MEDIUM | Silent | Dashboard delegation tracking |
| `subagent_processor.py` list check | LOW | Silent | Dashboard event filtering |
| Duplicate agents in `.claude/agents/` | HIGH | Intermittent | Redeploy without cleanup of old files |
| User scripts with hardcoded names | HIGH | Silent until run | User automation, CI/CD scripts |
| Memory file naming mismatch | MEDIUM | Silent (lost memories) | Agent memory lookups after rename |

---

## Recommendations from the Devil's Advocate

These are not suggestions that the rename IS wrong — they are minimum requirements to NOT break things:

1. **Update `agent_capabilities.yaml` keys simultaneously** — All outer keys must match the new hyphen names. All `agent_id` values must be consistent.

2. **Update `AgentNameNormalizer.CANONICAL_NAMES` and `ALIASES`** — Add hyphen keys OR normalize at the point of insertion.

3. **Update `scripts/bump_agent_versions.py`** — Completely rewrite to derive filenames dynamically from the filesystem rather than hardcoding.

4. **Cleanup deployed `.claude/agents/` files** — The rename script must also update the deployed directory AND remove old underscore files.

5. **Verify `subagent_type` resolution** — Confirm whether Claude Code resolves `subagent_type` from file stem or from frontmatter `name:` field. This is CRITICAL — if it's file stem, all existing Task tool calls with underscore names break immediately.

6. **Atomic migration** — Rename template sources, redeploy immediately, delete old names. Partial state (templates renamed, deployed still old) must be treated as broken.

---

## Evidence File Index

| Finding | Primary Evidence |
|---------|-----------------|
| `bump_agent_versions.py` hardcoding | `scripts/bump_agent_versions.py:10-42` |
| Raw stem without normalization | `src/claude_mpm/services/agent_capabilities_service.py:224` |
| YAML inconsistency | `src/claude_mpm/config/agent_capabilities.yaml:222-259` |
| Exact string matching | `src/claude_mpm/hooks/claude_hooks/tool_analysis.py:84-86` |
| Hardcoded agent type list | `src/claude_mpm/hooks/claude_hooks/services/subagent_processor.py:351-352` |
| Normalizer handles hyphens | `src/claude_mpm/core/agent_name_normalizer.py:283` |
| Normalizer NOT universally applied | `src/claude_mpm/services/agent_capabilities_service.py:224` (no normalizer call) |
| Deployed files mixed naming | `.claude/agents/` (golang_engineer.md vs python-engineer.md) |
| Rename script exists | `scripts/rename_templates_to_dashes.sh` |
| Pre-existing mixed naming | `scripts/bump_agent_versions.py:11-42` (hyphens mixed with underscores) |
