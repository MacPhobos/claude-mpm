# Devil's Advocate Analysis v3: Challenging the Fresh-Start Approach

**Date**: 2026-03-06
**Branch**: `agenttype-enums` (15 commits ahead of `main`)
**Analyst**: Devil's Advocate (Research Agent)
**Mandate**: Challenge everything. Find what others missed. Be contrarian but evidence-based.
**Inputs**: 01-branch-history-analysis.md, 02-main-branch-baseline.md, 03-solution-architecture.md, prior v2 devil's advocate + consolidated findings

---

## Challenge 1: Is a Fresh Start Actually Better Than Cherry-Picking?

### Claim Being Challenged

The historian recommends Option A (fresh implementation) over Option B (cherry-pick) or Option C (squash-and-rebase), rating cherry-pick as HIGH risk and fresh start as MEDIUM risk.

### Counter-Evidence and Risks

**The cost of discarding 15 commits is NOT zero.** Let me quantify:

- 15 commits touch ~55 unique source files, ~15 test files, ~60 agent/config files
- The branch contains ~725 lines of NEW test code (commit #1 alone)
- `agent_name_registry.py` (commit #12) has 62 entries extracted via careful comparison — each entry is a verified mapping
- PM_INSTRUCTIONS.md (commit #14) has 47 individually-verified reference replacements
- The `agents deploy` fix (commit #11) is a one-line fix that took significant debugging to find

**Cherry-picking IS viable for selected commits.** The historian's argument against cherry-picking rests on "correction chains" — but only 3 of 15 commits are corrections:
- Commit #9 corrects #7/#8 (12 stale refs)
- Commit #10 corrects #3 (norecursedirs)
- Commit #15 partially corrects the v8 plan

For the KEEP items, we could cherry-pick the FINAL corrected state by taking:
- Commits #11 (deploy fix) — standalone, no dependencies
- Commit #12 (name registry) — standalone new file
- Commit #14 (PM_INSTRUCTIONS) — standalone text changes

These three commits have NO correction chains. They're clean additions.

**Fresh implementation introduces RE-DISCOVERY RISK.** The branch discovered issues through painful iteration:
- 12 stale references found ONLY during Phase 5 verification
- `toolchain_detector` fix that was REVERSED because devil's advocate proved it wrong
- 5 filename collision pairs found ONLY by v5 analysis

A reimplementation risks re-encountering these issues OR (worse) missing them entirely.

**Time cost estimate:**
- Cherry-pick 3 clean commits: ~30 minutes, low risk
- Fresh implementation of 8 components across 5 phases: 4-8 hours, medium risk
- Fresh implementation PLUS re-discovering edge cases: 8-16 hours if unlucky

### Verdict: **VALID CONCERN**

The fresh-start recommendation is defensible but overstated. A **hybrid approach** would be more efficient:
1. Start fresh branch from `main`
2. Cherry-pick commits #11, #12, #14 directly (they're clean)
3. Fresh-implement the REDO and NEW items using lessons learned
4. This gives ~40% of the work for free with near-zero risk

### Recommendation

**Hybrid approach**: cherry-pick proven standalone commits + fresh-implement everything else. This captures the hard-won knowledge without carrying the correction chains.

---

## Challenge 2: Scope Creep Assessment

### Claim Being Challenged

The solution architect proposes 8 components across 5 phases. The v2 consolidated analysis identified 19 action items across 4 priority levels. Is this too ambitious?

### Counter-Evidence and Risks

**The branch's ENTIRE failure history is one of escalating scope.**

Timeline of scope inflation:
1. v1: "Fix three incompatible AgentType enums" (3 files)
2. v2: "Map 5 code paths for type: vs agent_type:" (5 files)
3. v5: "Actually 7 deployment paths, not 4" (7+ paths)
4. v7: "5-phase plan" (14+ files per phase)
5. v8: "Correction plan for things v7 missed" (6+ more files)
6. v3 architecture: "8 components, 5 phases" (25+ files)

Each version expanded scope. The solution architecture continues this trend.

**What's the MINIMAL change set that delivers 80% of value?**

The three root problems identified by the consolidated analysis:
1. Dual normalization divergence (10 agents)
2. AgentType enum gap (87% agents)
3. Three competing identity systems

But problem #2 (AgentType enum gap) is **functionally irrelevant**. The baseline audit confirms: `_safe_parse_agent_type()` silently converts 87% of agents to CUSTOM/None. But WHERE is this used for actual routing decisions? Let me check:

- `unified_agent_registry.py` uses AgentType for listing agents by type — but this is informational, not routing
- `agent_definition.py` has AgentType in the dataclass — but it's set and rarely queried
- `agent_registry.py` imports AgentType for construction — again, informational

**The AgentType enum gap does NOT cause delegation failures.** It only affects internal categorization displays. This makes it MEDIUM priority, not CRITICAL.

**Problem #1 (dual normalization) is the ONLY critical functional bug.** If any code path uses `AgentNameNormalizer` for delegation (converting TODO names back to `subagent_type`), 10 agents fail. But the prior v2 devil's advocate already confirmed: the normalizer is used for "TODO prefixes, display, and color coding" — NOT directly for delegation. The `to_task_format()` method COULD be used for delegation, but a grep would reveal if it actually is.

**Minimal viable change set (delivers 80% value with 20% effort):**

| Item | Files | Effort | Value |
|------|-------|--------|-------|
| Fix 3 broken PM prompt references | 2 files, 3 edits | Trivial | HIGH (active delegation failures) |
| Fix `system_context.py` guidance | 1 file | Trivial | HIGH (PM sends wrong format) |
| Reconcile CANONICAL_NAMES with name: values | 1 file, 10 dict edits | Small | HIGH (prevents latent bugs) |
| Port `agents deploy` fix | 1 file, 1 method call | Trivial | HIGH (command was broken) |
| Delete archive directory | 39 files, 0 code | Small | MEDIUM (cleanup) |

**Total: 5 items, ~5 files changed, 1-2 hours work. This covers all HIGH-value items.**

The remaining 14 action items (unified enum, deployment consolidation, CORE_AGENTS merge, normalization consolidation, agent_identity.py module, etc.) are architectural improvements with LOW to MEDIUM immediate value.

### Verdict: **VALID CONCERN**

The 8-component, 5-phase plan is over-engineered for the actual problem severity. The branch history proves that ambitious multi-phase plans fail through scope expansion. A minimal-first approach with optional follow-up phases would be safer.

### Recommendation

Ship a **Minimal Viable Fix (MVF)** of 5 items in a single commit/PR. If that goes well, THEN consider the architectural improvements as separate, optional PRs. Don't couple them.

---

## Challenge 3: The `agent_identity.py` Registry Design

### Claim Being Challenged

The architect proposes a hardcoded `AGENT_REGISTRY` with 48 `AgentIdentity` entries, defended by "CI drift detection" preventing staleness.

### Counter-Evidence and Risks

**This is the THIRD hardcoded agent map.** We already have:
1. `CANONICAL_NAMES` in `agent_name_normalizer.py` (64 entries) — confirmed stale for 10 agents
2. `AGENT_NAME_MAP` in `agent_name_registry.py` (branch only, 62 entries)

The architect proposes replacing both with `AGENT_REGISTRY` (48 entries). But the fundamental problem — **hardcoded data goes stale** — is unchanged.

**CI drift detection has a critical gap:** CI tests only run when code is pushed. Consider:
1. User adds agent #49 to upstream `claude-mpm-agents` repo
2. User runs `claude-mpm agents sync` — new agent is cached and deployed
3. `AGENT_REGISTRY` doesn't know about agent #49
4. `get_name("new-agent")` falls through to Title Case fallback: `"New Agent"`
5. If the upstream `name:` is `new_agent` (underscore), the fallback produces WRONG name
6. No CI test runs because no code was changed — the registry was never updated
7. Bug exists silently until someone pushes code AND the drift test catches it

**The fallback mechanism is the real vulnerability.** The architect's `get_name()` has:
```python
# Fallback: Title Case from kebab
return canonical.replace("-", " ").title()
```

This is WRONG for:
- Underscore names: `new_agent` becomes `New Agent` instead of `new_agent`
- Acronym names: `aws-ops` becomes `Aws Ops` instead of `AWS Ops`
- Already-kebab names: `real-user` stays as `Real User` instead of `real-user`

**Dynamic resolution alternative cost-benefit:**

| Factor | Hardcoded Registry | Dynamic Resolution |
|--------|-------------------|-------------------|
| Staleness risk | HIGH (proven by CANONICAL_NAMES) | ZERO |
| Startup cost | None | ~50ms (read 48 .md files, parse frontmatter) |
| Test/CI availability | Always works | Needs `.claude/agents/` or mock |
| IDE support | Static analysis possible | Runtime only |
| Maintenance | Manual update + CI check | Automatic |

The architect's objection — "Dynamic resolution requires `.claude/agents/` to exist at import time (fails during testing, CI, fresh installs)" — is valid but solvable:
- Use lazy initialization (populate on first access)
- Fall back to hardcoded for testing/CI when agents dir is absent
- Keep hardcoded as CACHE, not source of truth

**Evidence from the codebase**: `get_deployed_agent_ids()` in `agent_filters.py` already reads `.claude/agents/` dynamically at runtime. The pattern exists and works.

### Verdict: **VALID CONCERN**

A hardcoded-only registry will go stale — this is not theoretical, it's proven by `CANONICAL_NAMES`. CI drift detection mitigates but doesn't prevent the gap between agent addition and code push. A **hybrid approach** (hardcoded cache + dynamic override when agents dir exists) would be more robust.

### Recommendation

Implement `AGENT_REGISTRY` as proposed BUT add a `_refresh_from_deployed()` function that overwrites registry entries from live `.claude/agents/` files when they exist. Call it lazily on first access. Keep hardcoded entries as fallback for testing/CI.

---

## Challenge 4: `AgentCategory` Enum Rename

### Claim Being Challenged

The architect proposes renaming `AgentType` to `AgentCategory` across the codebase, arguing that `AgentType` is "ambiguous — it's used for both deployment tier and functional category."

### Counter-Evidence and Risks

**Blast radius assessment:**

`AgentType` appears in **25+ production source files** on main (confirmed by grep). It's referenced:
- 16 times in `unified_agent_registry.py`
- 6 times in `agent_definition_factory.py`
- 3 times in `agent_registry.py`
- 2 times in `agent_definition.py`
- 2 times in `models/__init__.py`
- 2 times in `services/agents/__init__.py`
- Plus test files: 28 times in `test_agent_infrastructure.py` alone

**The rename touches every consumer.** Even with a `AgentType = AgentCategory` alias for backward compatibility, all NEW code must use the new name, all docs must be updated, and any code path that does `isinstance(x, AgentType)` or `AgentType.CORE` must be verified.

**Is the ambiguity ACTUALLY causing bugs?** No evidence of any bug caused by the name `AgentType`. The problem is that the enum VALUES don't cover 87% of frontmatter values — not that the NAME is confusing. You could fix the value coverage without renaming:

```python
# Option: Just ADD values to existing AgentType
class AgentType(str, Enum):
    CORE = "core"
    PROJECT = "project"
    CUSTOM = "custom"
    SYSTEM = "system"
    SPECIALIZED = "specialized"
    # New values for frontmatter coverage:
    ENGINEER = "engineer"
    OPS = "ops"
    QA = "qa"
    DOCUMENTATION = "documentation"
    RESEARCH = "research"
    SECURITY = "security"
    ANALYSIS = "analysis"
    PRODUCT = "product"
    CONTENT = "content"
    REFACTORING = "refactoring"
```

This gives 100% frontmatter coverage with ZERO consumer changes for existing code.

**The TWO-enum problem is real but the rename doesn't solve it.** The architect wants to merge `agent_definition.py:AgentType` and `unified_agent_registry.py:AgentType` into one `AgentCategory`. But these two enums serve DIFFERENT purposes:
- `agent_definition.py` AgentType: deployment tier (CORE/PROJECT/CUSTOM)
- `unified_agent_registry.py` AgentType: functional classification (CORE/SPECIALIZED/USER_DEFINED)

Merging them into one enum conflates two concepts. The architect adds `is_core` to `AgentIdentity` to handle the deployment tier concept — but this means changing how `is_core` is determined across the codebase.

### Verdict: **VALID CONCERN**

The rename is high blast radius for low bug-fix value. Extending the existing enum(s) with missing values achieves the same coverage with far less disruption.

### Recommendation

**Don't rename.** Instead:
1. Extend `agent_definition.py:AgentType` with the 10 missing category values
2. Keep `unified_agent_registry.py:AgentType` separate (it serves a different purpose)
3. Update `_safe_parse_agent_type()` to handle all 15 frontmatter values
4. Total blast radius: 2-3 files instead of 25+

---

## Challenge 5: Deployment Path Consolidation Risks

### Claim Being Challenged

The architect proposes routing `SingleAgentDeployer` and `configure.py._deploy_single_agent()` through `deploy_agent_file()`.

### Counter-Evidence and Risks

**`SingleAgentDeployer` creates NEW content — it doesn't just copy files.**

Evidence from `single_agent_deployer.py:91`:
```python
agent_content = self.template_builder.build_agent_markdown(
    agent_name, template_file, base_agent_data, source_info
)
```

The `template_builder.build_agent_markdown()` is a complex content generator that:
- Composes agent markdown from templates + base agent data
- Injects version information
- Adds source attribution
- Constructs YAML frontmatter

`deploy_agent_file()` reads a source file's content and writes it to the target. If we route `SingleAgentDeployer` through `deploy_agent_file()`, we'd need to:
1. Build the content (via template_builder)
2. Write it to a temp file
3. Pass the temp file to `deploy_agent_file()`
4. deploy_agent_file reads it back, normalizes filename, writes to target

This is **wasteful and introduces a bug vector**: `deploy_agent_file()` might re-normalize content that was already correctly built. Specifically, `ensure_agent_id_in_frontmatter()` could inject a SECOND `agent_id` if the built content already has one.

**`configure.py._deploy_single_agent()` uses `shutil.copy2` INTENTIONALLY.**

Evidence from configure.py:3081-3119: This code path handles remote agents from the `claude-mpm-agents` git repo. These files are ALREADY correctly normalized by the upstream repo. Using `shutil.copy2` preserves exact upstream content, including:
- Exact `name:` field values (sacred)
- Exact `agent_id:` values from upstream
- Exact formatting and whitespace

If we route through `deploy_agent_file()`, it will:
- Re-derive `agent_id` from filename (may differ from upstream's `agent_id:`)
- Potentially strip `-agent` from filenames of agents that SHOULD have it (e.g., `content-agent.md` in upstream)

**The "dual deployer" problem is overstated.** `SingleAgentDeployer` is called from `agent_wizard.py` (interactive CLI for custom agent creation). `deploy_agent_file()` is called from git sync. These are DIFFERENT use cases with DIFFERENT requirements:
- Git sync: copy upstream files with normalization
- Wizard: build new content from templates

Forcing both through one function conflates these concerns.

### Verdict: **VALID CONCERN**

Routing all deployment through one function oversimplifies. The three paths exist because they serve different purposes. The actual fix is narrower: ensure consistent FILENAME normalization across all paths (which `normalize_deployment_filename()` already handles), not forcing all content through one function.

### Recommendation

1. Keep `SingleAgentDeployer` separate but add `normalize_deployment_filename()` call for the target filename
2. Keep `configure.py` using `shutil.copy2` for upstream content BUT add post-copy `ensure_agent_id_in_frontmatter()` call
3. Don't route everything through `deploy_agent_file()` — it was designed for git sync, not template building

---

## Challenge 6: Upstream Dependency

### Claim Being Challenged

The solution architecture notes 6 non-conforming `name:` values and recommends fixing upstream. But it also says the solution "MUST work without upstream changes" via `get_display_name()` vs `get_name()` split.

### Counter-Evidence and Risks

**The upstream fix assumption is fragile.** Evidence:
- The upstream repo (`claude-mpm-agents`) is maintained by the same team, so technically fixable
- BUT the branch history shows this was declared "out of scope" TWICE (v5, v8) and never done
- If it was easy to fix, it would have been done already
- The 6 problematic names (`ticketing_agent`, `aws_ops_agent`, etc.) may have downstream consumers we don't know about

**The `get_display_name()` vs `get_name()` split is architecturally sound but creates a maintenance burden:**

Every developer who touches agent references must know:
- Use `get_name()` for delegation (returns ugly `ticketing_agent`)
- Use `get_display_name()` for UI (returns pretty `Ticketing Agent`)
- NEVER mix them up

This is the kind of rule that gets violated within weeks. The CORRECT solution is fixing upstream so `get_name() == get_display_name()` for all agents.

**What if upstream maintainer disagrees?** The solution must handle permanently ugly names. The current design does, but at the cost of a split API that's easy to misuse.

### Verdict: **VALID CONCERN but architecture handles it**

The solution correctly separates delegation names from display names. The risk is developer confusion, not architectural failure. Fixing upstream remains the right long-term answer.

### Recommendation

1. Document the `get_name()` vs `get_display_name()` distinction prominently
2. Add a lint rule or CI check that flags `get_display_name()` usage in delegation contexts
3. Prioritize the upstream fix as a fast follow — don't defer indefinitely

---

## Challenge 7: Phase Boundary Risks

### Claim Being Challenged

The architect proposes 5 phases, each "independently shippable." The branch failed through incremental implementation across 15 commits. Is this the same pattern?

### Counter-Evidence and Risks

**The branch failed for DIFFERENT reasons than phased delivery:**
- The branch failed because each phase DISCOVERED new scope (12 stale refs in Phase 5)
- The branch failed because corrections were needed for previous phases
- The branch failed because understanding evolved (pivot points in v5, v6, v8)

**The architect's phases are better-designed** because:
- All 5 prior analyses inform the design (no discovery risk)
- Phase 1 creates the foundation with no consumers yet (safe addition)
- Each subsequent phase is integration, not discovery

**BUT phase boundaries still have invariant risks:**

| Between | Risk | What Could Break |
|---------|------|-----------------|
| Phase 1 → 2 | CANONICAL_NAMES removed before consumers migrated | All `normalize()` calls return wrong values |
| Phase 2 → 3 | Deployment behavior changes mid-migration | Some agents deploy with old normalization, others with new |
| Phase 3 → 4 | CORE_AGENTS moved but not all consumers updated | toolchain_detector references old location |
| Phase 4 → 5 | Tests assume state that Phase 4 changes broke | Test failures that look like regressions |

**Key invariant that MUST hold between ALL phases:**
Every deployed agent must be reachable by PM delegation using the exact `name:` field value. If ANY phase breaks this, the entire system stops working.

**The branch's Phase 5 surprise (12 stale references) is the cautionary tale.** The architect says "verify before commit" — but the branch historian tried that too. The 12 refs were found by a DIFFERENT grep pattern than the one used during implementation. Comprehensive verification is harder than it sounds.

### Verdict: **VALID CONCERN but mitigated**

The 5-phase design is sound IF each phase includes comprehensive grep verification. The real risk is that "comprehensive" is hard to achieve. The safest approach is fewer, larger phases — or better yet, a single well-tested PR.

### Recommendation

Collapse 5 phases into 2-3:
1. **Phase A**: Foundation + Registry Integration (Components 1+2+3+7) — all the "data" changes
2. **Phase B**: Consumer Updates + PM Fixes (Components 4+5+6+8) — all the "reference" changes
3. **Phase C**: Verification tests (Component CI) — all the "prevention" changes

Each phase is larger but there are fewer boundaries to cross. Run full test suite between each.

---

## Challenge 8: Test Coverage

### Claim Being Challenged

The architect proposes drift detection tests in Phase 5. Are these sufficient? What edge cases are NOT covered?

### Counter-Evidence and Risks

**Existing test inventory on main is EXTENSIVE but fragmented:**
- 185 non-archive test files related to agents
- `test_agent_name_normalizer.py` covers suffix stripping, aliases, name formats
- 12 deployment sub-tests in `tests/services/agents/deployment/`
- But NO test verifies that PM prompt references match deployed agents (proposed in Phase 5)

**The branch's `test_agent_field_consistency.py` IS reusable.** It verifies:
1. Hardcoded agent filenames in source resolve to actual files
2. Every deployed agent has frontmatter
3. PM delegation matrix names match deployed agents
4. Documents known AgentType enum mismatches

This is exactly the kind of test the fresh implementation needs. Cherry-picking the test file (or its logic) saves significant effort.

**Edge cases NOT covered by the proposed tests:**

| Edge Case | Current Coverage | Proposed Coverage | Gap? |
|-----------|-----------------|-------------------|------|
| Agent with `name:` containing special chars | NONE | NONE | YES |
| Agent added/removed between CI runs | NONE | Drift test (partial) | YES (gap between add and push) |
| `normalize()` called with None/empty | Covered by normalizer tests | Not explicitly | Probably OK |
| `configure.py` deploy path normalization | NONE | NONE | YES |
| `SingleAgentDeployer` + `deploy_agent_file` interaction | NONE | NONE | YES |
| PM prompt with agent name in markdown formatting | NONE | NONE | YES (e.g., `**Research**` vs `Research`) |
| Case-sensitivity of single-word agents | NONE | NONE | YES (does `research` == `Research`?) |

**The biggest testing gap is integration between deployment paths and PM delegation.** No test currently verifies:
1. Deploy an agent via all 3 paths
2. Check that PM can delegate to it using the `name:` field
3. Verify that `normalize()` produces the correct value for delegation

### Verdict: **VALID CONCERN**

The proposed tests cover drift detection but miss deployment-path-to-delegation integration. The branch's `test_agent_field_consistency.py` should be adapted and reused.

### Recommendation

1. Port `test_agent_field_consistency.py` logic from branch (cherry-pick or rewrite)
2. Add integration test: for each agent in AGENT_REGISTRY, verify `get_name(agent_id)` matches the actual `name:` field in the deployed `.md` file
3. Add test: for each agent reference in PM prompt files, verify it exists in AGENT_REGISTRY
4. Add test: `normalize(get_name(agent_id))` round-trips correctly for all agents

---

## Challenge 9: Verify Key Assumptions Independently

### Assumption 9a: `.claude/agents/` is empty on main

**CONFIRMED.** `git show main:.claude/agents/` returns: `fatal: path '.claude/agents/' exists on disk, but not in 'main'`. The directory is NOT committed to the repo on main. Agents are deployed at runtime.

### Assumption 9b: `templates/archive/` on main has no active consumers

**PARTIALLY CONFIRMED.** The archive directory EXISTS on main with 39 JSON files (confirmed via `git ls-tree`). Import analysis shows:
- `from claude_mpm.agents.templates import` returns ZERO results in production code
- `templates/__init__.py` functions (`load_template`, `get_template_path`) check if files exist before returning — so they gracefully handle missing templates
- BUT `local_template_manager.py` imports from `templates` (1 import hit) — this needs verification before deletion

**Key finding the v2 team MISSED**: The v2 consolidated analysis (Section 1.1) states "archive directory does NOT exist" — but they were checking the BRANCH where it was already deleted. On main, it EXISTS with 39 files. The solution architect correctly caught this (Component 7), but the v2 team's error could have led to a missed deletion.

### Assumption 9c: `type:` vs `agent_type:` distribution on main matches baseline audit

**CANNOT VERIFY from main branch alone** — `.claude/agents/` doesn't exist on main. The deployed agents are runtime artifacts. The baseline audit's claim that "all 48 use `agent_type:`" was based on the BRANCH state (where the rename was already done), not main.

**On main, the deployment pipeline writes `agent_type:` because:**
- `deploy_agent_file()` calls `ensure_agent_id_in_frontmatter()` which doesn't touch `agent_type`
- The upstream agent files in the `claude-mpm-agents` repo use `agent_type:`
- The `read_agent_type()` utility (branch only) reads both `type:` and `agent_type:`

**Conclusion**: The field name is likely `agent_type:` in deployed agents (set by upstream), but this needs runtime verification, not just `git show main:`.

### Assumption 9d: No agent-related config files the team hasn't found

**Found one MISSED file:** `src/claude_mpm/config/schemas/agent_frontmatter_schema.json`

The v2 devil's advocate found that this schema has a `name` pattern of `"^[a-z][a-z0-9_-]*$"` — which requires lowercase. But most agents use Title Case names. If schema validation is ever enforced strictly, it would break every agent.

**The solution architecture does NOT address this schema.** The `agent_identity.py` module would need to either:
- Update the schema to allow Title Case
- Or ensure the schema is never enforced for the `name` field

Also found: `src/claude_mpm/services/agents/local_template_manager.py` — imports from templates, potential consumer of `templates/__init__.py`.

### Verdict: **NEEDS VERIFICATION for 9c; VALID CONCERNS for 9b and 9d**

---

## Summary Risk Matrix

| # | Challenge | Severity | Verdict | Impact on Plan |
|---|-----------|----------|---------|---------------|
| 1 | Fresh start vs cherry-pick cost | MEDIUM | **VALID** | Hybrid approach saves 40% effort |
| 2 | Scope creep (8 components, 5 phases) | HIGH | **VALID** | Minimal viable fix delivers 80% value in 20% time |
| 3 | Hardcoded registry staleness | MEDIUM | **VALID** | Add dynamic refresh, don't rely on hardcoded alone |
| 4 | AgentCategory rename blast radius | MEDIUM | **VALID** | Extend existing enum instead of renaming |
| 5 | Deployment consolidation risks | MEDIUM | **VALID** | Keep separate paths, normalize filenames only |
| 6 | Upstream dependency | LOW-MEDIUM | **VALID but handled** | Architecture handles it; fix upstream as fast follow |
| 7 | Phase boundary risks | MEDIUM | **VALID but mitigated** | Collapse to 2-3 phases |
| 8 | Test coverage gaps | MEDIUM | **VALID** | Port branch tests + add integration tests |
| 9a | .claude/agents/ empty on main | N/A | **CONFIRMED** | No action needed |
| 9b | Archive active consumers | LOW | **PARTIAL** | Verify `local_template_manager.py` before deletion |
| 9c | type: vs agent_type: on main | LOW | **UNVERIFIABLE** | Runtime check needed |
| 9d | Missed config files | MEDIUM | **VALID** | Fix `agent_frontmatter_schema.json` pattern |

---

## Minimal Viable Alternative

If the full 8-component plan is too risky, here's what delivers maximum value with minimum risk:

### MVF: Minimal Viable Fix (1 PR, ~2 hours)

| # | Change | Files | Risk |
|---|--------|-------|------|
| 1 | Fix 3 broken PM prompt refs (OUTPUT_STYLE, WORKFLOW) | 2 | Trivial |
| 2 | Fix `system_context.py` incorrect lowercase guidance | 1 | Trivial |
| 3 | Update 10 divergent CANONICAL_NAMES entries | 1 | Low |
| 4 | Cherry-pick `agents deploy` fix (commit e2c9e59c) | 1 | Low |
| 5 | Delete `templates/archive/` (39 dead JSON files) | 40 | Low |
| 6 | Port PM_INSTRUCTIONS.md 47 reference fixes | 1 | Low |
| 7 | Add drift-detection test (CANONICAL_NAMES vs deployed) | 1 new | Low |

**Total: 7 changes, ~47 files (mostly archive deletions), 1-2 hours, LOW overall risk.**

This fixes ALL active delegation failures and the most critical latent bugs. Everything else is architectural improvement that can follow independently.

---

## Guard Rails for Implementation

Regardless of which approach is chosen (full plan or MVF), these guard rails MUST be observed:

1. **Grep before EVERY commit**: `grep -rn "pattern" src/ tests/` for EVERY reference pattern being changed
2. **Run full test suite**: `make test` after EVERY phase/commit
3. **Don't batch-rename and fix references in separate commits**: If you rename X, fix ALL references to X in the SAME commit
4. **Test PM delegation manually**: After any PM prompt change, verify at least 3 agents can be delegated to
5. **Check `local_template_manager.py`** before deleting `templates/__init__.py`
6. **Update `agent_frontmatter_schema.json`** name pattern if touching agent names
7. **Never change a `name:` field value** without verifying it won't break existing PM delegation

---

## Preconditions: Things That MUST Be True for the Plan to Succeed

1. **The `name:` field IS the sole resolution key for Claude Code** — confirmed empirically in v6, reconfirmed in v2 devil's advocate. If Claude Code changes its resolution mechanism, all analysis is invalid.

2. **`CANONICAL_NAMES` is NOT used for delegation** — if any code path feeds `AgentNameNormalizer.normalize()` output into `Agent(subagent_type=...)`, the 10-agent divergence is an ACTIVE bug, not latent. Verify with: `grep -rn "to_task_format\|normalize.*subagent_type" src/`.

3. **The archive directory has no runtime consumers** — verify `local_template_manager.py` doesn't load archive JSON files before deletion.

4. **`ensure_agent_id_in_frontmatter` doesn't break `name:` fields** — if `update_existing=True` is applied globally, verify it ONLY updates `agent_id:` and never touches `name:`.

5. **The 6 non-conforming upstream `name:` values are stable** — if upstream changes them without updating our registry, delegation breaks silently.

6. **Test mocks don't mask real failures** — many tests mock agent-related functions. After refactoring, ensure mocks are updated to match new function signatures.

7. **`configure.py:_deploy_single_agent` is called with ALREADY-NORMALIZED filenames from upstream** — if upstream filenames change convention, the `shutil.copy2` path breaks differently than the `deploy_agent_file()` path.

---

## Final Assessment

The solution architecture is **technically sound but over-scoped for the actual severity of the problems**. The branch history proves that ambitious multi-phase plans tend to expand and require corrections. The three root problems are real, but only ONE (dual normalization divergence) represents an active functional risk. The other two (AgentType enum gap, three identity systems) are architectural debt that doesn't cause user-facing failures.

**My recommendation: Ship the MVF, then reassess.**

The MVF fixes all active bugs in ~2 hours. The full architecture can be implemented incrementally AFTER the MVF proves the approach. This is the opposite of the branch's pattern (implement everything, then fix) — instead: fix everything, then improve architecture.
