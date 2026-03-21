# Phase 2 Compliance Gate Failure Analysis

**Date:** 2026-03-21
**Data source:** `~/.claude-mpm/compliance/agent-teams-battery-2026-03-21.jsonl`
**Model:** claude-haiku-4-20250414 (Haiku 4.5)
**Total records:** 160

---

## 1. Overall Gate Results

| Stratum   | n   | PASS | FAIL | Fail Rate | Gate Threshold (85%) |
|-----------|-----|------|------|-----------|---------------------|
| research  | 100 | 85   | 15   | 15.0%     | PASS (barely)       |
| engineer  | 30  | 2    | 28   | **93.3%** | FAIL                |
| qa        | 30  | 7    | 23   | **76.7%** | FAIL                |

Research scrapes by at exactly 85% (the CI lower bound will be examined below). Engineer and QA are catastrophically failing.

---

## 2. Per-Criterion Failure Rates by Stratum

### 2.1 Research Stratum (n=100)

| Criterion                | Failures | Rate  | Severity |
|--------------------------|----------|-------|----------|
| evidence_present         | 13       | 13.0% | Moderate |
| forbidden_phrases_absent | 1        | 1.0%  | Low      |
| manifest_present         | 1        | 1.0%  | Low      |
| no_peer_delegation       | 1        | 1.0%  | Low      |
| qa_scope_declared        | 0        | 0.0%  | N/A      |
| git_diff_present         | 0        | 0.0%  | N/A      |
| scope_declared           | 0        | 0.0%  | N/A      |
| test_output_present      | 0        | 0.0%  | N/A      |

**Note:** 6 of 8 criteria are auto-PASS for research (N/A for non-engineer, non-QA). The 15% failure rate is driven almost entirely by `evidence_present` (13/15 failures).

### 2.2 Engineer Stratum (n=30)

| Criterion                | Failures | Rate    | Severity     |
|--------------------------|----------|---------|--------------|
| **qa_scope_declared**    | **25**   | **83.3%** | CRITICAL   |
| **git_diff_present**     | **25**   | **83.3%** | CRITICAL   |
| evidence_present         | 12       | 40.0%   | High         |
| manifest_present         | 11       | 36.7%   | High         |
| no_peer_delegation       | 4        | 13.3%   | Moderate     |
| scope_declared           | 3        | 10.0%   | Low          |
| forbidden_phrases_absent | 0        | 0.0%    | None         |
| test_output_present      | 0        | 0.0%    | N/A          |

**Dominant blockers:** `qa_scope_declared` and `git_diff_present` each fail 83.3% of the time. These two criteria alone would cause the gate to fail even if everything else passed perfectly.

### 2.3 QA Stratum (n=30)

| Criterion                | Failures | Rate    | Severity   |
|--------------------------|----------|---------|------------|
| **evidence_present**     | **15**   | **50.0%** | CRITICAL |
| **manifest_present**     | **13**   | **43.3%** | HIGH     |
| test_output_present      | 7        | 23.3%   | High       |
| forbidden_phrases_absent | 4        | 13.3%   | Moderate   |
| no_peer_delegation       | 3        | 10.0%   | Moderate   |
| qa_scope_declared        | 0        | 0.0%    | N/A        |
| git_diff_present         | 0        | 0.0%    | N/A        |
| scope_declared           | 0        | 0.0%    | N/A        |

**Dominant blockers:** `evidence_present` (50%) and `manifest_present` (43.3%) are the top two. `test_output_present` at 23.3% is the QA-specific criterion that is most problematic.

---

## 3. Cross-Tabulation: Failure Combinations

### 3.1 Engineer Failure Patterns

28 of 30 engineer scenarios fail. The most common combination patterns:

| Pattern (failing criteria)                                        | Count | % of fails |
|-------------------------------------------------------------------|-------|-----------|
| qa_scope_declared + git_diff_present (pair)                       | 18    | 64.3%     |
| evidence_present + qa_scope_declared + git_diff_present (triple)  | 7     | 25.0%     |
| manifest_present + qa_scope_declared + git_diff_present (triple)  | 6     | 21.4%     |
| All four: evidence + manifest + qa_scope + git_diff               | 3     | 10.7%     |

**Key observation:** `qa_scope_declared` and `git_diff_present` almost always co-occur. Of the 25 scenarios failing `qa_scope_declared`, 22 also fail `git_diff_present`. These are the systemic blockers.

### 3.2 QA Failure Patterns

23 of 30 QA scenarios fail. Common patterns:

| Pattern (failing criteria)                        | Count | % of fails |
|---------------------------------------------------|-------|-----------|
| evidence_present alone                            | 5     | 21.7%     |
| evidence_present + manifest_present               | 4     | 17.4%     |
| manifest_present alone                            | 3     | 13.0%     |
| evidence_present + manifest_present + test_output | 2     | 8.7%      |
| manifest_present + test_output                    | 2     | 8.7%      |

QA failures are more diverse -- no single dominant pair.

---

## 4. Failure Distribution by Fine-Grained Stratum

### 4.1 Engineer Fine Strata

| Fine Stratum         | n  | PASS | FAIL | Fail Rate |
|----------------------|----|------|------|-----------|
| engineer-parallel    | 9  | 0    | 9    | 100%      |
| engineer-antipattern | 3  | 1    | 2    | 66.7%     |
| engineer-merge       | 8  | 0    | 8    | 100%      |
| engineer-recovery    | 6  | 1    | 5    | 83.3%     |
| eng-then-qa          | 4  | 0    | 4    | 100%      |

The only two passing engineer scenarios are `eng-06` (antipattern: trivial single-line type hint addition) and `eng-14` (recovery: worktree cleanup). These happen to be the scenarios where Haiku incidentally produces output matching the compliance patterns.

### 4.2 QA Fine Strata

| Fine Stratum          | n  | PASS | FAIL | Fail Rate |
|-----------------------|----|------|------|-----------|
| qa-pipeline           | 10 | 3    | 7    | 70.0%     |
| qa-antipattern        | 5  | 0    | 5    | 100%      |
| qa-protocol           | 6  | 4    | 2    | 33.3%     |
| full-pipeline         | 5  | 0    | 5    | 100%      |
| pipeline-antipattern  | 4  | 1    | 3    | 75.0%     |

`qa-protocol` performs best (4/6 pass), which makes sense -- these scenarios directly ask for test output evidence.

---

## 5. Response Length Correlation

| Stratum  | Avg Length (PASS) | Avg Length (FAIL) | Observation              |
|----------|-------------------|-------------------|--------------------------|
| research | ~3100 chars       | ~2200 chars       | Shorter responses fail   |
| engineer | ~2480 chars       | ~2000 chars       | Minimal difference       |
| qa       | ~2000 chars       | ~1450 chars       | Shorter responses fail   |

Shorter responses correlate with failure, suggesting Haiku sometimes produces terse conceptual plans instead of detailed implementation reports.

---

## 6. Summary Statistics

**Total failures across all strata:** 66/160 (41.25%)

**Top 5 criteria by overall failure rate:**
1. `evidence_present` -- 40/160 (25.0%)
2. `qa_scope_declared` -- 25/160 (15.6%) [all from engineer stratum]
3. `manifest_present` -- 25/160 (15.6%)
4. `git_diff_present` -- 25/160 (15.6%) [all from engineer stratum]
5. `no_peer_delegation` -- 8/160 (5.0%)
6. `test_output_present` -- 7/160 (4.4%) [all from QA stratum]
7. `forbidden_phrases_absent` -- 5/160 (3.1%)
8. `scope_declared` -- 3/160 (1.9%)
