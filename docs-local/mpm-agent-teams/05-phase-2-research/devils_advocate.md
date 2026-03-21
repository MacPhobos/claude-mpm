# Devil's Advocate: Phase 2 Research Plan

**Date:** 2026-03-20
**Subject:** Is this research plan asking the right questions? Will the answers be actionable?

---

## Concern 1: The Worktree Question May Already Be Answered

**The plan assumes** worktree behavior needs investigation (RQ1). But MPM already uses `isolation: "worktree"` for parallel agents. PM_INSTRUCTIONS.md lines 118-148 describe worktree isolation in detail. The PM already spawns parallel Engineers in worktrees via `run_in_background` + `isolation: "worktree"` — this is not new to Agent Teams.

**What's actually new with Agent Teams:** Teammates share a task list, can SendMessage each other, and have structured completion events. The worktree mechanics are IDENTICAL whether spawning via standard Agent tool or Agent Teams. Claude Code creates the worktree the same way regardless.

**Risk of wasted effort:** RQ1 may spend 0.5 days re-discovering what the codebase already documents. The real question isn't "how do worktrees work" — it's "how does merge work when BOTH agents are teammates in the same team session?"

**Amendment (if warranted):** Narrow RQ1 from "how do worktrees work" to "what is the merge path when Agent Teams teammates use worktrees?" Focus on the delta, not the baseline.

**Verdict: PARTIALLY HOLDS.** The baseline worktree investigation is redundant. The merge-path-specific investigation is not. Narrow the scope.

---

## Concern 2: RQ4 (Team Compositions) Is Premature Design

**The plan asks** "what team compositions make sense?" (RQ4) as a research question. But this is a design decision, not a research finding. You can't "discover" the right team compositions by reading code — you choose them based on user needs and engineering constraints.

**The real research questions are:**
- What do users actually want? (Issue #290 says: "Frontend + backend + test coordinating simultaneously" and "Multiple engineers working on different subsystems")
- What does the platform support? (Can teammates in different roles share context?)
- What breaks when you try compositions X, Y, Z? (Experimental, not analytical)

RQ4 as written will produce a taxonomy document that looks comprehensive but is actually just someone's opinion about which compositions are "valid." The taxonomy will need to be revised after RQ1-3 findings anyway.

**Amendment (if warranted):** Replace RQ4 with "RQ4: User Demand Analysis" — review issue #290 comments, MPM user feedback (if any), and the original devil's advocate Concern 7 to determine which 2-3 compositions users actually need. Design the top 2-3 compositions rather than enumerating all possibilities.

**Verdict: PARTIALLY HOLDS.** Narrowing to user-demanded compositions avoids analysis paralysis.

---

## Concern 3: RQ7 (SendMessage) May Be Investigating a Non-Problem

**The plan asks** whether teammates should coordinate via SendMessage or through the PM. But Phase 1 Rule 5 already prohibits peer delegation. The devil's advocate in Phase 0 and Phase 1 both concluded that peer coordination is a risk vector, not a feature.

**For Phase 2 Engineering:** Does Engineer A actually NEED to tell Engineer B about an interface change? In worktree-isolated development, each Engineer works independently. Interface contracts should be defined BEFORE spawning (by the PM's task decomposition), not discovered MID-task via SendMessage.

**If we allow peer SendMessage for Engineers:**
- Engineers coordinate interface changes in real-time (value)
- Engineers delegate subtasks to each other (violation of Rule 5)
- PM loses visibility into what was communicated (audit gap)
- Shadow workflows emerge (Phase 0 Concern)

**If we keep Rule 5 (no peer coordination):**
- Each Engineer works independently in their worktree
- Interface mismatches surface at merge/integration time
- PM maintains full control and visibility
- Slower but safer

**The question "should we relax Rule 5?" has a clear answer: No, not in Phase 2.** Phase 2's goal is to prove parallel Engineering works with the existing coordination model. Relaxing Rule 5 adds a second variable to an already complex experiment.

**Amendment (if warranted):** Downgrade RQ7 from a full investigation to a brief note: "Phase 2 maintains Rule 5 (no peer delegation). SendMessage coordination is deferred to Phase 3 pending Phase 2 results." Reallocate the 0.5 days to RQ2 (file conflicts), which is the actual hard problem.

**Verdict: HOLDS.** Don't investigate what you've already decided not to change. Keep Rule 5, focus effort on merge conflicts.

---

## Concern 4: The Dependency Chain Is Overfit

**The plan orders** RQs in a specific dependency chain: RQ1 → RQ2 → RQ3, with RQ4-8 feeding into the final synthesis. This looks rigorous but creates a serial bottleneck.

**The problem:** If RQ1 (worktree experiment) takes longer than 0.5 days (experiments always do), everything downstream shifts. RQ2 waits on RQ1. RQ3 waits on RQ2. The "3 days wall-clock" becomes 5.

**What can actually run in parallel:**
- RQ1 (worktree experiment) and RQ2 (conflict analysis) can overlap — you don't need complete worktree findings to start analyzing conflict scenarios theoretically
- RQ6 (protocol extensions) is truly independent
- RQ8 (rollback) is mostly design, with a small experiment component

**Amendment (if warranted):** Flatten the dependency chain. Run RQ1 + RQ2 as a single combined investigation ("Worktree Isolation and Merge Conflicts"). The experiment covers both. This eliminates one serialization point and produces one integrated findings doc instead of two.

**Verdict: PARTIALLY HOLDS.** Merging RQ1+RQ2 removes artificial serialization.

---

## Concern 5: Missing Research Question — "What Does PM Already Do?"

**The plan investigates** new capabilities but doesn't investigate what the PM already does for parallel Engineering WITHOUT Agent Teams.

**Current state:** The PM already spawns parallel Engineers using `run_in_background: true` + `isolation: "worktree"`. This works TODAY. The PM collects results via task notifications, merges worktrees manually (or delegates to Version Control agent), and runs integration tests.

**The question the plan doesn't ask:** "What specific problems does the current parallel Engineering pattern have, and does Agent Teams solve them?" If the current pattern works well enough, Phase 2's value proposition shrinks to:
- Structured completion notifications (nice, not essential)
- Teammate idle events (nice, not essential)
- PM context reduction (measured in Phase 1.5 Gate 2)

**This is exactly the same concern the Phase 1 devil's advocate raised about Research (Concern 3: "Is Parallel Research Actually Valuable?").** The answer for Research was: incremental value is real but narrow. The answer for Engineering may be the same.

**Amendment (if warranted):** Add RQ0: "Baseline Analysis — How does parallel Engineering work today without Agent Teams, and what are its pain points?" This provides the baseline against which Phase 2's value is measured. Without it, Phase 2 risks building a solution to a problem that's already solved.

**Verdict: HOLDS.** This is the most important missing question. Add it.

---

## Concern 6: 4-5 Days of Research Before Implementation Is Expensive

**The plan estimates** 4-5 days of research producing 9 documents before any implementation begins. For a feature that the Phase 1 devil's advocate described as "the real value" (Concern 7), spending 4-5 days researching before doing anything is risk-averse to the point of being counterproductive.

**Alternative approach:** Spike-first.
1. Day 1: Run the 2-Engineer worktree experiment (RQ1+RQ2 combined). Observe merge behavior.
2. Day 1 results determine the entire Phase 2 approach:
   - If merge works cleanly → Phase 2 is mostly PM instruction changes + protocol extensions
   - If merge fails badly → Phase 2 needs a merge coordination layer (significant engineering)
   - If merge is manual but manageable → Phase 2 adds PM merge delegation instructions
3. Days 2-3: Write the implementation plan based on spike findings. Skip theoretical analysis (RQ3-RQ5) and do just-in-time design during implementation.

**The 2-Engineer experiment is the critical path.** Everything else is secondary analysis that can happen during implementation rather than before it. 4-5 days of research documents is planning theater if the spike reveals that worktree merge is either trivial or impossible.

**Amendment (if warranted):** Restructure as "1-day spike + 1-day plan" instead of "4-5 days research + implementation later." The spike produces the one finding that matters: does worktree merge work for parallel Engineering?

**Verdict: PARTIALLY HOLDS.** The spike-first approach is more efficient, but some RQs (RQ6 protocol extensions, RQ8 rollback) are genuinely needed before implementation. Compress to "2-day spike-and-plan" instead of 4-5 day research program.

---

## Summary

| # | Concern | Severity | Amendment Needed? |
|---|---------|----------|:-:|
| 1 | RQ1 worktree investigation is partially redundant | LOW | Narrow scope to merge path only |
| 2 | RQ4 team compositions is premature design | MEDIUM | Narrow to user-demanded compositions |
| 3 | RQ7 SendMessage is a non-problem for Phase 2 | MEDIUM | Downgrade to brief note, keep Rule 5 |
| 4 | Dependency chain is overfit | LOW | Merge RQ1+RQ2 into single investigation |
| 5 | Missing: baseline analysis of current parallel Engineering | HIGH | Add RQ0 |
| 6 | 4-5 days research is expensive for spike-answerable question | MEDIUM | Consider spike-first approach |

### Recommended Amendments

**Must-do:**
- Add RQ0: "Baseline — how does parallel Engineering work today without Agent Teams?"

**Should-do:**
- Merge RQ1+RQ2 into a single worktree/merge investigation
- Narrow RQ4 to user-demanded compositions (2-3 patterns, not a taxonomy)
- Downgrade RQ7 to a brief note: "Rule 5 maintained in Phase 2"

**Consider:**
- Restructure from "4-5 day research" to "2-day spike-and-plan" if you want faster iteration
