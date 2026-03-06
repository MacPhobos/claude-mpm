# Remote Agent Source: Field Usage and Conversion Evidence

**Date**: 2026-03-03
**Session**: Interactive Q&A investigation
**Supplements**: analysis-v2/01-type-vs-agent_type-code-paths.md

---

## Overview

This document provides concrete evidence of the `agent_type` → `type` field conversion by examining the remote agent source (GitHub cache) and comparing it with deployed agents.

---

## Remote Agent Cache Location

```
~/.claude-mpm/cache/agents/bobmatnyc/claude-mpm-agents/agents/
├── claude-mpm/     (3 agents: mpm-agent-manager, mpm-skills-manager, BASE-AGENT)
├── documentation/  (2 agents: documentation, ticketing)
├── engineering/    (19+ agents: dart-engineer, golang-engineer, etc.)
├── ops/            (8+ agents: aws-ops, gcp-ops, etc.)
├── qa/             (4+ agents: qa, web-qa, api-qa, real-user)
├── security/       (1 agent: security)
└── universal/      (5+ agents: research, code-analyzer, etc.)
```

**Total remote agents**: 48 (excluding 5 BASE-AGENT.md files)

---

## Key Finding: 100% of Remote Agents Use `agent_type`

Every single remote agent uses `agent_type:` in its frontmatter. Not a single one uses `type:`.

### Complete Remote Agent Field Inventory

| Remote Agent | `agent_type` Value |
|---|---|
| agentic-coder-optimizer.md | `ops` |
| api-qa.md | `qa` |
| aws-ops.md | `ops` |
| clerk-ops.md | `ops` |
| code-analyzer.md | `research` |
| content-agent.md | `content` |
| dart-engineer.md | `engineer` |
| data-engineer.md | `engineer` |
| data-scientist.md | `engineer` |
| digitalocean-ops.md | `ops` |
| documentation.md | `documentation` |
| engineer.md | `engineer` |
| gcp-ops.md | `ops` |
| golang-engineer.md | `engineer` |
| imagemagick.md | `imagemagick` |
| java-engineer.md | `engineer` |
| javascript-engineer.md | `engineer` |
| local-ops.md | `specialized` |
| memory-manager-agent.md | `memory_manager` |
| mpm-agent-manager.md | `system` |
| mpm-skills-manager.md | `claude-mpm` |
| nestjs-engineer.md | `engineer` |
| nextjs-engineer.md | `engineer` |
| ops.md | `ops` |
| phoenix-engineer.md | `engineer` |
| php-engineer.md | `engineer` |
| product-owner.md | `product` |
| project-organizer.md | `ops` |
| prompt-engineer.md | `analysis` |
| python-engineer.md | `engineer` |
| qa.md | `qa` |
| react-engineer.md | `engineer` |
| real-user.md | `qa` |
| refactoring-engineer.md | `refactoring` |
| research.md | `research` |
| ruby-engineer.md | `engineer` |
| rust-engineer.md | `engineer` |
| security.md | `security` |
| svelte-engineer.md | `engineer` |
| tauri-engineer.md | `engineer` |
| ticketing.md | `documentation` |
| tmux-agent.md | `ops` |
| typescript-engineer.md | `engineer` |
| vercel-ops.md | `ops` |
| version-control.md | `ops` |
| visual-basic-engineer.md | `engineer` |
| web-qa.md | `qa` |
| web-ui.md | `engineer` |

---

## agent_type Value Distribution (Remote Agents)

| `agent_type` Value | Count | Agents |
|---|---|---|
| `engineer` | 19 | dart-, data-, golang-, java-, javascript-, nestjs-, nextjs-, php-, phoenix-, python-, react-, ruby-, rust-, svelte-, tauri-, typescript-, visual-basic-engineer, web-ui, engineer |
| `ops` | 8 | agentic-coder-optimizer, aws-, clerk-, digitalocean-, gcp-ops, ops, project-organizer, tmux-agent, vercel-, version-control |
| `qa` | 4 | api-qa, qa, real-user, web-qa |
| `documentation` | 2 | documentation, ticketing |
| `research` | 2 | code-analyzer, research |
| `security` | 1 | security |
| `specialized` | 1 | local-ops |
| `product` | 1 | product-owner |
| `analysis` | 1 | prompt-engineer |
| `refactoring` | 1 | refactoring-engineer |
| `content` | 1 | content-agent |
| `imagemagick` | 1 | imagemagick |
| `memory_manager` | 1 | memory-manager-agent |
| `system` | 1 | mpm-agent-manager |
| `claude-mpm` | 1 | mpm-skills-manager |

### Observations

1. **Values are functional roles**, NOT the AgentType enum (`core/project/custom/system/specialized`)
2. **Only 2 values overlap** with the AgentType enum: `specialized` (local-ops) and `system` (mpm-agent-manager)
3. **Some values are unique to a single agent**: `imagemagick`, `memory_manager`, `claude-mpm`, `content`
4. **Inconsistent use of underscore**: `memory_manager` uses underscore while all others use single words or hyphens

---

## Conversion Evidence: Remote → Deployed

### Verified Conversions

| Remote File | Remote Field | Deployed File | Deployed Field |
|---|---|---|---|
| `golang-engineer.md` | `agent_type: engineer` | `golang-engineer.md` | `type: engineer` |
| `research.md` | `agent_type: research` | `research.md` | `type: research` |
| `security.md` | `agent_type: security` | `security.md` | `type: security` |
| `qa.md` | `agent_type: qa` | `qa.md` | `type: qa` |
| `documentation.md` | `agent_type: documentation` | `documentation.md` | `type: documentation` |

### The Conversion Code

```python
# src/claude_mpm/services/agents/deployment/agent_template_builder.py

# Line 493: READ agent_type from source
agent_type = template_data.get("agent_type", "general")

# Line 567-568: WRITE as type to deployed file
if agent_type and agent_type != "general":
    frontmatter_lines.append(f"type: {agent_type}")
```

### What Gets Lost in Translation

| Present in Remote Source | Present in Deployed | Notes |
|---|---|---|
| `agent_type: engineer` | `type: engineer` | Field name changed |
| `model: sonnet` | (sometimes present) | Depends on template |
| Rich description | Enhanced description with example | Rewritten |
| Original instructions | Instructions + BASE_AGENT | Merged |
| Original skills list | Same skills list | Preserved |
| (nothing) | Color, formatting | Added by builder |

---

## Implications for Standardization

### If Standardizing to `type:`
- Remote agents repo would need updating (48 agents: `agent_type` → `type`)
- AgentTemplateBuilder conversion code (lines 493, 567-568) would simplify
- Archive JSON templates (39 files) would need updating
- Migration script would need updating

### If Standardizing to `agent_type:`
- AgentTemplateBuilder would need to STOP converting (write `agent_type:` instead of `type:`)
- All 45 deployed Gen 1 agents would need field rename (`type:` → `agent_type:`)
- All downstream readers of deployed agents would need updating
- Remote agents would need NO changes (already use `agent_type:`)

### Current State Risk
- AgentTemplateBuilder is the **single point of conversion** between the two field names
- If any code reads deployed agents expecting `agent_type:`, it won't find it (Gen 1 agents)
- If any code reads remote agents expecting `type:`, it won't find it (all remote agents)
- The conversion is invisible — no logging at the point of field name change
