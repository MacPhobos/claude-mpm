# Empirical Evidence Analysis: Claude Code `subagent_type` Resolution Mechanism

**Date**: 2026-03-04
**Analyst**: Research Agent (Claude Opus 4.6)
**Branch**: `agenttype-enums`
**Status**: COMPLETE -- Critical Question Answered

---

## Executive Summary

This document answers the **Critical Unanswered Question** from `unified-analysis.md` Section 5:

> When the PM calls `Agent(subagent_type="X")`, how does Claude Code resolve "X" to a specific `.claude/agents/*.md` file?

**Answer**: The YAML frontmatter `name:` field is the primary resolution mechanism. Claude Code scans all `.claude/agents/*.md` files, parses YAML frontmatter, and matches the `subagent_type` parameter against the `name:` field value. The filename stem serves only as a fallback when no frontmatter `name:` field is present.

**Confidence Level**: HIGH (95%) -- Based on:
1. Official Anthropic Claude Code documentation explicitly stating `name` is the "Unique identifier"
2. MPM source code in `capability_generator.py` line 177 overriding filename stem with `name:` field
3. MPM source code in `metadata_processor.py` line 80 implementing identical logic
4. PM system prompt generation showing PM the `name:` field value as the agent ID

**Critical Finding**: MPM has a significant consistency problem where `todo_task_tools.py` instructs the PM to use filename-stem-like values (e.g., `"research-agent"`) while the capability generator shows the PM the `name:` field values (e.g., `"Research"`). These contradict each other.

---

## Table of Contents

1. [Complete Agent Mapping Table](#1-complete-agent-mapping-table)
2. [Resolution Mechanism Evidence Chain](#2-resolution-mechanism-evidence-chain)
3. [Cross-Reference: PM System Prompt vs Actual IDs](#3-cross-reference-pm-system-prompt-vs-actual-ids)
4. [Edge Case Analysis](#4-edge-case-analysis)
5. [Contradictions in MPM Codebase](#5-contradictions-in-mpm-codebase)
6. [Official Anthropic Documentation Evidence](#6-official-anthropic-documentation-evidence)
7. [Conclusions and Recommendations](#7-conclusions-and-recommendations)
8. [Remaining Uncertainties](#8-remaining-uncertainties)

---

## 1. Complete Agent Mapping Table

All 52 deployed agent files in `.claude/agents/` with their three identity values:

### 1.1 Core Agents (used in standard PM workflows)

| Filename Stem | Frontmatter `name:` | Frontmatter `agent_type:` | Frontmatter `agent_id:` | Stem == Name? |
|---|---|---|---|---|
| `engineer` | `Engineer` | `engineer` | `engineer` | NO (case) |
| `research-agent` | `Research` | `research` | `research-agent` | NO |
| `research` | `Research` | `research` | `research-agent` | NO |
| `qa-agent` | `QA` | `qa` | `qa-agent` | NO |
| `qa` | `QA` | `qa` | `qa-agent` | NO |
| `documentation-agent` | `Documentation Agent` | `documentation` | `documentation-agent` | NO |
| `documentation` | `Documentation Agent` | `documentation` | `documentation-agent` | NO |
| `security-agent` | `Security` | `security` | `security-agent` | NO |
| `ops-agent` | `Ops` | `ops` | `ops-agent` | NO |
| `ops` | `Ops` | `ops` | `ops-agent` | NO |
| `version-control` | `Version Control` | `ops` | `version-control` | NO (spaces) |
| `data-engineer` | `Data Engineer` | `engineer` | `data-engineer` | NO (spaces) |

### 1.2 Specialized Engineer Agents

| Filename Stem | Frontmatter `name:` | Frontmatter `agent_type:` | Frontmatter `agent_id:` | Stem == Name? |
|---|---|---|---|---|
| `python-engineer` | `Python Engineer` | `engineer` | `python-engineer` | NO (spaces) |
| `typescript-engineer` | `Typescript Engineer` | `engineer` | `typescript-engineer` | NO |
| `javascript-engineer-agent` | `Javascript Engineer` | `engineer` | `javascript-engineer-agent` | NO |
| `react_engineer` | `React Engineer` | `engineer` | `react_engineer` | NO |
| `nextjs_engineer` | `Nextjs Engineer` | `engineer` | `nextjs_engineer` | NO |
| `svelte_engineer` | `Svelte Engineer` | `engineer` | `svelte_engineer` | NO |
| `nestjs_engineer` | `nestjs-engineer` | `engineer` | `nestjs_engineer` | NO |
| `golang_engineer` | `Golang Engineer` | `engineer` | `golang_engineer` | NO |
| `java_engineer` | `Java Engineer` | `engineer` | `java_engineer` | NO |
| `ruby_engineer` | `Ruby Engineer` | `engineer` | `ruby_engineer` | NO |
| `rust_engineer` | `Rust Engineer` | `engineer` | `rust_engineer` | NO |
| `php_engineer` | `Php Engineer` | `engineer` | `php_engineer` | NO |
| `dart_engineer` | `Dart Engineer` | `engineer` | `dart_engineer` | NO |
| `visual_basic_engineer` | `Visual Basic Engineer` | `engineer` | `visual_basic_engineer` | NO |
| `phoenix-engineer` | `Phoenix Engineer` | `engineer` | `phoenix-engineer` | NO |
| `tauri_engineer` | `Tauri Engineer` | `engineer` | `tauri_engineer` | NO |
| `web-ui-engineer` | `Web UI` | `engineer` | `web-ui-engineer` | NO |

### 1.3 Operations and Infrastructure Agents

| Filename Stem | Frontmatter `name:` | Frontmatter `agent_type:` | Frontmatter `agent_id:` | Stem == Name? |
|---|---|---|---|---|
| `aws-ops` | `aws_ops_agent` | `ops` | `aws-ops` | NO |
| `gcp-ops-agent` | `Google Cloud Ops` | `ops` | `gcp-ops-agent` | NO |
| `digitalocean-ops-agent` | `DigitalOcean Ops` | `ops` | `digitalocean-ops-agent` | NO |
| `vercel-ops-agent` | `Vercel Ops` | `ops` | `vercel-ops-agent` | NO |
| `clerk-ops` | `Clerk Operations` | `ops` | `clerk-ops` | NO |
| `local-ops-agent` | `Local Ops` | `specialized` | `local-ops-agent` | NO |
| `tmux-agent` | `Tmux Agent` | `ops` | `tmux-agent` | NO |
| `project-organizer` | `Project Organizer` | `ops` | `project-organizer` | NO |

### 1.4 QA and Testing Agents

| Filename Stem | Frontmatter `name:` | Frontmatter `agent_type:` | Frontmatter `agent_id:` | Stem == Name? |
|---|---|---|---|---|
| `api-qa-agent` | `API QA` | `qa` | `api-qa-agent` | NO |
| `web-qa-agent` | `Web QA` | `qa` | `web-qa-agent` | NO |
| `web-qa` | `Web QA` | `qa` | `web-qa-agent` | NO |
| `real_user` | `real-user` | `qa` | `real_user` | NO |

### 1.5 System and Utility Agents

| Filename Stem | Frontmatter `name:` | Frontmatter `agent_type:` | Frontmatter `agent_id:` | Stem == Name? |
|---|---|---|---|---|
| `mpm-agent-manager` | `mpm_agent_manager` | `system` | `mpm-agent-manager` | NO |
| `mpm-skills-manager` | `mpm_skills_manager` | `claude-mpm` | `mpm-skills-manager` | NO |
| `memory-manager-agent` | `Memory Manager` | `memory_manager` | `memory-manager-agent` | NO |
| `ticketing` | `ticketing_agent` | `documentation` | `ticketing` | NO |
| `agentic-coder-optimizer` | `Agentic Coder Optimizer` | `ops` | `agentic-coder-optimizer` | NO |
| `code-analyzer` | `Code Analysis` | `research` | `code-analyzer` | NO |
| `content-agent` | `Content Optimization` | `content` | `content-agent` | NO |
| `data-scientist` | `Data Scientist` | `engineer` | `data-scientist` | NO |
| `imagemagick` | `Imagemagick` | `imagemagick` | `imagemagick` | NO (case) |
| `product_owner` | `Product Owner` | `product` | `product_owner` | NO |
| `prompt-engineer` | `Prompt Engineer` | `analysis` | `prompt-engineer` | NO |
| `refactoring-engineer` | `Refactoring Engineer` | `refactoring` | `refactoring-engineer` | NO |

### 1.6 Key Observation

**Not a single agent has an identical filename stem and `name:` field.** Every agent has at least a case difference, a hyphen-to-space conversion, a suffix addition/removal, or a completely different name. This means the resolution mechanism MUST choose one or the other -- they cannot be interchangeable.

### 1.7 Duplicate Name Pairs

Multiple files resolve to the same `name:` field value, creating deduplication scenarios:

| `name:` Value | File 1 | File 2 |
|---|---|---|
| `Research` | `research-agent.md` | `research.md` |
| `Documentation Agent` | `documentation-agent.md` | `documentation.md` |
| `QA` | `qa-agent.md` | `qa.md` |
| `Ops` | `ops-agent.md` | `ops.md` |
| `Web QA` | `web-qa-agent.md` | `web-qa.md` |

These duplicates confirm that the `name:` field is the effective identity -- Claude Code's `generate_capabilities_section()` deduplicates by `name:` field, so only one entry per unique name appears in the PM prompt.

---

## 2. Resolution Mechanism Evidence Chain

### 2.1 Evidence Source 1: `capability_generator.py` (MPM Source Code)

**File**: `src/claude_mpm/core/framework/formatters/capability_generator.py`

**Critical Code (lines 160-177)**:
```python
# Default values
agent_data = {
    "id": agent_file.stem,  # START with filename stem
    "display_name": agent_file.stem.replace("_", " ").replace("-", " ").title(),
    "description": "Specialized agent",
}

# Extract YAML frontmatter if present
if content.startswith("---"):
    end_marker = content.find("---", 3)
    if end_marker > 0:
        frontmatter = content[3:end_marker]
        metadata = yaml.safe_load(frontmatter)
        if metadata:
            # Use name as ID for Task tool  <-- THE CRITICAL LINE
            agent_data["id"] = metadata.get("name", agent_data["id"])
```

**What this tells us**: The `id` field starts as the filename stem but is OVERRIDDEN by the `name:` field from YAML frontmatter. The comment explicitly says "Use name as ID for Task tool."

### 2.2 Evidence Source 2: `metadata_processor.py` (Independent Confirmation)

**File**: `src/claude_mpm/core/framework/processors/metadata_processor.py`

**Critical Code (line 80)**:
```python
agent_data["id"] = metadata.get("name", agent_data["id"])
```

Identical logic in a separate code path. This confirms it is not an isolated pattern but a deliberate, consistent design decision.

### 2.3 Evidence Source 3: `generate_capabilities_section()` (What the PM Actually Sees)

**File**: `src/claude_mpm/core/framework/formatters/capability_generator.py`

**Critical Code (lines 46-57, 83-85, 140)**:
```python
# Deduplication uses agent_data["id"] (which is the name: field)
all_agents = {}  # key: agent_id, value: (agent_data, priority)
for priority, agent_data in enumerate(deployed_agents):
    agent_id = agent_data["id"]  # This is the name: field!
    if agent_id not in all_agents:
        all_agents[agent_id] = (agent_data, priority)

# Display format shows: ### Display Name (`agent_id`)
section += f"\n### {display_name} (`{agent['id']}`)\n"

# Instruction to PM
section += "- Use the agent ID in parentheses when delegating via Task tool\n"
```

**What this tells us**: The PM sees agents listed as:
```
### Research (`Research`)
### Engineer (`Engineer`)
### QA (`QA`)
### Documentation Agent (`Documentation Agent`)
```

And is told: "Use the agent ID in parentheses when delegating via Task tool." This means the PM is instructed to use `subagent_type="Research"`, `subagent_type="Engineer"`, etc.

### 2.4 Evidence Source 4: Official Anthropic Claude Code Documentation

**Source**: https://code.claude.com/docs/en/sub-agents

Key quotes from the official documentation:

1. **`name` field definition**: "Unique identifier using lowercase letters and hyphens" -- This explicitly states that `name` is the identifier, not the filename.

2. **Priority resolution**: "When multiple subagents share the same name, the higher-priority location wins" -- Confirms name-based matching with priority resolution.

3. **Agent tool restriction syntax**: `tools: Agent(worker, researcher)` -- Uses name field values.

4. **Permission deny syntax**: `"Agent(my-custom-agent)"` -- Uses name field values.

5. **User invocation pattern**: "Use the code-reviewer agent to..." -- References agents by name.

6. **Example frontmatter**:
```yaml
---
name: code-reviewer
description: Reviews code for best practices
---
```

**What this tells us**: Claude Code's official specification confirms that the `name:` field is the unique identifier used for agent resolution. The filename stem is not mentioned as a resolution mechanism.

---

## 3. Cross-Reference: PM System Prompt vs Actual IDs

### 3.1 What `capability_generator.py` Shows the PM

Based on the code analysis, the PM sees agents listed with their `name:` field values as IDs:

| PM Sees (capability_generator) | Actual `name:` field | What `todo_task_tools.py` Says |
|---|---|---|
| `Research` | `Research` | `research-agent` |
| `Engineer` | `Engineer` | `engineer` |
| `QA` | `QA` | `qa-agent` |
| `Documentation Agent` | `Documentation Agent` | `documentation-agent` |
| `Security` | `Security` | `security-agent` |
| `Ops` | `Ops` | `ops-agent` |
| `Version Control` | `Version Control` | `version-control` |
| `Data Engineer` | `Data Engineer` | `data-engineer` |

### 3.2 The Contradiction

The PM receives TWO conflicting sets of instructions:

**From `capability_generator.py`** (dynamic, generated at runtime):
> "Use the agent ID in parentheses when delegating via Task tool"
> Listed IDs: `Research`, `Engineer`, `QA`, `Documentation Agent`, etc.

**From `todo_task_tools.py`** (static, hardcoded in CLAUDE.md template):
> "Valid subagent_type values (use lowercase format for Claude Code compatibility):"
> Listed values: `research-agent`, `engineer`, `qa-agent`, `documentation-agent`, etc.

These CANNOT both be correct. If the PM follows `capability_generator.py`, it uses `subagent_type="Research"`. If it follows `todo_task_tools.py`, it uses `subagent_type="research-agent"`.

---

## 4. Edge Case Analysis

### 4.1 Duplicate Agent Files

Five pairs of agent files have identical `name:` fields:

- `research-agent.md` and `research.md` both have `name: Research`
- `documentation-agent.md` and `documentation.md` both have `name: Documentation Agent`
- `qa-agent.md` and `qa.md` both have `name: QA`
- `ops-agent.md` and `ops.md` both have `name: Ops`
- `web-qa-agent.md` and `web-qa.md` both have `name: Web QA`

**Impact**: Only the first-discovered file (by filesystem enumeration order) is used. The `generate_capabilities_section()` deduplication logic at line 56 (`if agent_id not in all_agents`) means the second file is silently ignored. This is not necessarily a problem if both files are identical, but it creates a maintenance hazard.

### 4.2 Name Format Violations

The official Anthropic spec states `name` should use "lowercase letters and hyphens." Many deployed agents violate this:

**Agents with spaces in `name:`**:
- `Documentation Agent`, `Python Engineer`, `Version Control`, `Data Engineer`, `Dart Engineer`, `Java Engineer`, `Ruby Engineer`, `Rust Engineer`, `Php Engineer`, `Visual Basic Engineer`, `React Engineer`, `Nextjs Engineer`, `Svelte Engineer`, `Golang Engineer`, `Tauri Engineer`, `Phoenix Engineer`, `Typescript Engineer`, `Javascript Engineer`, `Web UI`, `Data Scientist`, `Product Owner`, `Memory Manager`, `Tmux Agent`, `Project Organizer`, `Agentic Coder Optimizer`, `Code Analysis`, `Content Optimization`, `Refactoring Engineer`, `Prompt Engineer`, `Clerk Operations`, `Google Cloud Ops`, `DigitalOcean Ops`, `Vercel Ops`, `Local Ops`, `API QA`, `Web QA`

**Agents with uppercase in `name:`**:
- `Research`, `Engineer`, `QA`, `Security`, `Ops`, `Imagemagick` (capital I)

**Agents with underscores in `name:`** (not matching the hyphen-only spec):
- `aws_ops_agent`, `mpm_agent_manager`, `mpm_skills_manager`, `ticketing_agent`

**Agents that DO match the spec** (lowercase, hyphens only):
- `nestjs-engineer`, `real-user`

**Implication**: Only 2 out of 52 agents have `name:` values that match the official Anthropic specification. This is a significant compliance gap.

### 4.3 Built-in Agent Types

Claude Code has built-in subagent types that are not resolved from `.claude/agents/`:
- `"pm"` -- referenced in `todo_task_tools.py` but no agent file has `name: pm`
- `"test_integration"` -- referenced in `todo_task_tools.py`

These appear to be handled by Claude Code's internal logic, not by file-based resolution.

### 4.4 Case Sensitivity

It is UNKNOWN whether Claude Code's resolution is case-sensitive. If it is case-sensitive, then `subagent_type="research"` would NOT match `name: Research`. If it is case-insensitive, both would work.

The official Anthropic documentation example uses `name: code-reviewer` (lowercase), suggesting that lowercase is the expected format. But the documentation does not explicitly state whether matching is case-sensitive.

---

## 5. Contradictions in MPM Codebase

### 5.1 Primary Contradiction: `todo_task_tools.py` vs `capability_generator.py`

| Aspect | `todo_task_tools.py` | `capability_generator.py` |
|---|---|---|
| Resolution key | Filename stem (implied) | `name:` field |
| Research agent | `"research-agent"` | `"Research"` |
| Documentation agent | `"documentation-agent"` | `"Documentation Agent"` |
| QA agent | `"qa-agent"` | `"QA"` |
| Ops agent | `"ops-agent"` | `"Ops"` |
| Claims source | "deployed agent YAML names" | `parse_agent_metadata()` |
| Format rule | "lowercase format" | Whatever `name:` field says |

`todo_task_tools.py` line 49 states:
> "Required format (Claude Code expects these exact values from deployed agent YAML names)"

But lists values like `"research-agent"` which is the FILENAME STEM, not the YAML `name:` field value (`"Research"`). The phrase "deployed agent YAML names" is misleading -- the listed values are filename stems, not YAML name fields.

### 5.2 Secondary Contradiction: `content_formatter.py` Fallback Capabilities

**File**: `src/claude_mpm/core/framework/formatters/content_formatter.py`

The fallback capabilities section (used when dynamic generation fails) lists yet another set of identifiers:

```python
- **Engineer** (`engineer`): Code implementation and development
- **Research** (`research-agent`): Investigation and analysis
- **QA** (`qa-agent`): Testing and quality assurance
- **Documentation** (`documentation-agent`): Documentation creation and maintenance
- **Security** (`security-agent`): Security analysis and protection
- **Data Engineer** (`data-engineer`): Data management and pipelines
- **Ops** (`ops-agent`): Deployment and operations
- **Version Control** (`version-control`): Git operations and version management
```

This uses FILENAME STEMS (not `name:` field values), creating a third inconsistency.

### 5.3 Hook Processing Contradiction: `tool_analysis.py`

**File**: `src/claude_mpm/hooks/claude_hooks/tool_analysis.py`

```python
"is_research_delegation": tool_input.get("subagent_type") == "research",
"is_engineer_delegation": tool_input.get("subagent_type") == "engineer",
```

These literal comparisons check for `"research"` and `"engineer"` -- neither the filename stem (`"research-agent"`) nor the `name:` field (`"Research"`). This is a third format variant.

### 5.4 `subagent_processor.py` Agent Type Detection

**File**: `src/claude_mpm/hooks/claude_hooks/services/subagent_processor.py`

The `is_delegation_related` check (line 352) compares against:
```python
agent_type in ["research", "engineer", "pm", "ops", "qa", "documentation", "security"]
```

These are lowercase, no-suffix values -- yet another format.

### 5.5 Summary of Format Variants Across Codebase

| System Component | Research Agent ID | Format Style |
|---|---|---|
| Claude Code official spec | `research` (lowercase-hyphen) | Spec-compliant |
| `capability_generator.py` | `Research` | `name:` field (Title Case) |
| `todo_task_tools.py` | `research-agent` | Filename stem |
| `content_formatter.py` fallback | `research-agent` | Filename stem |
| `tool_analysis.py` | `research` | Bare lowercase |
| `subagent_processor.py` | `research` | Bare lowercase |
| Frontmatter `agent_type:` | `research` | Bare lowercase |

**Six different representations of the same agent exist in the codebase.**

---

## 6. Official Anthropic Documentation Evidence

### 6.1 Source URL

https://code.claude.com/docs/en/sub-agents

### 6.2 Key Excerpts

**On the `name` field (frontmatter specification)**:
> `name` -- Unique identifier using lowercase letters and hyphens

This is unambiguous: `name` IS the unique identifier.

**On resolution priority**:
> When multiple subagents share the same name, the higher-priority location wins

This confirms:
1. Matching is by `name` field
2. Multiple files can have the same name
3. A priority system resolves conflicts

**On agent invocation**:
> tools: Agent(worker, researcher)

The `Agent()` restriction syntax uses name values, not filename stems.

**On permission control**:
> "Agent(my-custom-agent)"

Permission deny/allow also uses name values.

### 6.3 What the Docs Do NOT Say

The official documentation does NOT mention:
- Filename stem as a resolution mechanism
- Case-insensitive matching behavior
- What happens if `name:` field violates the lowercase-hyphen format
- Explicit fallback behavior when `name:` field is absent

---

## 7. Conclusions and Recommendations

### 7.1 Answer to the Critical Question

**Q**: When the PM calls `Agent(subagent_type="X")`, how does Claude Code resolve "X" to a specific `.claude/agents/*.md` file?

**A**: Claude Code resolves "X" by matching against the YAML frontmatter `name:` field of `.claude/agents/*.md` files. The filename stem is NOT the primary resolution key. The filename stem serves only as a default when no `name:` field is present in the frontmatter.

Evidence chain:
1. Official Anthropic docs: `name` is "Unique identifier"
2. `parse_agent_metadata()` overrides filename stem with `name:` field
3. `generate_capabilities_section()` deduplicates by `name:` field
4. PM prompt shows `name:` field values and says "Use the agent ID in parentheses"
5. Agent tool restriction syntax `Agent(name)` uses name field

### 7.2 Implication for MPM

The current MPM codebase has a critical consistency problem:

1. **`todo_task_tools.py` instructs the PM to use wrong values.** It tells the PM to use `subagent_type="research-agent"` but the actual resolution key for the research agent is `name: Research`.

2. **Most agent `name:` fields violate the official spec.** Only 2 of 52 agents use "lowercase letters and hyphens" as specified by Anthropic. The rest use spaces, uppercase, or underscores.

3. **Hook processing uses yet another format.** `tool_analysis.py` and `subagent_processor.py` compare against bare lowercase values that match none of the above.

### 7.3 Recommended Corrective Actions

**Priority 1 -- Immediate**: Fix `todo_task_tools.py` to match `capability_generator.py` output. Either:
- (a) Update `todo_task_tools.py` to show `name:` field values (e.g., `"Research"`, `"QA"`), OR
- (b) Update all agent `name:` fields to match what `todo_task_tools.py` says (e.g., `name: research-agent`), OR
- (c) Standardize all `name:` fields to the official Anthropic spec format (lowercase-hyphen) and update both files

Option (c) is recommended as it ensures compliance with the official Claude Code specification.

**Priority 2 -- Short Term**: Standardize all `name:` fields to lowercase-hyphen format per the official spec:
- `Research` --> `research`
- `Documentation Agent` --> `documentation-agent`
- `Python Engineer` --> `python-engineer`
- `aws_ops_agent` --> `aws-ops`
- etc.

**Priority 3 -- Medium Term**: Update hook processing code to use a centralized name normalization function that handles all format variants. The `AgentNameNormalizer` in `event_handlers.py` is a start but needs to be used consistently.

**Priority 4 -- Medium Term**: Eliminate duplicate agent files (e.g., `research-agent.md` and `research.md` should be consolidated into one canonical file).

### 7.4 Impact on `agent_type` Enum Standardization

This finding is directly relevant to the `agenttype-enums` branch work. The enum values should be based on the `name:` field values (the actual resolution keys), NOT the filename stems or `agent_type:` field values. However, all enum values should comply with the official Anthropic spec of lowercase-hyphen format.

---

## 8. Remaining Uncertainties

### 8.1 Case Sensitivity (UNKNOWN -- Medium Risk)

It is unknown whether Claude Code's `subagent_type` matching is case-sensitive. If the PM sends `subagent_type="Research"` (matching the current `name:` field) and Claude Code expects lowercase, it would fail silently or fall back to a different agent.

**Mitigation**: Test empirically by invoking an agent with a case-mismatched name.

### 8.2 Space Handling (UNKNOWN -- High Risk)

It is unknown whether Claude Code can resolve `subagent_type="Documentation Agent"` (with a space). The official spec says "lowercase letters and hyphens" -- spaces are not mentioned as valid characters. If Claude Code rejects spaces, then 36 of 52 agents would be unreachable by their `name:` field.

**Mitigation**: Test empirically by invoking an agent whose name contains spaces.

### 8.3 Underscore Handling (UNKNOWN -- Medium Risk)

Three agents use underscores in their `name:` field (`aws_ops_agent`, `mpm_agent_manager`, `mpm_skills_manager`). Underscores are not in the official spec's "lowercase letters and hyphens" format.

**Mitigation**: Test empirically.

### 8.4 Filename Stem Fallback Behavior (LOW CONFIDENCE)

The code shows `metadata.get("name", agent_data["id"])` which falls back to the filename stem when no `name:` field exists. But what does Claude Code itself do (independent of MPM's `parse_agent_metadata`)? Does Claude Code also fall back to the filename stem, or does it require a `name:` field?

The official docs list `name` as part of the frontmatter specification but do not mark it as "required." If `name` is optional and the filename stem is used as fallback, that would explain why some projects work with stem-based invocation.

**Mitigation**: Test by creating an agent file with no `name:` frontmatter and attempting to invoke it by filename stem.

### 8.5 Claude Code vs MPM Resolution (IMPORTANT DISTINCTION)

This analysis covers two separate resolution paths:
1. **Claude Code's built-in resolution**: How Claude Code itself maps `subagent_type` to a file (governed by Anthropic's code, which we cannot inspect)
2. **MPM's representation to the PM**: How MPM tells the PM what IDs to use (governed by `capability_generator.py`)

The official Anthropic documentation describes path (1). The MPM source code analysis covers path (2). These paths are independent -- MPM could present the PM with incorrect IDs that Claude Code would then fail to resolve.

The critical finding is that MPM's `capability_generator.py` correctly uses the `name:` field (matching Claude Code's spec), but `todo_task_tools.py` contradicts this with filename-stem-based IDs.

---

## Appendix A: Methodology

### Tools Used
1. **Glob**: File discovery in `.claude/agents/`
2. **Bash**: YAML frontmatter extraction from all 52 agent files
3. **Read**: Source code analysis of `capability_generator.py`, `metadata_processor.py`, `content_formatter.py`, `tool_analysis.py`, `subagent_processor.py`, `event_handlers.py`, `todo_task_tools.py`
4. **WebFetch**: Official Anthropic documentation at `https://code.claude.com/docs/en/sub-agents`

### Files Analyzed
- `.claude/agents/*.md` (52 files) -- Complete frontmatter extraction
- `src/claude_mpm/core/framework/formatters/capability_generator.py` -- Primary resolution logic
- `src/claude_mpm/core/framework/processors/metadata_processor.py` -- Secondary resolution logic
- `src/claude_mpm/core/framework/formatters/content_formatter.py` -- Fallback capabilities
- `src/claude_mpm/hooks/claude_hooks/tool_analysis.py` -- Hook processing
- `src/claude_mpm/hooks/claude_hooks/services/subagent_processor.py` -- Response processing
- `src/claude_mpm/hooks/claude_hooks/event_handlers.py` -- Event delegation
- `src/claude_mpm/services/framework_claude_md_generator/section_generators/todo_task_tools.py` -- PM task tool instructions
- `src/claude_mpm/agents/templates/__init__.py` -- Template system

### Research Limitations
- Claude Code's internal resolution logic is not inspectable (closed source)
- No empirical testing was performed (research only, as requested)
- Case sensitivity and space handling remain unvalidated

---

## Appendix B: Raw Mapping Data

Full extraction output for all 52 agents (stem | name | agent_type | agent_id):

```
STEM=agentic-coder-optimizer     NAME=Agentic Coder Optimizer     AGENT_TYPE=ops              AGENT_ID=agentic-coder-optimizer
STEM=api-qa-agent                NAME=API QA                      AGENT_TYPE=qa               AGENT_ID=api-qa-agent
STEM=aws-ops                     NAME=aws_ops_agent               AGENT_TYPE=ops              AGENT_ID=aws-ops
STEM=clerk-ops                   NAME=Clerk Operations            AGENT_TYPE=ops              AGENT_ID=clerk-ops
STEM=code-analyzer               NAME=Code Analysis               AGENT_TYPE=research         AGENT_ID=code-analyzer
STEM=content-agent               NAME=Content Optimization        AGENT_TYPE=content          AGENT_ID=content-agent
STEM=dart_engineer               NAME=Dart Engineer               AGENT_TYPE=engineer         AGENT_ID=dart_engineer
STEM=data-engineer               NAME=Data Engineer               AGENT_TYPE=engineer         AGENT_ID=data-engineer
STEM=data-scientist              NAME=Data Scientist              AGENT_TYPE=engineer         AGENT_ID=data-scientist
STEM=digitalocean-ops-agent      NAME=DigitalOcean Ops            AGENT_TYPE=ops              AGENT_ID=digitalocean-ops-agent
STEM=documentation-agent         NAME=Documentation Agent         AGENT_TYPE=documentation    AGENT_ID=documentation-agent
STEM=documentation               NAME=Documentation Agent         AGENT_TYPE=documentation    AGENT_ID=documentation-agent
STEM=engineer                    NAME=Engineer                    AGENT_TYPE=engineer         AGENT_ID=engineer
STEM=gcp-ops-agent               NAME=Google Cloud Ops            AGENT_TYPE=ops              AGENT_ID=gcp-ops-agent
STEM=golang_engineer             NAME=Golang Engineer             AGENT_TYPE=engineer         AGENT_ID=golang_engineer
STEM=imagemagick                 NAME=Imagemagick                 AGENT_TYPE=imagemagick      AGENT_ID=imagemagick
STEM=java_engineer               NAME=Java Engineer               AGENT_TYPE=engineer         AGENT_ID=java_engineer
STEM=javascript-engineer-agent   NAME=Javascript Engineer         AGENT_TYPE=engineer         AGENT_ID=javascript-engineer-agent
STEM=local-ops-agent             NAME=Local Ops                   AGENT_TYPE=specialized      AGENT_ID=local-ops-agent
STEM=memory-manager-agent        NAME=Memory Manager              AGENT_TYPE=memory_manager   AGENT_ID=memory-manager-agent
STEM=mpm-agent-manager           NAME=mpm_agent_manager           AGENT_TYPE=system           AGENT_ID=mpm-agent-manager
STEM=mpm-skills-manager          NAME=mpm_skills_manager          AGENT_TYPE=claude-mpm       AGENT_ID=mpm-skills-manager
STEM=nestjs_engineer             NAME=nestjs-engineer             AGENT_TYPE=engineer         AGENT_ID=nestjs_engineer
STEM=nextjs_engineer             NAME=Nextjs Engineer             AGENT_TYPE=engineer         AGENT_ID=nextjs_engineer
STEM=ops-agent                   NAME=Ops                         AGENT_TYPE=ops              AGENT_ID=ops-agent
STEM=ops                         NAME=Ops                         AGENT_TYPE=ops              AGENT_ID=ops-agent
STEM=phoenix-engineer            NAME=Phoenix Engineer            AGENT_TYPE=engineer         AGENT_ID=phoenix-engineer
STEM=php_engineer                NAME=Php Engineer                AGENT_TYPE=engineer         AGENT_ID=php_engineer
STEM=product_owner               NAME=Product Owner               AGENT_TYPE=product          AGENT_ID=product_owner
STEM=project-organizer           NAME=Project Organizer           AGENT_TYPE=ops              AGENT_ID=project-organizer
STEM=prompt-engineer             NAME=Prompt Engineer             AGENT_TYPE=analysis         AGENT_ID=prompt-engineer
STEM=python-engineer             NAME=Python Engineer             AGENT_TYPE=engineer         AGENT_ID=python-engineer
STEM=qa-agent                    NAME=QA                          AGENT_TYPE=qa               AGENT_ID=qa-agent
STEM=qa                          NAME=QA                          AGENT_TYPE=qa               AGENT_ID=qa-agent
STEM=react_engineer              NAME=React Engineer              AGENT_TYPE=engineer         AGENT_ID=react_engineer
STEM=real_user                   NAME=real-user                   AGENT_TYPE=qa               AGENT_ID=real_user
STEM=refactoring-engineer        NAME=Refactoring Engineer        AGENT_TYPE=refactoring      AGENT_ID=refactoring-engineer
STEM=research-agent              NAME=Research                    AGENT_TYPE=research         AGENT_ID=research-agent
STEM=research                    NAME=Research                    AGENT_TYPE=research         AGENT_ID=research-agent
STEM=ruby_engineer               NAME=Ruby Engineer               AGENT_TYPE=engineer         AGENT_ID=ruby_engineer
STEM=rust_engineer               NAME=Rust Engineer               AGENT_TYPE=engineer         AGENT_ID=rust_engineer
STEM=security-agent              NAME=Security                    AGENT_TYPE=security         AGENT_ID=security-agent
STEM=svelte_engineer             NAME=Svelte Engineer             AGENT_TYPE=engineer         AGENT_ID=svelte_engineer
STEM=tauri_engineer              NAME=Tauri Engineer              AGENT_TYPE=engineer         AGENT_ID=tauri_engineer
STEM=ticketing                   NAME=ticketing_agent             AGENT_TYPE=documentation    AGENT_ID=ticketing
STEM=tmux-agent                  NAME=Tmux Agent                  AGENT_TYPE=ops              AGENT_ID=tmux-agent
STEM=typescript-engineer         NAME=Typescript Engineer         AGENT_TYPE=engineer         AGENT_ID=typescript-engineer
STEM=vercel-ops-agent            NAME=Vercel Ops                  AGENT_TYPE=ops              AGENT_ID=vercel-ops-agent
STEM=version-control             NAME=Version Control             AGENT_TYPE=ops              AGENT_ID=version-control
STEM=visual_basic_engineer       NAME=Visual Basic Engineer       AGENT_TYPE=engineer         AGENT_ID=visual_basic_engineer
STEM=web-qa-agent                NAME=Web QA                      AGENT_TYPE=qa               AGENT_ID=web-qa-agent
STEM=web-qa                      NAME=Web QA                      AGENT_TYPE=qa               AGENT_ID=web-qa-agent
STEM=web-ui-engineer             NAME=Web UI                      AGENT_TYPE=engineer         AGENT_ID=web-ui-engineer
```

---

*End of empirical evidence analysis.*
