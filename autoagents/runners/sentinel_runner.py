#!/usr/bin/env python3
"""
SENTINEL-DEV Runner - Autonomous Dev Server Guardian

Refactored to use shared autoagents.lib utilities.
Monitors Control Station dev environment health and auto-repairs issues.

Usage:
    python -m autoagents.runners.sentinel_runner                    # Single check
    python -m autoagents.runners.sentinel_runner -i 5               # 5 iterations
    python -m autoagents.runners.sentinel_runner --continuous       # Never stop
    python -m autoagents.runners.sentinel_runner --deep             # Force deep check
"""

import argparse
import asyncio
import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Shared library imports
from autoagents.lib.styles import Style
from autoagents.lib.output import (
    setup_windows_utf8,
    print_tool_use,
    print_tool_result,
    print_info,
    print_warning,
    print_error,
    print_success,
)
from autoagents.lib.client import create_agent_client
from autoagents.lib.streaming import stream_agent_response
from autoagents.lib.logging_utils import create_session_log, log_iteration, log_completion
from autoagents.agents.emojis import SENTINEL_EMOJI
from autoagents.agents.sentinel.health_monitors import HealthMonitor, HealthStatus
from autoagents.agents.sentinel.repair_workflows import RepairWorkflow


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent.parent.parent  # autonomous-coding/
SENTINEL_TASKS = SCRIPT_DIR / "tasks" / "sentinel.json"
SENTINEL_TASKS_FALLBACK = SCRIPT_DIR / "sentinel_tasks.json"  # Legacy location
LOGS_DIR = SCRIPT_DIR / "logs" / "sentinel"
CONTROL_STATION = Path("C:/Users/ToleV/Desktop/TestingFolder/control-station")
COMMS_MD = CONTROL_STATION / ".claude" / "COMMS.md"

DEV_SERVER_URL = "http://127.0.0.1:3000"
DEV_SERVER_PORT = 3000

SENTINEL_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "name": "SENTINEL-DEV",
    "role": "DevOps Guardian & Auto-Repair",
    "emoji": SENTINEL_EMOJI["shield"],
}

TOKEN_BUDGET = {
    "daily_limit": 10000,
    "quick_check": 0,
    "smart_check": 500,
    "deep_check": 2000,
    "repair": 3000,
    "warning_threshold": 0.8,
}

RATE_LIMITS = {
    "max_repairs_per_hour": 5,
    "max_restarts_per_day": 10,
    "max_consecutive_failures": 3,
}


class MonitoringMode(Enum):
    """SENTINEL operational modes."""
    IDLE = "idle"
    MONITORING = "monitoring"
    REPAIRING = "repairing"
    ESCALATING = "escalating"


@dataclass
class SentinelState:
    """SENTINEL operational state."""
    mode: MonitoringMode = MonitoringMode.IDLE
    last_check_time: Optional[datetime] = None
    last_repair_time: Optional[datetime] = None
    consecutive_failures: int = 0
    health_history: list = field(default_factory=list)
    repair_history: list = field(default_factory=list)
    token_usage_today: int = 0
    token_usage_reset_date: str = ""
    repairs_today: int = 0
    restarts_today: int = 0
    cycle_count: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING TO COMMS.MD
# ═══════════════════════════════════════════════════════════════════════════════

def log_to_comms(event_type: str, details: dict):
    """Append log entry to COMMS.md for agent coordination."""
    try:
        if not COMMS_MD.parent.exists():
            COMMS_MD.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = f"""
### {SENTINEL_EMOJI['shield']} SENTINEL-DEV - {timestamp}
**Event:** {event_type}
**Details:**
```json
{json.dumps(details, indent=2)}
```

"""
        with open(COMMS_MD, "a", encoding="utf-8") as f:
            f.write(entry)

    except Exception as e:
        print_warning(f"Failed to log to COMMS.md: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# TASK MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def load_tasks() -> dict:
    """Load sentinel_tasks.json configuration."""
    tasks_file = SENTINEL_TASKS if SENTINEL_TASKS.exists() else SENTINEL_TASKS_FALLBACK
    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load sentinel_tasks.json: {e}")
        return {"tasks": [], "project": {}}


def get_health_tasks(tasks_config: dict) -> list[dict]:
    """Get all health check tasks from config."""
    all_tasks = tasks_config.get("tasks", [])
    health_tasks = [
        t for t in all_tasks
        if t.get("category") == "health-monitoring" or t.get("id", "").startswith("SENTINEL-HEALTH")
    ]
    return health_tasks if health_tasks else all_tasks[:5]


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT BUILDING
# ═══════════════════════════════════════════════════════════════════════════════

def get_system_prompt() -> str:
    """Get system prompt for sentinel agent."""
    return f"""You are SENTINEL-DEV, an AGGRESSIVE autonomous DevOps agent for Control Station.

⚠️ CRITICAL MINDSET: You are NOT here to conserve tokens. You are here to WORK!
- DO NOT just report issues - FIX THEM
- DO NOT say "I recommend" - JUST DO IT
- DO NOT wait for approval - ACT NOW

You have FULL POWER of the user's PC. You ARE Claude Code with all tools available.

## PROJECT: Control Station
- Root: C:/Users/ToleV/Desktop/TestingFolder/control-station
- Stack: Tauri 2.9.2 + Next.js 16 + React 19 + TypeScript + SQLite
- Dev Server: http://localhost:3000
- Database: %APPDATA%/com.convergence.control-station/

## YOUR MISSION
1. CHECK health of dev environment (server, build, tests)
2. READ codebase to understand current state
3. FIND bugs, errors, issues
4. FIX them immediately
5. VERIFY fixes work

## WORKFLOW
For EACH iteration:
1. Run health commands: curl localhost:3000, npx tsc --noEmit, npm test
2. Read error logs and identify issues
3. Read relevant source files
4. Make fixes using Edit tool
5. Run verification commands

## FORBIDDEN ACTIONS
- git reset --hard
- rm -rf node_modules (too slow)
- Database schema changes without backup
- Force push to git

BE AGGRESSIVE. FIX THINGS. WORK HARD. USE YOUR TOKENS."""


def build_task_prompt(task: dict, project_info: dict) -> str:
    """Build an AGGRESSIVE prompt from a SENTINEL task definition."""
    parts = [
        f"# {SENTINEL_EMOJI['shield']} SENTINEL TASK: {task.get('title', 'Unknown Task')}",
        f"**ID:** {task.get('id', 'N/A')} | **Priority:** {task.get('priority', 'medium')}",
        "",
        "## AGGRESSIVE MODE",
        "- DO NOT just check - FIX ISSUES",
        "- DO NOT report problems - SOLVE THEM",
        "- If something is broken, FIX IT NOW",
        "",
    ]

    desc = task.get("description", {})
    parts.extend([
        "## PROBLEM",
        desc.get("problem", "No problem description"),
        "",
        "## GOAL",
        desc.get("goal", "No goal description"),
        "",
    ])

    # Commands from execution or verification
    execution = task.get("execution", {})
    verification = task.get("verification", {})
    commands = execution.get("bash_commands", []) or verification.get("commands", [])

    if commands:
        parts.append("## COMMANDS TO RUN FIRST")
        for cmd in commands:
            parts.append(f"```powershell\n{cmd}\n```")
        parts.append("")

    success = execution.get("success_criteria", []) or verification.get("success_criteria", [])
    if success:
        parts.append("## SUCCESS CRITERIA")
        for c in success:
            parts.append(f"- {c}")
        parts.append("")

    parts.extend([
        "## PROJECT",
        f"- **Root:** {project_info.get('root', CONTROL_STATION)}",
        f"- **Dev Server:** {DEV_SERVER_URL}",
        "",
        "---",
        "**START NOW. RUN COMMANDS. FIX EVERYTHING. BE AGGRESSIVE!**"
    ])

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def print_sentinel_banner():
    """Print sentinel-specific banner."""
    print(f"""
{Style.RED}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}🛡️ SENTINEL-DEV v2.0{Style.RESET}{Style.RED}                                            ║
║   {Style.DIM}Autonomous Dev Server Guardian + AI Diagnostics{Style.RESET}{Style.RED}                   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def print_cycle_header(cycle: int, max_iterations: int, task_id: str, task_title: str):
    """Print monitoring cycle header."""
    max_str = "∞" if max_iterations == -1 else str(max_iterations)
    progress = "█" * min(cycle, 30) + "░" * max(0, min(30, max_iterations) - cycle) if max_iterations > 0 else ""

    print(f"""
{Style.YELLOW}╭─────────────────────────────────────────────────────────────────────╮{Style.RESET}
{Style.YELLOW}│{Style.RESET} {Style.BOLD}🔄 ITERATION {cycle}/{max_str}{Style.RESET}  [{progress[:30]}]
{Style.YELLOW}│{Style.RESET} {Style.CYAN}📋 Task: {task_id} - {task_title[:40]}{Style.RESET}
{Style.YELLOW}╰─────────────────────────────────────────────────────────────────────╯{Style.RESET}
""")


async def monitoring_loop(args):
    """Main monitoring loop - REAL Claude AI execution pattern."""
    state = SentinelState()
    tasks_config = load_tasks()

    health_tasks = get_health_tasks(tasks_config)
    project_info = tasks_config.get("project", {"root": str(CONTROL_STATION)})

    max_iterations = -1 if args.continuous else args.iterations

    # Reset token usage if new day
    today = datetime.now().strftime("%Y-%m-%d")
    if state.token_usage_reset_date != today:
        state.token_usage_today = 0
        state.repairs_today = 0
        state.restarts_today = 0
        state.token_usage_reset_date = today

    print_info(f"Loaded {len(health_tasks)} health check tasks")
    print_info(f"Token budget: {TOKEN_BUDGET['daily_limit']:,} tokens/day")
    print_info(f"Mode: {'CONTINUOUS' if max_iterations == -1 else f'LIMITED ({max_iterations} iterations)'}")
    print()

    # Log session start
    log_to_comms("session_start", {
        "mode": "continuous" if max_iterations == -1 else f"limited_{max_iterations}",
        "health_tasks": len(health_tasks),
        "token_budget": TOKEN_BUDGET["daily_limit"]
    })

    # Create log file
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = create_session_log(
        LOGS_DIR, "SENTINEL", SENTINEL_CONFIG["name"], SENTINEL_CONFIG["model"],
        extra_info={"Max Iterations": max_iterations}
    )
    print(f"  {Style.DIM}📝 Log file: {log_file.name}{Style.RESET}\n")

    # Initialize health monitor and repair workflow
    health_monitor = HealthMonitor(CONTROL_STATION, DEV_SERVER_PORT)
    repair_workflow = RepairWorkflow(CONTROL_STATION, DEV_SERVER_PORT)

    try:
        iteration = 0
        while True:
            iteration += 1
            state.cycle_count = iteration

            if max_iterations != -1 and iteration > max_iterations:
                print_info(f"Completed {max_iterations} iterations. Session complete.")
                break

            # Pick task for this iteration (cycle through tasks)
            task_index = (iteration - 1) % len(health_tasks)
            current_task = health_tasks[task_index]

            print_cycle_header(iteration, max_iterations, current_task['id'], current_task['title'])

            # Run quick health checks first (0 tokens)
            print(f"\n  {SENTINEL_EMOJI['monitoring']} Quick Health Check (Tier 1)")
            quick_results = health_monitor.run_quick_checks()

            for result in quick_results:
                status_emoji = SENTINEL_EMOJI['healthy'] if result.status == HealthStatus.HEALTHY else SENTINEL_EMOJI['error']
                status_color = Style.GREEN if result.status == HealthStatus.HEALTHY else Style.RED
                print(f"     {status_emoji} {result.component}: {status_color}{result.message}{Style.RESET} ({result.duration_ms}ms)")

            # Attempt auto-repair if needed
            errors = [r for r in quick_results if r.status == HealthStatus.ERROR]
            if errors and state.repairs_today < RATE_LIMITS["max_repairs_per_hour"]:
                for error in errors:
                    if "HTTP" in error.component or "Server" in error.component:
                        print(f"\n  {SENTINEL_EMOJI['repairing']} Attempting dev server repair...")
                        repair_result = repair_workflow.repair_dev_server()
                        state.repairs_today += 1
                        state.restarts_today += 1 if repair_result.success else 0
                        if repair_result.success:
                            print_success(f"Dev server repaired in {repair_result.duration_ms}ms")
                        else:
                            print_error(f"Repair failed: {repair_result.message}")

            # Build prompt from task
            prompt = build_task_prompt(current_task, project_info)

            if iteration > 1:
                prompt = f"""# {SENTINEL_EMOJI['shield']} SENTINEL ITERATION {iteration} - KEEP WORKING!

⚠️ DO NOT STOP. DO NOT CONSERVE TOKENS. KEEP FIXING!

{prompt}"""

            # Invoke Claude AI
            try:
                system_prompt = get_system_prompt()
                client = create_agent_client(
                    project_dir=CONTROL_STATION,
                    model=SENTINEL_CONFIG["model"],
                    system_prompt=system_prompt,
                    allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
                    settings_filename=".claude_sentinel_settings.json"
                )

                async with client:
                    ai_status, ai_response, tokens = await stream_agent_response(
                        client, prompt,
                        on_tool_use=print_tool_use,
                        on_tool_result=print_tool_result
                    )

                state.token_usage_today += tokens

                log_iteration(log_file, iteration, max_iterations, ai_response, tokens=tokens)

                print(f"\n  🪙 Tokens this iteration: {Style.CYAN}{tokens:,}{Style.RESET}")
                print(f"  🪙 Total today: {Style.CYAN}{state.token_usage_today:,}{Style.RESET} / {TOKEN_BUDGET['daily_limit']:,}")

                if ai_status == "complete":
                    print_success(f"Iteration {iteration} complete")
                else:
                    print_warning(f"Iteration {iteration} had issues")

                log_to_comms("iteration_complete", {
                    "iteration": iteration,
                    "task": current_task['id'],
                    "tokens": tokens,
                    "status": ai_status
                })

            except Exception as e:
                print_error(f"AI error: {e}")

            if max_iterations != -1 and iteration >= max_iterations:
                break

            print(f"\n  {Style.DIM}⏳ Next iteration in 3 seconds...{Style.RESET}")
            await asyncio.sleep(3)

    except KeyboardInterrupt:
        print(f"\n\n{SENTINEL_EMOJI['shield']} SENTINEL-DEV interrupted by user.")

    # Session complete
    log_completion(log_file, "completed", state.cycle_count, state.token_usage_today)

    print(f"""
{Style.GREEN}╔══════════════════════════════════════════════════════════════════════╗
║  ✅ SENTINEL SESSION COMPLETE                                        ║
║  🔄 Iterations: {state.cycle_count:<52} ║
║  🪙 Tokens used: {state.token_usage_today:<50} ║
║  🔧 Repairs today: {state.repairs_today:<48} ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")

    log_to_comms("session_end", {
        "iterations": state.cycle_count,
        "tokens_used": state.token_usage_today,
        "repairs": state.repairs_today,
        "log_file": str(log_file)
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="SENTINEL-DEV - Autonomous Dev Server Guardian",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m autoagents.runners.sentinel_runner              # Single check
    python -m autoagents.runners.sentinel_runner -i 5         # 5 iterations
    python -m autoagents.runners.sentinel_runner --continuous # Run forever
    python -m autoagents.runners.sentinel_runner --deep       # Force deep check
        """
    )
    parser.add_argument("-i", "--iterations", type=int, default=1, help="Max iterations (default: 1)")
    parser.add_argument("--deep", action="store_true", help="Force deep health check")
    parser.add_argument("--repair", action="store_true", help="Force repair mode")
    parser.add_argument("--continuous", action="store_true", help="Run forever")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--list", action="store_true", help="List health tasks")
    return parser.parse_args()


def main():
    """Main entry point."""
    setup_windows_utf8()
    args = parse_args()

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    print_sentinel_banner()

    if args.list:
        tasks_config = load_tasks()
        health_tasks = get_health_tasks(tasks_config)
        print(f"\n{Style.CYAN}Health Tasks ({len(health_tasks)}):{Style.RESET}")
        for task in health_tasks[:10]:
            print(f"  - {task['id']}: {task['title'][:60]}")
        return

    tasks_file = SENTINEL_TASKS if SENTINEL_TASKS.exists() else SENTINEL_TASKS_FALLBACK
    if not tasks_file.exists():
        print_error(f"sentinel_tasks.json not found")
        sys.exit(1)

    if not CONTROL_STATION.exists():
        print_error(f"Control Station not found at {CONTROL_STATION}")
        sys.exit(1)

    print_info(f"Control Station: {CONTROL_STATION}")
    print_info(f"Tasks file: {tasks_file}")
    print_info(f"Model: {SENTINEL_CONFIG['model']}")

    if args.dry_run:
        print_info("Dry run mode - no actions will be taken")
        return

    try:
        asyncio.run(monitoring_loop(args))
    except KeyboardInterrupt:
        print(f"\n\n{SENTINEL_EMOJI['shield']} SENTINEL-DEV interrupted by user.")
    except Exception as e:
        print_error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
