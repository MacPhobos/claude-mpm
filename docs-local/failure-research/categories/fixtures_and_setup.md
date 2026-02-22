# Failure Category: fixtures_and_setup

## A. Snapshot
- **Total failures**: 38
- **Top exception types**:
  - `(unknown)`: 38
- **Top subpatterns**:

  | Subpattern | Count |
  |---|---|
  | `failed on setup with "file <path>, line N \| <unknown>` | 38 |

## B. Representative Examples

### Subpattern: `failed on setup with "file <path>, line N | <unknown>` (38 failures)

**Example 1**
- **nodeid**: `tests/services/agents/test_agent_preset_service.py::TestAgentPresetService::test_list_presets`
- **file_hint**: `tests/services/agents/test_agent_preset_service/TestAgentPresetService.py`
- **failure**:
```
exc_type: 
message: failed on setup with "file /Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py, line 28
--- relevant traceback (up to 30 lines) ---
file /Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py, line 28
      def test_list_presets(self, service):
file /Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py, line 23
      @pytest.fixture
      def service(self, mock_source_manager):
file /Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py, line 15
      @pytest.fixture
      def mock_source_manager(self, mocker):
E       fixture 'mocker' not found
>       available fixtures: __pytest_repeat_step_number, _class_scoped_runner, _function_scoped_runner, _module_scoped_runner, _package_scoped_runner, _session_scoped_runner, anyio_backend, anyio_backend_name, anyio_backend_options, async_service, cache, capfd, capfdbinary, caplog, capsys, capsysbinary, capteesys, clean_env, cli_runner, config_file, cov, doctest_namespace, event_loop, event_loop_policy, free_tcp_port, free_tcp_port_factory, free_udp_port, free_udp_port_factory, mock_agent, mock_argparse_namespace, mock_async_client, mock_config, mock_logger, mock_memory_manager, mock_process, mock_service_registry, mock_session, mock_socketio_client, mock_socketio_server, mock_source_manager, mock_subprocess, monkeypatch, no_cover, project_root, pytestconfig, record_property, record_testsuite_property, record_xml_attribute, recwarn, sample_json_content, sample_yaml_content, service, subtests, temp_agent_dir, temp_memory_dir, test_env, testrun_uid, tmp_path, tmp_path_factory, tmpdir, tmpdir_factory, unused_tcp_port, unused_tcp_port_factory, unused_udp_port, unused_udp_port_factory, worker_id
>       use 'pytest --fixtures [testpath]' for help on them.

/Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py:15
```

**Example 2**
- **nodeid**: `tests/services/agents/test_agent_preset_service.py::TestAgentPresetService::test_validate_preset_valid`
- **file_hint**: `tests/services/agents/test_agent_preset_service/TestAgentPresetService.py`
- **failure**:
```
exc_type: 
message: failed on setup with "file /Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py, line 44
--- relevant traceback (up to 30 lines) ---
file /Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py, line 44
      def test_validate_preset_valid(self, service):
file /Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py, line 23
      @pytest.fixture
      def service(self, mock_source_manager):
file /Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py, line 15
      @pytest.fixture
      def mock_source_manager(self, mocker):
E       fixture 'mocker' not found
>       available fixtures: __pytest_repeat_step_number, _class_scoped_runner, _function_scoped_runner, _module_scoped_runner, _package_scoped_runner, _session_scoped_runner, anyio_backend, anyio_backend_name, anyio_backend_options, async_service, cache, capfd, capfdbinary, caplog, capsys, capsysbinary, capteesys, clean_env, cli_runner, config_file, cov, doctest_namespace, event_loop, event_loop_policy, free_tcp_port, free_tcp_port_factory, free_udp_port, free_udp_port_factory, mock_agent, mock_argparse_namespace, mock_async_client, mock_config, mock_logger, mock_memory_manager, mock_process, mock_service_registry, mock_session, mock_socketio_client, mock_socketio_server, mock_source_manager, mock_subprocess, monkeypatch, no_cover, project_root, pytestconfig, record_property, record_testsuite_property, record_xml_attribute, recwarn, sample_json_content, sample_yaml_content, service, subtests, temp_agent_dir, temp_memory_dir, test_env, testrun_uid, tmp_path, tmp_path_factory, tmpdir, tmpdir_factory, unused_tcp_port, unused_tcp_port_factory, unused_udp_port, unused_udp_port_factory, worker_id
>       use 'pytest --fixtures [testpath]' for help on them.

/Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py:15
```

**Example 3**
- **nodeid**: `tests/services/agents/test_agent_preset_service.py::TestAgentPresetService::test_validate_preset_invalid`
- **file_hint**: `tests/services/agents/test_agent_preset_service/TestAgentPresetService.py`
- **failure**:
```
exc_type: 
message: failed on setup with "file /Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py, line 50
--- relevant traceback (up to 30 lines) ---
file /Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py, line 50
      def test_validate_preset_invalid(self, service):
file /Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py, line 23
      @pytest.fixture
      def service(self, mock_source_manager):
file /Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py, line 15
      @pytest.fixture
      def mock_source_manager(self, mocker):
E       fixture 'mocker' not found
>       available fixtures: __pytest_repeat_step_number, _class_scoped_runner, _function_scoped_runner, _module_scoped_runner, _package_scoped_runner, _session_scoped_runner, anyio_backend, anyio_backend_name, anyio_backend_options, async_service, cache, capfd, capfdbinary, caplog, capsys, capsysbinary, capteesys, clean_env, cli_runner, config_file, cov, doctest_namespace, event_loop, event_loop_policy, free_tcp_port, free_tcp_port_factory, free_udp_port, free_udp_port_factory, mock_agent, mock_argparse_namespace, mock_async_client, mock_config, mock_logger, mock_memory_manager, mock_process, mock_service_registry, mock_session, mock_socketio_client, mock_socketio_server, mock_source_manager, mock_subprocess, monkeypatch, no_cover, project_root, pytestconfig, record_property, record_testsuite_property, record_xml_attribute, recwarn, sample_json_content, sample_yaml_content, service, subtests, temp_agent_dir, temp_memory_dir, test_env, testrun_uid, tmp_path, tmp_path_factory, tmpdir, tmpdir_factory, unused_tcp_port, unused_tcp_port_factory, unused_udp_port, unused_udp_port_factory, worker_id
>       use 'pytest --fixtures [testpath]' for help on them.

/Users/mac/workspace/claude-mpm/tests/services/agents/test_agent_preset_service.py:15
```

## C. Hypotheses

- Fixture defined in wrong conftest scope (session vs function).
- Async fixtures not declared with `async def` or missing `asyncio_mode`.
- Fixture depends on another fixture from a different scope.
- Test file missing import of shared conftest or plugin.
- Fixture name typo between definition and usage.

## D. Investigation Checklist

- [ ] Check CI logs for the first occurrence of this failure pattern.
- [ ] Reproduce locally by running the representative test above.
- [ ] Check recent commits (`git log --oneline -20`) for changes near the failure.
- [ ] Run with `-x` flag to stop at first failure and inspect state.
- [ ] Inspect `conftest.py` files for fixture scope declarations.
- [ ] Check for `@pytest.fixture(scope=...)` mismatch with test scope.
- [ ] Verify `asyncio_mode` setting in `pytest.ini` for async fixtures.
- [ ] Search for duplicate fixture names across conftest files.

## E. Targeted Repo Queries

```bash
rg "@pytest\.fixture" tests/ --include="*.py"
rg "conftest" tests/ --include="*.py" -l
rg "asyncio_mode|event_loop" . --include="*.ini" --include="*.toml" --include="*.cfg"
```

## F. Minimal Reproduction Plan

```bash
# Run single representative test
pytest "tests/services/agents/test_agent_preset_service.py::TestAgentPresetService::test_list_presets" -xvs

# Run small set for this bucket
pytest -k 'fixture or setup' --no-header -q 2>&1 | head -50
```

## G. Follow-up Claude Prompt

```
Given these failing tests in the fixtures_and_setup bucket:
  tests/services/agents/test_agent_preset_service.py::TestAgentPresetService::test_list_presets

And these relevant source files:
  tests/services/agents/test_agent_preset_service/TestAgentPresetService.py

Please:
1. Identify the root cause
2. Propose a fix plan
3. Estimate blast radius
```
