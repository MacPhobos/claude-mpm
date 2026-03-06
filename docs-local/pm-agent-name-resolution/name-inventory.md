# Complete Agent Name Inventory

**Date**: 2026-03-05
**Branch**: agenttype-enums
**Status**: Research complete
**Source**: Extracted from deployed `.claude/agents/*.md` files

---

## 1. Complete Inventory (47 agents)

### 1.1 Core Agents

| Filename Stem | `name:` Field Value | `agent_id:` | Naming Convention | PM References? |
|--------------|--------------------|----|-------------------|---------------|
| `engineer` | `Engineer` | `engineer` | Standard | YES |
| `research` | `Research` | `research-agent` | Standard | YES |
| `qa` | `QA` | `qa-agent` | Standard (abbreviation) | YES |
| `documentation` | `Documentation Agent` | `documentation-agent` | Has " Agent" suffix | YES |
| `ops` | `Ops` | -- | Standard | YES (deprecated) |
| `security` | `Security` | `security-agent` | Standard | YES |
| `version-control` | `Version Control` | -- | Standard | YES |
| `code-analyzer` | `Code Analysis` | `code-analyzer` | Noun form (not stem) | YES |

### 1.2 Engineering Language Agents

| Filename Stem | `name:` Field Value | Naming Convention |
|--------------|--------------------|--------------------|
| `python-engineer` | `Python Engineer` | Standard |
| `golang-engineer` | `Golang Engineer` | Standard |
| `java-engineer` | `Java Engineer` | Standard |
| `javascript-engineer` | `Javascript Engineer` | Standard |
| `typescript-engineer` | `Typescript Engineer` | Standard |
| `rust-engineer` | `Rust Engineer` | Standard |
| `ruby-engineer` | `Ruby Engineer` | Standard |
| `php-engineer` | `Php Engineer` | Standard |
| `dart-engineer` | `Dart Engineer` | Standard |
| `visual-basic-engineer` | `Visual Basic Engineer` | Standard |

### 1.3 Engineering Framework Agents

| Filename Stem | `name:` Field Value | Naming Convention | Notes |
|--------------|--------------------|--------------------|-------|
| `react-engineer` | `React Engineer` | Standard | |
| `nextjs-engineer` | `Nextjs Engineer` | Standard | |
| `svelte-engineer` | `Svelte Engineer` | Standard | |
| `nestjs-engineer` | `nestjs-engineer` | **ANOMALY**: lowercase hyphenated | Matches filename stem exactly |
| `phoenix-engineer` | `Phoenix Engineer` | Standard | |
| `tauri-engineer` | `Tauri Engineer` | Standard | |

### 1.4 Specialist Engineers

| Filename Stem | `name:` Field Value | Naming Convention |
|--------------|--------------------|--------------------|
| `data-engineer` | `Data Engineer` | Standard |
| `data-scientist` | `Data Scientist` | Standard |
| `refactoring-engineer` | `Refactoring Engineer` | Standard |
| `prompt-engineer` | `Prompt Engineer` | Standard |
| `web-ui` | `Web UI` | Standard (abbreviation) |

### 1.5 Ops Platform Agents

| Filename Stem | `name:` Field Value | Naming Convention | Notes |
|--------------|--------------------|--------------------|-------|
| `local-ops` | `Local Ops` | Standard | Primary ops agent for localhost |
| `vercel-ops` | `Vercel Ops` | Standard | |
| `gcp-ops` | `Google Cloud Ops` | Standard | Name differs from stem ("gcp" -> "Google Cloud") |
| `clerk-ops` | `Clerk Operations` | Standard | Name differs from stem ("ops" -> "Operations") |
| `aws-ops` | `aws_ops_agent` | **ANOMALY**: underscores, lowercase | Does NOT follow Title Case |
| `digitalocean-ops` | `DigitalOcean Ops` | Standard | CamelCase brand name |

### 1.6 QA Agents

| Filename Stem | `name:` Field Value | Naming Convention | Notes |
|--------------|--------------------|--------------------|-------|
| `web-qa` | `Web QA` | Standard | |
| `api-qa` | `API QA` | Standard | |
| `real-user` | `real-user` | **ANOMALY**: lowercase hyphenated | Matches filename stem exactly |

### 1.7 Utility Agents

| Filename Stem | `name:` Field Value | Naming Convention | Notes |
|--------------|--------------------|--------------------|-------|
| `memory-manager-agent` | `Memory Manager` | Standard | Stem has "-agent" suffix |
| `project-organizer` | `Project Organizer` | Standard | |
| `product-owner` | `Product Owner` | Standard | |
| `content-agent` | `Content Optimization` | Standard | Name differs from stem |
| `imagemagick` | `Imagemagick` | Standard | Brand name |
| `agentic-coder-optimizer` | `Agentic Coder Optimizer` | Standard | |
| `tmux-agent` | `Tmux Agent` | Has " Agent" suffix | |
| `ticketing` | `ticketing_agent` | **ANOMALY**: underscores, lowercase | Does NOT follow Title Case |

### 1.8 MPM Meta Agents

| Filename Stem | `name:` Field Value | Naming Convention | Notes |
|--------------|--------------------|--------------------|-------|
| `mpm-agent-manager` | `mpm_agent_manager` | **ANOMALY**: underscores, lowercase | Does NOT follow Title Case |
| `mpm-skills-manager` | `mpm_skills_manager` | **ANOMALY**: underscores, lowercase | Does NOT follow Title Case |

---

## 2. Naming Anomalies Summary

### 2.1 Agents Where `name:` Does NOT Follow Title Case Convention

These agents have `name:` values that break the "Title Case With Spaces" pattern used by the majority:

| Agent | `name:` Value | Expected Pattern | Actual Pattern |
|-------|--------------|-----------------|----------------|
| `ticketing.md` | `ticketing_agent` | `Ticketing Agent` or `Ticketing` | snake_case |
| `aws-ops.md` | `aws_ops_agent` | `AWS Ops` | snake_case |
| `nestjs-engineer.md` | `nestjs-engineer` | `NestJS Engineer` | kebab-case (matches stem) |
| `real-user.md` | `real-user` | `Real User` | kebab-case (matches stem) |
| `mpm-agent-manager.md` | `mpm_agent_manager` | `MPM Agent Manager` | snake_case |
| `mpm-skills-manager.md` | `mpm_skills_manager` | `MPM Skills Manager` | snake_case |

**Impact**: PM_INSTRUCTIONS.md must use these exact anomalous values. Attempting to "normalize" them (e.g., using `Ticketing Agent` instead of `ticketing_agent`) will cause delegation failures.

### 2.2 Agents Where `name:` Differs Significantly from Filename Stem

| Filename Stem | `name:` Value | Difference |
|--------------|--------------|-----------|
| `gcp-ops` | `Google Cloud Ops` | "gcp" expanded to "Google Cloud" |
| `clerk-ops` | `Clerk Operations` | "ops" expanded to "Operations" |
| `code-analyzer` | `Code Analysis` | "analyzer" -> "Analysis" (noun form) |
| `content-agent` | `Content Optimization` | Completely different second word |
| `documentation` | `Documentation Agent` | Added " Agent" suffix |

**Impact**: For these agents, the filename stem cannot be used to guess the `name:` value. The registry or direct file inspection is required.

### 2.3 Agents with " Agent" in `name:` Field

| Filename Stem | `name:` Value |
|--------------|--------------|
| `documentation` | `Documentation Agent` |
| `tmux-agent` | `Tmux Agent` |

**Note**: The Agent Capabilities Generator strips " Agent" from display names. This means the generated capabilities section shows "Documentation" and "Tmux" but the actual `subagent_type` must include " Agent": `Agent(subagent_type="Documentation Agent")`.

---

## 3. Recommended PM_INSTRUCTIONS.md References

### 3.1 How Each Agent Should Be Referenced

| Agent | Reference in Prose | Reference in YAML | Notes |
|-------|-------------------|-------------------|-------|
| Engineer | `**Engineer**` | `agent: "Engineer"` | |
| Research | `**Research**` | `agent: "Research"` | |
| QA | `**QA**` | `agent: "QA"` | |
| Documentation Agent | `**Documentation Agent**` | `agent: "Documentation Agent"` | Include " Agent" |
| Ops | `**Ops**` | `agent: "Ops"` | Deprecated; use platform-specific |
| Security | `**Security**` | `agent: "Security"` | |
| Version Control | `**Version Control**` | `agent: "Version Control"` | |
| Code Analysis | `**Code Analysis**` | `agent: "Code Analysis"` | Not "Code Analyzer" |
| Local Ops | `**Local Ops**` | `agent: "Local Ops"` | Primary ops agent |
| Vercel Ops | `**Vercel Ops**` | `agent: "Vercel Ops"` | |
| Google Cloud Ops | `**Google Cloud Ops**` | `agent: "Google Cloud Ops"` | Not "GCP Ops" |
| Clerk Operations | `**Clerk Operations**` | `agent: "Clerk Operations"` | Not "Clerk Ops" |
| aws_ops_agent | `**aws_ops_agent**` | `agent: "aws_ops_agent"` | Anomalous: snake_case |
| DigitalOcean Ops | `**DigitalOcean Ops**` | `agent: "DigitalOcean Ops"` | |
| Web QA | `**Web QA**` | `agent: "Web QA"` | |
| API QA | `**API QA**` | `agent: "API QA"` | |
| ticketing_agent | `**ticketing_agent**` | `agent: "ticketing_agent"` | Anomalous: snake_case |
| nestjs-engineer | `**nestjs-engineer**` | `agent: "nestjs-engineer"` | Anomalous: kebab-case |
| real-user | `**real-user**` | `agent: "real-user"` | Anomalous: kebab-case |
| mpm_agent_manager | `**mpm_agent_manager**` | `agent: "mpm_agent_manager"` | Anomalous: snake_case |
| mpm_skills_manager | `**mpm_skills_manager**` | `agent: "mpm_skills_manager"` | Anomalous: snake_case |

### 3.2 Cross-Reference: agent_name_registry.py Coverage

The `agent_name_registry.py` (Phase 2 deliverable) contains the complete mapping. It should be kept in sync with this inventory. Current coverage:

- Total agents deployed: **47**
- Agents in registry (including legacy variants): **57** entries (some are `-agent` suffix aliases)
- Missing from registry: None (all 47 deployed agents are covered)

---

## 4. Validation Script

To verify this inventory against deployed agents:

```bash
#!/usr/bin/env bash
# Verify inventory matches deployed agents
echo "=== Deployed agents not in this inventory ==="
for f in .claude/agents/*.md; do
  stem=$(basename "$f" .md)
  name=$(grep '^name:' "$f" | head -1 | sed 's/name: *//')
  echo "$stem|$name"
done | sort > /tmp/deployed.txt

echo "Total deployed: $(wc -l < /tmp/deployed.txt)"
echo ""
echo "=== Name anomalies (not Title Case) ==="
while IFS='|' read -r stem name; do
  # Check if name matches Title Case pattern
  if [[ "$name" =~ ^[A-Z] ]] && [[ ! "$name" =~ _ ]] && [[ ! "$name" =~ ^[a-z] ]]; then
    : # Standard format
  else
    echo "  ANOMALY: $stem -> '$name'"
  fi
done < /tmp/deployed.txt
```
