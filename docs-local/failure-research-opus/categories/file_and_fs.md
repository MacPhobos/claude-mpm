# File and Filesystem Errors

**Category**: `file_and_fs`

## A. Snapshot

- **Total failures in this category**: 103
- **Distinct subpatterns**: 10

### Top Exception Types

| Exception Type | Count |
|---|---|
| `FileNotFoundError` | 100 |
| `OSError` | 2 |
| `PermissionError` | 1 |

### Top Subpatterns

| # | Subpattern | Count |
|---|---|---|
| 1 | `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '<PATH>'` | 78 |
| 2 | `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '/private<PATH>` | 12 |
| 3 | `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '<LONG_STR>'` | 3 |
| 4 | `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '<PATH>` | 3 |
| 5 | `OSError: OSError: [Errno <N>] Directory not empty: '/private<PATH>'` | 2 |
| 6 | `FileNotFoundError: AssertionError: Failed to load agent template: [Errno <N>] No such file or direct...` | 1 |
| 7 | `FileNotFoundError: AssertionError: Agent deployment validation failed: [Errno <N>] No such file or d...` | 1 |
| 8 | `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: './claude-mpm'` | 1 |
| 9 | `FileNotFoundError: gitdb.exc.BadObject: BadObject: b'<LONG_STR>'` | 1 |
| 10 | `PermissionError: PermissionError: [Errno <N>] Operation not permitted: '/private<PATH>` | 1 |

## B. Representative Examples

### Subpattern: `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '<PATH>'`
- **Count**: 78
- **Exception**: `FileNotFoundError`

**Example 1**:
- **nodeid**: `tests.agents.test_mpm_skills_manager.TestAgentDefinitionStructure::test_json_is_valid`
- **file_hint**: `tests/agents/test_mpm_skills_manager.py`

```
Message: FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/agents/templates/mpm-skills-manager.json'

tests/agents/test_mpm_skills_manager.py:45: in test_json_is_valid
    with open(SKILLS_MANAGER_JSON) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/agents/templates/mpm-skills-manager.json'
```

**Example 2**:
- **nodeid**: `tests.agents.test_mpm_skills_manager.TestAgentDefinitionStructure::test_required_fields_present`
- **file_hint**: `tests/agents/test_mpm_skills_manager.py`

```
Message: FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/agents/templates/mpm-skills-manager.json'

tests/agents/test_mpm_skills_manager.py:51: in test_required_fields_present
    with open(SKILLS_MANAGER_JSON) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/agents/templates/mpm-skills-manager.json'
```

**Example 3**:
- **nodeid**: `tests.agents.test_mpm_skills_manager.TestAgentDefinitionStructure::test_schema_version`
- **file_hint**: `tests/agents/test_mpm_skills_manager.py`

```
Message: FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/agents/templates/mpm-skills-manager.json'

tests/agents/test_mpm_skills_manager.py:73: in test_schema_version
    with open(SKILLS_MANAGER_JSON) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm-tests/src/claude_mpm/agents/templates/mpm-skills-manager.json'
```

### Subpattern: `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '/private<PATH>`
- **Count**: 12
- **Exception**: `FileNotFoundError`

**Example 1**:
- **nodeid**: `tests.test_agent_deployment_comprehensive.TestPartialDeploymentFailures::test_deployment_failure_corrupted_template`
- **file_hint**: `tests/test_agent_deployment_comprehensive.py`

```
Message: FileNotFoundError: [Errno 2] No such file or directory: '/private/var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/pytest-of-mac/pytest-147/popen-gw9/test_deployment_failure_corrup0/templates/corrupted_agent.json'

tests/test_agent_deployment_comprehensive.py:384: in test_deployment_failure_corrupted_template
    corrupted_template.write_text('{"invalid": json syntax missing brace')
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1047: in write_text
    with self.open(mode='w', encoding=encoding, errors=errors, newline=newline) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1013: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/private/var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/pytest-of-mac/pytest-147/popen-gw9/test_deployment_failure_corrup0/templates/corrupted_agent.json'
```

**Example 2**:
- **nodeid**: `tests.test_agent_deployment_system.TestAgentDeployment::test_version_field_generation_semantic`
- **file_hint**: `tests/test_agent_deployment_system.py`

```
Message: FileNotFoundError: [Errno 2] No such file or directory: '/private/var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/pytest-of-mac/pytest-147/popen-gw9/test_version_field_generation_0/templates/test_agent.json'

tests/test_agent_deployment_system.py:51: in test_version_field_generation_semantic
    template_file.write_text(json.dumps(agent_template))
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1047: in write_text
    with self.open(mode='w', encoding=encoding, errors=errors, newline=newline) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1013: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/private/var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/pytest-of-mac/pytest-147/popen-gw9/test_version_field_generation_0/templates/test_agent.json'
```

**Example 3**:
- **nodeid**: `tests.test_agent_deployment_system.TestAgentDeployment::test_base_version_field_inclusion`
- **file_hint**: `tests/test_agent_deployment_system.py`

```
Message: FileNotFoundError: [Errno 2] No such file or directory: '/private/var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/pytest-of-mac/pytest-147/popen-gw9/test_base_version_field_inclus0/templates/agent_0.json'

tests/test_agent_deployment_system.py:79: in test_base_version_field_inclusion
    template_file.write_text(json.dumps(agent_template))
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1047: in write_text
    with self.open(mode='w', encoding=encoding, errors=errors, newline=newline) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1013: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/private/var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/pytest-of-mac/pytest-147/popen-gw9/test_base_version_field_inclus0/templates/agent_0.json'
```

### Subpattern: `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '<LONG_STR>'`
- **Count**: 3
- **Exception**: `FileNotFoundError`

**Example 1**:
- **nodeid**: `tests.hooks.claude_hooks.test_pre_split_verification.TestPreSplitVerification::test_file_size_justifies_split`
- **file_hint**: `tests/hooks/claude_hooks/test_pre_split_verification.py`

```
Message: FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'

tests/hooks/claude_hooks/test_pre_split_verification.py:119: in test_file_size_justifies_split
    lines = len(test_file_path.read_text().splitlines())
                ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1027: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1013: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'
```

**Example 2**:
- **nodeid**: `tests.hooks.claude_hooks.test_pre_split_verification.TestPreSplitVerification::test_proposed_split_reduces_size`
- **file_hint**: `tests/hooks/claude_hooks/test_pre_split_verification.py`

```
Message: FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'

tests/hooks/claude_hooks/test_pre_split_verification.py:124: in test_proposed_split_reduces_size
    current_lines = len(test_file_path.read_text().splitlines())
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1027: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1013: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'
```

**Example 3**:
- **nodeid**: `tests.hooks.claude_hooks.test_pre_split_verification.TestPreSplitVerification::test_verify_line_count`
- **file_hint**: `tests/hooks/claude_hooks/test_pre_split_verification.py`

```
Message: FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'

tests/hooks/claude_hooks/test_pre_split_verification.py:133: in test_verify_line_count
    actual_lines = len(test_file_path.read_text().splitlines())
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1027: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1013: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'
```

### Subpattern: `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '<PATH>`
- **Count**: 3
- **Exception**: `FileNotFoundError`

**Example 1**:
- **nodeid**: `tests.test_pack.TestPack::test_pack`
- **file_hint**: `tests/test_pack.py`

```
Message: FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm-tests/.venv/lib/python3.12/site-packages/gitdb/test/fixtures/packs/pack-a2bf8e71d8c18879e499335762dd95119d93d9f1.pack'

tests/test_pack.py:149: in test_pack
    self._assert_pack_file(pack, version, size)
tests/test_pack.py:89: in _assert_pack_file
    assert pack.version() == 2
           ^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/gitdb/pack.py:576: in version
    return self._version
           ^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/gitdb/util.py:253: in __getattr__
    self._set_cache_(attr)
.venv/lib/python3.12/site-packages/gitdb/pack.py:534: in _set_cache_
    self._cursor = mman.make_cursor(self._packpath).use_region()
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/smmap/mman.py:116: in use_region
    fsize = self._rlist.file_size()
            ^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/smmap/util.py:215: in file_size
    self._file_size = os.stat(self._path_or_fd).st_size
                      ^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm-tests/.venv/lib/python3.12/site-packages/gitdb/test/fixtures/packs/pack-a2bf8e71d8c18879e499335762dd95119d93d9f1.pack'
```

**Example 2**:
- **nodeid**: `tests.test_pack.TestPack::test_pack_entity`
- **file_hint**: `tests/test_pack.py`

```
Message: FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm-tests/.venv/lib/python3.12/site-packages/gitdb/test/fixtures/packs/pack-c0438c19fb16422b6bbcce24387b3264416d485b.idx'

.venv/lib/python3.12/site-packages/gitdb/test/lib.py:71: in wrapper
    return func(self, path)
           ^^^^^^^^^^^^^^^^
tests/test_pack.py:165: in test_pack_entity
    pack_objs.extend(entity.stream_iter())
.venv/lib/python3.12/site-packages/gitdb/pack.py:711: in _iter_objects
    _sha = self._index.sha
           ^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/gitdb/util.py:253: in __getattr__
    self._set_cache_(attr)
.venv/lib/python3.12/site-packages/gitdb/pack.py:287: in _set_cache_
    mmap = self._cursor.map()
           ^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/gitdb/util.py:253: in __getattr__
    self._set_cache_(attr)
.venv/lib/python3.12/site-packages/gitdb/pack.py:276: in _set_cache_
    self._cursor = mman.make_cursor(self._indexpath).use_region()
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/smmap/mman.py:116: in use_region
    fsize = self._rlist.file_size()
            ^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/smmap/util.py:215: in file_size
    self._file_size = os.stat(self._path_or_fd).st_size
                      ^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm-tests/.venv/lib/python3.12/site-packages/gitdb/test/fixtures/packs/pack-c0438c19fb16422b6bbcce24387b3264416d485b.idx'
```

**Example 3**:
- **nodeid**: `tests.test_pack.TestPack::test_pack_index`
- **file_hint**: `tests/test_pack.py`

```
Message: FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm-tests/.venv/lib/python3.12/site-packages/gitdb/test/fixtures/packs/pack-c0438c19fb16422b6bbcce24387b3264416d485b.idx'

tests/test_pack.py:138: in test_pack_index
    self._assert_index_file(index, version, size)
tests/test_pack.py:62: in _assert_index_file
    assert index.packfile_checksum() != index.indexfile_checksum()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/gitdb/pack.py:394: in packfile_checksum
    return self._cursor.map()[-40:-20]
           ^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/gitdb/util.py:253: in __getattr__
    self._set_cache_(attr)
.venv/lib/python3.12/site-packages/gitdb/pack.py:276: in _set_cache_
    self._cursor = mman.make_cursor(self._indexpath).use_region()
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/smmap/mman.py:116: in use_region
    fsize = self._rlist.file_size()
            ^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/smmap/util.py:215: in file_size
    self._file_size = os.stat(self._path_or_fd).st_size
                      ^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm-tests/.venv/lib/python3.12/site-packages/gitdb/test/fixtures/packs/pack-c0438c19fb16422b6bbcce24387b3264416d485b.idx'
```

### Subpattern: `OSError: OSError: [Errno <N>] Directory not empty: '/private<PATH>'`
- **Count**: 2
- **Exception**: `OSError`

**Example 1**:
- **nodeid**: `tests.unit.services.cli.test_session_resume_helper.TestGetSessionCount::test_returns_zero_when_directory_missing`
- **file_hint**: `tests/unit/services/cli/test_session_resume_helper.py`

```
Message: OSError: [Errno 66] Directory not empty: '/private/var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/pytest-of-mac/pytest-147/popen-gw4/test_returns_zero_when_directo0/test_project/.claude-mpm/sessions'

tests/unit/services/cli/test_session_resume_helper.py:899: in test_returns_zero_when_directory_missing
    helper.pause_dir.rmdir()
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1351: in rmdir
    os.rmdir(self)
E   OSError: [Errno 66] Directory not empty: '/private/var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/pytest-of-mac/pytest-147/popen-gw4/test_returns_zero_when_directo0/test_project/.claude-mpm/sessions'
```

**Example 2**:
- **nodeid**: `tests.unit.services.cli.test_session_resume_helper.TestListAllSessions::test_returns_empty_when_directory_missing`
- **file_hint**: `tests/unit/services/cli/test_session_resume_helper.py`

```
Message: OSError: [Errno 66] Directory not empty: '/private/var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/pytest-of-mac/pytest-147/popen-gw4/test_returns_empty_when_direct0/test_project/.claude-mpm/sessions'

tests/unit/services/cli/test_session_resume_helper.py:935: in test_returns_empty_when_directory_missing
    helper.pause_dir.rmdir()
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1351: in rmdir
    os.rmdir(self)
E   OSError: [Errno 66] Directory not empty: '/private/var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/pytest-of-mac/pytest-147/popen-gw4/test_returns_empty_when_direct0/test_project/.claude-mpm/sessions'
```

## C. Hypotheses

- Expected fixture files or template files removed or relocated.
- Tests relying on absolute paths that differ across environments.
- Temporary directories not created before test execution.
- Permission issues in CI environment or containerized tests.
- The dominant subpattern (`FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '<P`) accounts for 78/103 failures, suggesting a single root cause.

## D. Investigation Checklist

- [ ] Review the top subpatterns and confirm grouping is correct
- [ ] Verify expected files exist on disk
- [ ] Check if files were moved/renamed in recent commits
- [ ] Review `git log --diff-filter=D` for deleted files
- [ ] Inspect the top 3-5 failing test files listed below
  - `tests/agents/test_mpm_skills_manager.py`
- [ ] Check if failures are environment-specific or reproducible locally
- [ ] Look for patterns in git blame for recently changed source files

## E. Targeted Repo Queries

```bash
# Find where FileNotFoundError is raised in source code
rg 'raise FileNotFoundError' src/ --type py

# Find where OSError is raised in source code
rg 'raise OSError' src/ --type py

# Key test files to inspect
# tests/agents/test_mpm_skills_manager.py

```

## F. Minimal Reproduction Plan

Run a small subset to confirm the failures:

```bash
pytest 'tests/agents/test_mpm_skills_manager/TestAgentDefinitionStructure.py::test_json_is_valid' -x --tb=short
pytest 'tests/agents/test_mpm_skills_manager/TestAgentDefinitionStructure.py::test_required_fields_present' -x --tb=short
pytest 'tests/test_agent_deployment_comprehensive/TestPartialDeploymentFailures.py::test_deployment_failure_corrupted_template' -x --tb=short
pytest 'tests/test_agent_deployment_system/TestAgentDeployment.py::test_version_field_generation_semantic' -x --tb=short
pytest 'tests/hooks/claude_hooks/test_pre_split_verification/TestPreSplitVerification.py::test_file_size_justifies_split' -x --tb=short
pytest 'tests/hooks/claude_hooks/test_pre_split_verification/TestPreSplitVerification.py::test_proposed_split_reduces_size' -x --tb=short

# Run all failures in this category at once (sample)
pytest -k 'test_json_is_valid or test_deployment_failure_corrupted_template or test_file_size_justifies_split' --tb=short
```

## G. Follow-up Prompt

````
You are investigating **103 test failures** in the `file_and_fs` category (File and Filesystem Errors).

**Top patterns**:
  - `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '<PATH>'` (78 occurrences)
  - `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '/private<PATH>` (12 occurrences)
  - `FileNotFoundError: FileNotFoundError: [Errno <N>] No such file or directory: '<LONG_STR>'` (3 occurrences)

**Sample failing tests**:
  - `tests.agents.test_mpm_skills_manager.TestAgentDefinitionStructure::test_json_is_valid`
  - `tests.agents.test_mpm_skills_manager.TestAgentDefinitionStructure::test_required_fields_present`
  - `tests.test_agent_deployment_comprehensive.TestPartialDeploymentFailures::test_deployment_failure_corrupted_template`
  - `tests.test_agent_deployment_system.TestAgentDeployment::test_version_field_generation_semantic`

Your task:
1. Read the relevant source files and test files to understand why these tests fail.
2. Identify the root cause(s) -- is it a code change, missing dependency, config issue, or test bug?
3. Propose a minimal fix (code patch or configuration change) that resolves the largest subpattern first.
4. Verify your fix would not break other tests.

Start by reading the category markdown at `docs-local/failure-research-opus/categories/file_and_fs.md`
and the raw data at `docs-local/failure-research-opus/data/categories.json`.
````
