# Holistic Recommendation: AgentType Enum & Frontmatter Standardization

**Date**: 2026-03-03
**Author**: PM Agent (synthesis of 4 parallel research analyses)
**Branch**: `agenttype-enums`
**Status**: Complete recommendation — ready for implementation planning

---

## Executive Summary

Four independent research agents analyzed the AgentType enum and frontmatter field inconsistency from different angles: code-path tracing, enum relationship analysis, standardization impact quantification, and adversarial challenge. This document synthesizes their findings into a single actionable recommendation.

**The problem is bigger than initially understood.** The v1 analysis (problem-analysis.md) focused on three incompatible `AgentType` enums. The v2 analysis reveals:

1. **The primary issue is the frontmatter field name split**, not the enum inconsistency. Two parallel code paths read different field names (`type:` vs `agent_type:`) with no normalization.
2. **The root cause is a single line of code** in `agent_template_builder.py:568` that translates `agent_type` → `type` during deployment, creating an asymmetry between template source and deployed output.
3. **There are actually FOUR overlapping classification systems** (`AgentType` ×3 + `AgentCategory`) plus THREE separate `AgentTier` enums.
4. **The v1 analysis contained factual errors**: `_safe_parse_agent_type()` does not exist; the codebase has 75 agent files, not 48.
5. **75 agent files exist** with 14+ duplicate pairs (hyphen vs underscore naming) that should be deduplicated.

**Bottom line**: Standardize on `agent_type` as the canonical field name, consolidate to one `AgentRole` enum (`str, Enum`) with frontmatter-matching values, and clean up duplicates.

---

## 1. Key Findings Summary

### From Code-Path Tracer (01)

| Finding | Evidence |
|---------|----------|
| **7 distinct code paths** read type information, none share a normalization layer | Complete trace in 01-type-vs-agent_type-code-paths.md §10 |
| **AgentTemplateBuilder is the root cause** — reads `agent_type` from JSON (line 493), writes `type:` to frontmatter (line 568) | agent_template_builder.py:493,568 |
| **Claude Code platform ignores both fields** — `FrontmatterValidator.REQUIRED_FIELDS = {name, description, tools}` | frontmatter_validator.py:47 |
| **Fields are semantically identical** — both carry the agent's functional role | All 75 files inspected |
| **No file uses both fields** — clean split between generations | grep across all .claude/agents/*.md |

### From Enum Analyst (02)

| Finding | Evidence |
|---------|----------|
| **Enum 1** (models) parses `type:` but crashes (ValueError) for 95%+ of agents | agent_management_service.py:444 |
| **Enum 2** (registry) NEVER reads frontmatter — classifies by file path only | unified_agent_registry.py:431-448 |
| **Enum 3** (test) is the ONLY enum matching frontmatter values — but lives in tests | agent_response_parser.py:37-47 |
| **AgentCategory** (4th system) has 17 members with DIFFERENT naming (`engineering` vs `engineer`, `operations` vs `ops`) | core/enums.py:360-443 |
| **Three AgentTier enums** with incompatible casing (UPPERCASE vs lowercase) | core/types.py:78, unified_agent_registry.py:44, async_agent_loader.py:47 |
| **Factory's `agent_type` parameter is dead code** — accepted but never used | agent_definition_factory.py:49 |
| **No `from_dict()` on Enum 1's `AgentDefinition`** — round-trip impossible | agent_definition.py |

### From Impact Analyst (03)

| Metric | Approach A (`type`) | Approach B (`agent_type`) | Approach C (both) |
|--------|:---:|:---:|:---:|
| Agent .md files to change | 27 | 47 | 0 |
| Python src/ files to change | ~15 | ~8 | ~8 |
| Test files to change | ~30+ (250+ refs) | ~10 | ~0 |
| Event data contract breakage | **YES** | NO | NO |
| Serialization breakage | **YES** | NO | NO |
| Python builtin shadow fix | No | **Yes** | No |
| Risk of regression | **HIGH** | LOW | LOW |

**Root cause identified**: `agent_template_builder.py:568` translates `agent_type` → `type` during deployment.

### From Devil's Advocate (04)

| Challenge | Verdict |
|-----------|---------|
| "Is anyone actually broken?" | **YES** — two code paths read different fields, causing agents to be partially invisible |
| "Is this just theoretical?" | **NO** — the `_safe_parse_agent_type()` was reverted; line 444 throws ValueError for most agents |
| "YAGNI argument?" | **Fails** — the inconsistency is already shipped and widening with each new agent |
| "Option D (hybrid constants) is good?" | **Challenged** — unpythonic, false economy, neither type-safe nor simple |
| "Support both permanently?" | **Bad** — doubles testing, confuses authors, creates "which one?" question |
| "The `engineering` typo proves free-form strings fail" | `javascript_engineer_agent.json` uses `"engineering"` while all others use `"engineer"` |
| "14 duplicate file pairs exist" | hyphen-format + underscore-format represent the same logical agents |

---

## 2. Addressing the Devil's Advocate Concerns

### Concern: "Is standardization even necessary?"

**Yes.** The devil's advocate confirmed this through evidence:
- Two code paths produce different results for the same agent
- The management service throws ValueError for most agents (line 444)
- 14+ duplicate file pairs exist as artifacts of the split
- Information loss is ongoing (46 agents misclassified)

### Concern: "Option D (hybrid string + constants) is the worst of both worlds"

**Agreed.** The devil's advocate correctly identified that Option D provides neither the type safety of enums nor the simplicity of plain strings. The constants class is a Java pattern that doesn't align with Python idioms. Instead, we recommend a proper `str, Enum` with a safe `from_value()` classmethod that falls back to `CUSTOM` for unknown values.

### Concern: "Free-form strings enable silent typos"

**Confirmed.** The `"engineering"` vs `"engineer"` typo in `javascript_engineer_agent.json` is proof. The enum must validate known values while accepting unknowns gracefully.

### Concern: "Deprecation warnings are invisible"

**Partially agreed.** Log warnings alone are insufficient. The recommendation includes:
1. Log warnings (immediate awareness)
2. CI linting that flags `type:` usage as a warning (enforceable)
3. Template builder updated to emit `agent_type:` (prevents new occurrences)

### Concern: "What about the 14 duplicate file pairs?"

**Must be addressed.** The duplicate files are a precondition for clean standardization. Deduplication should happen in Phase 1 before any field name changes.

---

## 3. Recommendation: Three-Phase Approach

### Phase 1: Stabilize (No Breaking Changes)

**Goal**: Make the current system work correctly without changing any agent files or external contracts.

**1.1 Add normalization to all read paths**

Create a single utility function:

```python
# src/claude_mpm/utils/frontmatter_utils.py (new file)

def read_agent_type(frontmatter: dict, default: str = "custom") -> str:
    """Read agent type from frontmatter, supporting both field names.

    Canonical field: 'agent_type' (preferred)
    Legacy field: 'type' (accepted with deprecation warning)
    """
    if "agent_type" in frontmatter:
        return frontmatter["agent_type"]
    if "type" in frontmatter:
        import logging
        logging.getLogger(__name__).warning(
            "Frontmatter field 'type:' is deprecated. Use 'agent_type:' instead."
        )
        return frontmatter["type"]
    return default
```

Apply this to all 7 code paths identified in analysis 01.

**1.2 Fix the ValueError crash**

Replace line 444 of `agent_management_service.py`:

```python
# BEFORE (crashes for 95%+ of agents):
type=AgentType(post.metadata.get("type", "core")),

# AFTER (safe with normalization):
type=safe_parse_agent_role(read_agent_type(post.metadata)),
```

Where `safe_parse_agent_role()` is a classmethod on the new consolidated enum (see Phase 2).

**1.3 Deduplicate agent files**

The 14+ duplicate pairs (e.g., `dart-engineer.md` + `dart_engineer.md`) should be resolved:
- **Keep**: The hyphen-format files (these are what Claude Code expects in `.claude/agents/`)
- **Remove**: The underscore-format duplicates (these are template-format artifacts)
- **Migrate**: Any unique metadata from underscore files into the hyphen versions

**Estimated effort**: 1-2 hours
**Risk**: LOW — normalization is additive, crash fix is defensive, dedup is file cleanup
**Rollback**: Revert the utility function; files unchanged

---

### Phase 2: Consolidate Enums (Internal Refactoring)

**Goal**: Replace three `AgentType` enums with one canonical `AgentRole` enum.

**2.1 Create canonical `AgentRole` enum**

```python
# src/claude_mpm/models/agent_role.py (new file)

from enum import Enum

class AgentRole(str, Enum):
    """Functional role of an agent as declared in frontmatter.

    Values match the actual frontmatter values used in deployed agents.
    Use from_value() for safe parsing that never raises ValueError.
    """

    # Primary functional roles (from frontmatter)
    ENGINEER = "engineer"
    OPS = "ops"
    QA = "qa"
    RESEARCH = "research"
    DOCUMENTATION = "documentation"
    SECURITY = "security"
    PRODUCT = "product"

    # Framework/infrastructure roles
    SYSTEM = "system"
    SPECIALIZED = "specialized"
    CORE = "core"

    # Catch-all for unknown/niche types
    CUSTOM = "custom"

    @classmethod
    def from_value(cls, value: str) -> "AgentRole":
        """Safely parse a string to AgentRole, falling back to CUSTOM."""
        try:
            return cls(value.lower().strip())
        except ValueError:
            return cls.CUSTOM
```

**Why `AgentRole` instead of `AgentType`**:
- Eliminates name collision with existing enums during migration
- Distinguishes functional role (what it does) from deployment scope (where it lives)
- "Role" is semantically accurate — "engineer" is a role, not a type

**2.2 Rename Enum 2 to `AgentScope`**

The unified registry's enum classifies WHERE agents live, not WHAT they do:

```python
# In unified_agent_registry.py — rename only, values unchanged
class AgentScope(Enum):
    """Where the agent was discovered (orthogonal to role)."""
    CORE = "core"
    SPECIALIZED = "specialized"
    USER_DEFINED = "user_defined"
    PROJECT = "project"
    MEMORY_AWARE = "memory_aware"
```

**2.3 Deprecate Enum 1 and AgentCategory**

- `models.agent_definition.AgentType` → replaced by `AgentRole`
- `core.enums.AgentCategory` → superseded by `AgentRole` (mark deprecated)

**2.4 Update all import paths**

Replace imports in stages:
1. Add `AgentRole` alongside existing enums
2. Update consumers one-by-one
3. Remove old enums when no importers remain

**2.5 Consolidate AgentTier**

While we're at it, consolidate the three `AgentTier` enums into one canonical definition in `core/types.py` with consistent lowercase values.

**Estimated effort**: 4-6 hours
**Risk**: MEDIUM — enum rename affects many files but is mechanically verifiable
**Rollback**: Revert to deprecated enum aliases
**Testing**: All existing tests must pass; no external contract changes

---

### Phase 3: Standardize on `agent_type` Field Name

**Goal**: All agent files use `agent_type:` consistently, all code reads `agent_type:`.

**3.1 Update template builder output**

Change `agent_template_builder.py:568`:

```python
# BEFORE:
frontmatter_lines.append(f"type: {agent_type}")

# AFTER:
frontmatter_lines.append(f"agent_type: {agent_type}")
```

This is THE root cause fix. New deployments will use `agent_type:` going forward.

**3.2 Bulk-update 47 deployed agent files**

Mechanical find-and-replace across all `.claude/agents/*.md` files:

```bash
# Script to migrate frontmatter field name
for f in .claude/agents/*.md; do
    sed -i '' 's/^type: /agent_type: /' "$f"
done
```

**3.3 Update remaining Python code**

The ~8 source files that read `"type"` as a frontmatter key:
- `agent_management_service.py` — use `read_agent_type()` (from Phase 1)
- `agent_validator.py` — check for `agent_type:` prefix
- `agent_listing_service.py` — update dict key
- `agents_metadata.py` — update hardcoded dicts
- `agent_definition.py` — rename `AgentMetadata.type` to `AgentMetadata.agent_type`

**3.4 Remove Phase 1 compatibility layer**

After all files are migrated, remove the `type:` fallback from `read_agent_type()`:

```python
def read_agent_type(frontmatter: dict, default: str = "custom") -> str:
    return frontmatter.get("agent_type", default)
```

**3.5 Add CI lint rule**

Add a pre-commit or CI check that flags `type:` in frontmatter as deprecated:

```bash
# In CI pipeline
if grep -r "^type:" .claude/agents/*.md; then
    echo "WARNING: Use 'agent_type:' instead of 'type:' in agent frontmatter"
    exit 1
fi
```

**Estimated effort**: 2-3 hours
**Risk**: LOW — mechanical changes, validated by CI
**Rollback**: Re-add `type:` compatibility to `read_agent_type()`

---

## 4. Decision Matrix

| Criterion | Do Nothing | Approach A (`type`) | Approach B (`agent_type`) | Approach C (both) | **Recommended** |
|-----------|:---:|:---:|:---:|:---:|:---:|
| **Backwards compatibility** | ✅ | ⚠️ Event breakage | ⚠️ 47 file changes | ✅ | ✅→⚠️ (phased) |
| **Code clarity** | ❌ 3 enums, 2 fields | ⚠️ Builtin shadow | ✅ Clear naming | ⚠️ "Which one?" | ✅ |
| **Maintenance burden** | ❌ Growing | Low | Low | ⚠️ Dual paths | Low |
| **Risk of regression** | ❌ Active bugs | ❌ HIGH | ✅ LOW | ✅ LOW | ✅ LOW |
| **Impact on external users** | ❌ Silent failure | ⚠️ Medium | ⚠️ Medium | ✅ None | ⚠️→✅ (phased) |
| **Alignment with code majority** | N/A | ❌ ~15 files | ✅ ~40+ files | N/A | ✅ |
| **Alignment with docs** | N/A | ❌ Contradicts | ✅ Matches | ⚠️ Both | ✅ |
| **Enum health** | ❌ 4 overlapping | ⚠️ Still 3 enums | ✅ Clean split | ⚠️ Same mess | ✅ |

---

## 5. What NOT to Do

Based on the devil's advocate analysis, these approaches are explicitly rejected:

1. **Option D (Hybrid String + Constants class)**: Unpythonic, provides false comfort of type safety without actual enforcement. The `"engineering"` typo proves constants alone don't prevent inconsistency.

2. **Permanent dual-support**: Creates ongoing confusion for agent authors and doubles testing burden. Temporary dual-support during migration is acceptable.

3. **Free-form strings with no enum**: Loses IDE autocompletion, enables typos, makes refactoring harder. The system benefits from a defined vocabulary.

4. **Enum consolidation without fixing the field name split**: Fixing enums without normalizing `type:` vs `agent_type:` addresses symptoms while ignoring the root cause.

5. **Big-bang migration**: Changing everything at once is high risk. The phased approach (stabilize → consolidate → standardize) ensures rollback at every step.

---

## 6. Implementation Order and Dependencies

```
Phase 1: Stabilize (no breaking changes)
├── 1.1 Create read_agent_type() normalization utility
├── 1.2 Fix ValueError crash at line 444
├── 1.3 Deduplicate 14+ agent file pairs
└── 1.4 Verify: all 7 code paths handle both field names

Phase 2: Consolidate Enums (internal refactoring)
├── 2.1 Create AgentRole enum (str, Enum with from_value())
├── 2.2 Rename Enum 2 → AgentScope
├── 2.3 Deprecate Enum 1 and AgentCategory
├── 2.4 Update import paths (staged)
├── 2.5 Consolidate three AgentTier enums
└── 2.6 Verify: all tests pass, no external contract changes

Phase 3: Standardize field name (external-facing)
├── 3.1 Update template builder to write agent_type:
├── 3.2 Bulk-update 47 agent .md files
├── 3.3 Update remaining Python "type" references
├── 3.4 Remove Phase 1 compatibility layer
├── 3.5 Add CI lint rule
└── 3.6 Verify: grep confirms no "type:" in frontmatter
```

**Dependencies**:
- Phase 2 depends on Phase 1 (normalization needed before enum changes)
- Phase 3 depends on Phase 2 (enum must accept frontmatter values before migration)
- Each phase is independently rollback-able

---

## 7. Testing Requirements

### Phase 1
- Existing tests must continue to pass (normalization is additive)
- Add unit test for `read_agent_type()` covering: `type:` only, `agent_type:` only, both present, neither present
- Add test that `AgentManagementService.load_agent()` does not throw ValueError for any deployed agent
- Verify deduplication didn't remove any unique agents

### Phase 2
- All existing tests pass with new enum names (may need import updates)
- `AgentRole.from_value("engineer")` → `AgentRole.ENGINEER`
- `AgentRole.from_value("unknown_thing")` → `AgentRole.CUSTOM` (no ValueError)
- `AgentRole.from_value("Engineering")` → `AgentRole.CUSTOM` (case mismatch → fallback)
- Verify `AgentScope` serialization matches existing registry data

### Phase 3
- After bulk migration: `grep "^type:" .claude/agents/*.md` returns 0 results
- After migration: all 7 code paths return correct agent types
- CI lint passes on all agent files
- Event data contract unchanged (integration test)

---

## 8. Rollback Plans

| Phase | Rollback Method | Time to Rollback |
|-------|----------------|-----------------|
| Phase 1 | Revert `read_agent_type()` utility; restore deleted duplicate files from git | 5 minutes |
| Phase 2 | Restore deprecated enum aliases; revert import path changes | 15 minutes |
| Phase 3 | Re-add `type:` fallback to `read_agent_type()`; revert template builder | 5 minutes |

---

## 9. Open Questions for Implementation

1. **Should `AgentCategory` be removed entirely or kept as a separate facet?** It has 17 members that partially overlap with `AgentRole`. If it serves a distinct purpose (e.g., UI grouping), it could be retained. If not, it should be deprecated with `AgentRole` as the replacement.

2. **Should the Enum 3 (test) be aligned with `AgentRole`?** The test enum has `BASE`, `PROMPT_ENGINEER`, and `PM` members that don't exist in production. These could be added to `AgentRole` or the test enum could import `AgentRole` and extend it.

3. **What about niche types like `claude-mpm`, `imagemagick`, `memory_manager`?** These are single-agent types that don't justify enum members. They would map to `AgentRole.CUSTOM` through `from_value()`, preserving the raw string in frontmatter but categorizing uniformly in code.

4. **Should the `AgentMetadata.type` field rename (→ `agent_type`) happen in Phase 2 or Phase 3?** Moving it to Phase 2 affects the `to_dict()` serialization key, which is an internal contract. Moving it to Phase 3 keeps Phase 2 purely about enum consolidation.

---

## Appendix: Analysis Documents

| Document | Agent | Key Contribution |
|----------|-------|------------------|
| `01-type-vs-agent_type-code-paths.md` | code-path-tracer | 7 code paths mapped, mismatch diagram, root cause identified |
| `02-enum-relationship-analysis.md` | enum-analyst | 4th classification discovered (AgentCategory), 3 AgentTier enums, dead code identified |
| `03-standardization-impact.md` | impact-analyst | Quantitative comparison, phased migration strategy, Python builtin shadow analysis |
| `04-devils-advocate.md` | devils-advocate | Factual corrections to v1, duplicate files discovered, Option D challenged |
| `problem-analysis.md` (v1) | previous session | Original 3-enum inventory, incompatibility matrix, 4 consolidation options |
