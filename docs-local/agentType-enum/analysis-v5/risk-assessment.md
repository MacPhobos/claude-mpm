# Risk Assessment: Filename Standardization Plan
## Analysis Date: 2026-03-04
## Branch: agenttype-enums

---

## Risk Summary Table

| Risk | Severity | Likelihood | Blocking? |
|------|----------|------------|-----------|
| R1: Filename collision during -agent suffix stripping | CRITICAL | CERTAIN (5 pairs exist) | YES |
| R2: Frontmatter agent_id mismatch after rename | HIGH | CERTAIN (design gap) | NO, but latent bug |
| R3: Pipeline path re-creates underscore files | HIGH | HIGH | YES (regresses fix) |
| R4: Two conflicting normalization systems | HIGH | CERTAIN | NO, but correctness issue |
| R5: Async path _agent_name stays as underscore | MEDIUM | HIGH | NO |
| R6: Race condition during cleanup | LOW | LOW | NO |
| R7: No user migration strategy | MEDIUM | CERTAIN | NO |
| R8: Management service creates non-normalized files | MEDIUM | MEDIUM | NO |

---

## R1: Filename Collision During -agent Suffix Stripping (CRITICAL / BLOCKING)

### What the risk is

`normalize_deployment_filename()` strips both underscore separators AND the `-agent` suffix from filenames. The plan is aware of underscore stripping but does not mention `-agent` stripping at all. There are currently 15 files in `.claude/agents/` with `-agent` suffixes. When these are processed by `deploy_agent_file()`, five will collide with already-existing base-name files.

### The 5 collision pairs (as of branch `agenttype-enums`)

```
documentation-agent.md  normalizes to  documentation.md   CONFLICT: documentation.md already exists
ops-agent.md            normalizes to  ops.md             CONFLICT: ops.md already exists
qa-agent.md             normalizes to  qa.md              CONFLICT: qa.md already exists
research-agent.md       normalizes to  research.md        CONFLICT: research.md already exists
web-qa-agent.md         normalizes to  web-qa.md          CONFLICT: web-qa.md already exists
```

### What happens without mitigation

`deploy_agent_file()` has a `force` parameter. When `force=False` (default), it checks if the target file already exists before writing. However, the existing base file (e.g., `documentation.md`) is the product of a different agent source than `documentation-agent.md`. The two files have different content. Silently skipping the deploy means the `-agent` source agent never gets written. Silently overwriting means the base agent content is lost.

Neither behavior is correct. There is no current mechanism to merge two different agents that normalize to the same filename.

### Resolution required before plan execution

For each of the 5 collision pairs, a human decision is required:

1. Which of the two files is the "correct" agent for this role?
2. Should the other be deleted, renamed with a distinguishing qualifier, or merged?

No tooling in the current codebase makes this decision or surfaces it to the operator. The plan must explicitly address each collision pair before any batch normalization is run.

### Files affected

- `.claude/agents/documentation-agent.md` vs `.claude/agents/documentation.md`
- `.claude/agents/ops-agent.md` vs `.claude/agents/ops.md`
- `.claude/agents/qa-agent.md` vs `.claude/agents/qa.md`
- `.claude/agents/research-agent.md` vs `.claude/agents/research.md`
- `.claude/agents/web-qa-agent.md` vs `.claude/agents/web-qa.md`

---

## R2: Frontmatter `agent_id` Mismatch After Rename (HIGH / LATENT BUG)

### What the risk is

The 14 underscore-named files in `.claude/agents/` each contain a YAML frontmatter block where `agent_id:` matches the filename stem. After the plan renames these files to hyphen format, the `agent_id:` value in the frontmatter will remain as an underscore form, creating a permanent inconsistency.

### Root cause in code

`ensure_agent_id_in_frontmatter()` in `deployment_utils.py` explicitly returns content unchanged when `agent_id:` already exists:

```python
if isinstance(parsed, dict) and "agent_id" in parsed:
    return content  # Does NOT update existing agent_id
```

The function was designed to ADD a missing `agent_id:`, not to UPDATE an incorrect one. After the rename:

```
Filename:  ruby-engineer.md   (hyphen, normalized)
agent_id:  ruby_engineer      (underscore, NOT updated)
```

### Which code reads the frontmatter `agent_id` directly

- `DynamicAgentRegistry` in `agent_registry.py` discovers agents from the filesystem. Its `_discover_agents_from_directory()` method reads files and their frontmatter. The `agent_id:` from frontmatter is used as the lookup key when the registry resolves agent requests.
- `agent_management_service.py` reads and writes frontmatter directly when updating agents.

If `agent_registry.py` reads `agent_id: ruby_engineer` from the renamed `ruby-engineer.md` file, and then a caller requests `ruby-engineer` (the hyphen form), the lookup may fail depending on whether the registry normalizes before comparing.

### Why this is not immediately catastrophic

`agent_registry.py`'s `normalize_agent_id()` converts underscores to hyphens before lookup. So `ruby_engineer` would be normalized to `ruby-engineer` during resolution. This means the mismatch is currently masked by normalization. However:

1. The masking is not guaranteed. Not all code paths that read `agent_id:` go through `normalize_agent_id()`.
2. Debug output and logging will show inconsistent IDs (filename says `ruby-engineer`, field says `ruby_engineer`).
3. Any future code that does a direct string comparison without normalization will break.
4. The mismatch is invisible to operators inspecting files.

### Resolution required

`ensure_agent_id_in_frontmatter()` must be extended to accept a `normalize` or `update_existing` parameter that will overwrite the existing `agent_id:` when the caller provides a target value that differs from the stored value. The call in `deploy_agent_file()` must pass the normalized stem as the target `agent_id:`.

A new test covering this scenario must be added to `test_deployment_utils.py`:
- Input: file with `agent_id: ruby_engineer` in frontmatter
- Deployed as: `ruby-engineer.md`
- Expected output: frontmatter contains `agent_id: ruby-engineer`

---

## R3: Pipeline Path Will Re-Create Underscore Files (HIGH / REGRESSION RISK)

### What the risk is

Even if all 4 code locations the plan identifies are fixed, the pipeline deployment path (`AgentProcessingStep` -> `AgentDeploymentContext.from_template_file()`) will continue to write underscore-named files. This path is not in the plan's "Files to Modify" list. The result is a regression: files normalized by the fixed paths will be overwritten with underscore versions the next time the pipeline runs.

### The two missed classes

**`agent_deployment_context.py` - `from_template_file()` method:**
```python
agent_name = template_file.stem  # RAW STEM, no normalization
target_file = agents_dir / f"{agent_name}.md"
```
This method constructs `AgentDeploymentContext` objects that encode the target path at creation time. The raw stem is stored in `self.agent_name` and `self.target_file`. All downstream pipeline steps use these pre-computed paths.

**`agent_processing_step.py` - `process()` method:**
```python
for template_file in context.template_files:
    agent_name = template_file.stem  # Also RAW STEM
    agent_context = AgentDeploymentContext.from_template_file(...)
```
The step reads raw stem before even calling `from_template_file()`. Both the step and the factory need to be updated.

### When this pipeline runs

The pipeline system runs during deployment operations that go through `AgentDeploymentService`. If a user runs `claude-mpm agents deploy` and the implementation routes through the pipeline path, underscore files will be re-created even after normalization.

### Resolution required

Two files require changes that the plan does not list:

1. `src/claude_mpm/services/agents/deployment/processors/agent_deployment_context.py`
   - `from_template_file()` must normalize `template_file.stem` before using it as `agent_name`
   - Must call `normalize_deployment_filename(template_file.name)` and use that stem

2. `src/claude_mpm/services/agents/deployment/pipeline/steps/agent_processing_step.py`
   - The raw stem extraction at line 54 must be removed or normalized before calling `from_template_file()`

---

## R4: Two Conflicting Normalization Systems (HIGH / CORRECTNESS RISK)

### What the risk is

There are two separate modules in the codebase that normalize agent names, and they produce opposite canonical forms:

| Module | Method | Canonical form |
|--------|--------|----------------|
| `agent_name_normalizer.py` | `AgentNameNormalizer.normalize()` | underscore (e.g., `ruby_engineer`) |
| `agent_registry.py` | `DynamicAgentRegistry.normalize_agent_id()` | hyphen (e.g., `ruby-engineer`) |

The file-based convention is moving to hyphens (per the plan). `agent_registry.py` is aligned with this. But `agent_name_normalizer.py` moves in the opposite direction.

### Specific evidence of conflict

`agent_name_normalizer.py`:
```python
CANONICAL_NAMES = {
    "ruby_engineer": "Ruby Engineer",   # underscore key
    "dart_engineer": "Dart Engineer",   # underscore key
}
ALIASES = {
    "ruby-engineer": "ruby_engineer",   # dash alias maps TO underscore canonical
}
def normalize(cls, agent_name: str) -> str:
    cleaned = cleaned.replace("-", "_")  # converts hyphens to underscores
```

`agent_registry.py`:
```python
def normalize_agent_id(self, agent_id: str) -> str:
    normalized = normalized.replace("_", "-")  # converts underscores to hyphens
AGENT_ALIASES = {
    "product_owner": "product-owner",   # underscore maps to hyphen canonical
}
```

### Impact

Any code that calls `AgentNameNormalizer.normalize("ruby-engineer")` gets back `ruby_engineer`. Any code that calls `DynamicAgentRegistry.normalize_agent_id("ruby_engineer")` gets back `ruby-engineer`. If both results are used in the same system (e.g., for cache key generation, routing, or lookup), they will miss each other.

The plan's filename normalization aligns `.claude/agents/` files with the hyphen form. If `agent_name_normalizer.py` is not updated, every lookup through the normalizer will produce IDs that no longer match filenames.

### Resolution required

Choose one canonical form (hyphens, per the direction of `deploy_agent_file()` and `agent_registry.py`). Update `agent_name_normalizer.py`:
- Change all `CANONICAL_NAMES` keys from underscore to hyphen
- Change `ALIASES` target values from underscore to hyphen
- Change `normalize()` to convert underscores to hyphens instead of vice versa
- Update all callers that depend on the underscore canonical form

---

## R5: Async Path `_agent_name` Stays as Underscore (MEDIUM)

### What the risk is

In `async_agent_deployment.py`, agent data is loaded from JSON files in the cache. The `_agent_name` metadata field is set from the raw filename stem at load time:

```python
data["_agent_name"] = file_path.stem   # line 264, underscore if cache has underscore files
```

Later, when writing the deployed file, the current raw usage is:

```python
agent_name = agent.get("_agent_name", "unknown")
target_file = agents_dir / f"{agent_name}.md"   # underscore if _agent_name is underscore
```

If the plan fixes the second location (the target_file construction), it must also update `_agent_name` when loading - or normalize at the point of use. If only the target_file line is fixed by calling `normalize_deployment_filename()` on `_agent_name`, the tracking and logging throughout the async pipeline will still show underscore IDs. This is not a deployment failure but creates confusion during debugging.

### Impact scope

- Log entries will show mismatched IDs (logged as `ruby_engineer`, deployed as `ruby-engineer.md`)
- Deduplication logic in the async pipeline may use `_agent_name` as a key; if it does, underscore and hyphen versions of the same agent will not deduplicate

### Resolution required

When loading agent data from the cache JSON files, normalize `_agent_name` at line 264:
```python
# Current:
data["_agent_name"] = file_path.stem
# Fixed:
data["_agent_name"] = normalize_deployment_filename(file_path.name).replace(".md", "")
```

---

## R6: Race Condition During Legacy Cleanup (LOW)

### What the risk is

`deploy_agent_file()` performs a delete-then-write sequence:

1. Delete underscore variant (e.g., `ruby_engineer.md`)
2. Write hyphen version (e.g., `ruby-engineer.md`)

If the process is interrupted (SIGKILL, disk full, power loss) between steps 1 and 2, both files are absent. Claude Code can no longer find the agent.

### Severity assessment

Low severity because:
- The operation is fast (file delete + write, sub-millisecond on local disk)
- The source template file is unaffected; a re-run recovers the agent
- This is a standard file-replace problem, not a data loss scenario

### If mitigation is desired

Write-then-rename pattern: write to a temporary file, then `os.rename()` (atomic on POSIX), then delete the old file. This is a hardening concern, not a blocking issue for the plan.

---

## R7: No User Migration Strategy (MEDIUM)

### What the risk is

The plan's Step 6 addresses renaming files in the project repository's own `.claude/agents/` directory. It does not address users who have already deployed agents to their own systems.

Any user who has run `claude-mpm agents deploy` before this change has underscore-named files in their project or home `~/.claude/agents/` directories. After upgrading to the version that implements this plan:

- New deployments will produce hyphen-named files
- Old underscore files remain unless manually cleaned
- Both `ruby_engineer.md` and `ruby-engineer.md` may coexist
- Claude Code may load either, depending on filesystem ordering

### Who is affected

- All users with existing deployments (any prior release)
- Projects with agents referenced by underscore names in prompts or configuration

### Resolution required

A migration command or automatic migration on next deploy. Options:

1. **Automatic on next deploy:** When `deploy_agent_file()` runs, it already calls `get_underscore_variant_filename()` and deletes the underscore variant if found. This handles the case where re-deploying a hyphen source will clean up the old underscore file. BUT: it only works if the source agent is re-deployed. Agents not present in the current source set will not be cleaned up.

2. **Explicit migration command:** Add a `claude-mpm agents migrate` or `claude-mpm agents normalize` subcommand that scans `.claude/agents/` and renames underscore files to hyphen in place (updating frontmatter `agent_id:` at the same time).

3. **Post-install hook:** Run normalization automatically on package installation or first run after upgrade.

Option 2 is recommended for transparency and operator control.

---

## R8: Management Service Creates Non-Normalized Files (MEDIUM)

### What the risk is

`agent_management_service.py` line 97 writes agent files using raw `name` parameters:

```python
file_path = target_dir / f"{name}.md"
file_path.write_text(content, encoding="utf-8")
```

The `create_agent()` method is invoked by user-facing commands to create new agents. If a user provides a name with underscores (e.g., `new_feature`), the file will be created as `new_feature.md` regardless of the normalization plan.

### Compounding risk

Unlike the deployment paths that process existing template files, the management service creates new files that have no prior normalized form. The file written by the management service will not be picked up by any legacy-cleanup mechanism, because `get_underscore_variant_filename()` is only called from `deploy_agent_file()`, and this path bypasses `deploy_agent_file()` entirely.

### Resolution required

`agent_management_service.py` `create_agent()` must normalize the `name` parameter before constructing `file_path`:

```python
from claude_mpm.services.agents.deployment_utils import normalize_deployment_filename
normalized_name = normalize_deployment_filename(f"{name}.md").replace(".md", "")
file_path = target_dir / f"{normalized_name}.md"
```

And the `agent_id:` in the frontmatter being written must be set to `normalized_name` at creation time.

---

## Cumulative Scope Impact

### Total files affected by a complete normalization run

| Category | Count | Plan says |
|----------|-------|-----------|
| Underscore-named files in `.claude/agents/` | 14 | "~15" |
| `-agent` suffix files in `.claude/agents/` | 15 | Not mentioned |
| **Total `.claude/agents/` files needing rename** | **29** | **"~15"** |
| Collisions requiring manual resolution | 5 | 0 |
| Files with frontmatter `agent_id` mismatch after rename | 14 | 0 |

### Total code locations requiring changes

| File | Status in plan |
|------|----------------|
| `single_agent_deployer.py` (line 68) | Listed |
| `single_agent_deployer.py` (line 217) | Listed |
| `async_agent_deployment.py` (line 481) | Listed |
| `local_template_deployment.py` (line 113) | Listed |
| `agent_deployment_context.py` (line 73) | **Not listed** |
| `agent_processing_step.py` (line 54) | **Not listed** |
| `agent_deployment.py` (line 478) | **Not listed** |
| `agent_management_service.py` (line 97) | **Not listed** |
| `deployment_utils.py` ensure_agent_id_in_frontmatter | **Not listed** |
| `agent_name_normalizer.py` CANONICAL_NAMES and normalize() | **Not listed** |

The plan identifies 4 of the 10 code locations that require changes.

---

## Pre-Execution Checklist

Before running the filename standardization plan, the following must be completed:

1. [ ] Resolve the 5 collision pairs manually (choose winner for each)
2. [ ] Extend `ensure_agent_id_in_frontmatter()` to update existing `agent_id:` values
3. [ ] Add `agent_deployment_context.py` to the files-to-modify list
4. [ ] Add `agent_processing_step.py` to the files-to-modify list
5. [ ] Add `agent_deployment.py` to the files-to-modify list
6. [ ] Add `agent_management_service.py` to the files-to-modify list
7. [ ] Reconcile `agent_name_normalizer.py` with `agent_registry.py` (pick one canonical form)
8. [ ] Write test: underscore frontmatter agent_id updated after rename to hyphen filename
9. [ ] Write or document user migration strategy for existing deployments
10. [ ] Update plan's file count from "~15" to "29" (or resolve -agent suffix files separately)
