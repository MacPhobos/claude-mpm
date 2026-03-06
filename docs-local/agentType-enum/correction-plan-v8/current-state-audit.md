# Current State Audit — Agent Name Resolution

**Date**: 2026-03-05
**Purpose**: Reference data for correction-plan-v8

---

## Complete Agent Inventory

### Deployed Agents (`.claude/agents/` — 40 files)

| Filename | `name:` Field | `agent_id:` | Has `author:`? |
|----------|--------------|-------------|---------------|
| `agentic-coder-optimizer.md` | `Agentic Coder Optimizer` | `agentic-coder-optimizer` | YES |
| `aws-ops.md` | `aws_ops_agent` | `aws-ops` | NO |
| `clerk-ops.md` | `Clerk Operations` | `clerk-ops` | YES |
| `code-analyzer.md` | `Code Analysis` | `code-analyzer` | NO |
| `content-agent.md` | `Content Optimization` | `content-agent` | YES |
| `dart-engineer.md` | `Dart Engineer` | `dart-engineer` | YES |
| `data-engineer.md` | `Data Engineer` | `data-engineer` | YES |
| `data-scientist.md` | `Data Scientist` | `data-scientist` | YES |
| `documentation.md` | `Documentation Agent` | `documentation-agent` | YES |
| `engineer.md` | `Engineer` | `engineer` | YES |
| `golang-engineer.md` | `Golang Engineer` | `golang-engineer` | YES |
| `imagemagick.md` | `Imagemagick` | `imagemagick` | YES |
| `java-engineer.md` | `Java Engineer` | `java-engineer` | YES |
| `memory-manager-agent.md` | `Memory Manager` | `memory-manager-agent` | NO |
| `mpm-agent-manager.md` | `mpm_agent_manager` | `mpm-agent-manager` | YES |
| `mpm-skills-manager.md` | `mpm_skills_manager` | `mpm-skills-manager` | YES |
| `nestjs-engineer.md` | `nestjs-engineer` | `nestjs-engineer` | NO |
| `nextjs-engineer.md` | `Nextjs Engineer` | `nextjs-engineer` | YES |
| `ops.md` | `Ops` | `ops-agent` | YES |
| `phoenix-engineer.md` | `Phoenix Engineer` | `phoenix-engineer` | YES |
| `php-engineer.md` | `Php Engineer` | `php-engineer` | YES |
| `product-owner.md` | `Product Owner` | `product-owner` | YES |
| `project-organizer.md` | `Project Organizer` | `project-organizer` | YES |
| `prompt-engineer.md` | `Prompt Engineer` | `prompt-engineer` | YES |
| `python-engineer.md` | `Python Engineer` | `python-engineer` | YES |
| `qa.md` | `QA` | `qa-agent` | YES |
| `react-engineer.md` | `React Engineer` | `react-engineer` | YES |
| `real-user.md` | `real-user` | `real-user` | NO |
| `refactoring-engineer.md` | `Refactoring Engineer` | `refactoring-engineer` | YES |
| `research.md` | `Research` | `research-agent` | NO |
| `ruby-engineer.md` | `Ruby Engineer` | `ruby-engineer` | YES |
| `rust-engineer.md` | `Rust Engineer` | `rust-engineer` | YES |
| `svelte-engineer.md` | `Svelte Engineer` | `svelte-engineer` | YES |
| `tauri-engineer.md` | `Tauri Engineer` | `tauri-engineer` | YES |
| `ticketing.md` | `ticketing_agent` | `ticketing` | YES |
| `tmux-agent.md` | `Tmux Agent` | `tmux-agent` | NO |
| `typescript-engineer.md` | `Typescript Engineer` | `typescript-engineer` | YES |
| `version-control.md` | `Version Control` | `version-control` | YES |
| `visual-basic-engineer.md` | `Visual Basic Engineer` | `visual-basic-engineer` | YES |
| `web-qa.md` | `Web QA` | `web-qa-agent` | YES |

### Cached But NOT Deployed (8 agents)

| Filename | `name:` Field | Cache Path | Has `author:`? |
|----------|--------------|-----------|---------------|
| `api-qa.md` | `API QA` | `agents/qa/api-qa.md` | YES |
| `digitalocean-ops.md` | `DigitalOcean Ops` | `agents/ops/platform/digitalocean-ops.md` | YES |
| `gcp-ops.md` | `Google Cloud Ops` | `agents/ops/platform/gcp-ops.md` | YES |
| `javascript-engineer.md` | `Javascript Engineer` | `agents/engineering/...` | YES |
| `local-ops.md` | `Local Ops` | `agents/ops/platform/local-ops.md` | **NO** |
| `security.md` | `Security` | `agents/security/security.md` | YES |
| `vercel-ops.md` | `Vercel Ops` | `agents/ops/platform/vercel-ops.md` | YES |
| `web-ui.md` | `Web UI` | `agents/engineering/.../web-ui.md` | YES |

---

## PM_INSTRUCTIONS.md Agent Reference Audit

### References to Non-Deployed Agents

| Reference | Count | Agent Status |
|-----------|-------|-------------|
| `local-ops` | 18 | NOT DEPLOYED |
| `vercel-ops` | 2 | NOT DEPLOYED |
| `gcp-ops` | 2 | NOT DEPLOYED |
| `api-qa-agent` | 2 | NOT DEPLOYED |
| `security` (as agent target) | 1 | NOT DEPLOYED |

### References Using Wrong Format (Deployed Agents)

| PM Says | Count | Should Be (`name:` field) |
|---------|-------|--------------------------|
| `web-qa-agent` | 8 | `Web QA` |
| `clerk-ops` | 2 | `Clerk Operations` |
| `version-control` (as delegation target) | 2 | `Version Control` |
| `ticketing-agent` | 1 | `ticketing_agent` |

### References That Are Correct (or Close Enough)

| PM Says | `name:` Field | Match? |
|---------|--------------|--------|
| `Research` | `Research` | EXACT |
| `Engineer` | `Engineer` | EXACT |
| `QA` | `QA` | EXACT |
| `Documentation` | `Documentation Agent` | PARTIAL (may fail) |
| `Ops` | `Ops` | EXACT |
| `Code Analyzer` | `Code Analysis` | WRONG (name mismatch) |

---

## `name:` Field Anomalies (Out of Scope — From Git Repo)

These `name:` values don't follow the "Title Case Display Name" convention but cannot be changed (from external repo):

| Agent | `name:` Value | Expected Convention |
|-------|--------------|-------------------|
| `aws-ops.md` | `aws_ops_agent` | `AWS Ops` |
| `ticketing.md` | `ticketing_agent` | `Ticketing` |
| `mpm-agent-manager.md` | `mpm_agent_manager` | `MPM Agent Manager` |
| `mpm-skills-manager.md` | `mpm_skills_manager` | `MPM Skills Manager` |
| `nestjs-engineer.md` | `nestjs-engineer` | `NestJS Engineer` |
| `real-user.md` | `real-user` | `Real User` |

---

## Hardcoded Agent Lists in Source Code

### `framework_agent_loader.py` CORE_AGENTS

```python
# Line 35 — used as framework loading fallback
CORE_AGENTS = ["engineer", "research", "qa", "documentation", "ops", "ticketing"]
```

Format: filename stems (bare, no suffix). All exist as deployed files.

### `toolchain_detector.py` CORE_AGENTS

```python
# Line 162 — used for auto-configuration "always include"
CORE_AGENTS = [
    "engineer",            # EXISTS: engineer.md
    "qa-agent",            # DOES NOT EXIST (actual: qa.md)
    "memory-manager-agent",# EXISTS: memory-manager-agent.md
    "local-ops-agent",     # DOES NOT EXIST (actual: local-ops.md in cache only)
    "research-agent",      # DOES NOT EXIST (actual: research.md)
    "documentation-agent", # DOES NOT EXIST (actual: documentation.md)
    "security-agent",      # DOES NOT EXIST (actual: security.md in cache only)
]
```

Format: Mixed stems with `-agent` suffix. 5 of 7 entries reference non-existent files.

### `git_source_sync_service.py` Fallback List

```python
# Line 759 — used when GitHub API unavailable
[
    "research-agent.md",     # Repo has: research.md (no -agent suffix)
    "engineer.md",           # OK
    "qa-agent.md",           # Repo has: qa.md
    "documentation-agent.md",# Repo has: documentation.md
    "web-qa-agent.md",       # Repo has: web-qa.md
    "security.md",           # OK
    "ops.md",                # OK
    "ticketing.md",          # OK
    "product-owner.md",      # OK
    "version-control.md",    # OK
    "project-organizer.md",  # OK
]
```

Format: Filenames. Several use `-agent` suffix not present in actual repo.
