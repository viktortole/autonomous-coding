"""
AUTOAGENTS Test Fixtures
========================

Shared fixtures for pytest.
"""

import pytest
from pathlib import Path


@pytest.fixture
def project_dir(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "test_project"
    project.mkdir()
    return project


@pytest.fixture
def sample_task():
    """Sample task definition for tests."""
    return {
        "id": "TEST-001",
        "title": "Test Task",
        "category": "bugfix",
        "priority": "medium",
        "complexity": "easy",
        "status": "pending",
        "description": {
            "problem": "Test problem description",
            "goal": "Test goal",
            "scope": "Test scope",
            "user_impact": "Test impact"
        },
        "files": {
            "target": ["test.py"],
            "context": ["utils.py"]
        },
        "verification": {
            "commands": ["echo OK"]
        }
    }


@pytest.fixture
def sample_tasks_data(sample_task):
    """Sample tasks.json structure."""
    return {
        "_schema": {"version": "5.0.0", "name": "Test"},
        "project": {
            "name": "Test Project",
            "root": ".",
            "stack": ["Python"]
        },
        "queue": {
            "pending": ["TEST-001"],
            "in_progress": [],
            "completed": [],
            "failed": []
        },
        "tasks": [sample_task]
    }


@pytest.fixture
def logs_dir(tmp_path):
    """Create a temporary logs directory."""
    logs = tmp_path / "logs"
    logs.mkdir()
    return logs
