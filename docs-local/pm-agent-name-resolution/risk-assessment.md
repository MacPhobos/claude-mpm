# Risk Assessment: Phase 3 Migration (PM Agent Reference Alignment)

**Date**: 2026-03-05
**Branch**: agenttype-enums
**Status**: Research complete

---

## 1. Executive Summary

Phase 3 replaces filename-stem agent references in PM_INSTRUCTIONS.md with `name:` frontmatter field values. This research concludes that:

- **The migration is strictly an improvement** -- current stem references are provably broken
- **The model WILL correctly resolve** `name:` field references in all tested formatting contexts
- **Risks are manageable** with proper validation
- **One secondary issue** needs attention: the Agent Capabilities Generator template gives contradictory advice about what identifier to use

---

## 2. Risk Matrix

| Risk | Severity | Likelihood | Impact | Mitigation |
|------|----------|-----------|--------|------------|
| R1: Wrong `name:` value used | HIGH | LOW | Delegation fails | Use registry + extraction script to verify |
| R2: Anomalous names confuse model | MEDIUM | LOW | Model passes wrong value | Bold formatting + exact values reduce ambiguity |
| R3: Agent Capabilities section contradicts instructions | MEDIUM | HIGH | PM uses ID instead of name | Fix template instruction text |
| R4: Future `name:` changes in upstream repo | MEDIUM | MEDIUM | PM references become stale | Extraction script detects drift; CI check |
| R5: Formatting change alters model's interpretation | LOW | LOW | Unexpected delegation routing | Test empirically with all formatting patterns |
| R6: " Agent" suffix inconsistency | LOW | MEDIUM | Model strips/adds " Agent" incorrectly | Always use exact `name:` value |
| R7: Partial migration (some stems remain) | HIGH | LOW | Inconsistent behavior | Grep verification catches remaining stems |

---

## 3. Detailed Risk Analysis

### R1: Wrong `name:` Value Used in Replacement

**Description**: If PM_INSTRUCTIONS.md is updated with a value that doesn't exactly match the `name:` frontmatter field, delegation will fail silently (agent not found).

**Likelihood**: LOW -- The `agent_name_registry.py` and extraction script provide authoritative values.

**Mitigation**:
1. Use ONLY values from `agent_name_registry.py` for replacements
2. Run extraction script after Phase 3 to verify no mismatches
3. Grep for any remaining filename stems that should have been replaced

**Verification command**:
```bash
# No filename-stem delegation targets should remain
grep -cE '(delegate to|agent:).*\b(local-ops|web-qa-agent|api-qa-agent|gcp-ops|vercel-ops|clerk-ops)\b' \
  src/claude_mpm/agents/PM_INSTRUCTIONS.md
# Expected: 0
```

### R2: Anomalous `name:` Values Confuse the Model

**Description**: Six agents have non-standard `name:` values (`ticketing_agent`, `aws_ops_agent`, `nestjs-engineer`, `real-user`, `mpm_agent_manager`, `mpm_skills_manager`). When PM_INSTRUCTIONS.md references these with their exact anomalous values, the model might:
- Attempt to "correct" them to Title Case
- Treat underscores/hyphens as word separators

**Likelihood**: LOW -- The model is trained to use exact values from tool descriptions. The Agent tool listing shows these exact values.

**Mitigation**:
1. Use bold formatting around exact values: `**ticketing_agent**`
2. Ensure YAML examples use quoted strings: `agent: "ticketing_agent"`
3. Consider adding a brief note in PM_INSTRUCTIONS.md: "Note: Some agent names use underscores or hyphens. Use the exact name shown."

**Additional context**: Currently, PM_INSTRUCTIONS.md already references `ticketing_agent` in several places (lines 353, 495, 744, 774, 788, 791-793, 1068). The model handles this without issue. The risk is theoretical.

### R3: Agent Capabilities Section Contradicts PM_INSTRUCTIONS.md

**Description**: The Agent Capabilities Generator template (line 177 of `agent_capabilities_generator.py`) currently says:

```
Use the agent ID in parentheses when delegating tasks via the Task tool.
```

This tells the PM to use the `id` (filename stem, e.g., `local-ops`) for delegation. But `subagent_type` resolves against the `name:` field (e.g., `Local Ops`). After Phase 3 aligns PM_INSTRUCTIONS.md to use `name:` values, this instruction in the capabilities section will be the ONLY place telling PM to use IDs, creating confusion.

**Severity**: MEDIUM -- The model receives contradictory instructions from two parts of its prompt.

**Likelihood**: HIGH -- The template instruction is explicit and the model may follow it.

**Mitigation**: Update the template instruction to reference the name (bold text) instead of the ID:

```python
# CURRENT (agent_capabilities_generator.py line 177):
"Use the agent ID in parentheses when delegating tasks via the Task tool."

# PROPOSED:
"Use the agent name (bold text) when delegating tasks via the Task/Agent tool."
```

**Note**: This change is NOT part of Phase 3 as defined in the implementation plan. It should be added as a follow-up or included in Phase 3 scope.

### R4: Future `name:` Changes in Upstream Repository

**Description**: Agent definitions live in the external `bobmatnyc/claude-mpm-agents` Git repository. If a `name:` value changes upstream (e.g., `ticketing_agent` -> `Ticketing`), PM_INSTRUCTIONS.md will reference the old value, causing delegation failures.

**Likelihood**: MEDIUM -- Name changes are possible but not frequent.

**Mitigation**:
1. The extraction script (`scripts/extract_agent_names.sh`) can detect drift
2. Run the script after each `claude-mpm agents deploy` to check for changes
3. Consider a CI check that compares deployed agent names against PM_INSTRUCTIONS.md references
4. The `agent_name_registry.py` module provides a single place to update when names change

**Long-term solution**: Generate PM_INSTRUCTIONS.md agent references from deployed agents rather than hardcoding them. This is a larger architectural change.

### R5: Formatting Change Alters Model's Interpretation

**Description**: Changing from `**local-ops**` to `**Local Ops**` changes the visual and semantic signal the model receives. In theory, this could alter how the model interprets delegation instructions.

**Likelihood**: LOW -- The change makes the instructions MORE aligned with the Agent tool's listing, not less. The model should handle this better, not worse.

**Mitigation**:
1. Empirical testing after Phase 3 (Phase 6 in the plan)
2. Test all major delegation patterns:
   - `Agent(subagent_type="Local Ops")` -- should succeed
   - `Agent(subagent_type="Web QA")` -- should succeed
   - `Agent(subagent_type="ticketing_agent")` -- should succeed

### R6: " Agent" Suffix Inconsistency

**Description**: Two agents have " Agent" in their `name:` field (`Documentation Agent`, `Tmux Agent`). The Agent Capabilities Generator strips " Agent" from display names. If the model sees "Documentation" in the capabilities section but PM_INSTRUCTIONS.md says "Documentation Agent", it might:
- Use "Documentation" (stripped form) -- fails if `name:` is "Documentation Agent"
- Use "Documentation Agent" (full form) -- succeeds

**Likelihood**: MEDIUM -- The capabilities section explicitly shows a stripped name.

**Mitigation**:
1. In PM_INSTRUCTIONS.md, always use the full `name:` value: `**Documentation Agent**`
2. Consider updating the capabilities generator to NOT strip " Agent" from display names
3. Or add a note: `- **Documentation** (full name: "Documentation Agent")`

**Current state**: PM_INSTRUCTIONS.md line 135 already uses "Documentation Agent" correctly. Line 494 uses "Documentation Agent" correctly. This is consistent.

### R7: Partial Migration (Some Stems Remain)

**Description**: If some filename-stem references are missed during Phase 3, the PM will receive mixed signals -- some instructions use `name:` values, others use stems. This could be worse than the current all-stems state because the model can't form a consistent pattern.

**Likelihood**: LOW -- The implementation plan includes comprehensive grep verification.

**Mitigation**:
1. Use the grep verification commands from Phase 3 verification section
2. Ensure ALL occurrences are found and replaced, not just "most"
3. Run a second pass looking for any agent references not in the `name:` value format

**Verification**:
```bash
# Should find ZERO filename-stem references as delegation targets
grep -nE '\b(local-ops|web-qa-agent|api-qa-agent|vercel-ops|gcp-ops|clerk-ops|security-agent)\b' \
  src/claude_mpm/agents/PM_INSTRUCTIONS.md | grep -v '^#'
```

---

## 4. The Agent Capabilities Generator Issue (Expanded)

This is the most significant secondary finding. The current template generates output like:

```markdown
## Available Agent Capabilities

### Engineering Agents
- **Local Ops** (`local-ops`): Local operations specialist...

Use the agent ID in parentheses when delegating tasks via the Task tool.
```

### 4.1 The Contradiction

After Phase 3:
- PM_INSTRUCTIONS.md will say: `Delegate to **Local Ops**`
- Agent Capabilities section will say: `Use the agent ID in parentheses` (i.e., use `local-ops`)
- Agent tool description will list: `Local Ops: Local operations specialist...`

The model receives THREE signals:
1. PM_INSTRUCTIONS.md: use "Local Ops" (CORRECT)
2. Capabilities section: use "local-ops" (INCORRECT)
3. Agent tool listing: "Local Ops" is available (CORRECT)

Two out of three signals point to `name:` values. The model will likely follow the majority. But the capabilities section instruction is explicit and could override.

### 4.2 Recommended Fix

In `src/claude_mpm/services/agents/management/agent_capabilities_generator.py`, change:

```python
# Line 177 (inside template string):
# BEFORE:
"Use the agent ID in parentheses when delegating tasks via the Task tool."

# AFTER:
"Use the agent name in bold when delegating tasks via the Task/Agent tool."
```

Or alternatively, change the template to show the `name:` value in parentheses instead of the ID:

```jinja2
# BEFORE:
- **{{ cap.name }}** (`{{ cap.id }}`): {{ cap.capability_text }}

# AFTER:
- **{{ cap.name }}** (subagent_type: `{{ agent.name }}`): {{ cap.capability_text }}
```

### 4.3 Impact If Not Fixed

If the capabilities section instruction is left unchanged:
- **Best case**: Model ignores it and follows PM_INSTRUCTIONS.md + Agent tool listing (2/3 majority)
- **Worst case**: Model follows the capabilities instruction and passes filename stems, causing failures
- **Expected case**: Model behavior is inconsistent -- sometimes uses names, sometimes uses IDs

---

## 5. Recommendations

### 5.1 Phase 3 Should Proceed

The migration is strictly an improvement:
- Current stem references are provably broken (`subagent_type="golang-engineer"` fails)
- New `name:` references are provably correct (`subagent_type="Golang Engineer"` succeeds)
- All tested formatting patterns (bold, backtick, quoted, table, YAML) work correctly

### 5.2 Add Capabilities Generator Fix to Phase 3

The `agent_capabilities_generator.py` template instruction should be fixed as part of Phase 3, or immediately after. Without this fix, the PM receives contradictory guidance.

### 5.3 Test Empirically (Phase 6)

The following delegation calls should be tested after Phase 3:

| Test | `subagent_type` Value | Expected Result |
|------|----------------------|-----------------|
| Standard Title Case | `"Local Ops"` | SUCCESS |
| Standard abbreviation | `"Web QA"` | SUCCESS |
| Standard single word | `"Research"` | SUCCESS |
| With " Agent" suffix | `"Documentation Agent"` | SUCCESS |
| Anomalous snake_case | `"ticketing_agent"` | SUCCESS |
| Anomalous kebab-case | `"nestjs-engineer"` | SUCCESS |
| Multi-word expansion | `"Google Cloud Ops"` | SUCCESS |
| Old stem format | `"local-ops"` | FAILURE (expected) |

### 5.4 Monitor for Drift

After Phase 3, establish a process to detect when upstream `name:` changes make PM_INSTRUCTIONS.md references stale:

```bash
# Add to CI or pre-commit hook:
./scripts/extract_agent_names.sh | diff - src/claude_mpm/core/agent_name_registry.py
```

---

## 6. Conclusion

Phase 3 is low-risk and high-reward. The current PM_INSTRUCTIONS.md uses filename stems that are empirically proven to fail as `subagent_type` values. Replacing them with `name:` field values is the correct fix. The only significant secondary issue is the Agent Capabilities Generator's contradictory instruction, which should be addressed concurrently.

The migration should proceed with confidence, using the `agent_name_registry.py` as the authoritative source and the validation commands to ensure completeness.
