"""
Tests for autoagents.lib.logging_utils
"""

import pytest
from pathlib import Path

from autoagents.lib.logging_utils import (
    create_session_log,
    log_iteration,
    log_completion,
    get_log_path,
)


class TestCreateSessionLog:
    """Tests for create_session_log function."""

    def test_creates_log_file(self, logs_dir):
        """Should create a log file."""
        log_file = create_session_log(
            logs_dir, "TEST-001", "TestAgent", "claude-sonnet-4"
        )
        assert log_file.exists()
        assert "TEST-001" in log_file.name

    def test_log_contains_header(self, logs_dir):
        """Log should contain session header."""
        log_file = create_session_log(
            logs_dir, "TEST-001", "TestAgent", "claude-sonnet-4"
        )
        content = log_file.read_text(encoding='utf-8')
        assert "TestAgent" in content
        assert "claude-sonnet-4" in content

    def test_log_with_extra_info(self, logs_dir):
        """Should include extra info in header."""
        log_file = create_session_log(
            logs_dir, "TEST-001", "TestAgent", "claude-sonnet-4",
            extra_info={"Task": "Test Task", "Iterations": 5}
        )
        content = log_file.read_text(encoding='utf-8')
        assert "Test Task" in content
        assert "5" in content


class TestLogIteration:
    """Tests for log_iteration function."""

    def test_appends_iteration(self, logs_dir):
        """Should append iteration to log file."""
        log_file = create_session_log(logs_dir, "TEST-001", "TestAgent", "model")
        log_iteration(log_file, 1, 5, "Test response", tokens=100)

        content = log_file.read_text(encoding='utf-8')
        assert "ITERATION 1/5" in content
        assert "Test response" in content

    def test_logs_prompt_on_first_iteration(self, logs_dir):
        """Should log prompt on first iteration."""
        log_file = create_session_log(logs_dir, "TEST-001", "TestAgent", "model")
        log_iteration(log_file, 1, 5, "Response", prompt="Test prompt")

        content = log_file.read_text(encoding='utf-8')
        assert "PROMPT" in content
        assert "Test prompt" in content


class TestLogCompletion:
    """Tests for log_completion function."""

    def test_logs_completion(self, logs_dir):
        """Should log completion status."""
        log_file = create_session_log(logs_dir, "TEST-001", "TestAgent", "model")
        log_completion(log_file, "completed", 5, 1000)

        content = log_file.read_text(encoding='utf-8')
        assert "SESSION COMPLETE" in content
        assert "completed" in content


class TestGetLogPath:
    """Tests for get_log_path function."""

    def test_finds_log_file(self, logs_dir):
        """Should find most recent log file."""
        log_file = create_session_log(logs_dir, "TEST-001", "TestAgent", "model")
        found = get_log_path(logs_dir, "TEST-001")
        assert found == log_file

    def test_returns_none_for_missing(self, logs_dir):
        """Should return None if no log found."""
        found = get_log_path(logs_dir, "NONEXISTENT")
        assert found is None
