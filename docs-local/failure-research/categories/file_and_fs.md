# Failure Category: file_and_fs

## A. Snapshot
- **Total failures**: 74
- **Top exception types**:
  - `FileNotFoundError`: 72
  - `BadObject`: 1
  - `PermissionError`: 1
- **Top subpatterns**:

  | Subpattern | Count |
  |---|---|
  | `FileNotFoundError: [Errno N] No such file or directory: <str> \| <unknown>` | 72 |
  | `gitdb.exc.BadObject: BadObject: b<str> \| <unknown>` | 1 |
  | `PermissionError: [Errno N] Operation not permitted: <str> \| <unknown>` | 1 |

## B. Representative Examples

### Subpattern: `FileNotFoundError: [Errno N] No such file or directory: <str> | <unknown>` (72 failures)

**Example 1**
- **nodeid**: `tests/agents/test_mpm_skills_manager.py::TestAgentDefinitionStructure::test_json_is_valid`
- **file_hint**: `tests/agents/test_mpm_skills_manager/TestAgentDefinitionStructure.py`
- **failure**:
```
exc_type: FileNotFoundError
message: FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm/src/claude_mpm/agents/templates/mpm-skills-manager.json'
--- relevant traceback (up to 30 lines) ---
tests/agents/test_mpm_skills_manager.py:45: in test_json_is_valid
    with open(SKILLS_MANAGER_JSON) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm/src/claude_mpm/agents/templates/mpm-skills-manager.json'
```

**Example 2**
- **nodeid**: `tests/agents/test_mpm_skills_manager.py::TestAgentDefinitionStructure::test_required_fields_present`
- **file_hint**: `tests/agents/test_mpm_skills_manager/TestAgentDefinitionStructure.py`
- **failure**:
```
exc_type: FileNotFoundError
message: FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm/src/claude_mpm/agents/templates/mpm-skills-manager.json'
--- relevant traceback (up to 30 lines) ---
tests/agents/test_mpm_skills_manager.py:51: in test_required_fields_present
    with open(SKILLS_MANAGER_JSON) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm/src/claude_mpm/agents/templates/mpm-skills-manager.json'
```

**Example 3**
- **nodeid**: `tests/agents/test_mpm_skills_manager.py::TestAgentDefinitionStructure::test_schema_version`
- **file_hint**: `tests/agents/test_mpm_skills_manager/TestAgentDefinitionStructure.py`
- **failure**:
```
exc_type: FileNotFoundError
message: FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm/src/claude_mpm/agents/templates/mpm-skills-manager.json'
--- relevant traceback (up to 30 lines) ---
tests/agents/test_mpm_skills_manager.py:73: in test_schema_version
    with open(SKILLS_MANAGER_JSON) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm/src/claude_mpm/agents/templates/mpm-skills-manager.json'
```

### Subpattern: `gitdb.exc.BadObject: BadObject: b<str> | <unknown>` (1 failures)

**Example 1**
- **nodeid**: `tests/test_stream.py::TestStream::test_decompress_reader_special_case`
- **file_hint**: `tests/test_stream/TestStream.py`
- **failure**:
```
exc_type: BadObject
message: gitdb.exc.BadObject: BadObject: b'888401851f15db0eed60eb1bc29dec5ddcace911'
--- relevant traceback (up to 30 lines) ---
.venv/lib/python3.12/site-packages/gitdb/db/loose.py:133: in _map_loose_object
    return file_contents_ro_filepath(db_path, flags=self._fd_open_flags)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/gitdb/util.py:204: in file_contents_ro_filepath
    fd = os.open(filepath, os.O_RDONLY | getattr(os, 'O_BINARY', 0) | flags)
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm/.venv/lib/python3.12/site-packages/gitdb/test/fixtures/objects/88/8401851f15db0eed60eb1bc29dec5ddcace911'

The above exception was the direct cause of the following exception:
tests/test_stream.py:155: in test_decompress_reader_special_case
    ostream = odb.stream(hex_to_bin(sha))
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/gitdb/db/loose.py:165: in stream
    m = self._map_loose_object(sha)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv/lib/python3.12/site-packages/gitdb/db/loose.py:144: in _map_loose_object
    raise BadObject(sha) from e
E   gitdb.exc.BadObject: BadObject: b'888401851f15db0eed60eb1bc29dec5ddcace911'
```

### Subpattern: `PermissionError: [Errno N] Operation not permitted: <str> | <unknown>` (1 failures)

**Example 1**
- **nodeid**: `tests/unit/services/cli/test_session_resume_helper.py::TestGetMostRecentSession::test_returns_none_when_directory_missing`
- **file_hint**: `tests/unit/services/cli/test_session_resume_helper/TestGetMostRecentSession.py`
- **failure**:
```
exc_type: PermissionError
message: PermissionError: [Errno 1] Operation not permitted: '/private/var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/pytest-of-mac/pytest-147/popen-gw4/test_returns_none_when_directo0/test_project/.claude-mpm/sessions/pause'
--- relevant traceback (up to 30 lines) ---
tests/unit/services/cli/test_session_resume_helper.py:200: in test_returns_none_when_directory_missing
    file.unlink()
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1342: in unlink
    os.unlink(self)
E   PermissionError: [Errno 1] Operation not permitted: '/private/var/folders/vj/zf657c3n2lxcx6brdzzwp3zm0000z8/T/pytest-of-mac/pytest-147/popen-gw4/test_returns_none_when_directo0/test_project/.claude-mpm/sessions/pause'
```

## C. Hypotheses

- Temporary directory or fixture file not created before test.
- Permission denied on CI runner for specific paths.
- Hard-coded absolute paths that don't exist outside developer machines.
- File created by one test but depended on by another (ordering issue).
- Cleanup from prior test run left unexpected state.

## D. Investigation Checklist

- [ ] Check CI logs for the first occurrence of this failure pattern.
- [ ] Reproduce locally by running the representative test above.
- [ ] Check recent commits (`git log --oneline -20`) for changes near the failure.
- [ ] Run with `-x` flag to stop at first failure and inspect state.
- [ ] Check if test uses `tmp_path` fixture for temporary files.
- [ ] Search for hard-coded absolute paths in test files.
- [ ] Verify file permissions in CI runner for the affected paths.

## E. Targeted Repo Queries

```bash
rg "open\(|Path\(|os\.path" src/ --include="*.py"
rg "tmp_path|tmpdir|tempfile" tests/ --include="*.py"
```

## F. Minimal Reproduction Plan

```bash
# Run single representative test
pytest "tests/agents/test_mpm_skills_manager.py::TestAgentDefinitionStructure::test_json_is_valid" -xvs

# Run small set for this bucket
pytest -k 'file or fs or path' --no-header -q 2>&1 | head -50
```

## G. Follow-up Claude Prompt

```
Given these failing tests in the file_and_fs bucket:
  tests/agents/test_mpm_skills_manager.py::TestAgentDefinitionStructure::test_json_is_valid
  tests/test_stream.py::TestStream::test_decompress_reader_special_case
  tests/unit/services/cli/test_session_resume_helper.py::TestGetMostRecentSession::test_returns_none_when_directory_missing

And these relevant source files:
  tests/agents/test_mpm_skills_manager/TestAgentDefinitionStructure.py
  tests/test_stream/TestStream.py
  tests/unit/services/cli/test_session_resume_helper/TestGetMostRecentSession.py

Please:
1. Identify the root cause
2. Propose a fix plan
3. Estimate blast radius
```
