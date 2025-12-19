"""
Tests for autoagents.lib.output
"""

import pytest
from io import StringIO
import sys

from autoagents.lib.output import (
    print_tool_use,
    print_tool_result,
    print_info,
    print_warning,
    print_error,
    print_success,
)


class TestPrintToolUse:
    """Tests for print_tool_use function."""

    def test_print_tool_use_basic(self, capsys):
        """Should print tool name with emoji."""
        print_tool_use("Read")
        captured = capsys.readouterr()
        assert "Read" in captured.out

    def test_print_tool_use_with_file_path(self, capsys):
        """Should show filename for file_path input."""
        print_tool_use("Read", {"file_path": "/path/to/file.txt"})
        captured = capsys.readouterr()
        assert "file.txt" in captured.out

    def test_print_tool_use_with_pattern(self, capsys):
        """Should show pattern for glob/grep."""
        print_tool_use("Glob", {"pattern": "**/*.py"})
        captured = capsys.readouterr()
        assert "**/*.py" in captured.out

    def test_print_tool_use_with_command(self, capsys):
        """Should show truncated command for Bash."""
        print_tool_use("Bash", {"command": "npm test"})
        captured = capsys.readouterr()
        assert "npm test" in captured.out


class TestPrintToolResult:
    """Tests for print_tool_result function."""

    def test_print_tool_result_success(self, capsys):
        """Should print success indicator."""
        print_tool_result(is_error=False)
        captured = capsys.readouterr()
        assert "Done" in captured.out or "✅" in captured.out

    def test_print_tool_result_error(self, capsys):
        """Should print error indicator."""
        print_tool_result(is_error=True)
        captured = capsys.readouterr()
        assert "Error" in captured.out or "❌" in captured.out

    def test_print_tool_result_error_with_content(self, capsys):
        """Should show error content."""
        print_tool_result(is_error=True, content="Something went wrong")
        captured = capsys.readouterr()
        assert "Something went wrong" in captured.out or "Error" in captured.out


class TestMessagePrinting:
    """Tests for message printing functions."""

    def test_print_info(self, capsys):
        """Should print info message."""
        print_info("Test info")
        captured = capsys.readouterr()
        assert "Test info" in captured.out

    def test_print_warning(self, capsys):
        """Should print warning message."""
        print_warning("Test warning")
        captured = capsys.readouterr()
        assert "Test warning" in captured.out

    def test_print_error(self, capsys):
        """Should print error message."""
        print_error("Test error")
        captured = capsys.readouterr()
        assert "Test error" in captured.out

    def test_print_success(self, capsys):
        """Should print success message."""
        print_success("Test success")
        captured = capsys.readouterr()
        assert "Test success" in captured.out
