#!/usr/bin/env python3
"""
Backward-compatible wrapper for autoagents.runners.frontend_runner

This script maintains the original run_frontend_agent.py interface while using
the refactored package structure.
"""
from autoagents.runners.frontend_runner import main

if __name__ == "__main__":
    main()
