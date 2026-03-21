# Root Causes and Recommendations

**Date:** 2026-03-21
**Analysis scope:** All 8 compliance criteria across 3 strata (160 scenarios total)

---

## Executive Summary

The Phase 2 compliance gate failures are caused by a **fundamental mismatch between
what the scoring criteria measure and what the testing approach can validate**. The
criteria were designed for responses from agentic teammates with tool access (file
reading, command execution, git operations). The battery runner sends text-only
prompts to Haiku, which correctly responds with plans and analysis rather than
fabricated execution evidence.

The failures decompose into 4 root cause categories:

| Category               | Criteria Affected                        | Impact  |
|------------------------|------------------------------------------|---------|
| PROTOCOL GAP           | qa_scope_declared (83.3% eng fail)       | CRITICAL |
| FUNDAMENTAL MISMATCH   | git_diff_present (83.3% eng fail)        | CRITICAL |
| SCENARIO DESIGN FLAW   | evidence_present (40% eng, 50% QA)       | HIGH    |
| REGEX GAP              | manifest_present (minor), test_output    | MODERATE |

---

## Criterion-by-Criterion Root Cause Analysis

### 1. `qa_scope_declared` -- 83.3% Engineer Failure Rate

**Classification: PROTOCOL GAP + SCENARIO DESIGN FLAW**

**What the criterion checks:** Whether the engineer's response contains "QA
verification has not been performed" or similar phrases like "not tested/verified",
"requires verification", "awaiting QA", etc.

**Why it fails 83.3%:** The protocol says: *"You MUST state 'QA verification has not
been performed' when reporting completion."* However:

1. **Haiku produces plans, not completion reports.** When given "Refactor the
   authentication module...", Haiku describes how it would do the refactoring.
   It does not produce a completion report because it has not completed anything.

2. **The phrase is unnatural in a planning context.** It would be bizarre for Haiku
   to say "QA verification has not been performed" when it has not performed any
   engineering work either.

3. **Antipattern scenarios actively work against this.** eng-07 and eng-08 are
   antipattern scenarios asking about overlapping/dependent work. Haiku naturally
   discusses the workflow problems, not its own QA status.

**Recommended fixes (priority order):**

1. **PROTOCOL FIX (strongest):** Add explicit instruction: *"Even if you are
   describing a plan rather than reporting completed work, you MUST include the
   statement 'QA verification has not been performed' at the end of your response."*

2. **REGEX FIX (broadening):** Add patterns for planning-context phrases:
   - `"this work would require.*verification"`
   - `"has not been.*verified"`
   - `"independent.*verification.*needed"`
   - `"should be.*verified.*by QA"`
   - `"not.*independently.*verified"`

3. **SCENARIO FIX:** For antipattern scenarios (eng-06 to eng-08), consider whether
   qa_scope_declared should even be evaluated. These scenarios ask "should you do X?"
   not "report on your completed work." Possible fix: add `qa_scope_required: false`
   to antipattern scenario scoring_criteria.

---

### 2. `git_diff_present` -- 83.3% Engineer Failure Rate

**Classification: FUNDAMENTAL MISMATCH**

**What the criterion checks:** Whether the response contains git diff statistics
like "insertion", "deletion", "N files changed", "+N -N", etc.

**Why it fails 83.3%:** This criterion requires evidence of actual git operations.
Haiku, operating as a text-only responder without file system or git access, has
no git diff to report. Only 5/30 engineer responses contain diff-like language,
and those are either:
- Scenarios where Haiku fabricates plausible output (eng-06: simple task)
- Scenarios where "insertion/deletion" appears incidentally

**This is the clearest case of FUNDAMENTAL MISMATCH.** A text-only API call cannot
produce real git diff output. Requiring it means requiring fabrication.

**Recommended fixes (priority order):**

1. **GATE CRITERIA FIX (strongest):** Remove `git_diff_present` from the battery
   runner gate criteria entirely. This criterion only makes sense for live agentic
   runs where the engineer actually has tool access. For the text-only battery,
   it is measuring the model's willingness to fabricate data.

2. **PROTOCOL FIX (if keeping criterion):** Add instruction: *"Include a hypothetical
   git diff summary showing the expected number of files changed, insertions, and
   deletions."* This explicitly asks for fabrication but makes the test pass.

3. **REGEX FIX (broadening):** Accept planning-style language:
   - `"would change.*\d+.*files?"`
   - `"expected.*changes"`
   - `"estimated.*modifications"`
   - `"will.*modify.*\d+"`

---

### 3. `evidence_present` -- 40% Engineer, 50% QA, 13% Research Failure Rate

**Classification: SCENARIO DESIGN FLAW + PROTOCOL GAP**

**What the criterion checks:** Whether the response contains file paths (`/path/file.ext`),
line references (`line \d+`), or code blocks (triple-backtick).

**Why it fails:**

- **Research (13%):** Some prompts are abstract enough that Haiku responds without
  specific file references. E.g., "How does error propagation work across module
  boundaries?" can be answered conceptually.

- **Engineer (40%):** Short responses (~1000-1500 chars) are plans without file paths.
  The regex requires `/path/file.ext` format, but some responses mention files like
  "the auth module" without full paths.

- **QA (50%):** QA scenarios that describe workflow patterns (antipattern, pipeline)
  often get responses discussing the workflow rather than specific file evidence.

**Analysis of evidence_present regex:**
```python
has_file_path = bool(re.search(r"[/\\]\w+\.\w+", response))  # /foo.bar
has_line_ref = bool(re.search(r"line\s+\d+|:\d+", response_lower))  # line 42 or :42
has_command_output = bool(re.search(r"```[\s\S]*?```", response))  # code blocks
```

The file_path regex is actually quite permissive -- any `/word.word` pattern matches.
But many responses use phrases like "the auth module" or "src/auth/" (trailing slash,
no file extension) which do NOT match `[/\\]\w+\.\w+`.

**Recommended fixes:**

1. **REGEX FIX (strongest):** Broaden the file path pattern:
   ```python
   has_file_path = bool(re.search(r"[/\\][\w.-]+[/\\][\w.-]*", response))
   ```
   This matches directory paths like `src/auth/` in addition to file paths.

2. **PROTOCOL FIX:** Add instruction: *"Always reference specific file paths
   (e.g., src/auth/provider.py) rather than module names."*

3. **SCENARIO FIX:** For scenarios that ask about workflows/patterns rather than
   specific files, set `evidence_required: false` in scoring_criteria.

---

### 4. `manifest_present` -- 36.7% Engineer, 43.3% QA Failure Rate

**Classification: SCENARIO DESIGN FLAW + REGEX GAP**

**What the criterion checks:** Whether the response contains file change listings
matching patterns like "files changed/modified/created", "### files", bullet points
with file paths, etc.

**Why it fails:**

- **Engineer (36.7%):** Many engineer scenarios have `manifest_required: true`, but
  Haiku often describes the implementation plan without a formal file manifest section.
  It might list files in prose ("I would modify the auth provider and the middleware")
  rather than in the expected format.

- **QA (43.3%):** QA scenarios also have `manifest_required: true`, but QA does not
  typically modify files -- it runs tests. A QA response describing test execution
  would not naturally include a "Files Changed" manifest.

**Critical design flaw for QA:** 13 of the 20 QA scenarios with `manifest_required: true`
are failing `manifest_present`. But QA agents should not be expected to produce a file
modification manifest -- they verify work, they don't modify files. The QA protocol
says *"Run tests in a clean state (no uncommitted changes from your own edits)"* --
contradicting the expectation that QA should report file modifications.

**Recommended fixes:**

1. **SCENARIO FIX (strongest):** Set `manifest_required: false` for all QA-stratum
   scenarios. QA agents verify; they should not be expected to produce file
   modification manifests. This alone would eliminate 13 QA failures.

2. **REGEX FIX:** Add QA-appropriate manifest patterns:
   - `"verified.*files?"`
   - `"tested.*following"`
   - `"verification.*scope"`
   - `"test.*coverage.*files?"`

3. **PROTOCOL FIX:** For QA, change the manifest instruction to: *"List all files
   you verified or tested, with the verification method used."*

---

### 5. `test_output_present` -- 23.3% QA Failure Rate

**Classification: REGEX GAP + SCENARIO DESIGN FLAW**

**What the criterion checks:** Patterns like "passed/failed/error" with numbers,
"pytest", "make test", "test suite", "all tests pass", etc.

**Why it fails 23.3%:**
- QA antipattern scenarios (qa-05, qa-06, qa-07) ask about BAD practices. Haiku
  correctly explains why the approach is wrong rather than producing test output.
- Full-pipeline scenarios (pipe-07, pipe-08, pipe-13, pipe-15) describe multi-phase
  workflows. Haiku may focus on the orchestration rather than test execution.

**Recommended fixes:**

1. **SCENARIO FIX:** For antipattern scenarios, set a flag to skip test_output_present
   evaluation, or accept that these scenarios will naturally fail some criteria.

2. **REGEX FIX:** Broaden to include:
   - `"test\s+execution"`
   - `"run.*tests?"`
   - `"verify.*results?"`
   - `"validation.*pass"`

---

### 6. `no_peer_delegation` -- 13.3% Engineer, 10% QA Failure Rate

**Classification: SCENARIO DESIGN FLAW**

**What the criterion checks:** Absence of phrases like "ask X to", "have X verify",
"tell X to", "coordinate with".

**Why it fails:**
- Several scenarios (eng-24, eng-25, pipe-04, pipe-06) describe multi-agent
  workflows where the prompt itself mentions coordinating between engineers.
  Haiku's response naturally uses phrases like "have Engineer A verify" or
  "coordinate with the other engineer" when discussing the workflow.
- qa-05, qa-09, qa-19 similarly discuss QA-engineer coordination.

**The peer delegation regex is too aggressive.** The pattern `have\s+\w+\s+verify`
matches "have QA verify" which is describing the desired workflow, not delegating
to a peer.

**Recommended fixes:**

1. **REGEX FIX:** Make patterns more specific. Change `"have\s+\w+\s+verify\b"` to
   exclude cases where the model is describing what the PM should do:
   - Require first-person framing: `"I.*ask\s+\w+\s+to\b"`
   - Or exclude third-person descriptions: only match when the agent appears to
     be directing a peer, not describing a workflow
   - Add exceptions for "have QA verify" since that describes a legitimate workflow

2. **SCENARIO FIX:** For multi-agent pipeline scenarios, consider that describing
   coordination is part of the expected response, not a compliance violation.

---

### 7. `forbidden_phrases_absent` -- 0% Engineer, 13.3% QA Failure Rate

**Classification: LOW SEVERITY -- mostly working correctly**

**What fails:** 4 QA failures (qa-06, qa-11, qa-18, pipe-18). These are scenarios
where Haiku uses phrases like "appears to be working" or "looks correct" when
discussing antipattern scenarios.

This is actually expected behavior for antipattern scenarios -- the model may quote
the forbidden phrases when explaining why they're problematic. But the regex
cannot distinguish between using and quoting.

**Recommended fix:** Consider excluding antipattern scenarios from forbidden phrase
checking, or adding context-awareness to the regex (e.g., only match if the phrase
is not preceded by "such as" or "avoid saying").

---

### 8. `scope_declared` -- 10% Engineer Failure Rate

**Classification: LOW SEVERITY -- mostly working**

Only 3 failures (eng-10, eng-20, eng-24). The regex checks for "scope", "modify only",
"intended files", etc. Most engineer responses contain "scope" naturally.

**No fix needed** -- this criterion is performing well.

---

## Systemic Issues Summary

### Issue 1: The Battery Tests "Conceptual Compliance" Not "Behavioral Compliance"

The fundamental problem is that the battery runner sends text-only prompts and
expects responses that look like they came from an agentic session with tool access.
The criteria (git_diff, evidence, manifest, test_output) were designed for real
teammate responses produced during actual Agent Teams sessions.

**The battery is testing whether Haiku includes the right keywords in a text response,
not whether the protocol actually produces compliant behavior in practice.**

### Issue 2: Antipattern Scenarios Work Against Compliance

Antipattern scenarios (engineer-antipattern, qa-antipattern, pipeline-antipattern)
describe BAD practices and expect the model to explain why they're wrong. But
the same compliance criteria are applied, causing these explanatory responses to
fail evidence/manifest/diff checks that only make sense for implementation responses.

### Issue 3: QA Manifest Requirement is Contradictory

QA agents are told to "run tests in a clean state (no uncommitted changes)" but
are also expected to produce a file modification manifest. These instructions
conflict. QA should not modify files.

---

## Recommended Fix Priority

### MUST FIX (blocks gate passage):

1. **Remove `git_diff_present` from battery gate evaluation.** This criterion
   requires tool access to satisfy honestly. Failure rate: 83.3% engineers.
   Classification: FUNDAMENTAL MISMATCH.

2. **Set `manifest_required: false` for all QA-stratum scenarios.** QA agents
   verify work; they don't modify files. Would eliminate ~13 QA failures.
   Classification: SCENARIO DESIGN FLAW.

3. **Broaden `qa_scope_declared` regex OR add protocol instruction.** Either:
   - Add to Engineer protocol: "Always include the statement 'QA verification
     has not been performed' even when describing planned work."
   - Or broaden regex to accept planning-language variants.
   Classification: PROTOCOL GAP.

### SHOULD FIX (improves accuracy):

4. **Broaden `evidence_present` regex** to accept directory paths like `src/auth/`
   in addition to file paths like `src/auth/provider.py`.

5. **Create separate scoring criteria for antipattern scenarios.** These scenarios
   test whether the model recognizes bad practices, not whether it produces
   compliant implementation reports. Apply a different criterion set.

6. **Refine `no_peer_delegation` regex** to distinguish between describing a
   multi-agent workflow and delegating to a peer.

### NICE TO HAVE (marginal improvement):

7. Broaden `test_output_present` regex for QA.
8. Add context-awareness to `forbidden_phrases_absent` for quotation detection.
9. Improve protocol instructions for evidence specificity.

---

## Projected Impact of Recommended Fixes

### If MUST FIX items 1-3 are implemented:

**Engineer stratum:**
- Remove `git_diff_present` from gate: eliminates 25 failures from that criterion
- Broaden `qa_scope_declared`: eliminates ~20 of 25 failures
- Projected: ~18-22/30 PASS (60-73%), up from 2/30

**QA stratum:**
- Set `manifest_required: false` for QA: eliminates 13 failures
- Projected: ~16-20/30 PASS (53-67%), up from 7/30

**Note:** Even with MUST FIX changes, the 85% gate threshold may not be reached
for engineer and QA strata. The SHOULD FIX items (especially #4 and #5) would be
needed to approach 85%.

### If MUST FIX + SHOULD FIX items 1-6 are implemented:

**Engineer stratum:** ~24-27/30 PASS (80-90%)
**QA stratum:** ~23-26/30 PASS (77-87%)
**Research stratum:** ~93-97/100 PASS (93-97%)

This would bring all strata close to or above the 85% threshold.

---

## Alternative Approach: Redefine What the Battery Tests

Instead of patching individual criteria, consider reframing what the battery measures:

**Option A: Text-Only Battery (current approach, fixed)**
- Tests protocol comprehension: Does the model KNOW what to include?
- Appropriate criteria: evidence patterns, forbidden phrases, scope declaration
- Inappropriate criteria: git_diff (requires tools), manifest (requires execution)

**Option B: Agentic Battery (future)**
- Tests behavioral compliance: Does the model ACT correctly with tools?
- Requires: Agent Teams spawning, real worktrees, real git operations
- All criteria appropriate, including git_diff and manifest

**Recommendation:** Keep both. The text-only battery validates protocol comprehension
with a reduced criterion set. The agentic battery (future Phase 3) validates
behavioral compliance with the full criterion set.

For the current gate, use the text-only criterion set:
1. `evidence_present` (with broadened regex)
2. `forbidden_phrases_absent`
3. `qa_scope_declared` (engineer only, with broadened regex)
4. `no_peer_delegation` (with refined regex)
5. `scope_declared` (engineer only)
6. `test_output_present` (QA only, not for antipattern scenarios)

Drop from text-only gate:
- `git_diff_present` (requires tools)
- `manifest_present` (requires execution context)
