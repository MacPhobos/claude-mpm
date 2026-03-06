# Corrections and Enhancements to analysis-v2

**Date**: 2026-03-03
**Purpose**: Specific corrections and additions that analysis-v2 documents should incorporate

---

## Document-by-Document Corrections

### 01-type-vs-agent_type-code-paths.md

#### Correction 1: Updated File Counts
- **v2 stated**: "47 files use `type:`, 27 use `agent_type:`"
- **v2.1 finding**: 45 files use `type:` (Gen 1), 29 use `agent_type:` (14 Gen 2 underscore + 12 Gen 3 `-agent` suffix + 3 others). Total: 76 deployed files.

#### Correction 2: Three Generations, Not Two
- **v2 implied**: Two generations (newer schema vs older deployed)
- **v2.1 finding**: Three distinct generations:
  - Gen 1: AgentTemplateBuilder output (45 files, kebab-case, `type:`)
  - Gen 2: Migration script output (14 files, underscore, `agent_type:`, schema 1.3.0)
  - Gen 3: Legacy `-agent` suffix files (17 files, `agent_type:`, schema 1.2.0-1.3.0)

#### Enhancement: Remote Agent Source Confirmed
- **v2 identified** the AgentTemplateBuilder conversion on lines 493/568
- **v2.1 confirms** with live data: ALL 48 remote agents use `agent_type:`, ALL 45 Gen 1 deployed agents use `type:`. The conversion is 100% consistent.

#### Enhancement: Add Remote Agent Cache as Code Path
- **v2 documented** 5 code paths for reading `type`/`agent_type`
- **v2.1 adds**: Code Path #6: Remote Agent Source
  - Location: `~/.claude-mpm/cache/agents/bobmatnyc/claude-mpm-agents/agents/`
  - 48 agents, ALL using `agent_type:`
  - This is the authoritative SOURCE from which Gen 1 agents are built

---

### 02-enum-relationship-analysis.md

#### Enhancement: agent_type Values from Remote Source
- **v2** analyzed enum values in code
- **v2.1 provides** complete inventory of `agent_type` values used in the 48 remote agents:
  - 15 distinct values: `engineer` (19), `ops` (8), `qa` (4), `documentation` (2), `research` (2), `security` (1), `specialized` (1), `product` (1), `analysis` (1), `refactoring` (1), `content` (1), `imagemagick` (1), `memory_manager` (1), `system` (1), `claude-mpm` (1)
  - Only 2 overlap with AgentType enum: `specialized`, `system`
  - Most are functional role names, NOT enum values

---

### 03-standardization-impact.md

#### Correction: Archive JSON Templates Are Not Live Sources
- **v2 may imply** archive JSON templates feed the deployment pipeline
- **v2.1 clarifies**: Archive JSON templates are:
  - NOT read by the deployment pipeline (AgentDiscoveryService only scans `*.md`)
  - NOT read by the skill mapping system (path bug — scans wrong directory)
  - Manually maintained as canonical reference
  - Used only by the migration script (one-time)

#### New Section Needed: Skill Mapping Dead Code
- **v2** did not identify the SkillManager path bug
- **v2.1 finding**: The entire skill mapping system in `skill_manager.py` is dead code:
  - Scans `templates/*.json` but JSON files are in `templates/archive/*.json`
  - Loads zero mappings on every initialization
  - `AgentSkillsInjector` (replacement) is also unwired
  - Actual skill flow: AgentTemplateBuilder → frontmatter → Claude Code runtime
  - This should be added to the standardization impact assessment

#### Enhancement: Standardization Now Affects Remote Repo
- **v2** focused on local codebase changes
- **v2.1 adds**: Standardization must also address:
  - 48 remote agents in `bobmatnyc/claude-mpm-agents` repo
  - The git cache sync mechanism
  - The AgentTemplateBuilder conversion code

---

### 04-devils-advocate.md

#### Enhancement: New Argument Against Standardization
- The dead code status of SkillManager and AgentSkillsInjector actually **reduces the urgency** of standardization
- With these systems dormant, fewer code paths are actually affected by the field name split
- The only live path that crosses the boundary is: remote agents (`agent_type`) → AgentTemplateBuilder → deployed agents (`type`)

#### Enhancement: New Argument For Standardization
- 14 duplicate agent pairs and 12 duplicate `-agent` counterparts represent 26 redundant files
- Cleaning up duplicates is impossible without first standardizing the field name (which one to keep?)
- The longer duplicates persist, the more likely someone writes code that depends on a specific duplicate

---

### 05-holistic-recommendation.md

#### Enhancement: Updated Scope of Changes

If standardizing to `agent_type:` (keeping remote source convention):
- Modify AgentTemplateBuilder lines 567-568 (stop converting, write `agent_type:`)
- Update 45 Gen 1 deployed agents (automated: search-replace `type:` → `agent_type:`)
- Update any code that reads `type:` from deployed agents
- No changes needed to remote repo, archive JSON, Gen 2, or Gen 3 files

If standardizing to `type:` (keeping deployed convention):
- Update 48 remote agents in `bobmatnyc/claude-mpm-agents` repo
- Update 39 archive JSON templates
- Update 14 Gen 2 underscore files
- Update 17 Gen 3 `-agent` files
- Simplify AgentTemplateBuilder (remove conversion, pass through)

#### New Recommendation: Cleanup Duplicates
- After standardizing field names, remove the 26 duplicate files:
  - 14 Gen 2 underscore files (all have Gen 1 counterparts)
  - 12 Gen 3 `-agent` files with counterparts
- Preserve 5 unique Gen 3 files that have no counterpart
- This reduces the agent count from 76 to ~50

#### New Recommendation: Address Dead Skill Mapping
- Either fix the path bug in SkillManager or remove the dead code
- Either wire in AgentSkillsInjector or remove it
- Document the actual skill flow path (AgentTemplateBuilder → frontmatter → Claude Code)

---

## Summary of New Facts Discovered in v2.1

| # | Fact | Impact |
|---|---|---|
| 1 | 48 remote agents ALL use `agent_type:` | Confirms remote source is the `agent_type` canonical source |
| 2 | AgentTemplateBuilder conversion verified with live data | Proves field conversion is 100% consistent |
| 3 | Three generations exist (not two) | Gen 3 (`-agent` suffix) adds 17 more files to account for |
| 4 | 14 exact duplicate pairs identified | Cleanup opportunity: 14 underscore files are redundant |
| 5 | 12 `-agent` suffix duplicates identified | Cleanup opportunity: 12 more redundant files |
| 6 | SkillManager has path bug | Loads zero JSON templates; skill mapping is dead |
| 7 | AgentSkillsInjector is unwired | "New" replacement system was designed but never connected |
| 8 | Archive JSON templates maintained manually | No automated process; developer edits with Claude Code |
| 9 | Actual skill flow bypasses both mapping systems | Skills go: source template → AgentTemplateBuilder → frontmatter → Claude Code |
| 10 | `agent_type` values are functional roles | Not AgentType enum values; only 2 of 15 values overlap with enum |
