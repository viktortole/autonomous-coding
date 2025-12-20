#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run COMMANDER with 5 Iteration Budget
======================================

This script runs the COMMANDER agent orchestrator with a budget of 5 iterations.
The COMMANDER will analyze all pending tasks across agents and distribute
iterations optimally.

Usage:
    python run_commander.py          # Execute with budget
    python run_commander.py --dry    # Preview plan only

What happens:
1. COMMANDER displays epic ASCII banner
2. Scans all 6 agent task queues
3. Calculates priority scores per agent
4. Creates budget distribution plan
5. Spawns agents sequentially with calculated iterations
6. Reports completion stats with visual output
"""

import sys
import subprocess
from pathlib import Path

# Configuration
BUDGET = 5  # Total iterations to distribute
DRY_RUN = "--dry" in sys.argv or "--dry-run" in sys.argv

# Project directory
PROJECT_DIR = Path(__file__).parent


def main():
    """Run COMMANDER with budget mode."""
    print("\n" + "=" * 60)
    print("  COMMANDER Launcher - Budget Mode")
    print("=" * 60)
    print(f"\n  Budget: {BUDGET} iterations")
    print(f"  Mode: {'DRY RUN (preview only)' if DRY_RUN else 'LIVE EXECUTION'}")
    print(f"  Project: {PROJECT_DIR}")
    print("\n" + "=" * 60 + "\n")

    # Build command
    cmd = [
        sys.executable,
        "-m", "autoagents.agents.commander.runner",
        "--budget", str(BUDGET),
    ]

    if DRY_RUN:
        cmd.append("--dry-run")

    # Execute
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_DIR),
            check=False,
        )
        return result.returncode
    except KeyboardInterrupt:
        print("\n\n  Interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n  Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
