"""
Todo and Task Tools section generator for framework CLAUDE.md.
"""

from typing import Any, Dict

from . import BaseSectionGenerator


class TodoTaskToolsGenerator(BaseSectionGenerator):
    """Generates the Todo and Task Tools section."""

    def generate(self, data: Dict[str, Any]) -> str:
        """Generate the todo and task tools section."""
        return """
## B) TODO AND TASK TOOLS

### 🚨 MANDATORY: TodoWrite Integration with Task Tool

**Workflow Pattern:**
1. **Create TodoWrite entries** for complex multi-agent tasks with automatic agent name prefixes
2. **Mark todo as in_progress** when delegating via Task Tool
3. **Update todo status** based on subprocess completion
4. **Mark todo as completed** when agent delivers results

### Agent Name Prefix System

**Standard TodoWrite Entry Format:**
- **Research tasks** → `[Research] Analyze patterns and investigate implementation`
- **Documentation tasks** → `[Documentation] Update API reference and user guide`
- **Changelog tasks** → `[Documentation] Generate changelog for version 2.0`
- **QA tasks** → `[QA] Execute test suite and validate functionality`
- **DevOps tasks** → `[Ops] Configure deployment pipeline`
- **Security tasks** → `[Security] Perform vulnerability assessment`
- **Version Control tasks** → `[Version Control] Create feature branch and manage tags`
- **Version Management tasks** → `[Version Control] Apply semantic version bump`
- **Code Implementation tasks** → `[Engineer] Implement authentication system`
- **Data Operations tasks** → `[Data Engineer] Optimize database queries`

### Task Tool Subprocess Naming Conventions

**Task Tool Usage Pattern:**
```
Task(description="[task description]", subagent_type="[agent-type]")
```

**Valid subagent_type values (must match deployed agent YAML `name:` field values):**

**Required format (Claude Code expects these exact values from deployed agent YAML `name:` field):**
- `subagent_type="Research"` - For investigation and analysis
- `subagent_type="Engineer"` - For coding and implementation
- `subagent_type="QA"` - For testing and quality assurance
- `subagent_type="Documentation Agent"` - For docs and guides
- `subagent_type="Security"` - For security assessments
- `subagent_type="Ops"` - For deployment and infrastructure
- `subagent_type="Version Control"` - For git and version management
- `subagent_type="Data Engineer"` - For data processing and APIs
- `subagent_type="PM"` - For project management coordination

**Note:** Claude Code's Task tool requires exact agent names as defined in the deployed agent YAML frontmatter `name:` field. The names must match exactly - including capitalization and spaces.

**Examples of Proper Task Tool Usage (must match deployed agent YAML `name:` field):**
- ✅ `Task(description="Update framework documentation", subagent_type="Documentation Agent")`
- ✅ `Task(description="Execute test suite validation", subagent_type="QA")`
- ✅ `Task(description="Create feature branch and sync", subagent_type="Version Control")`
- ✅ `Task(description="Investigate performance patterns", subagent_type="Research")`
- ✅ `Task(description="Implement authentication system", subagent_type="Engineer")`
- ✅ `Task(description="Configure database and optimize queries", subagent_type="Data Engineer")`
- ✅ `Task(description="Coordinate project tasks", subagent_type="PM")`
- ❌ `Task(description="Analyze code patterns", subagent_type="research-agent")` (WRONG - use "Research")
- ❌ `Task(description="Update API docs", subagent_type="documentation-agent")` (WRONG - use "Documentation Agent")
- ❌ `Task(description="Create release tags", subagent_type="version-control")` (WRONG - use "Version Control")

### 🚨 MANDATORY: THREE SHORTCUT COMMANDS

#### 1. **"push"** - Version Control, Quality Assurance & Release Management
**Enhanced Delegation Flow**: PM → Documentation Agent (changelog & version docs) → QA Agent (testing/linting) → Data Engineer Agent (data validation & API checks) → Version Control Agent (tracking, version bumping & Git operations)

**Components:**
1. **Documentation Agent**: Generate changelog, analyze semantic versioning impact
2. **QA Agent**: Execute test suite, perform quality validation
3. **Data Engineer Agent**: Validate data integrity, verify API connectivity, check database schemas
4. **Version Control Agent**: Track files, apply version bumps, create tags, execute Git operations

#### 2. **"deploy"** - Local Deployment Operations
**Delegation Flow**: PM → Ops Agent (local deployment) → QA Agent (deployment validation)

#### 3. **"publish"** - Package Publication Pipeline
**Delegation Flow**: PM → Documentation Agent (version docs) → Ops Agent (package publication)

### Multi-Agent Coordination Workflows

**Example Integration:**
```
# TodoWrite entries with proper agent prefixes:
- ☐ [Documentation] Generate changelog and analyze version impact
- ☐ [QA] Execute full test suite and quality validation
- ☐ [Data Engineer] Validate data integrity and verify API connectivity
- ☐ [Version Control] Apply semantic version bump and create release tags

# Corresponding Task Tool delegations (must match deployed agent YAML name: field):
Task(description="Generate changelog and analyze version impact", subagent_type="Documentation Agent")
Task(description="Execute full test suite and quality validation", subagent_type="QA")
Task(description="Validate data integrity and verify API connectivity", subagent_type="Data Engineer")
Task(description="Apply semantic version bump and create release tags", subagent_type="Version Control")

# Update TodoWrite status based on agent completions
```

---"""
