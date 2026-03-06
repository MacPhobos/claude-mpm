# Devil's Advocate Resolution: Challenging the "Name Field is Primary" Hypothesis

**Date**: 2026-03-04
**Status**: Complete
**Scope**: Counter-analysis of unified-analysis.md Section 5 hypothesis
**Method**: Code-evidence-based adversarial review

---

## Executive Summary

The unified analysis (Section 5) asserts that Claude Code resolves `subagent_type` primarily via the YAML frontmatter `name:` field, making filename renames "safe" and "cosmetic." This devil's advocate analysis finds **the hypothesis is partially correct but dangerously incomplete**. While `name:` does flow into the PM system prompt as the agent ID, there are at least **four independent subsystems that use filename stems directly**, **five name-collision pairs that make name-based resolution ambiguous**, and a **critical black-box gap** where Claude Code's internal agent file selection mechanism remains empirically unvalidated. The "safe rename" conclusion requires significant qualification.

**Verdict**: The hypothesis correctly identifies ONE resolution pathway but incorrectly generalizes it to the ENTIRE system. Renaming files carries real risk in template routing, capabilities service discovery, hardcoded hook comparisons, and potentially Claude Code's own internal file matching.

---

## Table of Contents

1. [Counter-Argument 1: Two Competing Discovery Paths](#1-two-competing-discovery-paths)
2. [Counter-Argument 2: Template Routing Uses Stems, Not Names](#2-template-routing-uses-stems-not-names)
3. [Counter-Argument 3: Name Collision Pairs Create Ambiguity](#3-name-collision-pairs-create-ambiguity)
4. [Counter-Argument 4: Hardcoded String Comparisons Across Hooks](#4-hardcoded-string-comparisons-across-hooks)
5. [Counter-Argument 5: The Black Box Problem](#5-the-black-box-problem)
6. [Counter-Argument 6: Fallback Capabilities Reveal Inconsistency](#6-fallback-capabilities-reveal-inconsistency)
7. [Counter-Argument 7: Pre-existing Naming Chaos](#7-pre-existing-naming-chaos)
8. [Counter-Argument 8: The Normalization Stack Masks Problems](#8-the-normalization-stack-masks-problems)
9. [Worst-Case Scenarios](#9-worst-case-scenarios)
10. [What the Hypothesis Gets RIGHT](#10-what-the-hypothesis-gets-right)
11. [What the Hypothesis Gets WRONG or Overlooks](#11-what-the-hypothesis-gets-wrong-or-overlooks)
12. [Remaining Risks Even if Hypothesis is Correct](#12-remaining-risks-even-if-hypothesis-is-correct)
13. [Recommendations for Additional Testing](#13-recommendations-for-additional-testing)

---

## 1. Two Competing Discovery Paths

### The Claim Being Challenged
The unified analysis treats agent discovery as a single pipeline flowing through `CapabilityGenerator.parse_agent_metadata()`, where `name:` overrides the stem-based default ID.

### The Counter-Evidence

There are **two independent agent discovery systems** that produce **different IDs for the same agent files**:

**Path A: CapabilityGenerator (PM prompt generation)**
```python
# capability_generator.py, lines 161-177
agent_data = {
    "id": agent_file.stem,           # Default: filename stem
    ...
}
# Later overridden:
agent_data["id"] = metadata.get("name", agent_data["id"])  # name: field wins
```

**Path B: AgentCapabilitiesService (capabilities discovery)**
```python
# agent_capabilities_service.py, lines 224-248
agent_id = agent_file.stem           # Uses raw stem DIRECTLY
# ...
name = agent_id.replace("-", " ").replace("_", " ").title()  # Derives name FROM stem
# ...
discovered_agents[agent_id] = {
    "id": agent_id,                  # Stem IS the ID. No frontmatter parsing.
    "name": name,                    # Derived from stem, NOT from name: field
    ...
}
```

**Critical difference**: Path B at line 224 sets `agent_id = agent_file.stem` and NEVER reads the YAML frontmatter `name:` field. It attempts to extract a display name from `# ` headers or `Description:` lines (lines 235-242), but not from YAML frontmatter at all.

### Impact Assessment
If you rename `research.md` to `research_agent.md`, Path A continues to show "Research" in the PM prompt (because `name: Research` is unchanged), but Path B would now report the agent as `research_agent` instead of `research`. Any downstream consumer of `AgentCapabilitiesService` would see a different agent ID than what the PM prompt shows.

**Severity**: HIGH -- this is not theoretical. Both paths are active in the running system.

---

## 2. Template Routing Uses Stems, Not Names

### The Claim Being Challenged
The hypothesis implies that since `name:` is the primary identifier, filename changes are "cosmetic."

### The Counter-Evidence

Both template loading functions in `capability_generator.py` receive `agent_file.stem` as their argument -- NOT the `name:` field:

```python
# capability_generator.py, lines 190-199
if "routing" not in agent_data:
    routing_data = self.load_routing_from_template(agent_file.stem)  # <-- STEM
    ...

if "memory_routing" not in agent_data:
    memory_routing_data = self.load_memory_routing_from_template(
        agent_file.stem                                               # <-- STEM
    )
```

The template lookup then searches for `{agent_file.stem}.json` in the templates directory:

```python
# capability_generator.py, line 228/244
template_file = templates_package / f"{agent_name}.json"  # agent_name = stem
```

Similarly, `framework_loader.py` line 299:
```python
template_data = self.template_processor.load_template(agent_file.stem)
```

While the template functions do have fallback logic that tries variations (replacing `-` with `_`, stripping `-agent` suffix, etc.), these fallbacks are fragile string transformations, not semantic resolution.

### Impact Assessment
Renaming `research.md` to `research_agent.md` would cause `load_routing_from_template("research_agent")` to look for `research_agent.json`. If only `research.json` exists, the primary lookup fails. The fallback logic at lines 251-267 would try `research-agent`, `researchagent`, `research_agent` -- but NOT `research` (the original stem stripped of the added suffix). The routing data would be LOST unless you also rename the template file.

For `load_memory_routing_from_template`, the fallback logic is slightly different (lines 317-335) and includes stripping `-agent`/`_agent` suffixes and adding them. So renaming FROM `research` TO `research_agent` MIGHT be caught by the reverse strip (`research_agent` -> strip `_agent` -> `research`), but this depends on exact implementation details of the set operations.

**Severity**: MEDIUM-HIGH -- template routing breakage would silently degrade agent capabilities without error messages.

---

## 3. Name Collision Pairs Create Ambiguity

### The Claim Being Challenged
The hypothesis assumes that `name:` values provide unambiguous agent identification.

### The Counter-Evidence

The deployed agent directory (`.claude/agents/`) contains **5 collision pairs** where multiple filename stems map to the same `name:` value:

| name: Field Value | Filename Stems |
|---|---|
| `Documentation Agent` | `documentation-agent.md`, `documentation.md` |
| `Ops` | `ops-agent.md`, `ops.md` |
| `QA` | `qa-agent.md`, `qa.md` |
| `Research` | `research-agent.md`, `research.md` |
| `Web QA` | `web-qa-agent.md`, `web-qa.md` |

When both files in a collision pair are present and the PM prompt lists their shared `name:` value (e.g., "Research"), Claude Code must somehow resolve which `.md` file to load. The `name:` field CANNOT disambiguate because both files share the same value.

This means either:
1. Claude Code uses something OTHER than `name:` for final file selection (undermining the hypothesis), OR
2. Claude Code loads whichever file it encounters first (nondeterministic behavior), OR
3. One file in each pair shadows the other entirely (but which one?)

### Impact Assessment
The existence of these collision pairs proves that `name:` alone is insufficient for unambiguous agent resolution. If Claude Code does use `name:` as the primary mechanism, it would encounter ambiguity for 10 out of 53 deployed agents (18.9%). This is not a theoretical edge case -- it affects the core agents: Research, QA, Ops, and Documentation.

**Severity**: HIGH -- directly contradicts the "name is primary" hypothesis for nearly 1 in 5 agents.

---

## 4. Hardcoded String Comparisons Across Hooks

### The Claim Being Challenged
The hypothesis focuses on PM delegation routing as the primary concern. The implication is that other subsystems are unaffected by naming.

### The Counter-Evidence

Multiple hook and event handler files contain **hardcoded string literals** that compare against `subagent_type` values:

**tool_analysis.py (lines 84-86):**
```python
"is_pm_delegation": tool_input.get("subagent_type") == "pm",
"is_research_delegation": tool_input.get("subagent_type") == "research",
"is_engineer_delegation": tool_input.get("subagent_type") == "engineer",
```

**subagent_processor.py (lines 351-352):**
```python
"is_delegation_related": agent_type in [
    "research", "engineer", "pm", "ops", "qa", "documentation", "security"
],
```

**event_handlers.py (line 475):**
```python
if DEBUG or agent_type in ["research", "engineer", "qa", "documentation"]:
```

These comparisons use **lowercase bare names** (not `name:` field values like "Research" or "Engineer", and not stems like "research-agent"). They rely on normalization happening upstream, but the exact form of `subagent_type` as it arrives from Claude Code is unknown.

### Impact Assessment
If Claude Code sends `subagent_type` as the capitalized `name:` value (e.g., "Research"), these comparisons would ALL FAIL because `"Research" != "research"`. The event_handlers.py code at lines 420-439 does apply normalization (via `AgentNameNormalizer.to_task_format()` or fallback `lower().replace("_", "-")`), but this normalization is on the MPM side, not on the Claude Code side.

The critical question is: what exact string does Claude Code PUT into the `subagent_type` field? The hypothesis assumes it's the `name:` value, but these hardcoded comparisons assume it arrives as a lowercase bare word. These two assumptions cannot both be correct without normalization -- and the normalization layer is itself a source of potential failure.

**Severity**: MEDIUM -- these are observability/tracking features, not routing. But incorrect tracking leads to wrong dashboards, missed metrics, and incorrect delegation correlation.

---

## 5. The Black Box Problem

### The Claim Being Challenged
The unified analysis states (Section 5): "The pm-prompt-assembly.md analysis is based on reading the MPM source code and inferring Claude Code's behavior. It was not validated by empirically testing."

### The Counter-Evidence

The entire hypothesis chain is:

1. MPM generates PM system prompt containing agent ID (from `name:` field)
2. PM reads system prompt and delegates using that ID
3. Claude Code receives `subagent_type` value
4. Claude Code matches `subagent_type` to an agent `.md` file
5. Claude Code loads and executes the matched agent

MPM controls steps 1-2. The hypothesis is about step 1. But the CRITICAL step is **step 4** -- how Claude Code internally matches a `subagent_type` string to a physical `.md` file in `.claude/agents/`.

Possible resolution mechanisms Claude Code could use:
- **Exact filename match**: `subagent_type + ".md"` (stem-based)
- **Fuzzy filename match**: Normalize `subagent_type`, try variations
- **YAML frontmatter match**: Read all `.md` files, find one with matching `name:` field
- **LLM-based match**: Claude itself decides which file "sounds right" given the `subagent_type`
- **Registry/cache**: Maintain a lookup table built at startup

Without access to Claude Code's source or empirical testing, we cannot know which mechanism is used. The hypothesis ASSUMES frontmatter-based matching, but Claude Code is far more likely to use filename-based matching for performance reasons (reading and parsing YAML frontmatter in every `.md` file for each delegation would be expensive).

### Impact Assessment
If Claude Code uses filename-based matching (which is the simpler, more performant design), then the ENTIRE hypothesis is inverted:
- The filename stem IS the primary identifier
- The `name:` field is cosmetic (used only for display)
- Renaming files would BREAK resolution, not be "safe"

**Severity**: CRITICAL -- the hypothesis rests on an unvalidated assumption about Claude Code's internal behavior.

---

## 6. Fallback Capabilities Reveal Inconsistency

### The Claim Being Challenged
The hypothesis assumes a consistent naming convention flowing through the system.

### The Counter-Evidence

`capability_generator.py` lines 345-367 define `get_fallback_capabilities()` which is used when dynamic agent discovery fails. The hardcoded agent IDs in this fallback are **inconsistent**:

```
- **Engineer** (`engineer`):          bare name, no suffix
- **Research** (`research-agent`):    hyphen-suffix form
- **QA** (`qa-agent`):               hyphen-suffix form
- **Documentation** (`documentation-agent`):  hyphen-suffix form
- **Security** (`security-agent`):    hyphen-suffix form
- **Data Engineer** (`data-engineer`): hyphen-compound, no suffix
- **Ops** (`ops-agent`):             hyphen-suffix form
- **Version Control** (`version-control`):  hyphen-compound, no suffix
```

These fallback IDs mix two conventions:
1. Bare name: `engineer`, `data-engineer`, `version-control`
2. Name with `-agent` suffix: `research-agent`, `qa-agent`, `ops-agent`, etc.

If Claude Code receives `research-agent` as the `subagent_type` from these fallbacks, it must find a file. Both `research-agent.md` and `research.md` exist. Which one wins? The hypothesis does not address fallback-mode routing at all.

### Impact Assessment
The fallback capabilities section is the PM's guide when dynamic discovery fails. If the PM uses `research-agent` as the `subagent_type` (per the fallback instruction "Use the exact agent ID in parentheses"), Claude Code must resolve this to a file. This is a stem-like value, not a `name:` field value.

**Severity**: MEDIUM -- fallback mode should be rare, but when it activates, it uses stem-like IDs that contradict the "name is primary" hypothesis.

---

## 7. Pre-existing Naming Chaos

### The Claim Being Challenged
The hypothesis treats the current state as stable and analyzable. The "safe rename" recommendation implies the current naming is the only concern.

### The Counter-Evidence

The deployed `.claude/agents/` directory already contains mixed conventions:

**Underscore stems with hyphen names:**
- `nestjs_engineer.md` has `name: nestjs-engineer` (underscore in file, hyphen in name)

**Hyphen stems with underscore names:**
- `aws-ops.md` has `name: aws_ops_agent` (hyphen in file, underscore+suffix in name)

**Bare stems with suffixed names:**
- `ticketing.md` has `name: ticketing_agent` (bare stem, underscore suffix in name)

**Collision pairs (already documented above):**
- `research.md` AND `research-agent.md` both have `name: Research`
- `qa.md` AND `qa-agent.md` both have `name: QA`
- etc.

The system already lives with stem/name mismatches, and it works. This could mean:
1. The system is robust enough to handle mismatches (good), OR
2. The system is broken for these agents but nobody noticed because they're rarely used (bad), OR
3. One convention silently shadows the other (unpredictable)

### Impact Assessment
The pre-existing chaos means we cannot draw conclusions from "it works now" because we do not know IF it works correctly for the collision pairs. Has anyone tested that delegating to "Research" correctly loads `research.md` and not `research-agent.md`? Has anyone verified that `nestjs_engineer.md` is correctly resolved when the PM delegates to `nestjs-engineer`?

**Severity**: MEDIUM -- the existing state is not a reliable baseline for testing "safe" renames.

---

## 8. The Normalization Stack Masks Problems

### The Claim Being Challenged
The hypothesis implicitly assumes that normalization handles naming variations gracefully.

### The Counter-Evidence

There are **two competing normalization systems** in the codebase:

**AgentNameNormalizer** (`agent_name_normalizer.py`):
- Canonical form: **underscore-based** (e.g., `research_agent`)
- Used by: `event_handlers.py` line 429, response tracking

**AgentRegistry** (`agent_registry.py`):
- Canonical form: **hyphen-based** (e.g., `research-agent`)
- Used by: `agent_loader.py`, agent listing

The `event_handlers.py` code at line 427 comments: "Convert to Task format (lowercase with hyphens)" but calls `normalizer.to_task_format()` from `AgentNameNormalizer` which uses underscores. This is a contradiction in the code itself.

Additionally, `agent_loader.py` `get_agent_prompt()` (lines 740+) implements its OWN normalization:
```python
# Tries: exact match, _agent suffix, strip _agent, clean("-" -> "_", " " -> "_")
# Then falls back to CANONICAL_NAMES and ALIASES from agent_name_normalizer
```

This triple-normalization stack (AgentNameNormalizer, AgentRegistry, and agent_loader inline logic) means that ANY value can potentially resolve to ANY agent through a long chain of transformations. This makes the system resilient but also unpredictable -- you cannot determine which agent will be loaded from a given `subagent_type` without tracing through all three normalization layers.

### Impact Assessment
The normalization stack is a coping mechanism for the naming inconsistency. It makes things "work" but at the cost of predictability. A rename that the hypothesis claims is "safe" could interact with normalization in unexpected ways -- especially if the rename changes a stem from one that matches a CANONICAL_NAME to one that does not.

**Severity**: MEDIUM -- normalization resilience may mask real problems that surface only in edge cases.

---

## 9. Worst-Case Scenarios

### Scenario A: Claude Code Uses Filename Matching (Probability: 40-60%)
**Trigger**: Rename `research.md` to `research_agent.md` while keeping `name: Research`
**Outcome**: Claude Code looks for `research.md`, cannot find it, delegation FAILS silently or falls back to default agent. The PM prompt still shows "Research" as available, but Claude Code cannot load the file.
**Impact**: Complete delegation failure for renamed agents.
**Detection difficulty**: HIGH -- the PM prompt looks correct, delegations appear to go through, but the wrong agent file (or no agent file) is loaded.

### Scenario B: Template Routing Breaks (Probability: 70-80%)
**Trigger**: Rename `research.md` to `research_agent.md`
**Outcome**: `load_routing_from_template("research_agent")` looks for `research_agent.json`. Only `research.json` exists. Fallback tries `research-agent`, `researchagent`, `research_agent` but NOT `research` (the original). Agent loses routing metadata silently.
**Impact**: Agent functions but without proper routing configuration, leading to degraded behavior.
**Detection difficulty**: HIGH -- no error is raised, the function returns `None` silently.

### Scenario C: Capabilities Service Reports Different Agent Set (Probability: 95%)
**Trigger**: Any filename rename
**Outcome**: `AgentCapabilitiesService._discover_agents_from_dir()` reports the NEW stem as the agent ID. PM prompt (via CapabilityGenerator) still shows the `name:` field. Dashboard and capabilities endpoint show different agent names than the PM prompt.
**Impact**: User confusion, incorrect dashboard data, mismatched agent listings.
**Detection difficulty**: LOW -- visible in dashboard/API responses, but easy to dismiss as "cosmetic."

### Scenario D: Normalization Cascade Failure (Probability: 10-20%)
**Trigger**: Rename to a form that doesn't match any CANONICAL_NAME or ALIAS
**Outcome**: `agent_loader.py` exhausts all normalization attempts (exact, suffix, strip, clean, canonical, alias) and fails to find the agent. Returns None or raises error.
**Impact**: Agent becomes unreachable through the agent loading system despite being physically present.
**Detection difficulty**: MEDIUM -- would show up as "agent not found" errors in logs.

### Scenario E: Collision Pair Confusion (Probability: 30-40%)
**Trigger**: Both `research.md` and `research-agent.md` exist with `name: Research`
**Outcome**: Claude Code receives `subagent_type=Research`. If it uses name-based matching, it finds TWO files with `name: Research`. Resolution is nondeterministic -- may load the wrong one, may load whichever is alphabetically first, may load the last one discovered.
**Impact**: Wrong agent file loaded, wrong system prompt used, potentially wrong tool set.
**Detection difficulty**: VERY HIGH -- the agent "works" but with the wrong configuration. Only detectable by inspecting which file was actually loaded.

---

## 10. What the Hypothesis Gets RIGHT

To be fair, the hypothesis correctly identifies several important truths:

1. **The PM prompt assembly chain does use `name:` field**: `capability_generator.py` line 177 clearly shows `agent_data["id"] = metadata.get("name", agent_data["id"])`. The PM sees agent IDs derived from `name:`, not from stems. This is factually correct.

2. **The PM is the primary delegation interface**: Since Claude Code's delegation flows through the PM (via Task tool), the PM prompt IS the most important context for how `subagent_type` gets populated. The PM reads the capabilities section and uses those IDs.

3. **The `name:` field is present in all 53 agents**: There are no agents missing the `name:` field, so the hypothesis applies universally to the PM prompt generation path.

4. **MPM's hook system does normalize values**: The `event_handlers.py` normalization at lines 420-439 does process `subagent_type` before most downstream use, providing some resilience.

5. **The general direction is sound**: For PM delegation routing specifically, `name:` IS more important than the filename stem. The hypothesis is correct in identifying the PM-facing resolution mechanism.

---

## 11. What the Hypothesis Gets WRONG or Overlooks

1. **Overgeneralization**: The hypothesis identifies ONE resolution path (PM prompt -> CapabilityGenerator -> name: field) and incorrectly extrapolates to "the system." There are at least four other subsystems that use filename stems: AgentCapabilitiesService, template routing, framework_loader template processing, and get_deployed_agents().

2. **Ignoring the Claude Code black box**: The hypothesis makes claims about Claude Code's behavior based on what MPM feeds it, without validating how Claude Code actually uses that input. Step 4 of the chain (Claude Code matches subagent_type to a file) is completely unvalidated.

3. **Missing the collision problem**: Five collision pairs exist where `name:` values are duplicated. The hypothesis does not address how Claude Code resolves ambiguity when two files share the same `name:` value.

4. **Dismissing template routing**: The hypothesis calls filename renames "cosmetic" but template routing uses stems directly. This is not cosmetic -- it affects agent capabilities, routing metadata, and memory routing.

5. **Not addressing the capabilities service path**: `AgentCapabilitiesService` is a separate discovery system that ignores `name:` entirely. Its output feeds the dashboard, API endpoints, and agent management features.

6. **Underestimating hardcoded comparisons**: Multiple files contain hardcoded string lists for delegation tracking. While these are "just" observability features, incorrect tracking leads to incorrect monitoring, which leads to incorrect operational decisions.

7. **Ignoring the dual-normalization problem**: Two competing normalizers (underscore-canonical vs. hyphen-canonical) create an unpredictable resolution chain that the hypothesis does not account for.

8. **The "safe rename" conclusion is not safe**: Even if PM delegation continues to work after a filename rename (which is plausible), template routing, capabilities service, dashboard reporting, and potentially Claude Code's own internal matching could all break.

---

## 12. Remaining Risks Even if Hypothesis is Correct

Even accepting that `name:` IS the primary resolution mechanism for PM delegation, the following risks remain:

1. **Template files must be renamed in sync**: Any filename rename requires corresponding template JSON file renames. The hypothesis does not mention this dependency.

2. **AgentCapabilitiesService will report wrong IDs**: This service uses stems. Dashboard and API endpoints will show different agent names than the PM prompt until this service is updated.

3. **Collision pairs remain dangerous**: Even if `name:` is primary, the 5 collision pairs create ambiguity that no amount of renaming can fix without also deduplicating the `name:` values.

4. **Hardcoded strings need updating**: The hardcoded string lists in tool_analysis.py, subagent_processor.py, and event_handlers.py would need to be updated if agent naming changes, or replaced with dynamic lookups.

5. **Fallback capabilities are inconsistent**: The get_fallback_capabilities() function uses a mix of bare names and `-agent` suffixed names. If the PM falls back to these, the `subagent_type` values sent to Claude Code will not match the `name:` field convention.

6. **Response tracking may break**: `response_tracker.py` uses `agent_name` for file naming. If the name flowing through changes due to a rename, historical response files may become disconnected from current delegations.

7. **CANONICAL_NAMES and ALIASES tables**: If filenames are renamed, the normalization tables in `agent_name_normalizer.py` must be updated. The hypothesis does not mention this maintenance burden.

---

## 13. Recommendations for Additional Testing

### Empirical Validation Required

The following experiments would resolve the key uncertainties:

#### Test 1: Claude Code's Resolution Mechanism (CRITICAL)
**Setup**: Create two agent files in `.claude/agents/`:
- `test_alpha.md` with `name: TestBeta`
- `test_beta.md` with `name: TestAlpha`

Note the SWAPPED names: the file named "alpha" has name "Beta" and vice versa.

**Action**: Ask the PM to delegate to "TestAlpha"

**Expected outcomes**:
- If Claude Code uses `name:` field: loads `test_beta.md` (which has `name: TestAlpha`)
- If Claude Code uses filename stem: loads `test_alpha.md` (which matches the stem)

**This single test resolves the core hypothesis.**

#### Test 2: Collision Resolution (HIGH PRIORITY)
**Setup**: Use the existing collision pair `research.md` and `research-agent.md` (both have `name: Research`).

**Action**: Delegate to "Research" via the PM. Inspect which file is actually loaded.

**Verification**: Add a unique marker to each file's system prompt (e.g., "MARKER_RESEARCH_BARE" vs "MARKER_RESEARCH_SUFFIXED") and check which marker appears in the agent's response.

#### Test 3: Template Routing After Rename (MEDIUM PRIORITY)
**Setup**: Rename `research.md` to `research_agent.md`. Keep `name: Research` unchanged. Keep `research.json` template unchanged.

**Action**: Delegate to "Research" and inspect whether routing metadata is present in the agent's capabilities.

**Verification**: Check logs for "Could not load routing" messages.

#### Test 4: Capabilities Service Consistency (MEDIUM PRIORITY)
**Setup**: After any filename rename, query both:
- The PM system prompt (capabilities section)
- The `/api/agents` endpoint (from AgentCapabilitiesService)

**Verification**: Compare agent IDs between the two sources. They should match but currently will not due to the dual discovery path.

#### Test 5: End-to-End Dashboard Accuracy (LOW PRIORITY)
**Setup**: Perform a delegation and track the agent name through:
1. PM prompt (capabilities section)
2. Claude Code's `subagent_type` (in tool_input)
3. event_handlers normalization output
4. response_tracker file naming
5. Dashboard display

**Verification**: All five should show consistent agent identification. Currently, they likely do not for collision-pair agents.

---

## Conclusion

The "name field is primary" hypothesis is a **useful partial truth** that correctly identifies the PM-facing resolution mechanism. However, it is **dangerous as a basis for action** because:

1. It treats a multi-path system as single-path
2. It rests on unvalidated assumptions about Claude Code's internals
3. It ignores collision ambiguity affecting 18.9% of deployed agents
4. It dismisses stem-dependent subsystems (templates, capabilities service) as irrelevant

**The recommended path forward** is to run Test 1 (the swapped-name experiment) before making any filename changes. This single experiment would empirically resolve the core question and either validate or invalidate the hypothesis. Until that test is run, the hypothesis should be treated as **plausible but unproven**, and filename renames should be treated as **potentially breaking changes**, not "safe cosmetic" operations.
