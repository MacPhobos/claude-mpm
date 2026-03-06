# Three Deployment Generations: Complete Agent Lifecycle Map

**Date**: 2026-03-03
**Session**: Interactive Q&A investigation
**Supplements**: analysis-v2/01-type-vs-agent_type-code-paths.md

---

## Overview

The `.claude/agents/` directory contains 76 agent files produced by three distinct deployment mechanisms. This document maps each generation's complete lifecycle from source to deployed artifact.

---

## Generation 1: AgentTemplateBuilder (Primary Pipeline)

### Characteristics
- **Count**: 45 files
- **Naming**: kebab-case (`golang-engineer.md`)
- **Field**: `type: engineer`
- **Schema**: Simple (name, description, type, version, skills)
- **Content**: ~30KB, ~860 lines (full instructions + BASE_AGENT content)

### Lifecycle

```
Source: GitHub Repository (bobmatnyc/claude-mpm-agents)
    ↓
    ↓  git sync (GitSourceSyncService)
    ↓
Cache: ~/.claude-mpm/cache/agents/bobmatnyc/claude-mpm-agents/agents/
    ↓  agent_type: engineer (in source frontmatter)
    ↓
    ↓  AgentTemplateBuilder.build_agent_markdown()
    ↓    Line 493: agent_type = template_data.get("agent_type", "general")
    ↓    Line 568: frontmatter_lines.append(f"type: {agent_type}")
    ↓    + Appends BASE_AGENT instructions
    ↓    + Adds enhanced description with example
    ↓    + Includes full skills list
    ↓
Deploy: .claude/agents/golang-engineer.md
    type: engineer (CONVERTED from agent_type)
```

### Source → Deployed Field Mapping

| Source Frontmatter | Deployed Frontmatter | Notes |
|---|---|---|
| `name: golang-engineer` | `name: golang-engineer` | Preserved |
| `description: ...` | `description: ...` | Enhanced with example |
| `agent_type: engineer` | `type: engineer` | **CONVERTED** |
| `version: 1.0.0` | `version: "1.0.0"` | Preserved |
| `skills: [...]` | `skills: [...]` | Preserved |
| (not present) | (BASE_AGENT appended) | Added during build |

### Complete File List (45 files)

```
agentic-coder-optimizer.md    engineer.md                  project-organizer.md
api-qa.md                     gcp-ops.md                   prompt-engineer.md
aws-ops.md                    golang-engineer.md            python-engineer.md
clerk-ops.md                  imagemagick.md                qa.md
code-analyzer.md              java-engineer.md              react-engineer.md
dart-engineer.md              javascript-engineer.md        real-user.md
data-engineer.md              local-ops.md                  refactoring-engineer.md
data-scientist.md             nestjs-engineer.md            research.md
digitalocean-ops.md           nextjs-engineer.md            ruby-engineer.md
documentation.md              ops.md                        rust-engineer.md
                              php-engineer.md               security.md
                              phoenix-engineer.md           svelte-engineer.md
                              product-owner.md              tauri-engineer.md
                              typescript-engineer.md        version-control.md
                              vercel-ops.md                 visual-basic-engineer.md
                              web-qa.md                     web-ui.md
```

---

## Generation 2: Migration Script (One-Time Conversion)

### Characteristics
- **Count**: 14 files
- **Naming**: underscore (`golang_engineer.md`)
- **Field**: `agent_type: engineer`
- **Schema**: Rich (`schema_version: 1.3.0`, `agent_id`, `resource_tier`, `tags`, `category`, `color`)
- **Content**: ~10KB, ~285 lines (instructions only, no BASE_AGENT)

### Lifecycle

```
Source: JSON templates
    src/claude_mpm/agents/templates/archive/*.json
    ↓  "agent_type": "engineer" (in JSON)
    ↓
    ↓  scripts/migrate_json_to_markdown.py
    ↓    Line 114: "agent_type": template_data.get("agent_type", "specialized")
    ↓    Preserves agent_type as-is (NO conversion)
    ↓    Adds rich metadata (schema_version, tags, category, etc.)
    ↓
Deploy: .claude/agents/golang_engineer.md
    agent_type: engineer (PRESERVED from JSON source)
```

### Source → Deployed Field Mapping

| JSON Template | Deployed Frontmatter | Notes |
|---|---|---|
| `"agent_id": "golang_engineer"` | `agent_id: golang_engineer` | Preserved |
| `"metadata.name": "Golang Engineer"` | `name: Golang Engineer` | Extracted from nested |
| `"metadata.description": ...` | `description: ...` | Extracted from nested |
| `"agent_type": "engineer"` | `agent_type: engineer` | **PRESERVED** (not converted) |
| `"agent_version": "1.0.0"` | `version: 1.0.0` | Field renamed |
| `"schema_version": "1.3.0"` | `schema_version: 1.3.0` | Preserved |
| `"capabilities.resource_tier"` | `resource_tier: standard` | Extracted from nested |
| `"metadata.tags": [...]` | `tags: [...]` | Extracted from nested |

### Complete File List (14 files)

```
dart_engineer.md       nextjs_engineer.md     ruby_engineer.md
golang_engineer.md     php_engineer.md        rust_engineer.md
java_engineer.md       product_owner.md       svelte_engineer.md
nestjs_engineer.md     react_engineer.md      tauri_engineer.md
                       real_user.md           visual_basic_engineer.md
```

### All 14 Have Gen 1 Counterparts (Duplicate Pairs)

Every Gen 2 file has a corresponding Gen 1 file:
- `golang_engineer.md` ↔ `golang-engineer.md`
- `rust_engineer.md` ↔ `rust-engineer.md`
- etc.

---

## Generation 3: Legacy Agent Deployments

### Characteristics
- **Count**: 17 files (12 with counterparts + 5 unique)
- **Naming**: kebab-case with `-agent` suffix (`qa-agent.md`, `research-agent.md`)
- **Field**: `agent_type:` (mixed values)
- **Schema**: Mixed (`schema_version: 1.2.0` or `1.3.0`)
- **Content**: Variable size

### Lifecycle

```
Source: Unknown earlier deployment mechanism
    ↓  Predates current AgentTemplateBuilder pipeline
    ↓  Uses older schema versions (1.2.0)
    ↓
Deploy: .claude/agents/qa-agent.md
    agent_type: qa (no conversion applied)
```

### Files with Gen 1 Counterparts (12 files)

| Gen 3 File | Gen 1 Counterpart | Schema Version |
|---|---|---|
| `api-qa-agent.md` | `api-qa.md` | 1.2.0 |
| `digitalocean-ops-agent.md` | `digitalocean-ops.md` | 1.3.0 |
| `documentation-agent.md` | `documentation.md` | 1.2.0 |
| `gcp-ops-agent.md` | `gcp-ops.md` | 1.2.0 |
| `javascript-engineer-agent.md` | `javascript-engineer.md` | 1.2.0 |
| `local-ops-agent.md` | `local-ops.md` | 1.3.0 |
| `ops-agent.md` | `ops.md` | 1.2.0 |
| `qa-agent.md` | `qa.md` | 1.3.0 |
| `research-agent.md` | `research.md` | 1.3.0 |
| `security-agent.md` | `security.md` | 1.2.0 |
| `vercel-ops-agent.md` | `vercel-ops.md` | 1.2.0 |
| `web-qa-agent.md` | `web-qa.md` | 1.2.0 |

### Unique Files (No Counterpart) (5 files)

| File | Schema Version | Has `agent_type` |
|---|---|---|
| `content-agent.md` | None | No |
| `memory-manager-agent.md` | None | No |
| `tmux-agent.md` | None | No |
| `mpm-agent-manager.md` | 1.3.0* | Yes |
| `mpm-skills-manager.md` | None* | Yes |
| `web-ui-engineer.md` | None | Yes |

*Note: `mpm-agent-manager.md` and `mpm-skills-manager.md` don't follow the `-agent` suffix pattern but are included as they use `agent_type:` without a counterpart.

---

## Visual Summary

```
                    SOURCE                          DEPLOYED (.claude/agents/)
                    ======                          =========================

GitHub Repo ──→ Git Cache ──→ AgentTemplateBuilder ──→ [45 kebab-case files]
(remote)        (agent_type:)  (converts field)        (type: engineer)
                                                        Gen 1


JSON Templates ──→ migrate_json_to_markdown.py ──→ [14 underscore files]
(archive/)          (preserves field)                (agent_type: engineer)
(agent_type:)                                        Gen 2


Unknown Earlier ──→ ??? ──→ [17 -agent suffix files]
Process               (no conversion)  (agent_type: engineer)
                                        Gen 3
```

---

## Duplicate Overlap Map

```
Logical Agent     Gen 1 (type:)         Gen 2 (agent_type:)    Gen 3 (agent_type:)
=============     =============         ===================    ===================
Golang Engineer   golang-engineer.md    golang_engineer.md     —
Rust Engineer     rust-engineer.md      rust_engineer.md       —
QA                qa.md                 —                      qa-agent.md
Research          research.md           —                      research-agent.md
Security          security.md           —                      security-agent.md
Documentation     documentation.md      —                      documentation-agent.md
...               (45 total)            (14 total)             (17 total)
```

Total unique logical agents: ~53 (76 files - ~23 duplicates)

---

## Cleanup Implications

### Safe to Remove (26 files)
- **14 Gen 2 underscore files**: Every one has a Gen 1 counterpart with richer content
- **12 Gen 3 -agent files with counterparts**: Superseded by Gen 1 versions

### Must Preserve (50 files)
- **45 Gen 1 files**: Primary deployment output, actively used
- **5 Gen 3 unique files**: No counterpart exists (`content-agent.md`, `memory-manager-agent.md`, `tmux-agent.md`, `mpm-agent-manager.md`, `mpm-skills-manager.md`)

### Caution
Before removal, verify that no code references the duplicate files by their specific names (e.g., `qa-agent` vs `qa`, `golang_engineer` vs `golang-engineer`). The PM instructions and delegation matrix may reference specific filenames.
