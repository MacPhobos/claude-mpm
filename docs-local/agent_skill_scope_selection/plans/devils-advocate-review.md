# Devil's Advocate Review: Scope Implementation Plans

**Reviewer:** devils-advocate (Research Agent)
**Date:** 2026-02-28
**Reviewing:**
- `master-plan.md` (primary target)
- `cli-path-plan.md`
- `api-path-plan.md`
- `test-plan.md`
**Grounded against:** Research files + live source code spot-checks

---

## 1. Prior Concerns Check

The research-phase devil's advocate raised 10 concerns (Sections 1–10) plus two supplementary points (11–12). Here's an honest accounting of each:

---

### Concern 1: Is a unified abstraction actually needed?

**Was it addressed?** Partially. The master plan acknowledges the "fourth resolver" concern and counter-argues that DeploymentContext is "a convenience wrapper, not a resolver. All path logic remains in config_scope.py."

**Adequately addressed?** No. The counter-argument is a semantic distinction without functional difference. To a contributor reading the codebase, `deployment_context.py` *is* a path resolver — it has `agents_dir`, `skills_dir`, `config_dir` properties that return paths. Calling it a "wrapper" doesn't reduce confusion. The master plan commits to deleting `configure_paths.py` and `path_resolver.py` (in Phase 7) which reduces resolvers from 3 to 1, then immediately adds a new one (Phase 2), leaving you at 2. That's progress, but the "we're going from 3 to 2, not 3 to 4" framing should be explicit in the plan — it's not.

---

### Concern 2: What does the abstraction actually fix?

**Was it addressed?** Yes. The master plan clearly separates "Real Bug #1" (CLI scope doesn't affect deployment) from the API scope work. The success criteria explicitly state the CLI fix as criteria 1 and 2.

**Adequately addressed?** Mostly. The CLI bug fix is now clearly motivated. The API scope work is still questionable (see Concern 4 below), but at least the distinction is acknowledged.

---

### Concern 3: The fourth resolver problem

**Was it addressed?** Yes — with Phase 7 committing to delete `configure_paths.py` and `path_resolver.py`. The master plan includes this explicitly in success criterion #6.

**Adequately addressed?** Partially. Phase 7 comes AFTER Phases 4A, 4B, 5, and 6. This means you're running the full implementation of scope in CLI and API (Phases 4–6) while `configure_paths.py` is still alive. If any Phase 4–6 work accidentally references `configure_paths.py` instead of `DeploymentContext`, the bug won't be caught until Phase 7 cleanup. The deletion should gate Phase 4A, not follow it. **This is a real sequencing risk.**

---

### Concern 4: YAGNI — building for hypothetical dashboard needs

**Was it addressed?** Acknowledged but dismissed. The master plan lists API scope (Phases 5–8) as a core deliverable. No justification is given for why the API needs user-scope support *now*, given that the dashboard has zero scope UI.

**Adequately addressed?** No. The plan says "the dashboard will need user scope when scope UI is added" — this is circular reasoning. "We'll need it when we need it" is not a justification for building it now. The research devil's advocate explicitly recommended deferring Phases 5–8 until a dashboard scope selector exists. The master plan doesn't rebut this — it just proceeds. This is the most significant unaddressed concern. **Phases 5–8 represent ~60% of the implementation work (API mutation scope, read scope, Socket.IO events, dashboard notes) for a feature with no frontend consumer.**

---

### Concern 5: CLI scope — broken or by design?

**Was it addressed?** No. The master plan asserts "the bug" without citing any user story, issue report, or documentation that specifies what `--scope user` is *supposed* to do. The research devil's advocate wrote: "Before fixing scope, write down what it should do." The master plan does not do this. The API plan adds a docstring to `config_scope.py` (Task 0.1) that documents scope semantics, but this is the plan authoring team's assumption of what scope *should* mean — not a product decision captured in an issue or spec.

**Adequately addressed?** No. This is a gap that could waste all implementation work if the intended semantics turn out to be different.

---

### Concern 6: The singleton manager problem is worse than acknowledged

**Was it addressed?** Yes — and well. Phase 4B is entirely dedicated to fixing the singleton before any scope is added to API endpoints. The master plan treats this as a "highest-risk safety gate." The ordering (fix singleton in 4B before API scope in 5–6) is correct.

**Adequately addressed?** Yes. This concern was taken seriously.

---

### Concern 7: The validation security argument is overstated

**Was it addressed?** No. The plans continue to reference "moving validation to core" (abstraction-opportunities.md section 9, Phase 2) as a motivation for unification. The research devil's advocate correctly pointed out that CLI path traversal protection doesn't improve security because the CLI user owns the machine.

**Adequately addressed?** No. The validation migration argument appears in the abstraction-opportunities research but is not a deliverable in any plan. This is fine (it's deferred), but the plans never explicitly say "we reject the validation abstraction argument." It lingers as an implied future work item that may never be needed.

---

### Concern 8: Migration risks

**Was it addressed?** Partially. The risk register in the master plan covers most of the identified risks. The `shutil.copy2` vs. service call risk (Concern 8, Risk 1) is explicitly addressed in Phase 4A ("confirmed: CLI uses shutil.copy2 directly, NOT AgentDeploymentService"). The `_get_config_path()` missing-file risk is addressed in Phase 5 (Task 3.4).

**Adequately addressed?** Partially. New risks not in the original research are missing from the register (see Section 5 below).

---

### Concern 9: The state model mismatch (enabled vs. deployed)

**Was it addressed?** No. The master plan does not mention the `is_enabled` (user intent) vs. `is_deployed` (filesystem reality) mismatch at all. The abstraction-opportunities research raised this as a "conceptual mistake" in any unified abstraction. The master plan's DeploymentContext doesn't carry state — it's just a path resolver — so the mismatch isn't directly introduced. But the test plan's cross-scope isolation tests (TC-4-09, TC-4-10) that check agent_states.json isolation may fail or behave unexpectedly if the state model is misunderstood.

**Adequately addressed?** No. At minimum, the plan should document that `agent_states.json` and filesystem deployment are separate state machines and that scope-switching affects both independently.

---

### Concern 10: The simpler alternative (10-line fix)

**Was it addressed?** Dismissed without proper comparison. The master plan includes the CLI bug fix (the "10-line" alternative) but bundles it with 8 phases of additional work. The research devil's advocate's comparison table showed the minimal approach fixes the actual bug with ~30 lines. The master plan acknowledges the simpler path in the executive summary but doesn't justify why the full 9-phase plan is preferred over "fix CLI + defer API."

**Adequately addressed?** No. This is the core strategic question that remains unanswered.

---

## 2. Plan-Level Gaps

### Gap 1: The xfail-to-pass transition is incorrectly specified

**Location:** Master plan Phase 1 + Phase 4A

The test plan defines TC-0-04 and TC-0-05 as characterization tests that document the CURRENT BROKEN behavior:
- TC-0-04 asserts `shutil.copy2` is called with target in `project_dir/.claude/agents/` (the bug)
- TC-0-05 asserts skill written to `{cwd}/.claude/skills/` regardless of scope (the bug)

The test plan notes: "This test is expected to FAIL after the Phase 2 fix is applied."

But the master plan Phase 4A says: "Formerly-XFAIL tests TC-0-04, TC-0-05 now PASS (xfail markers removed)."

**These two statements are contradictory.** After the bug is fixed:
- TC-0-04 would FAIL (its assertion checks the broken behavior)
- TC-0-05 would FAIL (same reason)

You can't "remove the xfail marker" and have these tests pass — the assertions are wrong for the new behavior. The plan needs to specify: **update the assertions** in TC-0-04 and TC-0-05 to reflect correct post-fix behavior, or delete them and rely on TC-2-01/TC-2-02 as the regression tests.

The master plan has this backwards. This will cause Phase 4A to fail CI.

---

### Gap 2: BackupManager backs up the wrong directory for user-scope operations

**Location:** api-path-plan.md "Cross-Cutting Concerns / BackupManager and Scope"

The plan acknowledges that BackupManager always backs up project-scope directories, even for user-scope operations. It says: "Leave BackupManager with its current behavior. The backup still provides journaling and recovery for the operation that matters."

**This is wrong.** For a user-scope deploy to `~/.claude/agents/engineer.md`, the backup captures `{cwd}/.claude/agents/` — the project agents directory, which is unrelated to the operation being performed. If the user-scope deploy fails after the backup is created, the backup is useless for recovery because it doesn't contain the user-scope agents directory.

This is not just a "limitation" — it's a data safety failure in the safety protocol. The plan correctly describes the backup→journal→execute→verify protocol as critical, then accepts a broken backup step for user-scope operations.

**This needs a clear decision:** Either extend BackupManager to accept scope (so it backs up the correct directory), or explicitly disable the backup protocol for user-scope operations (with a warning), or add a `TODO: user-scope backup not implemented` to the operation journal entry. None of these is currently in the plan.

---

### Gap 3: `from_user()` silently stores a meaningless `project_path`

**Location:** api-path-plan.md Phase 1, Task 1.1; master-plan.md Phase 2

The `DeploymentContext.from_user()` factory:
```python
@classmethod
def from_user(cls) -> "DeploymentContext":
    return cls(scope=ConfigScope.USER, project_path=Path.cwd())
```

For USER scope, `project_path` is irrelevant — `resolve_agents_dir(USER, any_path)` ignores `project_path` and returns `~/.claude/agents/`. Yet the frozen dataclass stores `project_path=Path.cwd()`.

This is misleading: two `from_user()` calls made from different directories will produce contextually different frozen instances that happen to resolve to the same paths. A developer doing `ctx1 == ctx2` comparison will get False even though both contexts resolve to identical directories.

More importantly: the frozen dataclass's `__hash__` is derived from `(scope, project_path)`. Using USER-scope contexts as dict keys (as the per-scope `_agent_managers` dict does) requires using the scope string as the key, not the context itself — which is what the plan does. But the inconsistency could lead to bugs.

**Fix needed:** `from_user()` should store `project_path=None` (not `Path.cwd()`) or explicitly document that `project_path` is ignored for USER scope.

---

### Gap 4: Concurrent initialization race in per-scope dict

**Location:** api-path-plan.md Phase 2, Task 2.1

The replacement code:
```python
_agent_managers: Dict[str, Any] = {}

def _get_agent_manager(scope: str = "project") -> Any:
    if scope not in _agent_managers:
        # ... create and store
        _agent_managers[scope] = AgentManager(project_dir=ctx.agents_dir)
    return _agent_managers[scope]
```

This is a classic check-then-act race condition. Two simultaneous requests for user scope could both pass the `if scope not in _agent_managers` check and create two different AgentManager instances, with the second overwriting the first. Under Python's GIL this is unlikely but not impossible in async code where the check and the set span multiple operations. More importantly, the aiohttp server uses asyncio — the `asyncio.to_thread()` calls spawn real threads for the sync operations, and `_get_agent_manager()` is called from within those threads.

The original singleton code had the same race, but replacing one race with a slightly different race isn't progress. **The plan should either add a lock or use `dict.setdefault()` with a factory pattern.**

---

### Gap 5: No plan for what happens when user-scope directory doesn't exist at read time

**Location:** api-path-plan.md Phase 4, risk table

The risk table notes: "`AgentManager` with user-scope path fails if `~/.claude/agents/` doesn't exist." The mitigation says "AgentManager should handle gracefully (return empty)."

But this is stated as a hope, not a verified fact. The plan says "Test with missing directory; AgentManager should handle gracefully" — the word "should" reveals this hasn't been confirmed by reading the AgentManager code.

**This needs to be verified before Phase 4 starts**, not discovered during Phase 4 when AgentManager raises a `FileNotFoundError` during an integration test. The plan should include a pre-coding verification step: "Read `AgentManager.__init__` and `list_agents()` to confirm behavior with non-existent directory."

---

### Gap 6: `autoconfig` test TC-3-22 contradicts the API plan decision

**Location:** test-plan.md Phase 3-E, TC-3-22 vs. api-path-plan.md "Cross-Cutting Concerns / Autoconfig Handler"

The API plan explicitly decides: autoconfig endpoints only support project scope; passing `scope=user` returns HTTP 400.

Yet TC-3-22 (`test_autoconfig_apply_user_scope`) is written as a positive test: it expects autoconfig with `scope=user` to deploy agents to home dir.

**This test will fail by design** — the API plan says to REJECT user scope for autoconfig, but the test plan writes a test that EXPECTS it to succeed. Either the test plan author didn't read the API plan decision, or there's a genuine disagreement. The master plan doesn't notice or resolve this contradiction.

---

### Gap 7: `configure_paths.py` retirement is undefined

**Location:** master-plan.md Phase 7

Phase 7 says "retire dead resolvers" and lists `configure_paths.py` as a deletion target. But `configure_paths.py` is reportedly used by the CLI configure command. The CLI plan (Phase 3) wires `DeploymentContext` for `config_dir` only — leaving other `configure_paths.py` calls in place until Phase 7.

The Phase 7 description in the master plan is one line: "retire dead resolvers + skills --scope." There's no task breakdown, no list of callsites to migrate, and no identification of which `configure_paths.py` functions are still in use vs. dead after Phase 3. If Phase 7 is handed to an engineer with only the master plan, they won't know what to do.

---

## 3. Sequencing Problems

### Sequencing Problem 1: Phase 7 (delete resolvers) should gate Phase 4A, not follow it

If `configure_paths.py` is still alive during Phase 4A, there's a risk that scope-related fixes in configure.py accidentally import from `configure_paths.py` instead of `DeploymentContext`. Phase 7 cleanup should run immediately after Phase 3 (the refactor phase), before Phase 4A introduces the actual behavior change. The current sequence allows the old resolvers to coexist with the new abstraction for 4+ phases.

### Sequencing Problem 2: Phase 4A and 4B parallel claim is weakly supported

The plan says 4A (CLI bug fix) and 4B (API singleton fix) can run in parallel because they touch different files. This is mostly true, but:
- 4B.3 modifies `agent_deployment_handler.py`
- 4B.4 modifies `skill_deployment_handler.py`

If Phase 4A is in progress on branch `fix/cli-scope` and Phase 4B is on `fix/api-singleton`, and both go through any shared test infrastructure changes (e.g., conftest.py updates), the merge will conflict. The master plan doesn't specify how parallel branches coordinate or which merges first.

### Sequencing Problem 3: Phase 9 dependency underspecified

The master plan shows Phase 9 (E2E integration tests) depending on "4A and 6." But Phase 6 (API read scope) depends on 4B. And Phases 5 and 6 require Phase 4B. Phase 8 (Socket.IO events) says "depends on Phase 3" but the events work needs Phase 5 (mutation scope) too — you can't add scope to config_events before the mutations support scope.

The dependency graph in Section 2 of the master plan has Phase 8 branching from Phase 5, which is correct. But the text says "Phase 8 depends on Phase 3" which is incorrect. This inconsistency will confuse whoever implements Phase 8.

### Sequencing Problem 4: "Each phase independently mergeable" is overstated

The plan claims each phase can be independently merged with CI passing. But:
- Phase 1 adds xfail tests that MUST fail before Phase 4A (by design)
- Phase 2 makes the xfail tests start passing (they become regular tests)
- If Phase 1 is merged, CI shows "some tests xfail" which is expected
- If Phase 2 is merged without Phase 1, the new tests (from test_scope_selector.py) try to import `DeploymentContext` which doesn't exist yet

This ordering is correct (1 before 2), but the "independently mergeable" claim is more nuanced than stated. Only certain phases are truly independently mergeable — others are pairs that must be merged together or in strict sequence.

---

## 4. Test Plan Adequacy

### Test Plan Strength: Characterization-first approach

The plan follows the devil's advocate's recommendation: write characterization tests before any code change. This is correct and is the plan's biggest methodological strength.

### Test Plan Weakness 1: TC-0-04/TC-0-05 contradiction (see Gap 1 above)

This is a critical flaw that will block Phase 4A from passing CI. The test assertions document broken behavior and will be wrong after the fix, but the plan says to just "remove xfail markers."

### Test Plan Weakness 2: No test for BackupManager user-scope behavior

The 100-test plan has no test that validates backup behavior during user-scope operations. Specifically, there is no test that answers: "When a user-scope agent deploy fails after backup creation, does the recovery mechanism restore the correct directory?" This is a critical safety path with no coverage.

### Test Plan Weakness 3: No concurrency test for `_agent_managers` dict

The per-scope dict introduced in Phase 4B has a race condition (see Gap 4). There is no concurrency test to catch this. The test plan has `test_same_scope_returns_cached_manager` (TC from api-path-plan.md Phase 2) but this is single-threaded. A concurrent test with two threads simultaneously calling `_get_agent_manager("user")` would expose the race.

### Test Plan Weakness 4: The ~100 test count is misleading

Of the ~100 tests:
- 23 are pure value-object unit tests for `DeploymentContext` (testing that a frozen dataclass has the properties you wrote into it — trivially true by inspection)
- 12 are characterization tests documenting current behavior (will become incorrect after fix)
- 16 are E2E tests (the ones that actually matter)

The E2E tests in Phase 4 are where scope correctness is actually proven, but they depend on getting `Path.home()` mocking right, `AgentManager` handling missing dirs correctly, and the full server stack being testable. These are the highest-complexity tests, and the plan's description of them is the least detailed (no setup code, just descriptions).

### Test Plan Weakness 5: No test for `scope=null` JSON behavior

TC-3-05 tests `{"scope": null}` — is it treated as project scope, or is it an error? The test says "treated as project (or returns clear error)." This ambiguity in a test specification means the implementation can go either way and the test will be written to match whatever was implemented. This is not a useful test — it needs a clear expected behavior stated upfront.

---

## 5. Risk Assessment

### Risks in the Master Plan (9 total)

The master plan lists 9 risks in its risk register. Several are valid and well-mitigated. The following are missing or underrated:

### Missing Risk 1: `configure_paths.py` callsite inventory is not confirmed

The plan commits to retiring `configure_paths.py` (Phase 7) without listing which callsites use it. If there are more callsites than expected (in commands other than `configure.py`), Phase 7 could expand significantly. This should be verified before Phase 3 begins: `grep -r "configure_paths" src/` should produce a finite, confirmed list.

### Missing Risk 2: `AgentManager` behavior with non-existent user-scope directory

The plan lists this as a "Medium" risk with mitigation "should handle gracefully" — but "should" is not a verification. If `AgentManager.__init__` or `list_agents()` raises on a missing directory (plausible for a manager that wasn't designed for user scope), Phase 4B will introduce a regression on every user-scope GET request. **Verify before Phase 4B.**

### Missing Risk 3: `DeploymentVerifier` default captured at first-use time, not construction time

The research devil's advocate identified this as a risk. The actual code confirms: `DeploymentVerifier()` is lazy-initialized (first call) and captures `default_agents_dir = resolve_agents_dir(ConfigScope.PROJECT, Path.cwd())` AT THAT TIME. If `Path.cwd()` changes between server start and first verifier call (unlikely in production, possible in tests with `monkeypatch.chdir()`), the default will be wrong.

The plan's mitigation (pass `agents_dir` explicitly to every verifier call) is correct, but the risk is understated as a "singleton" issue when it's actually a "mutable global captured at lazy-init time" issue.

### Missing Risk 4: The `from_user()` stores irrelevant `project_path` (see Gap 3)

Not in the risk register. Can cause subtle bugs when user-scope contexts are compared for equality or used in hash maps.

### Missing Risk 5: No API backward compat test for `scope: null` or `scope: ""`

The plan claims 100% backward compatibility. But adding scope validation to the request schema means:
- `{"agent_name": "x", "scope": null}` — will this hit the validation error branch? What does `body.get("scope", "project")` return when scope is null in JSON? It returns `None`, and `DeploymentContext.from_request_scope(None)` will either fail with `TypeError` or `ValueError` depending on how the guard is written. The test TC-3-05 is ambiguous about this.

If any existing client sends `scope: null` (e.g., a Svelte form that includes a scope field set to null when not selected), this will now return HTTP 400 where it previously worked. This IS a breaking change for null-sending clients.

---

## 6. Alternative Approaches

The master plan does not formally evaluate alternatives. Let me do that here.

### Alternative A: Minimal fix (10 lines) — The Dismissed Option

**What it does:**
1. Fix CLI user scope in `_deploy_single_agent()` and `_install_skill_from_dict()` (~10 lines)
2. Retire `configure_paths.py` by migrating its 5-6 callsites to `config_scope.py` (~30 lines)
3. Delete dead `path_resolver.py` (~0 lines, just delete)
4. Defer API scope until dashboard has a scope selector (no timeline given)

**Why it might be better:**
- Fixes the actual user-facing bug immediately
- No new abstraction added
- Reduces resolver count by deletion, not addition
- Avoids the YAGNI trap of 5+ phases of API scope work with no UI consumer
- Total diff: ~40 lines changed, ~160 lines deleted. Net: -120 lines

**Why it might be worse:**
- API scope work remains deferred indefinitely, accumulating as technical debt
- No unified abstraction means future API scope work (when dashboard needs it) will require understanding the same ad-hoc patterns
- The singleton trap remains unfixed — if someone adds user scope to the API without the master plan's Phase 4B first, the silent bug returns

**Honest assessment:** Alternative A fixes the user-facing bug now. The master plan's extra work (8 phases beyond the CLI fix) is justified ONLY if there's a firm commitment to ship the dashboard scope selector. Without that commitment, the master plan is building a platform for a feature that may never arrive.

### Alternative B: CLI fix + singleton fix only

Fix the CLI bug (Phase 4A), fix the singleton trap (Phase 4B), write the characterization tests (Phase 1), add DeploymentContext for cleanliness (Phase 2 + 3). Stop. Defer Phases 5–9.

**Net result:** The CLI scope bug is fixed. The API singleton trap is eliminated (proactively safe). The codebase has a clean `DeploymentContext` abstraction ready when the dashboard scope selector is needed. The dangerous parts of the plan (14+ API call sites, per-scope Socket.IO events) are not built until they're needed.

**This is likely the right answer.** It resolves the YAGNI objection while retaining the architectural improvement. The master plan should explicitly evaluate this option and either adopt it or explain why Phases 5–9 are needed now.

---

## 7. Verdict

### Overall Assessment: NEEDS REVISION

The plans are technically sound and methodologically thoughtful. The characterization-first testing approach is excellent. The phase ordering (singleton fix before scope addition) is correct. The detail level in the API and CLI plans is genuinely impressive.

However, there are three critical issues that must be addressed before implementation begins:

---

### Top 3 Concerns That MUST Be Addressed

#### MUST-1: Justify or eliminate Phases 5–9 (API scope)

The research-phase devil's advocate asked: "Who would use API user scope?" The planning team did not answer. Phases 5–9 represent the bulk of the implementation effort (API mutation scope, read scope, Socket.IO events, dashboard notes) and serve no currently existing user-facing feature.

**Required action:** Identify the concrete trigger for building API scope now. Is there a dashboard scope selector in the current sprint? An open GitHub issue? If no trigger exists, cut Phases 5–9 and add them to a backlog. The plan without Phases 5–9 is a cleaner, lower-risk, more defensible plan.

#### MUST-2: Fix the TC-0-04/TC-0-05 xfail contradiction

The test plan says TC-0-04 "is expected to FAIL after the Phase 2 fix." The master plan says TC-0-04 "now PASS (xfail markers removed)" after Phase 4A. These are contradictory. If the master plan is implemented as written, Phase 4A will fail CI because TC-0-04 asserts the broken behavior that Phase 4A just fixed.

**Required action:** Specify clearly: (a) what happens to TC-0-04 and TC-0-05 after the fix — are they deleted, updated with new assertions, or left as failing tests that document the behavior change? The master plan must pick one and be explicit.

#### MUST-3: Resolve the BackupManager user-scope backup failure

For user-scope operations, the backup captures the wrong directory (project-scope agents dir, not user-scope agents dir). The plan acknowledges this as a known limitation and adds a TODO comment. This is insufficient for a feature that advertises safety-protocol coverage.

**Required action:** Choose one of:
a) Extend BackupManager to accept scope (explicit fix, adds to Phase 4B scope)
b) Disable the backup step for user-scope operations (with a clear warning logged)
c) Document in the API response that user-scope operations have no backup/rollback support (user faces reduced safety guarantees)

Leaving it silently broken with a TODO comment is not acceptable for a safety-critical component.

---

### Top 3 Strengths of the Plan

#### Strength 1: Singleton fix gated before scope addition

Phase 4B (eliminate `_agent_manager` singleton) is correctly placed before Phases 5–6 (add scope to API endpoints). The research devil's advocate flagged the singleton as "worse than acknowledged." The plans took this seriously and made it a safety gate. This is the right call.

#### Strength 2: Characterization-first test methodology

Phase 1 (write tests that characterize current behavior before any production code change) is the correct approach for refactoring untested code. The fixture design (`project_scope_dirs`, `user_scope_dirs`, `both_scopes`) is clean and composable. The use of `xfail(strict=True)` to document known-broken behavior is exactly right.

#### Strength 3: DeploymentContext design is clean

The frozen dataclass with pure property accessors that delegate to existing `config_scope.py` resolvers is the right abstraction. It's immutable (thread-safe for async handlers), testable without mocking, and small (65 lines). The "fourth resolver" concern is legitimate but the counter (delete two others, net -1) is also legitimate. The design itself is not the problem — the scope of what's built around it is.

---

## Summary Table

| Concern | Status | Blocking? |
|---------|--------|-----------|
| Prior concern 1: Abstraction needed? | Partially addressed | No |
| Prior concern 4: YAGNI on API scope | **Not addressed** | **YES — MUST-1** |
| Prior concern 5: CLI scope intent? | Not addressed | Moderate |
| Prior concern 9: State model mismatch | Not addressed | No (DeploymentContext avoids it) |
| Gap 1: xfail contradiction | **Critical bug in plan** | **YES — MUST-2** |
| Gap 2: BackupManager wrong directory | **Safety protocol hole** | **YES — MUST-3** |
| Gap 3: `from_user()` stores irrelevant project_path | Design smell | No |
| Gap 4: Concurrent singleton init race | Missing risk | No (GIL makes it unlikely) |
| Gap 5: AgentManager missing dir behavior unverified | Missing verification step | Moderate |
| Gap 6: TC-3-22 contradicts autoconfig 400 decision | Test bug | Moderate |
| Gap 7: Phase 7 has no task breakdown | Underspecification | No |
| Sequencing 1: Phase 7 should gate Phase 4A | Ordering risk | Moderate |
| Sequencing 3: Phase 8 dependency wrong in text | Documentation error | No |
| Test weakness 1: xfail contradiction | Same as Gap 1 | **YES** |
| Test weakness 2: No backup behavior test | Coverage gap | Moderate |
| Missing risk: `scope: null` backward compat | Unacknowledged risk | Moderate |
