# Devil's Advocate: Risk Analysis for Archive Removal

**Date**: 2026-03-03
**Task**: Challenge the plan to remove `src/claude_mpm/agents/templates/archive/` and switch entirely to git-cached agents.
**Verdict**: **HIGH RISK - DO NOT PROCEED WITHOUT MITIGATIONS**

---

## Executive Summary

The plan to remove `archive/` has **multiple critical risks** that could break the product for new users, offline users, and destroy metadata that is actively consumed by runtime code. The archive is NOT dead code. This analysis identifies **7 critical risks**, **5 high risks**, and **8 moderate risks**.

---

## Risk Matrix

| # | Risk | Likelihood | Impact | Severity | Category |
|---|------|-----------|--------|----------|----------|
| R1 | Memory routing data loss | **CERTAIN** | **CRITICAL** | **P0** | Data Loss |
| R2 | First-run offline failure | **HIGH** | **CRITICAL** | **P0** | First-Run |
| R3 | Packaged template resolution breaks | **CERTAIN** | **HIGH** | **P0** | Distribution |
| R4 | `delegation_matrix_poc.py` breaks | **CERTAIN** | **MEDIUM** | **P1** | Tooling |
| R5 | Validation handoff_agents checks fail | **HIGH** | **MEDIUM** | **P1** | Runtime |
| R6 | Cache structure mismatch | **CERTAIN** | **HIGH** | **P0** | Architecture |
| R7 | `pyproject.toml` package-data stale refs | **HIGH** | **MEDIUM** | **P1** | Distribution |
| R8 | `.secrets.baseline` stale refs | **MEDIUM** | **LOW** | **P2** | Security |
| R9 | Enterprise/air-gapped deployment fails | **MEDIUM** | **HIGH** | **P1** | Offline |
| R10 | Agent count mismatch (39 archive vs 53+ cache) | **HIGH** | **MEDIUM** | **P1** | Compatibility |
| R11 | Major version bump required | **HIGH** | **MEDIUM** | **P1** | Semver |
| R12 | Partial cache sync race condition | **MEDIUM** | **MEDIUM** | **P2** | Edge Case |
| R13 | GitHub repo structure changes | **LOW** | **HIGH** | **P2** | External Dep |
| R14 | Multiple users sharing cache | **LOW** | **MEDIUM** | **P3** | Edge Case |
| R15 | Test suite impact | **LOW** | **LOW** | **P3** | Testing |
| R16 | Documentation staleness | **MEDIUM** | **LOW** | **P3** | Docs |
| R17 | Skill manager template scanning | **MEDIUM** | **MEDIUM** | **P2** | Runtime |
| R18 | Agent state manager template listing | **MEDIUM** | **MEDIUM** | **P2** | CLI |
| R19 | Native agent converter JSON scanning | **MEDIUM** | **LOW** | **P3** | Tooling |
| R20 | Cache nested structure vs flat archive | **CERTAIN** | **HIGH** | **P0** | Architecture |

---

## P0 Critical Risks (Must Fix Before Proceeding)

### R1: Memory Routing Data Loss - CERTAIN / CRITICAL

**The archive JSON files contain `memory_routing` data that is ACTIVELY READ by production code.**

The `TemplateProcessor` (`src/claude_mpm/core/framework/processors/template_processor.py:66`) loads JSON templates from `claude_mpm.agents.templates` package path:

```python
templates_package = files("claude_mpm.agents.templates")
template_file = templates_package / f"{agent_name}.json"  # Looks for JSON!
```

This resolves to `src/claude_mpm/agents/templates/` - the directory that CONTAINS `archive/`. But critically, it looks for `{agent_name}.json` at the templates root level, NOT in archive/. Since archive JSON files are in a subdirectory, this code would NOT find them.

**HOWEVER**, the `memory_routing` data is consumed by:

1. **`src/claude_mpm/services/memory/router.py:506-536`** - Loads memory routing from templates and builds dynamic keyword patterns for memory classification. This directly affects how agent memories are routed.

2. **`src/claude_mpm/core/framework/formatters/capability_generator.py:275-335`** - `load_memory_routing_from_template()` searches for JSON templates in the templates directory and its alternatives. In dev mode, it searches `templates_dir / f"{agent_name}.json"`.

3. **`src/claude_mpm/core/framework/loaders/agent_loader.py:178-179`** - Loads `memory_routing` from template data into agent data.

**Key finding**: The runtime code searches for `.json` files at `templates/*.json`, NOT `templates/archive/*.json`. The archive README itself notes: "SkillManager (path bug: scans `templates/*.json`, not `templates/archive/*.json`)". This means the memory_routing data exists in archive but may NOT be actively consumed today due to this path bug.

**Risk**: If someone fixes the path bug (or if code accesses archive data through package traversal), removing archive would break memory routing. The data exists ONLY in archive JSONs - 30+ agents have rich `memory_routing` with keywords, categories, and routing descriptions.

**Evidence**: `src/claude_mpm/agents/templates/archive/engineer.json:139-165` contains:
```json
"memory_routing": {
  "description": "Stores implementation patterns...",
  "categories": ["Implementation patterns...", "Code architecture..."],
  "keywords": ["implementation", "code", "programming", ...]
}
```

**Mitigation**: Extract all `memory_routing` data from archive JSONs BEFORE deletion. Either embed in cache markdown YAML frontmatter or create a standalone `memory_routing_registry.json`.

---

### R3: Packaged Template Resolution Breaks - CERTAIN / HIGH

The `pyproject.toml` package-data specification at line 319:

```toml
claude_mpm = ["agents/templates/*.json", "agents/templates/*.md", ...]
```

This glob pattern `agents/templates/*.json` does NOT match `agents/templates/archive/*.json`. The archive JSONs are NOT included in pip-installed packages today.

**Implication**: For pip/Homebrew/npm installations, archive JSON files are ALREADY not shipped. This means:
1. Removing archive changes nothing for pip users (they never had it)
2. BUT this proves the `TemplateProcessor` code that loads from `files("claude_mpm.agents.templates")` was NEVER finding these JSONs in production
3. The memory routing code path is currently broken/silent for packaged installs

**Risk Requalification**: R1 memory_routing is already broken for packaged users, but archive removal would break it permanently for DEVELOPMENT MODE users (who run from source).

---

### R6: Cache Structure Mismatch - CERTAIN / HIGH

**The cache is NOT a flat directory of markdown files.** The actual cache structure is:

```
~/.claude-mpm/cache/agents/
  bobmatnyc/
    claude-mpm-agents/
      agents/
        BASE-AGENT.md
        claude-mpm/
          BASE-AGENT.md
          mpm-agent-manager.md
          mpm-skills-manager.md
        documentation/
          documentation.md
          ticketing.md
        engineer/
          BASE-AGENT.md
          backend/
            golang-engineer.md
            java-engineer.md
            python-engineer.md
            ...
          frontend/
            ...
          specialized/
            ...
        ops/
          ...
        qa/
          ...
```

This is a DEEPLY NESTED directory structure organized by category, NOT a flat list matching archive filenames. The archive has flat filenames like `engineer.json`, `qa.json`, `research.json`. The cache has paths like `engineer/backend/python-engineer.md`.

**Risk**: Code that expects `cache_dir / f"{agent_name}.md"` (flat lookup) will NOT find agents in the nested cache structure. The `single_agent_deployer.py:346-353` does `cache_root.rglob(f"{agent_name}.md")` which handles this with recursive glob, but other code paths may assume flat structure.

**The agent naming conventions also differ**: Archive has `python_engineer.json` (underscore), cache has `python-engineer.md` (hyphen). Archive has `qa.json`, cache has agents under `qa/` subdirectory.

---

### R20: Cache Nested Structure vs Flat Archive - CERTAIN / HIGH

**This is the architectural incompatibility that makes a direct swap impossible.**

Archive: 39 flat JSON files with rich structured metadata (memory_routing, interactions, testing, dependencies, etc.)
Cache: 53+ markdown files in a hierarchical directory tree with YAML frontmatter (different schema, different naming, different structure)

These are fundamentally different data formats serving different purposes:
- Archive JSON: Rich metadata store (machine-readable, structured fields)
- Cache Markdown: Deployment artifacts (human-readable, minimal frontmatter)

You cannot simply "switch from archive to cache" because they are not interchangeable.

---

### R2: First-Run Offline Failure - HIGH / CRITICAL

**Scenario**: New user installs `pip install claude-mpm`, is behind a firewall, runs `claude-mpm configure`.

**Current behavior**: Archive doesn't help either (not included in pip package). Cache is empty. Git sync fails due to no internet. BUT there are hardcoded fallback agents.

**What happens**:
1. `git_source_sync_service.py:758-771` has a hardcoded fallback list of 11 agent filenames
2. But this list only provides filenames for HTTP download - if HTTP also fails, cache stays empty
3. `deployment_reconciler.py:128-131` reports: "Agent '{id}' not found in cache. Run 'claude-mpm agents sync' first."
4. User gets errors, no agents deployed

**Risk**: If archive were to be the safety net for first-run offline, removing it would eliminate that possibility. Currently archive is NOT used as a fallback, but it COULD be added as one. Removing it closes that door permanently.

**Mitigation**: Before removing archive, ensure robust offline fallback. Options:
- Bundle a minimal set of agent markdown files in the pip package
- Ship a "seed cache" with the package
- Include fallback agents directly in code as string constants

---

## P1 High Risks

### R4: `delegation_matrix_poc.py` Breaks - CERTAIN / MEDIUM

`scripts/delegation_matrix_poc.py:20` directly references:
```python
templates_dir = Path(__file__).parent.parent / "src/claude_mpm/agents/templates/archive"
```

This script loads all agent JSON templates to generate a delegation matrix. Removing archive breaks this entirely.

**Mitigation**: Update script to use cache or maintain a separate data source.

---

### R5: Validation handoff_agents Checks - HIGH / MEDIUM

`src/claude_mpm/validation/agent_validator.py:238` reads:
```python
handoff_agents = agent_data.get("interactions", {}).get("handoff_agents", [])
```

The `interactions.handoff_agents` field exists in archive JSONs (e.g., engineer.json:185-189 lists `["qa", "security", "documentation"]`). This validation code checks for self-referential handoffs.

**Risk**: If this validator is fed archive data (or data originally sourced from archive), removing archive removes the data source.

---

### R7: `pyproject.toml` Package-Data References - HIGH / MEDIUM

Line 319 includes: `"agents/templates/*.json"`. While this doesn't match archive subdirectory, removing archive could cause confusion or break tooling that expects the archive directory to exist.

Line 329: `norecursedirs = ["archive", ...]` in pytest config - this won't cause errors but becomes a stale reference.

---

### R9: Enterprise/Air-Gapped Deployment - MEDIUM / HIGH

Enterprise customers behind firewalls cannot reach GitHub. Currently they have no guaranteed offline agent source (archive isn't shipped in pip). If the plan is to make cache the ONLY source, enterprise offline deployment becomes permanently impossible without a workaround.

**Mitigation**: Document an enterprise deployment guide that includes pre-populating the cache directory from a local/corporate mirror.

---

### R10: Agent Count Mismatch - HIGH / MEDIUM

Archive has **39 agents** (all flat JSON). Cache has **53+ agents** (nested markdown). These are NOT the same set:
- Archive has agents like `clerk-ops`, `imagemagick`, `prompt-engineer` that may not exist in cache
- Cache has agents like `nestjs-engineer`, `visual-basic-engineer`, `phoenix-engineer` that don't exist in archive
- Naming conventions differ: `dart_engineer` (archive) vs `dart-engineer` (cache)

**Risk**: Any code relying on "the set of all known agents" using archive as the source of truth will get a different (larger but differently-named) set from cache.

---

### R11: Semver - Removing Archive May Require Major Version Bump - HIGH / MEDIUM

If any user or tool depends on the existence of `archive/*.json` files (even transitively through the package), removing them is a BREAKING CHANGE per semver.

Evidence of external consumption:
- `scripts/delegation_matrix_poc.py` directly uses archive
- `.secrets.baseline` references archive files
- Documentation references archive paths

**Mitigation**: If archive removal proceeds, increment to a major version (e.g., 6.0.0).

---

## P2 Moderate Risks

### R8: `.secrets.baseline` Stale References - MEDIUM / LOW

`.secrets.baseline` references 4 archive files:
- `archive/local_ops_agent.json`
- `archive/ops.json`
- `archive/security.json`
- `archive/typescript_engineer.json`

Removing archive would make these entries stale but not break `detect-secrets`.

### R12: Partial Cache Sync Race Condition - MEDIUM / MEDIUM

`git_source_sync_service.py` syncs agents individually. If sync fails midway, cache has a partial set. Code deploying agents from cache will get inconsistent state.

Current mitigations:
- Individual failures don't stop sync (partial success allowed)
- ETag caching prevents re-downloading unchanged files
- BUT: no atomic "all or nothing" guarantee

### R13: GitHub Repo Structure Changes - LOW / HIGH

Cache agents come from `bobmatnyc/claude-mpm-agents` GitHub repo. If the repo reorganizes, renames, or goes private, all cache syncs fail. Unlike archive (which is versioned with the code), cache depends on an external service.

### R17: Skill Manager Template Scanning - MEDIUM / MEDIUM

`src/claude_mpm/skills/skill_manager.py:37`:
```python
for template_file in agent_templates_dir.glob("*.json"):
```

Scans templates directory for JSON files. Currently finds nothing at `templates/*.json` (bug noted in archive README). If archive JSONs were moved to root templates level to fix the bug, they would be found. Removing archive forecloses this fix.

### R18: Agent State Manager Template Listing - MEDIUM / MEDIUM

`src/claude_mpm/cli/commands/agent_state_manager.py:141`:
```python
for template_file in sorted(self.templates_dir.glob("*.json")):
```

Lists JSON templates for agent state management. Same root-level scanning issue.

### R19: Native Agent Converter - MEDIUM / LOW

`src/claude_mpm/services/native_agent_converter.py:284`:
```python
json_files = list(templates_dir.glob("*.json"))
```

Scans for JSON files to convert. Archive is the only source of JSON agent templates.

---

## P3 Low Risks

### R14: Multiple Users Sharing Cache - LOW / MEDIUM

Cache is at `~/.claude-mpm/cache/agents/`. Multiple users on a shared machine would have separate caches. If cache is at a system path instead, there could be permission/ownership conflicts.

### R15: Test Suite Impact - LOW / LOW

`pyproject.toml:329` excludes `archive` from pytest recursion. No test files directly import from archive. The test impact is minimal. `tests/services/test_archive_manager.py` tests the project archive manager, NOT the agent template archive.

### R16: Documentation Staleness - MEDIUM / LOW

Multiple docs reference archive:
- `docs/migration/JSON_TO_MARKDOWN_MIGRATION_SUMMARY.md`
- `docs/_archive/2025-12-implementation/` (multiple files)
- `src/claude_mpm/agents/templates/archive/README.md`

These would become stale but are mostly historical.

---

## Data Unique to Archive (Not in Cache)

The following structured fields exist ONLY in archive JSON files and have NO equivalent in cache markdown:

| Field | Present In | Used By Runtime Code? | Risk of Loss |
|-------|-----------|----------------------|-------------|
| `memory_routing` | 30+ agents | YES (router.py, capability_generator.py) | **CRITICAL** |
| `interactions.handoff_agents` | 25+ agents | YES (agent_validator.py) | **HIGH** |
| `interactions.input_format` | 25+ agents | Possibly (config_routes.py) | MEDIUM |
| `interactions.output_format` | 25+ agents | Possibly | MEDIUM |
| `testing.test_cases` | 30+ agents | No direct evidence | LOW |
| `testing.performance_benchmarks` | 30+ agents | No direct evidence | LOW |
| `dependencies.python` | 20+ agents | No direct evidence | LOW |
| `dependencies.system` | 20+ agents | No direct evidence | LOW |
| `knowledge.domain_expertise` | 35+ agents | No direct evidence | LOW |
| `knowledge.best_practices` | 35+ agents | No direct evidence | LOW |
| `capabilities.resource_tier` | 30+ agents | Possibly | MEDIUM |
| `capabilities.max_tokens` | 30+ agents | Possibly | MEDIUM |
| `capabilities.temperature` | 30+ agents | Possibly | MEDIUM |
| `template_changelog` | 39 agents | No direct evidence | LOW |
| `skills` array | 39 agents | skill_manager.py (but path bug) | MEDIUM |
| `benchmark_data` | Some agents | No direct evidence | LOW |
| `tool_use_patterns` | Some agents | No direct evidence | LOW |
| `health_checks` | Some agents (ops, vercel) | No direct evidence | LOW |
| `security` | Some agents | No direct evidence | LOW |
| `vercel_specific` | vercel agent | No direct evidence | LOW |

---

## Verdict

### DO NOT remove archive without these mandatory mitigations:

1. **Extract and preserve `memory_routing` data** - This is actively consumed by `router.py` and `capability_generator.py`. Create a standalone `memory_routing_registry.json` or embed in cache markdown frontmatter.

2. **Extract and preserve `interactions.handoff_agents`** - Used by `agent_validator.py`. Must be available somewhere.

3. **Solve the first-run offline problem** - Either bundle minimal agent markdown files in the pip package, or create an embedded fallback that doesn't require network access.

4. **Address the cache structure mismatch** - Cache is nested (`engineer/backend/python-engineer.md`), archive is flat (`python_engineer.json`). Any code that uses archive as source of truth must be updated to navigate the nested cache structure.

5. **Update all direct references** - `delegation_matrix_poc.py`, `.secrets.baseline`, documentation files.

6. **Determine semver impact** - If any external consumers depend on archive, this is a breaking change requiring a major version bump.

7. **Create an enterprise/offline deployment guide** - Document how to pre-populate cache for air-gapped environments.

### Recommended Approach:

**Phase 1 (Safe)**: Keep archive, fix the path bugs so runtime code actually reads from archive JSONs.

**Phase 2 (Migration)**: Embed critical structured data (memory_routing, interactions, skills) into cache markdown YAML frontmatter. Verify parity.

**Phase 3 (Deprecation)**: Mark archive as deprecated, add deprecation warnings if any code accesses it.

**Phase 4 (Removal)**: Remove archive in a MAJOR version bump after confirming:
- All memory_routing data is available from cache/markdown
- All interactions data is migrated
- Offline fallback exists
- All direct references updated
- Enterprise deployment documented

**Timeline**: This should be a multi-sprint effort, NOT a single PR.

---

## Appendix: Files That Reference Archive

### Direct Code References
- `scripts/delegation_matrix_poc.py:20` - Hard-coded archive path
- `.secrets.baseline:226-270` - 4 archive file entries

### Documentation References
- `docs/migration/JSON_TO_MARKDOWN_MIGRATION_SUMMARY.md:31`
- `docs/_archive/2025-12-implementation/json-template-documentation-audit-2025-12-23.md:16`
- `docs/_archive/2025-12-implementation/agent-deployment-warnings-analysis-2025-12-19.md:164`
- `docs/_archive/research-2025/skills-auto-linking-investigation-2025-12-29.md:34`
- `docs/_archive/research-2025/pm-instruction-gaps-investigation-2025-12-25.md:287,311`

### Configuration References
- `pyproject.toml:209` - `_archive` in ruff exclude
- `pyproject.toml:329` - `archive` in pytest norecursedirs
- `Makefile:919` - Reference to dashboard static archive

### Self-Referential
- `src/claude_mpm/agents/templates/archive/README.md` - Archive documentation

### Runtime Code That Loads JSON Templates (would break if JSONs were at templates root)
- `src/claude_mpm/core/framework/processors/template_processor.py:66` - `templates/*.json`
- `src/claude_mpm/core/framework/formatters/capability_generator.py:294-335` - `templates/*.json`
- `src/claude_mpm/skills/skill_manager.py:37` - `templates/*.json`
- `src/claude_mpm/cli/commands/agent_state_manager.py:141` - `templates/*.json`
- `src/claude_mpm/services/native_agent_converter.py:284` - `templates/*.json`
