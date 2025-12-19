#!/usr/bin/env python3
"""
Backward-compatible wrapper for autoagents.runners.sentinel_runner

This script maintains the original run_sentinel.py interface while using
the refactored package structure.
"""
from autoagents.runners.sentinel_runner import main

if __name__ == "__main__":
    main()
