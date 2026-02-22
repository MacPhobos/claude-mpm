# Failure Category: parametrize_and_collection

## A. Snapshot
- **Total failures**: 39
- **Top exception types**:
  - `FileNotFoundError`: 26
  - `(unknown)`: 11
  - `NameError`: 2
- **Top subpatterns**:

  | Subpattern | Count |
  |---|---|
  | `FileNotFoundError: [Errno N] No such file or directory: <str> \| <unknown>` | 26 |
  | `failed on setup with <str> \| <unknown>` | 10 |
  | `NameError: name <str> is not defined \| <unknown>` | 2 |
  | `assert N > N \| <unknown>` | 1 |

## B. Representative Examples

### Subpattern: `FileNotFoundError: [Errno N] No such file or directory: <str> | <unknown>` (26 failures)

**Example 1**
- **nodeid**: `tests/agents/test_mpm_skills_manager.py::TestErrorHandling::test_skill_validation_errors`
- **file_hint**: `tests/agents/test_mpm_skills_manager/TestErrorHandling.py`
- **failure**:
```
exc_type: FileNotFoundError
message: FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm/src/claude_mpm/agents/templates/mpm-skills-manager.md'
--- relevant traceback (up to 30 lines) ---
tests/agents/test_mpm_skills_manager.py:604: in test_skill_validation_errors
    with open(SKILLS_MANAGER_MD) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm/src/claude_mpm/agents/templates/mpm-skills-manager.md'
```

**Example 2**
- **nodeid**: `tests/agents/test_mpm_skills_manager.py::TestErrorHandling::test_git_operation_errors`
- **file_hint**: `tests/agents/test_mpm_skills_manager/TestErrorHandling.py`
- **failure**:
```
exc_type: FileNotFoundError
message: FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm/src/claude_mpm/agents/templates/mpm-skills-manager.md'
--- relevant traceback (up to 30 lines) ---
tests/agents/test_mpm_skills_manager.py:613: in test_git_operation_errors
    with open(SKILLS_MANAGER_MD) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: '/Users/mac/workspace/claude-mpm/src/claude_mpm/agents/templates/mpm-skills-manager.md'
```

**Example 3**
- **nodeid**: `tests/hooks/claude_hooks/test_pre_split_verification.py::TestPreSplitVerification::test_file_size_justifies_split`
- **file_hint**: `tests/hooks/claude_hooks/test_pre_split_verification/TestPreSplitVerification.py`
- **failure**:
```
exc_type: FileNotFoundError
message: FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'
--- relevant traceback (up to 30 lines) ---
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

### Subpattern: `failed on setup with <str> | <unknown>` (10 failures)

**Example 1**
- **nodeid**: `tests/hooks/claude_hooks/test_pre_split_verification.py::TestPreSplitVerification::test_no_shared_fixtures`
- **file_hint**: `tests/hooks/claude_hooks/test_pre_split_verification/TestPreSplitVerification.py`
- **failure**:
```
exc_type: 
message: failed on setup with "FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'"
--- relevant traceback (up to 30 lines) ---
tests/hooks/claude_hooks/test_pre_split_verification.py:34: in test_file_content
    return test_file_path.read_text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1027: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1013: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'
```

**Example 2**
- **nodeid**: `tests/hooks/claude_hooks/test_pre_split_verification.py::TestPreSplitVerification::test_count_test_classes`
- **file_hint**: `tests/hooks/claude_hooks/test_pre_split_verification/TestPreSplitVerification.py`
- **failure**:
```
exc_type: 
message: failed on setup with "FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'"
--- relevant traceback (up to 30 lines) ---
tests/hooks/claude_hooks/test_pre_split_verification.py:34: in test_file_content
    return test_file_path.read_text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1027: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1013: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'
```

**Example 3**
- **nodeid**: `tests/hooks/claude_hooks/test_pre_split_verification.py::TestPreSplitVerification::test_count_test_functions`
- **file_hint**: `tests/hooks/claude_hooks/test_pre_split_verification/TestPreSplitVerification.py`
- **failure**:
```
exc_type: 
message: failed on setup with "FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'"
--- relevant traceback (up to 30 lines) ---
tests/hooks/claude_hooks/test_pre_split_verification.py:34: in test_file_content
    return test_file_path.read_text()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1027: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
../../.asdf/installs/python/3.12.11/lib/python3.12/pathlib.py:1013: in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   FileNotFoundError: [Errno 2] No such file or directory: 'tests/hooks/claude_hooks/test_hook_handler_comprehensive.py'
```

### Subpattern: `NameError: name <str> is not defined | <unknown>` (2 failures)

**Example 1**
- **nodeid**: `tests/test_error_handling.py::test_permission_errors`
- **file_hint**: `tests/test_error_handling.py`
- **failure**:
```
exc_type: NameError
message: NameError: name 'tmp_path' is not defined
--- relevant traceback (up to 30 lines) ---
tests/test_error_handling.py:25: in test_permission_errors
    with tmp_path as tmpdir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

**Example 2**
- **nodeid**: `tests/test_error_handling.py::test_recovery_after_errors`
- **file_hint**: `tests/test_error_handling.py`
- **failure**:
```
exc_type: NameError
message: NameError: name 'tmp_path' is not defined
--- relevant traceback (up to 30 lines) ---
tests/test_error_handling.py:399: in test_recovery_after_errors
    with tmp_path as tmpdir:
         ^^^^^^^^
E   NameError: name 'tmp_path' is not defined
```

## C. Hypotheses

- Invalid parameter type or structure passed to `@pytest.mark.parametrize`.
- Syntax error in test file preventing collection.
- Plugin incompatibility causing collection failure.
- Test class or module import error surfaced at collection time.
- Indirect parametrize target fixture not found.

## D. Investigation Checklist

- [ ] Check CI logs for the first occurrence of this failure pattern.
- [ ] Reproduce locally by running the representative test above.
- [ ] Check recent commits (`git log --oneline -20`) for changes near the failure.
- [ ] Run with `-x` flag to stop at first failure and inspect state.
- [ ] Run `pytest --collect-only` to see collection errors without running tests.
- [ ] Check syntax in the test file (missing colon, indentation, etc.).
- [ ] Validate `@pytest.mark.parametrize` argument types match fixture expectations.

## E. Targeted Repo Queries

```bash
rg "parametrize" tests/ --include="*.py"
rg "CollectError|collection" . --include="*.log"
rg "syntax error|SyntaxError" tests/ --include="*.py"
```

## F. Minimal Reproduction Plan

```bash
# Run single representative test
pytest "tests/agents/test_mpm_skills_manager.py::TestErrorHandling::test_skill_validation_errors" -xvs

# Run small set for this bucket
pytest -k 'parametrize' --no-header -q 2>&1 | head -50
```

## G. Follow-up Claude Prompt

```
Given these failing tests in the parametrize_and_collection bucket:
  tests/agents/test_mpm_skills_manager.py::TestErrorHandling::test_skill_validation_errors
  tests/hooks/claude_hooks/test_pre_split_verification.py::TestPreSplitVerification::test_no_shared_fixtures
  tests/test_error_handling.py::test_permission_errors

And these relevant source files:
  tests/agents/test_mpm_skills_manager/TestErrorHandling.py
  tests/hooks/claude_hooks/test_pre_split_verification/TestPreSplitVerification.py
  tests/test_error_handling.py

Please:
1. Identify the root cause
2. Propose a fix plan
3. Estimate blast radius
```
