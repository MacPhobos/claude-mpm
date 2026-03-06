# Code Evidence: Filename Standardization Plan Verification

---

## Evidence for Claim 1: Inconsistent Naming

### `.claude/agents/` directory listing (underscore files only)
```
dart_engineer.md
golang_engineer.md
java_engineer.md
nestjs_engineer.md
nextjs_engineer.md
php_engineer.md
product_owner.md
react_engineer.md
real_user.md
ruby_engineer.md
rust_engineer.md
svelte_engineer.md
tauri_engineer.md
visual_basic_engineer.md
```
Count: 14 files (plan says "~15" - off by one)

### `.claude/agents/` directory listing (-agent suffix files)
```
api-qa-agent.md
content-agent.md
digitalocean-ops-agent.md
documentation-agent.md
gcp-ops-agent.md
javascript-engineer-agent.md
local-ops-agent.md
memory-manager-agent.md
ops-agent.md
qa-agent.md
research-agent.md
security-agent.md
tmux-agent.md
vercel-ops-agent.md
web-qa-agent.md
```
Count: 15 files (plan does not mention these)

---

## Evidence for Claim 3: Functions Exist in deployment_utils.py

### `normalize_deployment_filename()` - lines 36-80
```python
def normalize_deployment_filename(
    source_filename: str, agent_id: Optional[str] = None
) -> str:
    path = Path(source_filename)
    stem = path.stem
    normalized_stem = stem.lower().replace("_", "-")
    if normalized_stem.endswith("-agent"):
        normalized_stem = normalized_stem[:-6]  # Remove "-agent"
    return f"{normalized_stem}.md"
```

### `get_underscore_variant_filename()` - lines 135-161
```python
def get_underscore_variant_filename(normalized_filename: str) -> Optional[str]:
    path = Path(normalized_filename)
    stem = path.stem
    if "-" not in stem:
        return None
    underscore_stem = stem.replace("-", "_")
    return f"{underscore_stem}.md"
```

### `deploy_agent_file()` - lines 299-448 (key algorithm)
```python
def deploy_agent_file(
    source_file: Path,
    deployment_dir: Path,
    *,
    cleanup_legacy: bool = True,
    ensure_frontmatter: bool = True,
    force: bool = False,
) -> DeploymentResult:
    # Step 2: Normalize filename to dash-based convention
    normalized_filename = normalize_deployment_filename(source_file.name)
    target_file = deployment_dir / normalized_filename

    # Step 3: Clean up legacy underscore variants
    if cleanup_legacy:
        underscore_variant = get_underscore_variant_filename(normalized_filename)
        if underscore_variant:
            underscore_path = deployment_dir / underscore_variant
            if underscore_path.exists() and underscore_path != target_file:
                underscore_path.unlink()
                cleaned_legacy.append(underscore_variant)
```

---

## Evidence for Claim 4: Legacy Paths Use Raw stem

### Path 1: single_agent_deployer.py lines 68-69 (confirmed)
```python
agent_name = template_file.stem
target_file = agents_dir / f"{agent_name}.md"
```

### Path 2: single_agent_deployer.py line 217 (confirmed)
```python
target_file = target_dir / f"{agent_name}.md"
```
Note: `agent_name` here is the parameter passed to `deploy_agent()`, not normalized.

### Path 3: async_agent_deployment.py lines 481-482 (confirmed)
```python
agent_name = agent.get("_agent_name", "unknown")
target_file = agents_dir / f"{agent_name}.md"
```
And `_agent_name` is set from `file_path.stem` at line 264:
```python
data["_agent_name"] = file_path.stem
```

### Path 4: local_template_deployment.py line 113 (confirmed)
```python
target_file = self.target_dir / f"{template.agent_id}.md"
```

### MISSED Path 5: agent_deployment_context.py lines 73-74
```python
@classmethod
def from_template_file(
    cls,
    template_file: Path,
    agents_dir: Path,
    ...
) -> "AgentDeploymentContext":
    agent_name = template_file.stem  # RAW STEM, no normalization
    target_file = agents_dir / f"{agent_name}.md"

    return cls(
        agent_name=agent_name,
        template_file=template_file,
        target_file=target_file,
        ...
    )
```

### MISSED Path 6: agent_deployment.py line 478
```python
for template_file in template_files:
    template_file_path = (
        template_file
        if isinstance(template_file, Path)
        else Path(template_file)
    )
    agent_name = template_file_path.stem  # RAW STEM before passing to deployer
```

### MISSED Path 7: agent_management_service.py line 97
```python
file_path = target_dir / f"{name}.md"  # name is raw parameter
file_path.write_text(content, encoding="utf-8")
```

---

## Evidence for Claim 7: Tests Coverage

### test_deployment_utils.py - confirmed to cover normalize and deploy functions
File location: `tests/services/agents/test_deployment_utils.py`
Classes covered:
- `TestNormalizeDeploymentFilename` (7 test methods)
- `TestEnsureAgentIdInFrontmatter` (6 test methods)
- `TestGetUnderscoreVariantFilename` (4 test methods)
- `TestDeploymentUtilsIntegration` (3 test methods)
- `TestValidateAgentFile` (6 test methods)
- `TestDeployAgentFile` (8 test methods)

### MISSING test scenario: frontmatter agent_id preservation after rename
No test exists for the case where source file has `agent_id: ruby_engineer` in frontmatter
and is being deployed to `ruby-engineer.md`. The function silently preserves the
underscore `agent_id`, leaving a filename/frontmatter mismatch.

---

## Evidence for Gap 2: Frontmatter Not Updated

### `ensure_agent_id_in_frontmatter()` - lines 121-125
```python
try:
    parsed = yaml.safe_load(yaml_content)
    if isinstance(parsed, dict) and "agent_id" in parsed:
        # agent_id already exists, return unchanged
        return content  # <-- CRITICAL: does NOT update existing agent_id
except yaml.YAMLError:
    pass
```

### Current frontmatter in ruby_engineer.md (will NOT be fixed)
```yaml
---
name: Ruby Engineer
description: '...'
version: 2.0.0
schema_version: 1.3.0
agent_id: ruby_engineer    # <- will remain "ruby_engineer" after rename to ruby-engineer.md
agent_type: engineer
---
```

### Verification via Python simulation
Running the actual code confirms: when `ruby_engineer.md` content (which has `agent_id: ruby_engineer`)
is passed through `ensure_agent_id_in_frontmatter(content, "ruby-engineer.md")`, the content
is returned unchanged. The `agent_id` stays as `ruby_engineer`.

---

## Evidence for Gap 1: Filename Collisions

Five pairs where both the `-agent` and the base version already exist:

```
documentation-agent.md  ->  documentation.md   (CONFLICT: documentation.md exists)
ops-agent.md            ->  ops.md             (CONFLICT: ops.md exists)
qa-agent.md             ->  qa.md              (CONFLICT: qa.md exists)
research-agent.md       ->  research.md        (CONFLICT: research.md exists)
web-qa-agent.md         ->  web-qa.md          (CONFLICT: web-qa.md exists)
```

The `deploy_agent_file()` function handles the underscore->hyphen cleanup via
`get_underscore_variant_filename()`. However, `get_underscore_variant_filename()` only
converts dashes to underscores - it does NOT produce the `-agent` variant. So there is
NO automatic cleanup of the `-agent` versions when deploying a base version.

---

## Evidence for Gap 3: Two Conflicting Normalization Systems

### agent_name_normalizer.py - CANONICAL_NAMES uses underscore keys
```python
CANONICAL_NAMES = {
    "ruby_engineer": "Ruby Engineer",     # underscore key
    "dart_engineer": "Dart Engineer",     # underscore key
    "product_owner": "Product Owner",     # underscore key
    ...
}

ALIASES = {
    "ruby_engineer": "ruby_engineer",    # maps to underscore canonical
    "ruby": "ruby_engineer",             # maps to underscore canonical
    "dart_engineer": "dart_engineer",    # maps to underscore canonical
}

def normalize(cls, agent_name: str) -> str:
    # Converts hyphens and spaces TO underscores for lookup:
    cleaned = cleaned.replace("-", "_").replace(" ", "_")
```

### agent_registry.py - normalize_agent_id() uses hyphen as canonical
```python
def normalize_agent_id(self, agent_id: str) -> str:
    normalized = agent_id.lower()
    normalized = normalized.replace("_", "-")   # underscores become hyphens
    normalized = normalized.replace(" ", "-")
    ...
    return normalized  # dash-based
```

### AGENT_ALIASES in agent_registry.py - maps specific underscore to hyphen
```python
AGENT_ALIASES: Dict[str, str] = {
    "python_engineer": "python-engineer",
    "product_owner": "product-owner",
    ...
}
```

These two systems produce opposite canonical forms: `agent_name_normalizer.py` normalizes
everything to underscores, while `agent_registry.py` normalizes to hyphens. They are used
in different parts of the codebase and will give different results for the same input.

---

## Evidence for Gap 4: Pipeline Path Missing from Plan

### agent_processing_step.py lines 54-70
```python
for template_file in context.template_files:
    agent_name = template_file.stem  # RAW STEM
    ...
    agent_context = AgentDeploymentContext.from_template_file(
        template_file=template_file,
        agents_dir=context.actual_target_dir,
        ...
    )
```

### agent_deployment_context.py lines 73-74
```python
agent_name = template_file.stem  # RAW STEM - no normalization
target_file = agents_dir / f"{agent_name}.md"
```

This pipeline path (`AgentProcessingStep` -> `AgentProcessor` -> writes to `context.target_file`)
is not listed in the plan's "Files to Modify" section.

---

## Evidence for What Already Works

### git_source_sync_service.py - ALREADY uses deploy_agent_file()
```python
# Phase 3 Fix (Issue #299): Use unified deploy_agent_file() function
result = deploy_agent_file(
    source_file=cache_file,
    deployment_dir=deployment_dir,
    cleanup_legacy=True,
    ensure_frontmatter=True,
    force=force,
)
```

### single_tier_deployment_service.py - ALREADY imports deploy_agent_file
```python
from claude_mpm.services.agents.deployment_utils import (
    deploy_agent_file,
)
```

These paths already use the correct unified function - the plan correctly identifies them
as "Files to Reference (no changes needed)."
