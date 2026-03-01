# Decisions Log: Scope-Aware Agent & Skill Deployment

**Date:** 2026-02-28
**Branch:** agent_skill_scope_selection
**Context:** Three MUST-level issues were raised by the devil's advocate review
(`docs-local/agent_skill_scope_selection/plans/devils-advocate-review.md`, Section 7).
The project owner reviewed those issues and made the following binding decisions.

---

## MUST-1: API Scope Phases — SCOPED DOWN

### Issue

The devil's advocate flagged that Phases 5–9 of the master plan (API mutation scope, API read
scope, Socket.IO events, dashboard notes) represent the majority of the implementation effort and
serve no currently existing user-facing feature. The dashboard has no scope selector UI. Building
full dual-scope API support now is YAGNI.

### Decision

**Scope down the API work: implement project-scope-only with an explicitly extensible design.**

Specifically:

- API endpoints get a `scope` parameter that accepts `"project"` and validates it (rejects
  everything else with HTTP 400).
- `DeploymentContext` and API handlers are designed to be scope-extensible — the enum-based
  routing structure is there, but user-scope file paths, user-scope manager instances, and
  user-scope Socket.IO event routing are NOT wired up in this iteration.
- The dashboard sends `scope: "project"` explicitly in all requests rather than relying on
  server-side hardcoding. This makes the scope contract explicit at the call site and prepares
  the dashboard for the future moment when it needs to send `scope: "user"`.
- All read endpoints accept `?scope=project` query param (validated, project-only).

### What is deferred

- User-scope file path resolution in API handlers.
- Per-scope `_agent_managers` dict (only project-scope manager is wired; dict structure is in
  place but user-scope branch is not exercised).
- User-scope Socket.IO event routing.
- Dashboard-integration-notes.md (not needed until dashboard scope selector is planned).
- Full Phase 4 (API read scope for user-scope dirs) and Phase 5 (Socket.IO scope events) as
  originally specified in the master plan.

### Impact on master plan

- API phases are trimmed: keep DeploymentContext (Phase 0/1), keep singleton fix for project-scope
  safety (Phase 2), add `scope` parameter validation to mutation endpoints (Phase 3, project-only),
  add `scope` parameter validation to read endpoints (Phase 4, project-only).
- Estimated API work reduces by roughly 40% (no user-scope wiring, no event routing changes,
  no dashboard notes document to produce).
- Risk register entries for user-scope directory existence, user-scope manager initialization, and
  user-scope backup coverage are deferred — they move to a future "enable user-scope API" task.

---

## MUST-2: xfail Test Contradiction — RESOLVED

### Issue

The devil's advocate identified a direct contradiction between the test plan and the master plan
regarding TC-0-04 and TC-0-05:

- **test-plan.md** says TC-0-04 and TC-0-05 "are expected to FAIL after the Phase 2 fix" (because
  the assertions document the broken behavior).
- **master-plan.md** (Phase 4A) says "Formerly-XFAIL tests TC-0-04, TC-0-05 now PASS (xfail
  markers removed)."

These are contradictory: the assertions check broken behavior, so after the fix the tests would
fail, not pass.

### Decision

**Delete TC-0-04 and TC-0-05 after the CLI scope fix lands in Phase 4A.**

The characterization tests serve their purpose during Phases 1–3: they are written before any
code changes and committed as a snapshot of the known-broken behavior, marked `xfail(strict=True)`
so CI tracks them. When Phase 4A lands and the CLI scope bug is fixed, TC-0-04 and TC-0-05 are
deleted in the same PR. The new-behavior tests (TC-2-01 through TC-2-06) replace them as the
regression anchors for correct scope behavior.

There is no attempt to update TC-0-04/TC-0-05 assertions — they are characterization tests whose
job is done once the behavior they documented no longer exists. Delete them cleanly.

### Impact on master plan

- Phase 4A deliverables now explicitly include: delete TC-0-04 and TC-0-05.
- The CI gate for Phase 4A is: TC-2-01 and TC-2-02 pass (new behavior confirmed), TC-0-04 and
  TC-0-05 are absent from the test suite (no longer needed).
- Removes the ambiguity about xfail marker handling from the master plan.

---

## MUST-3: BackupManager Scope — EXTEND

### Issue

The devil's advocate identified that `BackupManager` always backs up the project-scope agents
directory (`{cwd}/.claude/agents/`), even during user-scope operations. For a user-scope deploy,
the backup captures an unrelated directory. If the user-scope operation fails after backup creation,
the backup is useless for recovery. The original plan left this as a TODO comment.

### Decision

**Extend BackupManager to accept a `scope` parameter (or a `backup_dir` override) so it backs up
the correct directory for the given scope.**

This is needed even for project-scope-only API work (the current iteration) because:

1. It eliminates the silent architectural error before it can ever be triggered.
2. The fix is small and localized to `backup_manager.py`.
3. Keeping the TODO and shipping with broken backup semantics is not acceptable for a
   safety-critical component.

The implementation adds a `scope` parameter (or `agents_dir` override) to
`BackupManager.__init__()` or the backup call site in the deployment handler, so that when scope
is resolved at the handler level, the correct directory is passed to BackupManager. For the current
(project-scope-only) iteration, the behavioral difference is zero — project-scope handlers already
resolve the project agents directory. But the wiring is explicit rather than accidental.

### Impact on master plan

- A BackupManager scope extension task is added to Phase 3 (alongside the mutation endpoint scope
  changes, since both touch `agent_deployment_handler.py`).
- The "Cross-Cutting Concerns / BackupManager" section in the API path plan is superseded: the
  TODO comment approach is rejected.
- The risk register entry "user-scope backup not implemented" is resolved and removed.
- Test plan gains a test verifying that `BackupManager` is called with the scope-resolved directory
  (not the hardcoded project directory) for each mutation handler.

---

## Summary

| MUST | Decision | Phase impact |
|------|----------|-------------|
| MUST-1: API scope | Project-scope-only; extensible design; user-scope wiring deferred | Phases 5–9 cut or deferred; Phase 3–4 trimmed to validation-only |
| MUST-2: xfail tests | Delete TC-0-04 + TC-0-05 when CLI fix lands in Phase 4A | Phase 4A explicitly deletes two tests |
| MUST-3: BackupManager | Extend to accept scope; wire correct dir at handler level | New task in Phase 3 (or as a sub-task of Phase 4B) |
