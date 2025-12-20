#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKEND Runner - Rust/Axum/Tauri Backend Agent
===============================================

Handles backend development: API endpoints, database, Tauri commands.

Usage:
    python -m autoagents.agents.backend.runner                    # Run single task
    python -m autoagents.agents.backend.runner -i 5               # Run 5 iterations
    python -m autoagents.agents.backend.runner --task BACK-001    # Run specific task
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from autoagents.lib.styles import Style
from autoagents.lib.output import (
    setup_windows_utf8,
    print_tool_use,
    print_tool_result,
    print_info,
    print_warning,
    print_error,
    print_success,
    print_task_header,
)
from autoagents.lib.client import create_agent_client
from autoagents.lib.streaming import stream_agent_response
from autoagents.lib.logging_utils import create_session_log, log_iteration, log_completion
from autoagents.lib.comms import (
    update_agent_section,
    log_agent_action,
    set_agent_status,
    STATUS_ACTIVE,
    STATUS_IDLE,
)
from autoagents.lib.budget import create_budget_tracker
from autoagents.agents.registry import get_agent_config, get_agent_system_prompt


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

BASE_DIR = Path(__file__).parent.parent.parent.parent
PROJECT_DIR = Path("C:/Users/ToleV/Desktop/TestingFolder/control-station")
COMMS_PATH = BASE_DIR / "COMMS.md"
LOGS_DIR = BASE_DIR / "logs" / "backend"

CONFIG = get_agent_config("BACKEND")


# ═══════════════════════════════════════════════════════════════════════════════
# TASK MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def load_tasks() -> dict:
    """Load Backend's task definitions."""
    tasks_file = Path(__file__).parent / "tasks.json"
    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load tasks: {e}")
        return {"tasks": []}


def get_pending_task(tasks_config: dict, task_id: str = None) -> dict | None:
    """Get next pending task or specific task by ID."""
    tasks = tasks_config.get("tasks", [])

    if task_id:
        for task in tasks:
            if task.get("id") == task_id:
                return task
        return None

    # Get first pending task
    for task in tasks:
        if task.get("status") != "completed":
            return task
    return None


def build_task_prompt(task: dict) -> str:
    """Build prompt from task definition."""
    desc = task.get("description", {})
    verification = task.get("verification", {})

    parts = [
        f"# {CONFIG.emoji} BACKEND Task: {task.get('title', 'Untitled')}",
        f"**ID:** {task.get('id', 'N/A')} | **Priority:** {task.get('priority', 'medium')}",
        "",
        "## Problem",
        desc.get("problem", "No problem description"),
        "",
        "## Goal",
        desc.get("goal", "No goal description"),
        "",
    ]

    files = task.get("files", [])
    if files:
        parts.append("## Files to Work On")
        for f in files:
            parts.append(f"- `{f}`")
        parts.append("")

    commands = verification.get("commands", [])
    if commands:
        parts.append("## Verification Commands")
        for cmd in commands:
            parts.append(f"```bash\n{cmd}\n```")
        parts.append("")

    criteria = verification.get("success_criteria", [])
    if criteria:
        parts.append("## Success Criteria")
        for c in criteria:
            parts.append(f"- {c}")
        parts.append("")

    parts.extend([
        "---",
        f"**Project:** {PROJECT_DIR}",
        "**START NOW. Write clean Rust. Handle errors properly.**"
    ])

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════

def print_backend_banner():
    """Print Backend-specific banner."""
    print(f"""
{Style.YELLOW}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}⚙️ BACKEND v{CONFIG.version}{Style.RESET}{Style.YELLOW}                                                ║
║   {Style.DIM}Rust/Axum/Tauri Backend Agent{Style.RESET}{Style.YELLOW}                                   ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

async def run_task_loop(args):
    """Main task execution loop."""
    budget = create_budget_tracker("BACKEND", LOGS_DIR)
    tasks_config = load_tasks()
    max_iterations = args.iterations

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = create_session_log(
        LOGS_DIR, "BACKEND", CONFIG.name, CONFIG.model,
        extra_info={"Max Iterations": max_iterations}
    )
    print(f"  {Style.DIM}📝 Log file: {log_file.name}{Style.RESET}\n")

    # Update COMMS.md
    update_agent_section(
        agent_id="BACKEND",
        emoji="⚙️",
        status=STATUS_ACTIVE,
        mission="Backend development",
        task_queue=[],
        progress=[],
        session_log=[f"[{datetime.now().strftime('%H:%M')}] Session started"],
        comms_path=COMMS_PATH
    )

    total_tokens = 0

    try:
        for iteration in range(1, max_iterations + 1):
            task = get_pending_task(tasks_config, args.task)
            if not task:
                print_info("No pending tasks found")
                break

            print_task_header(task, CONFIG.model, max_iterations, PROJECT_DIR)

            can_run, reason = budget.can_run_task()
            if not can_run:
                print_error(f"Budget exhausted: {reason}")
                break

            prompt = build_task_prompt(task)
            log_agent_action("BACKEND", f"Starting task {task.get('id')}", COMMS_PATH)

            try:
                client = create_agent_client(
                    project_dir=PROJECT_DIR,
                    model=CONFIG.model,
                    system_prompt=get_agent_system_prompt("BACKEND"),
                    allowed_tools=CONFIG.allowed_tools,
                    settings_filename=".claude_backend_settings.json"
                )

                async with client:
                    status, response, tokens = await stream_agent_response(
                        client, prompt,
                        on_tool_use=print_tool_use,
                        on_tool_result=print_tool_result
                    )

                total_tokens += tokens
                budget.record_usage(tokens, task.get("id", "unknown"))

                log_iteration(log_file, iteration, max_iterations, response, tokens=tokens)

                print(f"\n  🪙 Tokens: {Style.CYAN}{tokens:,}{Style.RESET}")
                budget.print_status()

                if status == "complete":
                    print_success(f"Task {task.get('id')} complete")

            except Exception as e:
                print_error(f"AI error: {e}")

            if iteration < max_iterations:
                await asyncio.sleep(3)

    except KeyboardInterrupt:
        print(f"\n\n⚙️ BACKEND interrupted.")

    set_agent_status("BACKEND", STATUS_IDLE, COMMS_PATH)
    log_completion(log_file, "completed", max_iterations, total_tokens)

    print(f"""
{Style.GREEN}╔══════════════════════════════════════════════════════════════════════╗
║  ✅ BACKEND SESSION COMPLETE                                         ║
║  🪙 Tokens used: {total_tokens:<49} ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def parse_args():
    parser = argparse.ArgumentParser(description="BACKEND - Rust/Axum Agent")
    parser.add_argument("-i", "--iterations", type=int, default=1)
    parser.add_argument("--task", type=str, help="Specific task ID")
    parser.add_argument("--list", action="store_true", help="List tasks")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main():
    setup_windows_utf8()
    args = parse_args()

    print_backend_banner()

    if args.list:
        tasks = load_tasks().get("tasks", [])
        print(f"\n{Style.CYAN}Backend Tasks ({len(tasks)}):{Style.RESET}")
        for t in tasks:
            status_icon = "✅" if t.get("status") == "completed" else "⏳"
            print(f"  {status_icon} {t['id']}: {t['title'][:50]}")
        return

    print_info(f"Model: {CONFIG.model}")
    print_info(f"Project: {PROJECT_DIR}")

    if args.dry_run:
        print_info("Dry run mode")
        return

    try:
        asyncio.run(run_task_loop(args))
    except KeyboardInterrupt:
        print("\n\n⚙️ BACKEND interrupted.")
    except Exception as e:
        print_error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
