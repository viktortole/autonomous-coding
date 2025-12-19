#!/usr/bin/env python3
"""
Backward-compatible wrapper for autoagents.runners.task_runner

This script maintains the original run_task.py interface while using
the refactored package structure.
"""
from autoagents.runners.task_runner import main

if __name__ == "__main__":
    main()
