
When using the CLI to configure agents and skills via the 'claude-mpm configure' command we are able to deploy and undeploy agents and skills.
This happens using the user or project scope, with the project scope being active by default. 
user scope allows modification of deployed agents and skills in the ~/.claude/agents and ~/.claude/skills directory. 
project scope allows modification of deployed agents and skills in the .claude/agents and .claude/skills directories within the project directory. 

Currently, we have two different code paths which allow configuration of agents and skills:
 1) CLI path - using the 'claude-mpm configure' command to deploy and undeploy agents and skills in either user or project scope. 
 2) API path - using the /config endpoints in the API, which require the project scope.

We need an abstraction which will allow us to unify these two code paths and provide a reusable code path for configuration of agents and skills, using specified scope.

Goals:
  - CLI path functionality must remain unaffected. Any changes should not break the existing CLI configuration process.
  - API path functionality must be able to select and utilize the project scope for configuration of agents and skills. The current API path implementation assumes operation using project scope only.
  - Test case coverage for both CLI and API paths should be maintained or improved to ensure reliability of the configuration process across both CLI and API paths.

Create an agent team to explore this from different angles: teammates to research specific angles (e.g. one to research cli path, one to research api path, one to research abstraction aspects, one on test relevance, one on implementation strategies, one to understand how the dashboard config process interacts with the backend). one teammate to play devil's advocate.
Write findings to docs-local/agent_skill_scope_selection/research/ for my review. 

---

Ignore the prior question, removing the "unused" archive feature is out of scope.
Next step is to create a comprehensive phased implementation plan based on the research findings in docs-local/agent_skill_scope_selection/research/ . 
The docs-local/agent_skill_scope_selection/research/implementation-strategies.md provides a starting point. 
Create an agent team to create a detailed implementation plan that includes:
  - Specific tasks and milestones for both CLI and API paths.
  - Clear delineation of responsibilities among team members.
  - Test case development and integration into the existing testing framework.
One teammate to play devil's advocate 
Write phased plan files to docs-local/agent_skill_scope_selection/plans/ for my review.

----

Answers to "Top 3 Concerns That MUST Be Addressed"

MUST-1: Justify or eliminate Phases 5–9 (API scope)
For now, we need the dashboard UI to specify the project scope for API operations. 
This should be done in such a way as to permit future extension to user scope if we choose to implement it later. 

MUST-2: Fix the TC-0-04/TC-0-05 xfail contradiction
Delete TC-0-04 and TC-0-05 after the fix

MUST-3: Resolve the BackupManager user-scope backup failure
Extend BackupManager to accept scope

----

Implement the scope-aware agent & skill deployment abstraction as specified in
docs-local/agent_skill_scope_selection/plans/master-plan-v2.md

This plan has 7 phases (plus Phase 4A/4B parallel):
Phase 1: Test Foundation (characterization tests + fixtures)
Phase 2: DeploymentContext Core (new frozen dataclass)
Phase 3: CLI Config Path Wire (zero behavior change refactor)
Phase 4A: CLI Bug Fix (parallel with 4B)
Phase 4B: API Singleton Fix + BackupManager scope extension (parallel with 4A)
Phase 5: API Mutation Endpoints get scope param (project-only validation)
Phase 6: API Read-Only Endpoints get scope param
Phase 7: Code Cleanup + E2E Integration Tests

Supporting plan docs (read these for detailed task specs):
- docs-local/agent_skill_scope_selection/plans/cli-path-plan.md
- docs-local/agent_skill_scope_selection/plans/api-path-plan.md
- docs-local/agent_skill_scope_selection/plans/test-plan.md
- docs-local/agent_skill_scope_selection/plans/decisions-log.md

Research docs (for context on design decisions):
- docs-local/agent_skill_scope_selection/research/ (7 files)

Create an agent team with these teammates:
1. "test-engineer" (Python Engineer) — Owns Phase 1 (characterization tests + fixtures) and all test tasks in subsequent phases. Reads test-plan.md for detailed test case specs.
2. "core-engineer" (Python Engineer) — Owns Phase 2 (DeploymentContext dataclass). Reads implementation-strategies.md research for design context.
3. "cli-engineer" (Python Engineer) — Owns Phase 3 (CLI config wire) and Phase 4A (CLI bug fix). Also owns Phase 7 code cleanup (delete configure_paths.py and path_resolver.py). Reads cli-path-plan.md for detailed task specs.
4. "api-engineer" (Python Engineer) — Owns Phase 4B (singleton fix + BackupManager scope), Phase 5 (mutation endpoints), and Phase 6 (read endpoints). Reads api-path-plan.md for detailed task specs.
5. "qa-engineer" (QA) — Reviews each phase after completion. Runs full test suite between phases. Validates backward compatibility. Owns Phase 7 E2E integration tests.
6. "devil-advocate" — Reviews all plans and implementations with a critical eye. Challenges assumptions. Ensures edge cases are considered. Validates that the implementation is as simple as possible while meeting requirements.

Execution rules:
- Each phase MUST be committed separately (independently mergeable)
- Run pytest after each phase — CI must be green before starting the next phase. Ignore existing test failures that are unrelated to the current phase.
- Phases 1 → 2 → 3 are strictly sequential
- Phases 4A and 4B are the ONLY parallel phases
- Phase 5 depends on 4B; Phase 7 depends on 4A + 6
- Delete TC-0-04 and TC-0-05 in Phase 4A (per decisions-log.md MUST-2)
- BackupManager must accept scope in Phase 4B (per MUST-3)
- API scope param accepts only "project" this iteration; "user" returns HTTP 400 (per MUST-1)

Start by having all teammates read master-plan-v2.md and their respective detail plans,
then begin Phase 1 with test-engineer.
