"""
Tests for shared CLI utilities including argument patterns and output formatters.

WHY: Verify that shared utilities work correctly and provide consistent
behavior across all CLI commands.
"""

import dataclasses
import json
from argparse import ArgumentParser

import yaml

from claude_mpm.cli.shared.argument_patterns import (
    CommonArguments,
    add_agent_arguments,
    add_common_arguments,
    add_config_arguments,
    add_logging_arguments,
    add_memory_arguments,
    add_output_arguments,
)
from claude_mpm.cli.shared.base_command import CommandResult
from claude_mpm.cli.shared.error_handling import CLIErrorHandler, handle_cli_errors
from claude_mpm.cli.shared.output_formatters import OutputFormatter, format_output


class TestCommonArguments:
    """Test CommonArguments registry."""

    def test_verbose_argument(self):
        """Test verbose argument definition."""
        verbose = CommonArguments.VERBOSE
        assert verbose["flags"] == ["-v", "--verbose"]
        assert verbose["action"] == "store_true"
        assert "verbose" in verbose["help"].lower()

    def test_quiet_argument(self):
        """Test quiet argument definition."""
        quiet = CommonArguments.QUIET
        assert quiet["flags"] == ["-q", "--quiet"]
        assert quiet["action"] == "store_true"
        assert "suppress" in quiet["help"].lower() or "quiet" in quiet["help"].lower()

    def test_debug_argument(self):
        """Test debug argument definition."""
        debug = CommonArguments.DEBUG
        assert debug["flags"] == ["--debug"]
        assert debug["action"] == "store_true"
        assert "debug" in debug["help"].lower()

    def test_config_file_argument(self):
        """Test config file argument definition."""
        config_file = CommonArguments.CONFIG_FILE
        assert config_file["flags"] == ["-c", "--config"]
        assert "config" in config_file["help"].lower()

    def test_output_format_argument(self):
        """Test output format argument definition."""
        output_format = CommonArguments.OUTPUT_FORMAT
        assert output_format["flags"] == ["-f", "--format"]
        assert set(output_format["choices"]) == {"text", "json", "yaml", "table"}
        assert "format" in output_format["help"].lower()


class TestArgumentPatterns:
    """Test argument pattern functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = ArgumentParser()

    def test_add_common_arguments(self):
        """Test adding common arguments to parser."""
        add_common_arguments(self.parser)

        # Parse test arguments
        args = self.parser.parse_args(["-v", "--debug"])
        assert args.verbose is True
        assert args.debug is True

    def test_add_logging_arguments(self):
        """Test adding logging arguments to parser."""
        add_logging_arguments(self.parser)

        # Parse test arguments
        args = self.parser.parse_args(["-q"])
        assert args.quiet is True

    def test_add_config_arguments(self):
        """Test adding config arguments to parser."""
        add_config_arguments(self.parser)

        # Parse test arguments
        args = self.parser.parse_args(["-c", "test.yaml"])
        assert str(args.config) == "test.yaml"

    def test_add_output_arguments(self):
        """Test adding output arguments to parser."""
        add_output_arguments(self.parser)

        # Parse test arguments
        args = self.parser.parse_args(["-f", "json", "-o", "output.json"])
        assert args.format == "json"
        assert str(args.output) == "output.json"

    def test_add_agent_arguments(self):
        """Test adding agent arguments to parser."""
        add_agent_arguments(self.parser)

        # Parse test arguments
        args = self.parser.parse_args(
            ["--agent-dir", "/test/agents", "--agent", "test-agent"]
        )
        assert str(args.agent_dir) == "/test/agents"
        assert args.agent == "test-agent"

    def test_add_memory_arguments(self):
        """Test adding memory arguments to parser."""
        add_memory_arguments(self.parser)

        # Parse test arguments
        args = self.parser.parse_args(["--memory-dir", "/test/memories"])
        assert str(args.memory_dir) == "/test/memories"


class TestOutputFormatter:
    """Test OutputFormatter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = OutputFormatter()
        # OutputFormatter takes generic dicts, not CommandResult objects.
        # Use dataclasses.asdict to convert.
        self.success_result = dataclasses.asdict(
            CommandResult.success_result("Test success", {"key": "value"})
        )
        self.error_result = dataclasses.asdict(
            CommandResult.error_result("Test error", data={"error": "details"})
        )

    def test_format_text_success(self):
        """Test formatting success result as text."""
        output = self.formatter.format_text(self.success_result)
        assert "Test success" in output

    def test_format_text_error(self):
        """Test formatting error result as text."""
        output = self.formatter.format_text(self.error_result)
        assert "Test error" in output

    def test_format_json_success(self):
        """Test formatting success result as JSON."""
        output = self.formatter.format_json(self.success_result)
        data = json.loads(output)

        assert data["success"] is True
        assert data["message"] == "Test success"
        assert data["data"]["key"] == "value"

    def test_format_json_error(self):
        """Test formatting error result as JSON."""
        output = self.formatter.format_json(self.error_result)
        data = json.loads(output)

        assert data["success"] is False
        assert data["message"] == "Test error"
        assert data["data"]["error"] == "details"

    def test_format_yaml_success(self):
        """Test formatting success result as YAML."""
        output = self.formatter.format_yaml(self.success_result)
        data = yaml.safe_load(output)

        assert data["success"] is True
        assert data["message"] == "Test success"
        assert data["data"]["key"] == "value"

    def test_format_yaml_error(self):
        """Test formatting error result as YAML."""
        output = self.formatter.format_yaml(self.error_result)
        data = yaml.safe_load(output)

        assert data["success"] is False
        assert data["message"] == "Test error"
        assert data["data"]["error"] == "details"

    def test_format_table_success(self):
        """Test formatting success result as table."""
        # format_table takes a dict or list of dicts
        output = self.formatter.format_table(self.success_result)
        assert "message" in output  # key name is shown
        assert "Test success" in output

    def test_format_table_error(self):
        """Test formatting error result as table."""
        output = self.formatter.format_table(self.error_result)
        assert "message" in output
        assert "Test error" in output

    def test_format_unknown_format(self):
        """Test formatting with unknown format defaults to text."""
        # format_output() falls back to text for unknown formats
        output = format_output(self.success_result, "unknown")
        # Should default to text format
        assert "Test success" in output


class TestFormatOutputFunction:
    """Test format_output convenience function."""

    def test_format_output_text(self):
        """Test format_output with text format."""
        data = {"success": True, "message": "Test success"}
        output = format_output(data, "text")
        assert "Test success" in output

    def test_format_output_json(self):
        """Test format_output with JSON format."""
        data = {"success": True, "message": "Test success"}
        output = format_output(data, "json")
        parsed = json.loads(output)
        assert parsed["success"] is True
        assert parsed["message"] == "Test success"

    def test_format_output_yaml(self):
        """Test format_output with YAML format."""
        data = {"success": True, "message": "Test success"}
        output = format_output(data, "yaml")
        parsed = yaml.safe_load(output)
        assert parsed["success"] is True
        assert parsed["message"] == "Test success"

    def test_format_output_table(self):
        """Test format_output with table format."""
        data = {"message": "Test success", "key": "value"}
        output = format_output(data, "table")
        assert "Test success" in output
        assert "key" in output


class TestCLIErrorHandler:
    """Test CLIErrorHandler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = CLIErrorHandler("test-command")

    def test_handle_keyboard_interrupt(self):
        """Test handling KeyboardInterrupt."""
        error = KeyboardInterrupt()
        exit_code = self.handler.handle_error(error)
        assert exit_code == 130

    def test_handle_file_not_found_error(self):
        """Test handling FileNotFoundError."""
        error = FileNotFoundError("test.txt")
        exit_code = self.handler.handle_error(error)
        assert exit_code == 2

    def test_handle_permission_error(self):
        """Test handling PermissionError."""
        error = PermissionError("Access denied")
        exit_code = self.handler.handle_error(error)
        assert exit_code == 13

    def test_handle_generic_exception(self):
        """Test handling generic exception."""
        error = Exception("Generic error")
        exit_code = self.handler.handle_error(error)
        assert exit_code == 1

    def test_format_error_message(self):
        """Test error message formatting via handle_error output."""
        # CLIErrorHandler.format_error_message doesn't exist; test handle_error instead.
        # ValueError returns exit code 22 per implementation.
        error = ValueError("Invalid value")
        exit_code = self.handler.handle_error(error)
        assert exit_code == 22  # Invalid argument exit code for ValueError


class TestHandleCLIErrorsDecorator:
    """Test handle_cli_errors decorator."""

    def test_decorator_success(self):
        """Test decorator with successful function."""

        @handle_cli_errors("test-command")
        def test_function():
            return 0

        result = test_function()
        assert result == 0

    def test_decorator_with_exception(self):
        """Test decorator with function that raises exception."""

        @handle_cli_errors("test-command")
        def test_function():
            raise ValueError("Test error")

        result = test_function()
        # ValueError is handled with exit code 22 (invalid argument) per CLIErrorHandler
        assert result == 22

    def test_decorator_with_keyboard_interrupt(self):
        """Test decorator with KeyboardInterrupt."""

        @handle_cli_errors("test-command")
        def test_function():
            raise KeyboardInterrupt()

        result = test_function()
        assert result == 130  # Keyboard interrupt exit code

    def test_decorator_with_command_result(self):
        """Test decorator with function returning CommandResult."""

        @handle_cli_errors("test-command")
        def test_function():
            return CommandResult.success_result("Test success")

        result = test_function()
        assert result == 0

    def test_decorator_with_command_result_error(self):
        """Test decorator with function returning error CommandResult."""

        @handle_cli_errors("test-command")
        def test_function():
            return CommandResult.error_result("Test error", exit_code=2)

        result = test_function()
        assert result == 2
