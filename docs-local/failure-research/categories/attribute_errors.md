# Failure Category: attribute_errors

## A. Snapshot
- **Total failures**: 512
- **Top exception types**:

> **Note**: This category has 512 failures. See `data/failures.jsonl` for the complete list.

  - `AttributeError`: 457
  - `(unknown)`: 55
- **Top subpatterns**:

  | Subpattern | Count |
  |---|---|
  | `AttributeError: <str> object has no attribute <str> \| <unknown>` | 231 |
  | `AttributeError: <str> object has no attribute <str>. Did you mean: <str>? \| <unknown>` | 90 |
  | `AttributeError: module <str> has no attribute <str> \| <unknown>` | 57 |
  | `failed on setup with <str> \| <unknown>` | 52 |
  | `AttributeError: <module <str> from <str>> does not have the attribute <str> \| <unknown>` | 34 |
  | `AttributeError: type object <str> has no attribute <str> \| <unknown>` | 22 |
  | `AttributeError: <claude_mpm.services.agents.memory.agent_memory_manager.AgentMemoryManager object at <hex>> does not hav \| <unknown>` | 8 |
  | `AttributeError: property <str> of <str> object has no deleter \| <unknown>` | 7 |
  | `AttributeError: property <str> of <str> object has no setter \| <unknown>` | 5 |
  | `AttributeError: <tests.services.test_agent_capabilities_service.TestAgentCapabilitiesService object at <hex>> does not h \| <unknown>` | 2 |

## B. Representative Examples

### Subpattern: `AttributeError: <str> object has no attribute <str> | <unknown>` (231 failures)

**Example 1**
- **nodeid**: `tests/integration/test_schema_integration.py::TestSchemaIntegration::test_agent_deployment_with_new_format`
- **file_hint**: `tests/integration/test_schema_integration/TestSchemaIntegration.py`
- **failure**:
```
exc_type: AttributeError
message: AttributeError: 'TestSchemaIntegration' object has no attribute 'get_agent'
--- relevant traceback (up to 30 lines) ---
tests/integration/test_schema_integration.py:53: in test_agent_deployment_with_new_format
    agent = self.get_agent("engineer")
            ^^^^^^^^^^^^^^
E   AttributeError: 'TestSchemaIntegration' object has no attribute 'get_agent'
```

**Example 2**
- **nodeid**: `tests/integration/test_schema_integration.py::TestSchemaIntegration::test_model_compatibility_enforcement`
- **file_hint**: `tests/integration/test_schema_integration/TestSchemaIntegration.py`
- **failure**:
```
exc_type: AttributeError
message: AttributeError: 'TestSchemaIntegration' object has no attribute 'glob'
--- relevant traceback (up to 30 lines) ---
tests/integration/test_schema_integration.py:143: in test_model_compatibility_enforcement
    for agent_file in self.glob("*.json"):
                      ^^^^^^^^^
E   AttributeError: 'TestSchemaIntegration' object has no attribute 'glob'
```

**Example 3**
- **nodeid**: `tests/integration/test_schema_integration.py::TestSchemaIntegration::test_resource_tier_distribution`
- **file_hint**: `tests/integration/test_schema_integration/TestSchemaIntegration.py`
- **failure**:
```
exc_type: AttributeError
message: AttributeError: 'TestSchemaIntegration' object has no attribute 'glob'
--- relevant traceback (up to 30 lines) ---
tests/integration/test_schema_integration.py:161: in test_resource_tier_distribution
    for agent_file in self.glob("*.json"):
                      ^^^^^^^^^
E   AttributeError: 'TestSchemaIntegration' object has no attribute 'glob'
```

### Subpattern: `AttributeError: <str> object has no attribute <str>. Did you mean: <str>? | <unknown>` (90 failures)

**Example 1**
- **nodeid**: `tests/integration/test_schema_integration.py::TestSchemaIntegration::test_all_agents_load_successfully`
- **file_hint**: `tests/integration/test_schema_integration/TestSchemaIntegration.py`
- **failure**:
```
exc_type: AttributeError
message: AttributeError: 'UnifiedAgentRegistry' object has no attribute 'load_agents'. Did you mean: 'list_agents'?
--- relevant traceback (up to 30 lines) ---
tests/integration/test_schema_integration.py:28: in test_all_agents_load_successfully
    loader = AgentLoader()
             ^^^^^^^^^^^^^
src/claude_mpm/agents/agent_loader.py:184: in __init__
    self.registry.load_agents()
    ^^^^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'UnifiedAgentRegistry' object has no attribute 'load_agents'. Did you mean: 'list_agents'?
```

**Example 2**
- **nodeid**: `tests/services/test_agent_capabilities_generator.py::TestAgentCapabilitiesGenerator::test_group_by_tier`
- **file_hint**: `tests/services/test_agent_capabilities_generator/TestAgentCapabilitiesGenerator.py`
- **failure**:
```
exc_type: AttributeError
message: AttributeError: 'TestAgentCapabilitiesGenerator' object has no attribute '_group_by_tier'. Did you mean: 'test_group_by_tier'?
--- relevant traceback (up to 30 lines) ---
tests/services/test_agent_capabilities_generator.py:149: in test_group_by_tier
    grouped = self._group_by_tier(sample_agents)
              ^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'TestAgentCapabilitiesGenerator' object has no attribute '_group_by_tier'. Did you mean: 'test_group_by_tier'?
```

**Example 3**
- **nodeid**: `tests/services/test_agent_capabilities_generator.py::TestAgentCapabilitiesGenerator::test_group_by_tier_unknown_tier`
- **file_hint**: `tests/services/test_agent_capabilities_generator/TestAgentCapabilitiesGenerator.py`
- **failure**:
```
exc_type: AttributeError
message: AttributeError: 'TestAgentCapabilitiesGenerator' object has no attribute '_group_by_tier'. Did you mean: 'test_group_by_tier'?
--- relevant traceback (up to 30 lines) ---
tests/services/test_agent_capabilities_generator.py:164: in test_group_by_tier_unknown_tier
    grouped = self._group_by_tier(agents)
              ^^^^^^^^^^^^^^^^^^^
E   AttributeError: 'TestAgentCapabilitiesGenerator' object has no attribute '_group_by_tier'. Did you mean: 'test_group_by_tier'?
```

### Subpattern: `AttributeError: module <str> has no attribute <str> | <unknown>` (57 failures)

**Example 1**
- **nodeid**: `tests/mcp/test_session_manager.py::TestStartSession::test_creates_session_and_returns_result`
- **file_hint**: `tests/mcp/test_session_manager/TestStartSession.py`
- **failure**:
```
exc_type: AttributeError
message: AttributeError: module 'claude_mpm' has no attribute 'mcp'
--- relevant traceback (up to 30 lines) ---
tests/mcp/test_session_manager.py:76: in test_creates_session_and_returns_result
    with patch(
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1451: in __enter__
    self.target = self.getter()
                  ^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pkgutil.py:528: in resolve_name
    result = getattr(result, p)
             ^^^^^^^^^^^^^^^^^^
src/claude_mpm/__init__.py:57: in __getattr__
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
E   AttributeError: module 'claude_mpm' has no attribute 'mcp'
```

**Example 2**
- **nodeid**: `tests/mcp/test_session_manager.py::TestStartSession::test_tracks_session`
- **file_hint**: `tests/mcp/test_session_manager/TestStartSession.py`
- **failure**:
```
exc_type: AttributeError
message: AttributeError: module 'claude_mpm' has no attribute 'mcp'
--- relevant traceback (up to 30 lines) ---
tests/mcp/test_session_manager.py:106: in test_tracks_session
    with patch(
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1451: in __enter__
    self.target = self.getter()
                  ^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pkgutil.py:528: in resolve_name
    result = getattr(result, p)
             ^^^^^^^^^^^^^^^^^^
src/claude_mpm/__init__.py:57: in __getattr__
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
E   AttributeError: module 'claude_mpm' has no attribute 'mcp'
```

**Example 3**
- **nodeid**: `tests/mcp/test_session_manager.py::TestStartSession::test_session_status_transitions`
- **file_hint**: `tests/mcp/test_session_manager/TestStartSession.py`
- **failure**:
```
exc_type: AttributeError
message: AttributeError: module 'claude_mpm' has no attribute 'mcp'
--- relevant traceback (up to 30 lines) ---
tests/mcp/test_session_manager.py:138: in test_session_status_transitions
    with patch(
../../.asdf/installs/python/3.12.11/lib/python3.12/unittest/mock.py:1451: in __enter__
    self.target = self.getter()
                  ^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pkgutil.py:528: in resolve_name
    result = getattr(result, p)
             ^^^^^^^^^^^^^^^^^^
src/claude_mpm/__init__.py:57: in __getattr__
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
E   AttributeError: module 'claude_mpm' has no attribute 'mcp'
```

## C. Hypotheses

- Object attribute removed or renamed in recent commit.
- Mock missing attribute that real object has.
- Module-level attribute accessed before module fully initialised.
- Typo in attribute name introduced during refactoring.
- Lazy property not available in test context.

## D. Investigation Checklist

- [ ] Check CI logs for the first occurrence of this failure pattern.
- [ ] Reproduce locally by running the representative test above.
- [ ] Check recent commits (`git log --oneline -20`) for changes near the failure.
- [ ] Run with `-x` flag to stop at first failure and inspect state.
- [ ] Search for the attribute name in recent git diff.
- [ ] Verify object being tested is properly initialised.
- [ ] Check if attribute was moved to a different class/module.

## E. Targeted Repo Queries

```bash
rg "AttributeError" tests/ --include="*.py"
rg "hasattr|getattr" src/ --include="*.py" | head -30
```

## F. Minimal Reproduction Plan

```bash
# Run single representative test
pytest "tests/integration/test_schema_integration.py::TestSchemaIntegration::test_agent_deployment_with_new_format" -xvs

# Run small set for this bucket
pytest -k 'attribute' --no-header -q 2>&1 | head -50
```

## G. Follow-up Claude Prompt

```
Given these failing tests in the attribute_errors bucket:
  tests/integration/test_schema_integration.py::TestSchemaIntegration::test_agent_deployment_with_new_format
  tests/integration/test_schema_integration.py::TestSchemaIntegration::test_all_agents_load_successfully
  tests/mcp/test_session_manager.py::TestStartSession::test_creates_session_and_returns_result

And these relevant source files:
  tests/integration/test_schema_integration/TestSchemaIntegration.py
  tests/integration/test_schema_integration/TestSchemaIntegration.py
  tests/mcp/test_session_manager/TestStartSession.py

Please:
1. Identify the root cause
2. Propose a fix plan
3. Estimate blast radius
```
