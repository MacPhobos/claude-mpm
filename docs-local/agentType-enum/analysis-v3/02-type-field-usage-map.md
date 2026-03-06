# Comprehensive Type/Agent_Type Field Usage Map

**Date**: 2026-03-03
**Investigator**: Research Agent (Claude Opus 4.6)
**Branch**: `agenttype-enums`
**Task**: Map ALL type/agent_type usage across the entire codebase
**Builds on**: analysis-v2 (5 docs) + analysis-v2.1 (5 docs)

---

## Executive Summary

This document provides a **complete, line-level inventory** of every location in the codebase that reads, writes, or transforms the `type` or `agent_type` field related to agent classification. Each location is classified by:

- **R/W**: Whether it reads or writes the field
- **Field**: Which field name it uses (`"type"` vs `"agent_type"` vs both)
- **Classification**: SOURCE_TEMPLATE | DEPLOYMENT | RUNTIME | CLI | CONFIG | SKILL_MAPPING | HOOKS | DASHBOARD | TEST | ENUM_DEF | SERIALIZATION

**Key counts**:
- **57 Python source files** in `src/` reference `agent_type`
- **71 test files** reference `agent_type`
- **49 agent `.md` files** use `type:` in frontmatter
- **30 agent `.md` files** use `agent_type:` in frontmatter (including body references)
- **39 JSON template files** use `"agent_type"` in `src/claude_mpm/agents/templates/archive/`
- **3 AgentType enum definitions** + 1 AgentCategory enum
- **0 YAML config files** reference either field

---

## 1. ENUM DEFINITIONS (ENUM_DEF)

### 1.1 Enum 1: `models.agent_definition.AgentType`

| File | Line | Code | R/W | Field | Notes |
|------|------|------|-----|-------|-------|
| `src/claude_mpm/models/agent_definition.py` | 25-36 | `class AgentType(str, Enum): CORE, PROJECT, CUSTOM, SYSTEM, SPECIALIZED` | DEF | N/A | 5 members. Base: `str, Enum` |
| `src/claude_mpm/models/agent_definition.py` | 99 | `type: AgentType` | DEF | `type` | Dataclass field on `AgentMetadata`. **Shadows Python builtin** |
| `src/claude_mpm/models/__init__.py` | 13, 22 | `from .agent_definition import AgentType` / `"AgentType"` | EXPORT | N/A | Re-exported from models package |

### 1.2 Enum 2: `core.unified_agent_registry.AgentType`

| File | Line | Code | R/W | Field | Notes |
|------|------|------|-----|-------|-------|
| `src/claude_mpm/core/unified_agent_registry.py` | 52-59 | `class AgentType(Enum): CORE, SPECIALIZED, USER_DEFINED, PROJECT, MEMORY_AWARE` | DEF | N/A | 5 members. Base: `Enum` (NOT `str, Enum`) |
| `src/claude_mpm/core/unified_agent_registry.py` | 75 | `agent_type: AgentType` | DEF | `agent_type` | Dataclass field on `AgentMetadata` |
| `src/claude_mpm/core/unified_agent_registry.py` | 952 | `"AgentType"` in `__all__` | EXPORT | N/A | |
| `src/claude_mpm/services/agents/registry/__init__.py` | 6, 25 | `from ...core.unified_agent_registry import AgentType` | EXPORT | N/A | Re-exported |
| `src/claude_mpm/services/agents/__init__.py` | 44, 69 | `from .registry import AgentType` | EXPORT | N/A | Re-exported again |

### 1.3 Enum 3: `tests/eval/agents/shared/agent_response_parser.AgentType`

| File | Line | Code | R/W | Field | Notes |
|------|------|------|-----|-------|-------|
| `tests/eval/agents/shared/agent_response_parser.py` | 37-47 | `class AgentType(str, Enum): BASE, RESEARCH, ENGINEER, QA, OPS, DOCUMENTATION, PROMPT_ENGINEER, PM` | DEF | N/A | 8 members. **Only enum matching frontmatter values** |

### 1.4 AgentCategory (4th classification)

| File | Line | Code | R/W | Field | Notes |
|------|------|------|-----|-------|-------|
| `src/claude_mpm/core/enums.py` | 360-443 | `class AgentCategory(StrEnum): ENGINEERING, RESEARCH, ANALYSIS, QUALITY, QA, SECURITY, OPERATIONS, ...` | DEF | N/A | 17+ members. Different naming: `engineering` vs `engineer`, `operations` vs `ops` |
| `src/claude_mpm/core/enums.py` | 448 | `"AgentCategory"` in `__all__` | EXPORT | N/A | |
| `src/claude_mpm/agents/agent_loader.py` | 41 | `from claude_mpm.core.enums import AgentCategory` | IMPORT | N/A | |
| `src/claude_mpm/agents/agent_loader.py` | 328-333 | `category = AgentCategory(category_str)` / fallback `AgentCategory.GENERAL` | R | `agent_type` (indirect) | Uses AgentCategory to classify agents |

---

## 2. FRONTMATTER - AGENT MARKDOWN FILES (SOURCE_TEMPLATE / DEPLOYMENT)

### 2.1 Files using `type:` (49 lines across 48 files + 1 body reference)

**Classification**: DEPLOYMENT (these are deployed agent files read at runtime)

| File | Line | Value | Notes |
|------|------|-------|-------|
| `.claude/agents/agentic-coder-optimizer.md` | 4 | `type: ops` | Gen 1 |
| `.claude/agents/api-qa.md` | 4 | `type: qa` | Gen 1 |
| `.claude/agents/aws-ops.md` | 5 | `type: ops` | Gen 1 |
| `.claude/agents/clerk-ops.md` | 4 | `type: ops` | Gen 1 |
| `.claude/agents/code-analyzer.md` | 4 | `type: research` | Gen 1 |
| `.claude/agents/content-agent.md` | 4 | `type: content` | Gen 3 unique |
| `.claude/agents/dart-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/data-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/data-scientist.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/digitalocean-ops.md` | 5 | `type: ops` | Gen 1 |
| `.claude/agents/documentation.md` | 4 | `type: documentation` | Gen 1 |
| `.claude/agents/engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/gcp-ops.md` | 4 | `type: ops` | Gen 1 |
| `.claude/agents/golang-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/imagemagick.md` | 4 | `type: imagemagick` | Gen 1 |
| `.claude/agents/java-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/javascript-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/local-ops.md` | 4 | `type: specialized` | Gen 1 |
| `.claude/agents/memory-manager-agent.md` | 4 | `type: memory_manager` | Gen 3 unique |
| `.claude/agents/mpm-agent-manager.md` | 4 | `type: system` | Gen 1 |
| `.claude/agents/mpm-skills-manager.md` | 4 | `type: claude-mpm` | Gen 1 |
| `.claude/agents/nestjs-engineer.md` | 5 | `type: engineer` | Gen 1 |
| `.claude/agents/nextjs-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/ops.md` | 4 | `type: ops` | Gen 1 |
| `.claude/agents/phoenix-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/php-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/product-owner.md` | 4 | `type: product` | Gen 1 |
| `.claude/agents/project-organizer.md` | 4 | `type: ops` | Gen 1 |
| `.claude/agents/prompt-engineer.md` | 4 | `type: analysis` | Gen 1 |
| `.claude/agents/python-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/qa.md` | 4 | `type: qa` | Gen 1 |
| `.claude/agents/react-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/real-user.md` | 4 | `type: qa` | Gen 1 |
| `.claude/agents/refactoring-engineer.md` | 4 | `type: refactoring` | Gen 1 |
| `.claude/agents/research.md` | 4 | `type: research` | Gen 1 |
| `.claude/agents/ruby-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/rust-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/security.md` | 4 | `type: security` | Gen 1 |
| `.claude/agents/svelte-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/tauri-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/ticketing.md` | 4 | `type: documentation` | Gen 1 |
| `.claude/agents/tmux-agent.md` | 4 | `type: ops` | Gen 3 unique |
| `.claude/agents/typescript-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/vercel-ops.md` | 4 | `type: ops` | Gen 1 |
| `.claude/agents/version-control.md` | 4 | `type: ops` | Gen 1 |
| `.claude/agents/visual-basic-engineer.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/web-qa.md` | 4 | `type: qa` | Gen 1 |
| `.claude/agents/web-ui.md` | 4 | `type: engineer` | Gen 1 |
| `.claude/agents/mpm-agent-manager.md` | 1218 | `type: engineer\|ops\|research\|qa\|security\|docs` | Body reference (schema doc) |

### 2.2 Files using `agent_type:` (28 frontmatter + 2 body references)

**Classification**: DEPLOYMENT (Gen 2 + Gen 3 files)

| File | Line | Value | Generation |
|------|------|-------|------------|
| `.claude/agents/api-qa-agent.md` | 7 | `agent_type: qa` | Gen 3 |
| `.claude/agents/dart_engineer.md` | 7 | `agent_type: engineer` | Gen 2 |
| `.claude/agents/digitalocean-ops-agent.md` | 7 | `agent_type: ops` | Gen 3 |
| `.claude/agents/documentation-agent.md` | 7 | `agent_type: documentation` | Gen 3 |
| `.claude/agents/gcp-ops-agent.md` | 7 | `agent_type: ops` | Gen 3 |
| `.claude/agents/golang_engineer.md` | 7 | `agent_type: engineer` | Gen 2 |
| `.claude/agents/java_engineer.md` | 7 | `agent_type: engineer` | Gen 2 |
| `.claude/agents/javascript-engineer-agent.md` | 7 | `agent_type: engineer` | Gen 3 |
| `.claude/agents/local-ops-agent.md` | 7 | `agent_type: specialized` | Gen 3 |
| `.claude/agents/nestjs_engineer.md` | 15 | `agent_type: engineer` | Gen 2 |
| `.claude/agents/nextjs_engineer.md` | 7 | `agent_type: engineer` | Gen 2 |
| `.claude/agents/ops-agent.md` | 7 | `agent_type: ops` | Gen 3 |
| `.claude/agents/php_engineer.md` | 7 | `agent_type: engineer` | Gen 2 |
| `.claude/agents/product_owner.md` | 7 | `agent_type: product` | Gen 2 |
| `.claude/agents/qa-agent.md` | 7 | `agent_type: qa` | Gen 3 |
| `.claude/agents/react_engineer.md` | 7 | `agent_type: engineer` | Gen 2 |
| `.claude/agents/real_user.md` | 5 | `agent_type: qa` | Gen 2 |
| `.claude/agents/research-agent.md` | 7 | `agent_type: research` | Gen 3 |
| `.claude/agents/ruby_engineer.md` | 7 | `agent_type: engineer` | Gen 2 |
| `.claude/agents/rust_engineer.md` | 7 | `agent_type: engineer` | Gen 2 |
| `.claude/agents/security-agent.md` | 7 | `agent_type: security` | Gen 3 |
| `.claude/agents/svelte_engineer.md` | 7 | `agent_type: engineer` | Gen 2 |
| `.claude/agents/tauri_engineer.md` | 7 | `agent_type: engineer` | Gen 2 |
| `.claude/agents/vercel-ops-agent.md` | 7 | `agent_type: ops` | Gen 3 |
| `.claude/agents/visual_basic_engineer.md` | 7 | `agent_type: engineer` | Gen 2 |
| `.claude/agents/web-qa-agent.md` | 7 | `agent_type: qa` | Gen 3 |
| `.claude/agents/web-ui-engineer.md` | 7 | `agent_type: engineer` | Gen 3 |
| `.claude/agents/mpm-agent-manager.md` | 259 | `agent_type: engineer\|qa\|ops\|...` | Body (schema doc) |
| `.claude/agents/mpm-agent-manager.md` | 1569 | `agent_type: engineer\|qa\|ops\|...` | Body (schema doc) |
| `.claude/agents/mpm-skills-manager.md` | 2276 | `agent_type: engineer\|qa\|ops\|...` | Body (schema doc) |

---

## 3. JSON TEMPLATES (SOURCE_TEMPLATE)

All 39 JSON templates in `src/claude_mpm/agents/templates/archive/` use `"agent_type"`:

| File | Line | Value | Notes |
|------|------|-------|-------|
| `agent-manager.json` | 28 | `"agent_type": "system"` | |
| `agentic-coder-optimizer.json` | 28 | `"agent_type": "ops"` | |
| `api_qa.json` | 5 | `"agent_type": "qa"` | |
| `clerk-ops.json` | 5 | `"agent_type": "ops"` | |
| `code_analyzer.json` | 5 | `"agent_type": "research"` | |
| `content-agent.json` | 15 | `"agent_type": "content"` | |
| `dart_engineer.json` | 15 | `"agent_type": "engineer"` | |
| `data_engineer.json` | 5 | `"agent_type": "engineer"` | |
| `documentation.json` | 33 | `"agent_type": "documentation"` | |
| `engineer.json` | 25 | `"agent_type": "engineer"` | |
| `gcp_ops_agent.json` | 13 | `"agent_type": "ops"` | |
| `golang_engineer.json` | 15 | `"agent_type": "engineer"` | |
| `imagemagick.json` | 20 | `"agent_type": "imagemagick"` | |
| `java_engineer.json` | 15 | `"agent_type": "engineer"` | |
| `javascript_engineer_agent.json` | 13 | `"agent_type": "engineering"` | **TYPO**: should be `"engineer"` |
| `memory_manager.json` | 5 | `"agent_type": "memory_manager"` | |
| `nextjs_engineer.json` | 25 | `"agent_type": "engineer"` | |
| `ops.json` | 28 | `"agent_type": "ops"` | |
| `php-engineer.json` | 25 | `"agent_type": "engineer"` | |
| `product_owner.json` | 15 | `"agent_type": "product"` | |
| `project_organizer.json` | 5 | `"agent_type": "ops"` | |
| `prompt-engineer.json` | 23 | `"agent_type": "analysis"` | |
| `python_engineer.json` | 45 | `"agent_type": "engineer"` | |
| `qa.json` | 23 | `"agent_type": "qa"` | |
| `react_engineer.json` | 20 | `"agent_type": "engineer"` | |
| `refactoring_engineer.json` | 23 | `"agent_type": "refactoring"` | |
| `research.json` | 68 | `"agent_type": "research"` | |
| `ruby-engineer.json` | 20 | `"agent_type": "engineer"` | |
| `rust_engineer.json` | 20 | `"agent_type": "engineer"` | |
| `security.json` | 5 | `"agent_type": "security"` | |
| `svelte-engineer.json` | 20 | `"agent_type": "engineer"` | |
| `tauri_engineer.json` | 15 | `"agent_type": "engineer"` | |
| `ticketing.json` | 5 | `"agent_type": "documentation"` | |
| `typescript_engineer.json` | 20 | `"agent_type": "engineer"` | |
| `vercel_ops_agent.json` | 5 | `"agent_type": "ops"` | |
| `version_control.json` | 5 | `"agent_type": "ops"` | |
| `web_qa.json` | 5 | `"agent_type": "qa"` | |
| `web_ui.json` | 5 | `"agent_type": "engineer"` | |

**Count**: 39 files, all use `"agent_type"`. One typo: `"engineering"` instead of `"engineer"`.

---

## 4. PYTHON SOURCE CODE - READING `"type"` (AGENT CONTEXT ONLY)

### 4.1 Agent Management Service (RUNTIME - Primary CRUD path)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/agents/management/agent_management_service.py` | 153 | `elif key in ["type", "model_preference", "tags", "specializations"]:` | R | RUNTIME |
| `services/agents/management/agent_management_service.py` | 318 | `"type": agent_def.metadata.type.value,` | R (serialize) | RUNTIME |
| `services/agents/management/agent_management_service.py` | 444 | `type=AgentType(post.metadata.get("type", "core")),` | R | RUNTIME **CRITICAL: crashes for most agents** |
| `services/agents/management/agent_management_service.py` | 625 | `"type": definition.metadata.type.value,` | W (to frontmatter dict) | RUNTIME |
| `services/agents/management/agent_management_service.py` | 723 | `content.append(f"**Agent Type**: {definition.metadata.type.value}")` | R (display) | RUNTIME |

### 4.2 Agent Validator (DEPLOYMENT)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/agents/deployment/agent_validator.py` | 329 | `"type": "agent",  # Default type` | W (default) | DEPLOYMENT |
| `services/agents/deployment/agent_validator.py` | 362-363 | `agent_info["type"] = stripped_line.split(":", 1)[1].strip()` | R (parses `type:` from frontmatter) | DEPLOYMENT |

### 4.3 Deployment Wrapper (DEPLOYMENT)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/agents/deployment/deployment_wrapper.py` | 111 | `"type": agent.get("type", "agent"),` | R | DEPLOYMENT |

### 4.4 Deployed Agent Discovery (RUNTIME)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/agents/registry/deployed_agent_discovery.py` | 109 | `"id": agent.get("type", agent.get("name", "unknown")),` | R | RUNTIME |
| `services/agents/registry/deployed_agent_discovery.py` | 133 | `agent_type = getattr(agent, "type", None)` | R | RUNTIME |
| `services/agents/registry/deployed_agent_discovery.py` | 193 | `"id": json_data.get("agent_type", registry_info.get("type", "unknown")),` | R (HYBRID: reads `agent_type` first, fallback `type`) | RUNTIME |

### 4.5 Agent Lifecycle Manager (DEPLOYMENT)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/agents/deployment/agent_lifecycle_manager.py` | 310 | `"type": agent_metadata.type,` | R (serialize) | DEPLOYMENT |

### 4.6 CLI Agent Listing Service (CLI)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/cli/agent_listing_service.py` | 214 | `type=agent_data.get("type", "agent"),` | R | CLI |
| `services/cli/agent_listing_service.py` | 250 | `type=agent_data.get("type", "agent"),` | R | CLI |
| `services/cli/agent_listing_service.py` | 296 | `type=metadata.get("type", "agent"),` | R | CLI |
| `services/cli/agent_listing_service.py` | 372 | `"type": getattr(agent, "type", "agent"),` | R | CLI |

### 4.7 Agent Registry Compatibility Layer (RUNTIME)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `core/agent_registry.py` | 73 | `type=unified_metadata.agent_type.value,` | R/TRANSFORM: reads `agent_type` from Enum 2, writes as `type` | RUNTIME |
| `core/agent_registry.py` | 105 | `"type": unified_metadata.agent_type.value,` | TRANSFORM | RUNTIME |
| `core/agent_registry.py` | 208 | `"type": unified_metadata.agent_type.value,` | TRANSFORM | RUNTIME |
| `core/agent_registry.py` | 239 | `all_types = {metadata["type"] for metadata in self.agents.values()}` | R | RUNTIME |
| `core/agent_registry.py` | 321 | `"type": agent.agent_type.value,` | TRANSFORM | RUNTIME |
| `core/agent_registry.py` | 747 | `"type": metadata.agent_type.value,` | TRANSFORM | RUNTIME |
| `core/agent_registry.py` | 801 | `"type": unified_agent.agent_type.value,` | TRANSFORM | RUNTIME |

**Key finding**: `agent_registry.py` is a **translation layer** -- it reads `agent_type` from Enum 2 objects and serializes them under the key `"type"`.

### 4.8 Agents Metadata (CONFIG)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `agents/agents_metadata.py` | 14, 36, 59, 82, 107, 132, 154, 177, 200, 223, 247 | `"type": "core_agent"` | W (hardcoded) | CONFIG |
| `agents/agents_metadata.py` | 270, 296 | `"type": "optimization_agent"` | W (hardcoded) | CONFIG |
| `agents/agents_metadata.py` | 322 | `"type": "system_agent"` | W (hardcoded) | CONFIG |

**Note**: Uses `"type"` key but with values like `"core_agent"` and `"optimization_agent"` -- NEITHER matching Enum 1 values NOR frontmatter values.

### 4.9 Dynamic Skills Generator (RUNTIME)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/dynamic_skills_generator.py` | 110 | `agent_type = agent_info.get("type", "general-purpose")` | R (HYBRID: variable named `agent_type`, reads from `"type"` key) | RUNTIME |

### 4.10 System Agent Config (CONFIG)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `agents/system_agent_config.py` | 513 | `"type": agent.agent_type,` | TRANSFORM: reads `.agent_type` attr, writes as `"type"` key | CONFIG |

---

## 5. PYTHON SOURCE CODE - READING/WRITING `"agent_type"`

### 5.1 Agent Template Builder (DEPLOYMENT - ROOT CAUSE)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/agents/deployment/agent_template_builder.py` | 493 | `agent_type = template_data.get("agent_type", "general")` | R | DEPLOYMENT |
| `services/agents/deployment/agent_template_builder.py` | 567-568 | `frontmatter_lines.append(f"type: {agent_type}")` | W **Writes `type:` from `agent_type` source -- ROOT CAUSE of split** | DEPLOYMENT |
| `services/agents/deployment/agent_template_builder.py` | 910 | `agent_type = template_data.get("agent_type", "general")` | R | DEPLOYMENT |
| `services/agents/deployment/agent_template_builder.py` | 1052 | `agent_type = template_data.get("agent_type", "general")` | R | DEPLOYMENT |
| `services/agents/deployment/agent_template_builder.py` | 1083 | `agent_type = template_data.get("agent_type", "general")` | R | DEPLOYMENT |

### 5.2 Agent Discovery Service (DEPLOYMENT)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/agents/deployment/agent_discovery_service.py` | 320-322 | `"type": frontmatter.get("agent_type", frontmatter.get("category", "agent"))` | R/TRANSFORM: reads `agent_type`, writes to `"type"` dict key | DEPLOYMENT |

### 5.3 Template Validator (DEPLOYMENT)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/agents/deployment/validation/template_validator.py` | 31 | `"agent_type": str` | DEF (required field) | DEPLOYMENT |

### 5.4 Remote Agent Discovery Service (DEPLOYMENT)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/agents/deployment/remote_agent_discovery_service.py` | 234 | `"agent_type"` in `simple_keys` list | R | DEPLOYMENT |

### 5.5 Local Template Manager (DEPLOYMENT)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/agents/local_template_manager.py` | 83 | `"agent_type": self.agent_type or self.agent_id,` | W | DEPLOYMENT |
| `services/agents/local_template_manager.py` | 109 | `agent_type=data.get("agent_type", ""),` | R | DEPLOYMENT |

### 5.6 Config Routes - Dashboard API (DASHBOARD)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/monitor/config_routes.py` | 817 | `"agent_type": fmdata.get("agent_type", ""),` | R | DASHBOARD |

### 5.7 Unified Agent Registry (SERIALIZATION)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `core/unified_agent_registry.py` | 108 | `data["agent_type"] = self.agent_type.value` | W (serialize) | SERIALIZATION |
| `core/unified_agent_registry.py` | 116 | `data["agent_type"] = AgentType(data["agent_type"])` | R (deserialize) | SERIALIZATION |
| `core/unified_agent_registry.py` | 336 | `agent_type = self._determine_agent_type(file_path, tier)` | W (computed) | RUNTIME |
| `core/unified_agent_registry.py` | 386 | `agent_type=agent_type,` | W | RUNTIME |
| `core/unified_agent_registry.py` | 431-448 | `def _determine_agent_type(...)` | W (path-based, ignores frontmatter) | RUNTIME |
| `core/unified_agent_registry.py` | 600 | `metadata.agent_type = AgentType.MEMORY_AWARE` | W (override) | RUNTIME |
| `core/unified_agent_registry.py` | 645-659 | `agent_type: Optional[AgentType] = None` / filter | R | RUNTIME |
| `core/unified_agent_registry.py` | 675, 679, 687 | `list_agents(agent_type=AgentType.CORE/SPECIALIZED/MEMORY_AWARE)` | R | RUNTIME |
| `core/unified_agent_registry.py` | 877-880 | `agent_type: Optional[AgentType] = None` (top-level func) | R | RUNTIME |

### 5.8 Agent Definition Factory (DEPLOYMENT)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/agents/deployment/agent_definition_factory.py` | 48-57 | `type_map = {ModificationTier.USER: AgentType.CUSTOM, ...}` / `type=type_map.get(tier, AgentType.CUSTOM)` | W (maps tier to Enum 1's `type` field) | DEPLOYMENT |

### 5.9 Skill Manager (SKILL_MAPPING - dead code)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `skills/skill_manager.py` | 42 | `agent_id = agent_data.get("agent_id") or agent_data.get("agent_type")` | R | SKILL_MAPPING |

### 5.10 Model/Session Data (RUNTIME)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `models/agent_session.py` | 73, 95 | `agent_type: str` | DEF (dataclass field) | RUNTIME |
| `models/agent_session.py` | 112 | `"agent_type": self.agent_type,` | W (serialize) | RUNTIME |
| `models/agent_session.py` | 282 | `agent_type = data.get("agent_type", "unknown")` | R | RUNTIME |
| `models/agent_session.py` | 284-288 | `self.metrics.agents_used.add(agent_type)` / `agent_type=agent_type,` | R/W | RUNTIME |
| `models/agent_session.py` | 306 | `agent_type=self.current_agent or "unknown",` | W | RUNTIME |
| `models/agent_session.py` | 488 | `agent_type=del_data["agent_type"],` | R | RUNTIME |

### 5.11 Hook Event System (HOOKS)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `hooks/claude_hooks/event_handlers.py` | 420 | `raw_agent_type = tool_input.get("subagent_type", "unknown")` | R (`subagent_type`) | HOOKS |
| `hooks/claude_hooks/event_handlers.py` | 428-437 | `agent_type = normalizer.to_task_format(raw_agent_type)` | TRANSFORM | HOOKS |
| `hooks/claude_hooks/event_handlers.py` | 442-443 | `"agent_type": agent_type, "original_agent_type": raw_agent_type,` | W | HOOKS |
| `hooks/claude_hooks/event_handlers.py` | 462 | `"agent_type": agent_type,` | W (delegation request data) | HOOKS |
| `hooks/claude_hooks/event_handlers.py` | 464 | `self.hook_handler._track_delegation(session_id, agent_type, ...)` | W | HOOKS |
| `hooks/claude_hooks/event_handlers.py` | 491-492 | `"agent_type": agent_type, "agent_id": f"{agent_type}_{session_id}"` | W | HOOKS |
| `hooks/claude_hooks/event_handlers.py` | 516-517 | `"agent_type": agent_type, "agent_id": ...` | W | HOOKS |
| `hooks/claude_hooks/event_handlers.py` | 809 | `agent_type = self.hook_handler._get_delegation_agent_type(session_id)` | R | HOOKS |
| `hooks/claude_hooks/event_handlers.py` | 1374 | `agent_type = event.get("agent_type") or event.get("subagent_type") or "unknown"` | R (HYBRID) | HOOKS |
| `hooks/claude_hooks/event_handlers.py` | 1386 | `"agent_type": agent_type,` | W | HOOKS |
| `hooks/claude_hooks/hook_handler.py` | 600 | `def _track_delegation(self, session_id: str, agent_type: str, ...)` | R | HOOKS |
| `hooks/claude_hooks/hook_handler.py` | 604-606 | `def _get_delegation_agent_type(self, session_id: str) -> str` | R | HOOKS |
| `hooks/claude_hooks/hook_handler.py` | 676 | `hook_data["agent_type"] = event.get("agent_type", "unknown")` | R/W | HOOKS |
| `hooks/claude_hooks/hook_handler.py` | 719 | `agent_type = event.get("agent_type", "unknown")` | R | HOOKS |
| `hooks/claude_hooks/services/state_manager.py` | 52 | `# Store recent Task delegations: session_id -> agent_type` | COMMENT | HOOKS |
| `hooks/claude_hooks/services/state_manager.py` | 71-98 | `track_delegation(session_id, agent_type, ...)` | W | HOOKS |
| `hooks/claude_hooks/services/state_manager.py` | 90 | `"agent_type": agent_type,` | W (delegation_requests dict) | HOOKS |
| `hooks/claude_hooks/services/state_manager.py` | 121-131 | `get_delegation_agent_type(session_id)` | R | HOOKS |
| `hooks/claude_hooks/services/subagent_processor.py` | 67 | `self.state_manager.delegation_requests[sid].get('agent_type', 'unknown')` | R | HOOKS |
| `hooks/claude_hooks/services/subagent_processor.py` | 133-169 | `_extract_basic_info()` reads `agent_type` from state, event, heuristics | R | HOOKS |
| `hooks/claude_hooks/services/subagent_processor.py` | 147 | `agent_type = event.get("agent_type", event.get("subagent_type", "unknown"))` | R (HYBRID) | HOOKS |
| `hooks/claude_hooks/services/subagent_processor.py` | 204-341 | Multiple methods pass `agent_type` as parameter | R/W | HOOKS |
| `hooks/claude_hooks/services/connection_manager.py` | 182-188 | `agent_type = data.get("agent_type", "unknown")` / delegation | R | HOOKS |
| `hooks/claude_hooks/services/connection_manager_http.py` | 125-131 | Same pattern: `data.get("agent_type", "unknown")` | R | HOOKS |
| `hooks/claude_hooks/services/protocols.py` | 35-40 | `track_delegation(session_id, agent_type, ...)` / `get_delegation_agent_type()` | DEF | HOOKS |
| `hooks/claude_hooks/services/protocols.py` | 120, 156, 162 | `agent_type: str` parameter in protocol methods | DEF | HOOKS |
| `hooks/claude_hooks/response_tracking.py` | 117-247 | `track_subagent_response(session_id, agent_type, event, ...)` | R | HOOKS |
| `hooks/claude_hooks/memory_integration.py` | 151-263 | `trigger_pre_delegation_hook(agent_type, ...)` / `trigger_post_delegation_hook(agent_type, ...)` | R | HOOKS |
| `hooks/claude_hooks/tool_analysis.py` | 76-86 | `"subagent_type": tool_input.get("subagent_type", "unknown")` / delegation type checks | R | HOOKS |
| `hooks/failure_learning/failure_detection_hook.py` | 198-204 | `agent_type = context.data.get("agent_type") or context.data.get("subagent_type") or ...` | R (HYBRID) | HOOKS |
| `hooks/failure_learning/fix_detection_hook.py` | 180-186 | Same pattern | R (HYBRID) | HOOKS |
| `hooks/failure_learning/learning_extraction_hook.py` | 184-196 | Same pattern + `failure_event.context["agent_type"]` | R (HYBRID) | HOOKS |

### 5.12 `subagent_type` (Claude Code API Parameter) (RUNTIME / CLI)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/utility_service.py` | 49, 74-75 | `"subagent_type="` / regex extraction | R | RUNTIME |
| `services/memory_hook_service.py` | 322-330 | `data.get("subagent_type")` / `params.get("subagent_type")` | R | RUNTIME |
| `services/framework_claude_md_generator/section_generators/todo_task_tools.py` | 44-106 | `subagent_type="[agent-type]"` (documentation/examples) | W (doc) | CONFIG |
| `core/system_context.py` | 19, 29 | `subagent_type` in system prompt documentation | W (doc) | CONFIG |
| `hooks/claude_hooks/services/duplicate_detector.py` | 79 | `agent = tool_input.get("subagent_type", "")` | R | HOOKS |
| `hooks/claude_hooks/event_handlers.py` | 420 | `raw_agent_type = tool_input.get("subagent_type", "unknown")` | R | HOOKS |

### 5.13 Other Services Using `agent_type` (RUNTIME)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/analysis/postmortem_service.py` | 337 | `if "agent_type" in failure.context:` | R | RUNTIME |
| `services/agent_capabilities_service.py` | 77 | `def generate_agent_capabilities(self, agent_type: str = "general")` | R (param) | RUNTIME |
| `services/memory_hook_service.py` | 322-330 | `data.get("subagent_type")` | R | RUNTIME |
| `services/memory/failure_tracker.py` | 317, 439, 442 | `failure_event.context["agent_type"]` | R | RUNTIME |
| `services/memory/router.py` | (various) | `agent_type` parameter | R | RUNTIME |
| `services/socketio/handlers/hook.py` | (various) | `agent_type` in event data | R | RUNTIME |
| `services/skills/git_skill_source_manager.py` | (various) | `agent_type` parameter | R | RUNTIME |
| `services/skills/skill_discovery_service.py` | (various) | `agent_type` parameter | R | RUNTIME |
| `services/core/interfaces/agent.py` | (various) | `agent_type` interface field | DEF | RUNTIME |
| `core/tool_access_control.py` | 62-168 | `agent_type` parameter throughout (12+ methods) | R | RUNTIME |
| `core/agent_session_manager.py` | 38-201 | `agent_type` parameter throughout (8+ methods) | R/W | RUNTIME |
| `core/system_context.py` | 19, 29 | `subagent_type` in documentation strings | W (doc) | CONFIG |
| `core/interfaces.py` | 293, 298 | `agent_type: Optional[str]` parameter | DEF | RUNTIME |
| `slack_client/handlers/commands.py` | (various) | `agent_type` parameter | R | RUNTIME |
| `slack_client/services/mpm_client.py` | (various) | `agent_type` parameter | R | RUNTIME |

### 5.14 CLI Commands (CLI)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `cli/interactive/agent_wizard.py` | 123, 479-521 | `_get_agent_type()` returns agent type string | R | CLI |
| `cli/interactive/agent_wizard.py` | 753 | `"type": agent_type,` | W (writes `type` key from `agent_type` variable) | CLI **TRANSLATION** |
| `cli/commands/aggregate.py` | 361, 432 | `delegation.agent_type` | R | CLI |
| `cli/commands/configure_template_editor.py` | 151 | `"agent_type": agent.name.replace("-", "_"),` | W | CLI |

### 5.15 Agent System Config (CONFIG)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `agents/system_agent_config.py` | 40 | `agent_type: str` (dataclass field) | DEF | CONFIG |
| `agents/system_agent_config.py` | 82-328 | `agent_type="orchestrator/engineer/architecture/documentation/qa/research/ops/security/data_engineer/version_control"` | W (hardcoded per agent) | CONFIG |
| `agents/system_agent_config.py` | 363-576 | Multiple methods using `agent_type` as dict key | R/W | CONFIG |
| `agents/system_agent_config.py` | 438, 451, 464 | `"agent_type": agent_type,` in validation results | W | CONFIG |
| `agents/system_agent_config.py` | 513 | `"type": agent.agent_type,` | TRANSFORM: reads `agent_type`, writes as `"type"` | CONFIG |
| `agents/system_agent_config.py` | 598 | `def get_agent_model_assignment(agent_type: str)` | R | CONFIG |

### 5.16 Agent Loader (RUNTIME)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `agents/agent_loader.py` | 410 | `agent_type = getattr(agent, "agent_type", None)` | R | RUNTIME |
| `agents/agent_loader.py` | 417-419 | `"category": agent_type.value if hasattr(agent_type, "value") else str(agent_type or "general")` | R | RUNTIME |

### 5.17 Deployment Results/Metrics (DEPLOYMENT)

| File | Line | Code | R/W | Classification |
|------|------|------|-----|----------------|
| `services/agents/deployment/deployment_results_manager.py` | (various) | `agent_type` in result tracking | R/W | DEPLOYMENT |
| `services/agents/deployment/agent_metrics_collector.py` | (various) | `agent_type` in metrics | R/W | DEPLOYMENT |
| `services/agents/deployment/agent_operation_service.py` | (various) | `agent_type` parameter | R | DEPLOYMENT |

---

## 6. TRANSLATION POINTS (Where Field Name Changes)

These are the critical locations where `agent_type` gets converted to/from `type`:

| # | File | Line | Direction | Code |
|---|------|------|-----------|------|
| **T1** | `agent_template_builder.py` | 493/568 | `agent_type` -> `type:` | Reads `template_data.get("agent_type")`, writes `type: {agent_type}` to frontmatter |
| **T2** | `agent_discovery_service.py` | 320 | `agent_type:` -> `"type"` key | `"type": frontmatter.get("agent_type", ...)` |
| **T3** | `agent_registry.py` | 73,105,208,321,747,801 | `.agent_type` -> `"type"` key | `"type": unified_metadata.agent_type.value` (6 locations) |
| **T4** | `system_agent_config.py` | 513 | `.agent_type` -> `"type"` key | `"type": agent.agent_type` |
| **T5** | `dynamic_skills_generator.py` | 110 | `"type"` -> `agent_type` var | `agent_type = agent_info.get("type", "general-purpose")` |
| **T6** | `agent_wizard.py` | 753 | `agent_type` var -> `"type"` key | `"type": agent_type` |
| **T7** | `event_handlers.py` | 420/442 | `subagent_type` -> `agent_type` | `raw_agent_type = tool_input.get("subagent_type")` then `"agent_type": agent_type` |

---

## 7. YAML CONFIG FILES

**Result**: No YAML config files reference `agent_type` or use `type:` in an agent context. Zero matches.

---

## 8. TEST FILES SUMMARY

71 test files reference `agent_type`. These overwhelmingly use `"agent_type"` as the field name in test data construction. Key test files:

| File | Role | Field Used |
|------|------|-----------|
| `tests/eval/agents/shared/agent_response_parser.py` | Enum 3 definition | `agent_type` (param) |
| `tests/eval/agents/shared/agent_metrics.py` | Test metrics | `agent_type` |
| `tests/eval/agents/shared/agent_test_base.py` | Test base class | `agent_type` |
| `tests/services/agents/deployment/test_base_agent_hierarchy.py` | Tests agent hierarchy | `agent_type` in frontmatter |
| `tests/test_agent_deployment_comprehensive.py` | Deployment tests | Both fields |
| `tests/test_agent_discovery_service.py` | Discovery tests | `agent_type` |
| `tests/test_agent_hierarchy.py` | Hierarchy tests | `agent_type` |

---

## 9. CLASSIFICATION SUMMARY

### By Classification Category

| Classification | Locations Using `"type"` | Locations Using `"agent_type"` | Translation Points |
|----------------|:---:|:---:|:---:|
| **ENUM_DEF** | 1 (Enum 1 field `type: AgentType`) | 1 (Enum 2 field `agent_type: AgentType`) | 0 |
| **SOURCE_TEMPLATE** | 0 | 39 JSON templates | 0 |
| **DEPLOYMENT** | 8 locations in 5 files | 12 locations in 7 files | T1, T2 |
| **RUNTIME** | 15 locations in 7 files | 50+ locations in 20+ files | T3, T5 |
| **CLI** | 4 locations in 1 file | 5 locations in 3 files | T6 |
| **CONFIG** | 15 hardcoded in 1 file | 20+ in 3 files | T4 |
| **HOOKS** | 0 | 80+ locations in 12 files | T7 |
| **DASHBOARD** | 0 | 1 location | 0 |
| **SKILL_MAPPING** | 0 | 1 location (dead code) | 0 |
| **SERIALIZATION** | 0 | 2 locations | 0 |
| **FRONTMATTER** | 48 files | 27 files | N/A |
| **TEST** | ~10 files | ~70 files | 0 |

### Grand Totals

| Dimension | `"type"` | `"agent_type"` | Ratio |
|-----------|:---:|:---:|:---:|
| Python src locations (agent context) | ~42 | ~170+ | 1:4 |
| Frontmatter files | 48 | 27 | 2:1 |
| JSON templates | 0 | 39 | 0:39 |
| Test files | ~10 | ~71 | 1:7 |
| Hook system | 0 | 80+ | 0:80+ |
| Event data contract | 0 | Yes (primary) | 0:1 |
| Serialization format | 0 | Yes (primary) | 0:1 |

---

## 10. KEY FINDINGS

### Finding 1: `agent_type` dominates the Python codebase by 4:1

The `"agent_type"` field name is used in approximately 170+ locations across 57 source files, compared to ~42 locations for `"type"` (in agent context). The hook system alone accounts for 80+ `agent_type` references.

### Finding 2: `type:` dominates frontmatter by 2:1

48 deployed agent files use `type:` vs 27 using `agent_type:`. This is because `AgentTemplateBuilder` writes `type:` (translation point T1).

### Finding 3: Seven translation points exist

Seven locations silently convert between field names (T1-T7). The most impactful is T1 (`agent_template_builder.py` lines 493/568), which is the root cause of the frontmatter split.

### Finding 4: The agent_registry.py compatibility layer performs 6 translations

`core/agent_registry.py` reads `.agent_type` from Enum 2 objects and serializes them under the `"type"` key in 6 separate locations. This is a systematic translation, not ad-hoc.

### Finding 5: Hook system exclusively uses `agent_type`

The entire hook/event system (12 files, 80+ references) uses `"agent_type"` in event payloads. Changing to `"type"` would break the dashboard frontend and all WebSocket consumers.

### Finding 6: `subagent_type` is a third naming variant

Claude Code's API uses `subagent_type` as the parameter name. This gets translated to `agent_type` in the hook system (T7). 6 source files handle this translation.

### Finding 7: agents_metadata.py uses `"type"` with non-standard values

`agents_metadata.py` uses `"type": "core_agent"` / `"optimization_agent"` / `"system_agent"` -- values that match NEITHER Enum 1 NOR frontmatter values. This is a separate classification entirely.

### Finding 8: agent_wizard.py creates the same translation as agent_template_builder

The interactive agent wizard (line 753) assigns `"type": agent_type` -- reading a variable named `agent_type` but writing it under the `"type"` key. This mirrors the same translation as T1.

### Finding 9: Zero YAML config files involved

No YAML configuration files reference either field name. The usage is entirely in Python code, JSON templates, and Markdown frontmatter.

### Finding 10: Standardizing to `agent_type` requires fewer Python changes

- Changing `"type"` -> `"agent_type"`: ~42 source locations in ~15 files
- Changing `"agent_type"` -> `"type"`: ~170+ source locations in ~57 files + event contract breakage
- Additionally, 71 test files already use `"agent_type"` vs ~10 using `"type"`

---

## Appendix A: Complete File Index

### Files that use ONLY `"type"` (agent context)

1. `src/claude_mpm/services/agents/management/agent_management_service.py` (5 locations)
2. `src/claude_mpm/services/agents/deployment/agent_validator.py` (2 locations)
3. `src/claude_mpm/services/agents/deployment/deployment_wrapper.py` (1 location)
4. `src/claude_mpm/services/cli/agent_listing_service.py` (4 locations)
5. `src/claude_mpm/agents/agents_metadata.py` (14 locations)
6. `src/claude_mpm/models/agent_definition.py` (2 locations)

### Files that use ONLY `"agent_type"`

*(57 files in src/, see Section 5 above for complete listing)*

### Files that use BOTH (translation points)

1. `src/claude_mpm/core/agent_registry.py` - reads `.agent_type`, writes `"type"` key (6 locations)
2. `src/claude_mpm/services/agents/deployment/agent_template_builder.py` - reads `"agent_type"`, writes `type:` to frontmatter
3. `src/claude_mpm/services/agents/deployment/agent_discovery_service.py` - reads `"agent_type"`, stores in `"type"` key
4. `src/claude_mpm/services/agents/registry/deployed_agent_discovery.py` - reads both with fallback chain
5. `src/claude_mpm/agents/system_agent_config.py` - reads `.agent_type`, writes `"type"` key
6. `src/claude_mpm/services/dynamic_skills_generator.py` - reads `"type"` key into `agent_type` variable
7. `src/claude_mpm/cli/interactive/agent_wizard.py` - reads `agent_type` variable, writes `"type"` key
8. `src/claude_mpm/hooks/claude_hooks/event_handlers.py` - reads `subagent_type`, writes `"agent_type"` key

---

## Appendix B: Value Vocabulary

All distinct values used across all locations:

### Frontmatter/functional role values (from agent files + JSON templates)

`engineer`, `ops`, `qa`, `research`, `documentation`, `security`, `product`, `specialized`, `system`, `analysis`, `refactoring`, `content`, `imagemagick`, `memory_manager`, `claude-mpm`, `engineering` (typo)

### Enum 1 values (models)

`core`, `project`, `custom`, `system`, `specialized`

### Enum 2 values (unified registry)

`core`, `specialized`, `user_defined`, `project`, `memory_aware`

### Enum 3 values (tests)

`base`, `research`, `engineer`, `qa`, `ops`, `documentation`, `prompt_engineer`, `pm`

### agents_metadata values

`core_agent`, `optimization_agent`, `system_agent`

### system_agent_config values

`orchestrator`, `engineer`, `architecture`, `documentation`, `qa`, `research`, `ops`, `security`, `data_engineer`, `version_control`

### subagent_type values (Claude Code API / documentation)

`research-agent`, `engineer`, `qa-agent`, `documentation-agent`, `security-agent`, `ops-agent`, `version-control`, `data-engineer`, `pm`, `test_integration`
