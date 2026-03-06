# Devil's Advocate Analysis: Filename Standardization Plan
## Analysis Date: 2026-03-04
## Branch: agenttype-enums

---

## Executive Summary

The plan is partially correct but significantly underestimates scope. It identifies 4 code locations but misses at least 2 additional deployment paths. The plan focuses exclusively on underscore-to-hyphen conversion but ignores a second naming problem already present in the codebase: `-agent` suffix stripping. This creates **5 filename collision pairs** that the plan provides zero guidance on resolving. Additionally, a foundational assumption about `agent_id` frontmatter is incorrect: renaming files will NOT update existing `agent_id:` fields, creating a permanent mismatch between filenames and internal IDs.

---

## Claim-by-Claim Verification

### Claim 1: "Agent files have inconsistent naming - some underscore, some hyphen in .claude/agents/"

**Verdict: TRUE, but scope is larger than stated**

The plan correctly identifies the inconsistency. Actual count in `.claude/agents/`:
- 14 underscore-named files (e.g., `dart_engineer.md`, `ruby_engineer.md`)
- 15 hyphen-named files ending in `-agent` (e.g., `api-qa-agent.md`, `research-agent.md`)

The plan presents this as purely an underscore problem. In reality there are two separate naming problems:
1. Underscore vs hyphen separators
2. Files with `-agent` suffix that `normalize_deployment_filename()` strips

The plan acknowledges neither the `-agent` stripping behavior nor that it affects 15 additional files.

---

### Claim 2: "Remote cache uses hyphens consistently"

**Verdict: UNVERIFIABLE from this codebase**

The `~/.claude-mpm/cache/agents/` directory was inaccessible during analysis (returned no output). The plan cannot be verified on this point. What the code reveals is that the cache is populated from git repositories, and the `_resolve_cache_path()` method in `git_source_sync_service.py` handles both flat and nested structures - suggesting real-world inconsistency may exist there as well.

---

### Claim 3: "`normalize_deployment_filename()` and `deploy_agent_file()` exist in `deployment_utils.py`"

**Verdict: TRUE**

Both functions exist and are correctly described. Additionally verified:
- `get_underscore_variant_filename()` exists (also mentioned in plan)
- `ensure_agent_id_in_frontmatter()` exists (not mentioned in plan, but relevant)
- `validate_agent_file()` and `ValidationResult`/`DeploymentResult` dataclasses exist

The module is well-structured and the docstring even states it is the "SINGLE SOURCE OF TRUTH for agent file deployment."

---

### Claim 4: "Legacy deployment paths bypass them using raw `template_file.stem`"

**Verdict: TRUE for 3 of 4 claimed paths, STALE for the 5th path (which the plan misses)**

Verified raw `template_file.stem` usage:

1. `single_agent_deployer.py` line 68: `agent_name = template_file.stem` - CONFIRMED
2. `single_agent_deployer.py` line 217: `target_file = target_dir / f"{agent_name}.md"` - CONFIRMED (the `agent_name` parameter is used directly, not normalized)
3. `async_agent_deployment.py` line 481-482: `agent_name = agent.get("_agent_name", "unknown")` then `target_file = agents_dir / f"{agent_name}.md"` - CONFIRMED
4. `local_template_deployment.py` line 113: `target_file = self.target_dir / f"{template.agent_id}.md"` - CONFIRMED

**MISSED PATH 5: `agent_deployment_context.py` line 73-74:**
```python
agent_name = template_file.stem
target_file = agents_dir / f"{agent_name}.md"
```
The `AgentDeploymentContext.from_template_file()` factory method does the same raw stem extraction. This is called by `AgentProcessingStep` (the pipeline system), making it a 5th unaddressed deployment path.

**MISSED PATH 6: `agent_deployment.py` line 478:**
```python
agent_name = template_file_path.stem
```
The main `AgentDeploymentService.deploy_agents()` orchestrator also uses raw stem without normalization before passing to `single_agent_deployer.deploy_single_agent()`.

**MISSED PATH 7: `agent_management_service.py` line 97:**
```python
file_path = target_dir / f"{name}.md"
```
The management service's `create_agent()` method writes files using raw `name` parameter without normalization. This path is invoked by user-facing commands to create agents.

---

### Claim 5: "4 specific code locations need fixing"

**Verdict: PARTIALLY TRUE - line numbers are accurate, but count is wrong**

Verified line numbers:
- `single_agent_deployer.py` ~line 68: ACCURATE (actual line 68-69)
- `single_agent_deployer.py` ~line 217: ACCURATE (actual line 217)
- `async_agent_deployment.py` ~line 482: ACCURATE (actual line 481-482)
- `local_template_deployment.py` ~line 113: ACCURATE (actual line 113)

However, the plan's claim of exactly 4 locations is wrong. At minimum 3 additional paths require attention (see Claim 4 above).

---

### Claim 6: "~15 underscore-named files currently exist in .claude/agents/"

**Verdict: FALSE - count is 14 underscore files, but total affected files is 29**

Actual underscore files: **14**, not ~15.

But the critical omission: normalization also strips `-agent` suffixes. A full normalization run on the current `.claude/agents/` directory would affect **29 files total** (14 underscore + 15 `-agent` suffix files).

---

### Claim 7: "Existing tests cover normalization logic"

**Verdict: TRUE - but tests do not cover the `agent_id` frontmatter mismatch problem**

`tests/services/agents/test_deployment_utils.py` provides comprehensive coverage of:
- `normalize_deployment_filename()`
- `get_underscore_variant_filename()`
- `ensure_agent_id_in_frontmatter()`
- `validate_agent_file()`
- `deploy_agent_file()`

However, the tests do NOT cover the scenario where a file already has an underscore-format `agent_id:` in frontmatter and gets renamed to a hyphen filename. The `ensure_agent_id_in_frontmatter()` function explicitly skips files that already have `agent_id:`, leaving a permanent inconsistency. This is an untested failure mode.

---

### Claim 8: "`get_underscore_variant_filename` exists in deployment_utils.py"

**Verdict: TRUE**

Function exists at line 135-161 of `deployment_utils.py`. Correctly described.

---

## Gaps the Plan Does Not Address

### Gap 1: The `-agent` Suffix Stripping Problem (CRITICAL)

`normalize_deployment_filename()` strips the `-agent` suffix. This means applying the plan will rename **15 additional files**. Five of these collide with already-existing files:

| Source file | Would become | Conflict? |
|-------------|-------------|-----------|
| `documentation-agent.md` | `documentation.md` | YES - file exists |
| `ops-agent.md` | `ops.md` | YES - file exists |
| `qa-agent.md` | `qa.md` | YES - file exists |
| `research-agent.md` | `research.md` | YES - file exists |
| `web-qa-agent.md` | `web-qa.md` | YES - file exists |

The plan has no strategy for resolving these conflicts. Naive application would silently overwrite one file with another.

### Gap 2: Frontmatter `agent_id` Mismatch After Rename (CRITICAL)

The current underscore-named files have `agent_id:` in their YAML frontmatter that matches their filenames:
- `dart_engineer.md` contains `agent_id: dart_engineer`
- `ruby_engineer.md` contains `agent_id: ruby_engineer`

The plan proposes renaming these files to hyphen format. However, `deploy_agent_file()` calls `ensure_agent_id_in_frontmatter()`, which explicitly skips files that already contain an `agent_id:` field. After the rename:
- File: `ruby-engineer.md`
- Internal `agent_id`: still `ruby_engineer` (underscore)

This creates a permanent disconnect between the filename convention and the internal ID. Code that reads agent_id from frontmatter (e.g., `agent_registry.py` discovers agents and normalizes from filename stem) may behave inconsistently versus code that reads the frontmatter `agent_id` directly.

The plan mentions "Verify the `name:` frontmatter field inside deployed files matches the filename convention" but this is the wrong field to check. The `agent_id:` field is what matters for lookup and it is NOT automatically updated.

### Gap 3: `AgentNameNormalizer` Uses Underscore Keys as Canonical

`agent_name_normalizer.py` has hardcoded underscore-based lookup tables:
- `CANONICAL_NAMES` keys: `"ruby_engineer"`, `"dart_engineer"`, etc.
- `ALIASES` maps both underscore and hyphen variants TO underscore canonical keys

If the deployed files change to hyphen names but `AgentNameNormalizer` still uses underscores as canonical keys, lookups that go through the normalizer may produce different results than lookups that go through `agent_registry.py`'s `normalize_agent_id()` (which uses hyphens as canonical).

These two normalization systems are in direct conflict and the plan addresses neither.

### Gap 4: The Pipeline Deployment Path (5th Unaddressed Location)

`AgentDeploymentContext.from_template_file()` in `agent_deployment_context.py` creates target paths using raw `template_file.stem`. This is used by `AgentProcessingStep` in the deployment pipeline system. The plan does not list this file as requiring changes.

### Gap 5: No Migration Strategy for Existing Users

Users who have run `claude-mpm agents deploy` already have underscore-named files deployed to their `.claude/agents/` directories. The plan's Step 6 ("rename existing underscore files") addresses only the project repository's own `.claude/agents/`. It provides no strategy for:
- Users with existing deployments in their home directories
- Projects that reference agents by their underscore names
- Smooth transition without breaking Claude Code's ability to find agents during the rename

### Gap 6: `_agent_name` Value in Async Path Is Already Underscore

In `async_agent_deployment.py` line 264:
```python
data["_agent_name"] = file_path.stem
```
The `_agent_name` is set from `file_path.stem` when loading JSON files from the cache. If the cache contains files with underscore names, normalizing at deployment time fixes the output file but the `_agent_name` field throughout the async pipeline remains underscore. This affects results tracking and logging, and may affect deduplication logic.

### Gap 7: Race Condition During Cleanup

The `deploy_agent_file()` function does: delete underscore variant, then write hyphen version. If interrupted between these steps, both files are gone. For long-running deployments with many agents, this window exists for each agent.

---

## Recommended Plan Adjustments

1. **Add `AgentDeploymentContext.from_template_file()` to the fix list** - this is the 5th deployment path.

2. **Add explicit frontmatter `agent_id` update logic** - `ensure_agent_id_in_frontmatter()` must be extended to optionally UPDATE an existing `agent_id:` to match the normalized filename, not just skip it when present.

3. **Resolve the 5 filename collision pairs before normalizing** - decide which version of `documentation.md` vs `documentation-agent.md` wins, then remove the loser before running normalization.

4. **Reconcile `AgentNameNormalizer` with `agent_registry.py`** - both normalize agent names but use different canonical forms (underscore vs hyphen). Pick one standard and update both.

5. **Expand scope count** - the plan says "~15 files", the actual count needing changes is 29 files in `.claude/agents/` alone.

6. **Add user migration guidance** - provide a command or script for existing users to migrate their deployed agent directories.
