#!/usr/bin/env python3
"""
COMMANDER Runner - Agent Orchestrator
======================================

The COMMANDER is the ONLY agent you need to run.
It spawns and monitors all other agents automatically.

Usage:
    python -m autoagents.agents.commander.runner --budget 10        # ⭐ RECOMMENDED: Distribute 10 iterations
    python -m autoagents.agents.commander.runner                    # Start orchestrating (default)
    python -m autoagents.agents.commander.runner --agents 3         # Max 3 concurrent agents
    python -m autoagents.agents.commander.runner --interval 60      # 60 second cycles
    python -m autoagents.agents.commander.runner --once             # Single orchestration cycle
    python -m autoagents.agents.commander.runner --status           # Show all agent statuses
    python -m autoagents.agents.commander.runner --ai               # Use Claude for decisions (legacy)

Budget Mode (Recommended):
    commander --budget 10     # COMMANDER analyzes ALL pending tasks across agents
                              # Distributes iterations based on priority & complexity
                              # Spawns agents sequentially with calculated iterations
                              # Reports on completion and token usage
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

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
    print_divider,
)
from autoagents.lib.client import create_agent_client
from autoagents.lib.streaming import stream_agent_response
from autoagents.lib.logging_utils import create_session_log, log_iteration, log_completion
from autoagents.lib.comms import (
    read_comms,
    update_agent_section,
    log_agent_action,
    set_agent_status,
    get_all_agent_statuses,
    update_status_dashboard,
    add_announcement,
    STATUS_ACTIVE,
    STATUS_IDLE,
)
from autoagents.lib.budget import create_budget_tracker
from autoagents.agents.registry import get_agent_config, get_agent_system_prompt, list_agent_ids


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.parent.parent.parent
COMMS_PATH = BASE_DIR / "COMMS.md"
LOGS_DIR = BASE_DIR / "logs" / "commander"

CONFIG = get_agent_config("COMMANDER")


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_system_prompt() -> str:
    """Load system prompt for Commander."""
    return get_agent_system_prompt("COMMANDER")


def load_tasks() -> dict:
    """Load Commander's task definitions."""
    tasks_file = Path(__file__).parent / "tasks.json"
    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load tasks: {e}")
        return {"tasks": []}


def get_all_pending_tasks() -> dict[str, list]:
    """Collect pending tasks from all agents."""
    pending_by_agent = {}
    agents_dir = Path(__file__).parent.parent

    for agent_id in list_agent_ids():
        tasks_file = agents_dir / agent_id.lower() / "tasks.json"
        if tasks_file.exists():
            try:
                with open(tasks_file, "r") as f:
                    data = json.load(f)
                    tasks = data.get("tasks", [])
                    pending = [t for t in tasks if t.get("status") != "completed"]
                    if pending:
                        pending_by_agent[agent_id] = pending
            except Exception:
                pass

    return pending_by_agent


def build_orchestration_prompt(cycle: int, focus: str = None) -> str:
    """Build the prompt for an orchestration cycle."""
    # Get current state
    agent_statuses = get_all_agent_statuses(COMMS_PATH)
    pending_tasks = get_all_pending_tasks()

    # Build prompt
    parts = [
        f"# 👑 COMMANDER Orchestration Cycle {cycle}",
        f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Current Agent Status",
    ]

    if agent_statuses:
        parts.append("| Agent | Status | Last Update | Mission |")
        parts.append("|-------|--------|-------------|---------|")
        for agent_id, info in agent_statuses.items():
            parts.append(
                f"| {info.get('emoji', '❓')} {agent_id} | "
                f"{info.get('status', 'Unknown')} | "
                f"{info.get('last_update', 'Never')} | "
                f"{info.get('mission', 'No mission')[:30]} |"
            )
    else:
        parts.append("_No agent statuses found in COMMS.md_")

    parts.extend(["", "## Pending Tasks by Agent"])

    if pending_tasks:
        for agent_id, tasks in pending_tasks.items():
            parts.append(f"\n### {agent_id} ({len(tasks)} pending)")
            for task in tasks[:5]:  # Show max 5 per agent
                priority = task.get("priority", "medium")
                priority_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
                parts.append(f"- {priority_icon} **{task.get('id', 'N/A')}**: {task.get('title', 'Untitled')}")
    else:
        parts.append("_No pending tasks found_")

    parts.extend([
        "",
        "## Your Mission This Cycle",
        "1. Review agent statuses above",
        "2. Identify blocked or idle agents",
        "3. Make task assignment decisions",
        "4. Update COMMS.md with your decisions",
        "5. Post announcements for urgent items",
        "",
    ])

    if focus:
        parts.extend([
            f"## Focus: {focus}",
            f"The user specifically wants you to focus on: {focus}",
            "",
        ])

    parts.extend([
        "---",
        "**EXECUTE: Read COMMS.md, analyze, and update with your orchestration decisions.**"
    ])

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def print_commander_banner():
    """Print Commander-specific banner."""
    print(f"""
{Style.YELLOW}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}👑 COMMANDER v{CONFIG.version}{Style.RESET}{Style.YELLOW}                                               ║
║   {Style.DIM}Orchestration Agent - Opus 4.5{Style.RESET}{Style.YELLOW}                                  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def print_cycle_header(cycle: int, max_cycles: int):
    """Print cycle header."""
    max_str = "∞" if max_cycles == -1 else str(max_cycles)
    print(f"""
{Style.YELLOW}╭─────────────────────────────────────────────────────────────────────╮{Style.RESET}
{Style.YELLOW}│{Style.RESET} {Style.BOLD}👑 ORCHESTRATION CYCLE {cycle}/{max_str}{Style.RESET}
{Style.YELLOW}│{Style.RESET} {Style.DIM}Time: {datetime.now().strftime("%H:%M:%S")}{Style.RESET}
{Style.YELLOW}╰─────────────────────────────────────────────────────────────────────╯{Style.RESET}
""")


def print_status_summary():
    """Print current agent statuses."""
    statuses = get_all_agent_statuses(COMMS_PATH)

    print(f"\n{Style.CYAN}┌─────────────────────────────────────┐{Style.RESET}")
    print(f"{Style.CYAN}│{Style.RESET} {Style.BOLD}📊 AGENT STATUS OVERVIEW{Style.RESET}")
    print(f"{Style.CYAN}├─────────────────────────────────────┤{Style.RESET}")

    if statuses:
        for agent_id, info in statuses.items():
            emoji = info.get("emoji", "❓")
            status = info.get("status", "Unknown")
            print(f"{Style.CYAN}│{Style.RESET} {emoji} {agent_id:12} │ {status}")
    else:
        print(f"{Style.CYAN}│{Style.RESET} No agents reporting in COMMS.md")

    print(f"{Style.CYAN}└─────────────────────────────────────┘{Style.RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATION LOOP
# ═══════════════════════════════════════════════════════════════════════════════

async def orchestration_loop(args):
    """Main Commander orchestration loop."""
    budget = create_budget_tracker("COMMANDER", LOGS_DIR)
    max_cycles = args.iterations

    # Create log file
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = create_session_log(
        LOGS_DIR, "COMMANDER", CONFIG.name, CONFIG.model,
        extra_info={"Max Cycles": max_cycles}
    )
    print(f"  {Style.DIM}📝 Log file: {log_file.name}{Style.RESET}\n")

    # Update COMMS.md on session start
    update_agent_section(
        agent_id="COMMANDER",
        emoji="👑",
        status=STATUS_ACTIVE,
        mission="Orchestrating agent coordination",
        task_queue=[{"id": "CMD-001", "desc": "Monitor and coordinate", "status": "in_progress"}],
        progress=[],
        session_log=[f"[{datetime.now().strftime('%H:%M')}] Session started"],
        comms_path=COMMS_PATH
    )

    total_tokens = 0

    try:
        for cycle in range(1, max_cycles + 1):
            print_cycle_header(cycle, max_cycles)

            # Check budget
            can_run, reason = budget.can_run_task()
            if not can_run:
                print_error(f"Budget exhausted: {reason}")
                break

            # Build prompt
            prompt = build_orchestration_prompt(cycle, args.focus)

            # Log action
            log_agent_action("COMMANDER", f"Starting cycle {cycle}", COMMS_PATH)

            # Invoke Claude
            try:
                client = create_agent_client(
                    project_dir=BASE_DIR,
                    model=CONFIG.model,
                    system_prompt=get_system_prompt(),
                    allowed_tools=CONFIG.allowed_tools,
                    settings_filename=".claude_commander_settings.json"
                )

                async with client:
                    status, response, tokens = await stream_agent_response(
                        client, prompt,
                        on_tool_use=print_tool_use,
                        on_tool_result=print_tool_result
                    )

                total_tokens += tokens
                budget.record_usage(tokens, f"cycle-{cycle}")

                log_iteration(log_file, cycle, max_cycles, response, tokens=tokens)

                print(f"\n  🪙 Tokens this cycle: {Style.CYAN}{tokens:,}{Style.RESET}")
                budget.print_status()

                if status == "complete":
                    print_success(f"Cycle {cycle} complete")
                else:
                    print_warning(f"Cycle {cycle} had issues")

            except Exception as e:
                print_error(f"AI error: {e}")

            if cycle < max_cycles:
                print(f"\n  {Style.DIM}⏳ Next cycle in 5 seconds...{Style.RESET}")
                await asyncio.sleep(5)

    except KeyboardInterrupt:
        print(f"\n\n👑 COMMANDER interrupted by user.")

    # Session complete
    set_agent_status("COMMANDER", STATUS_IDLE, COMMS_PATH)
    update_status_dashboard(COMMS_PATH)
    log_completion(log_file, "completed", max_cycles, total_tokens)

    print(f"""
{Style.GREEN}╔══════════════════════════════════════════════════════════════════════╗
║  ✅ COMMANDER SESSION COMPLETE                                       ║
║  🔄 Cycles: {max_cycles:<55} ║
║  🪙 Tokens used: {total_tokens:<49} ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="COMMANDER - Agent Orchestrator (spawns and monitors all agents)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m autoagents.agents.commander.runner              # Start orchestrating (runs forever)
    python -m autoagents.agents.commander.runner --budget 10  # Distribute 10 iterations across agents
    python -m autoagents.agents.commander.runner --agents 3   # Max 3 concurrent agents
    python -m autoagents.agents.commander.runner --interval 60  # 60 second cycles
    python -m autoagents.agents.commander.runner --once       # Single cycle then exit
    python -m autoagents.agents.commander.runner --status     # Show statuses only
    python -m autoagents.agents.commander.runner --ai -i 5    # Use Claude AI mode (legacy)
        """
    )
    # Budget mode - RECOMMENDED - simple interface
    parser.add_argument("--budget", type=int, help="Total iteration budget to distribute across agents (e.g. 10)")

    # Orchestrator mode (default)
    parser.add_argument("--agents", type=int, default=2, help="Max concurrent agents (default: 2)")
    parser.add_argument("--interval", type=int, default=30, help="Cycle interval in seconds (default: 30)")
    parser.add_argument("--once", action="store_true", help="Single orchestration cycle then exit")

    # AI mode (legacy - uses Claude for decisions)
    parser.add_argument("--ai", action="store_true", help="Use Claude AI for orchestration decisions")
    parser.add_argument("-i", "--iterations", type=int, default=1, help="AI mode: number of cycles")
    parser.add_argument("--focus", type=str, help="AI mode: focus area for session")

    # Status
    parser.add_argument("--status", action="store_true", help="Show all agent statuses and exit")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")

    return parser.parse_args()


def main():
    """Main entry point."""
    setup_windows_utf8()
    args = parse_args()

    if args.status:
        print_commander_banner()
        print_status_summary()
        return

    # Budget mode - RECOMMENDED - simple interface
    if args.budget:
        from autoagents.agents.commander.budget_orchestrator import run_budget_orchestration

        if args.budget < 1:
            print_error("Budget must be at least 1 iteration")
            sys.exit(1)

        run_budget_orchestration(args.budget, dry_run=args.dry_run)
        return

    if args.ai:
        # Legacy AI mode - uses Claude for decisions
        print_commander_banner()

        # Check COMMS.md exists
        if not COMMS_PATH.exists():
            print_warning(f"COMMS.md not found at {COMMS_PATH}")
            print_info("Run without --status to initialize COMMS.md")

        print_info(f"Mode: AI (Claude)")
        print_info(f"Model: {CONFIG.model}")
        print_info(f"COMMS: {COMMS_PATH}")

        if args.dry_run:
            print_info("Dry run mode - no actions will be taken")
            return

        try:
            asyncio.run(orchestration_loop(args))
        except KeyboardInterrupt:
            print("\n\n👑 COMMANDER interrupted.")
        except Exception as e:
            print_error(f"Fatal error: {e}")
            sys.exit(1)
    else:
        # Default: Orchestrator mode - spawns and monitors agents
        from autoagents.agents.commander.orchestrator import run_orchestrator

        if args.dry_run:
            print_info("Dry run mode - would start orchestrator with:")
            print_info(f"  Max concurrent agents: {args.agents}")
            print_info(f"  Cycle interval: {args.interval} seconds")
            print_info(f"  Single cycle: {args.once}")
            return

        run_orchestrator(
            max_concurrent=args.agents,
            cycle_interval=args.interval,
            single_cycle=args.once,
        )


def run():
    """Entry point for pyproject.toml scripts."""
    main()


if __name__ == "__main__":
    main()
