#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEBUGGER Runner - Error Investigation Agent
============================================

Investigates and fixes bugs, errors, and issues.

Usage:
    python -m autoagents.agents.debugger.runner                    # Run investigation
    python -m autoagents.agents.debugger.runner -i 5               # Run 5 iterations
    python -m autoagents.agents.debugger.runner --error "message"  # Investigate specific error
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


BASE_DIR = Path(__file__).parent.parent.parent.parent
PROJECT_DIR = Path("C:/Users/ToleV/Desktop/TestingFolder/control-station")
COMMS_PATH = BASE_DIR / "COMMS.md"
LOGS_DIR = BASE_DIR / "logs" / "debugger"

CONFIG = get_agent_config("DEBUGGER")


def load_tasks() -> dict:
    tasks_file = Path(__file__).parent / "tasks.json"
    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load tasks: {e}")
        return {"tasks": []}


def get_pending_task(tasks_config: dict, task_id: str = None) -> dict | None:
    tasks = tasks_config.get("tasks", [])
    if task_id:
        for task in tasks:
            if task.get("id") == task_id:
                return task
        return None
    for task in tasks:
        if task.get("status") != "completed":
            return task
    return None


def build_task_prompt(task: dict, error_message: str = None) -> str:
    desc = task.get("description", {})
    execution = task.get("execution", {})
    verification = task.get("verification", {})

    parts = [
        f"# {CONFIG.emoji} DEBUGGER Task: {task.get('title', 'Untitled')}",
        f"**ID:** {task.get('id', 'N/A')} | **Priority:** {task.get('priority', 'medium')}",
        "",
        "## Problem",
        desc.get("problem", "No problem description"),
        "",
        "## Goal",
        desc.get("goal", "No goal description"),
        "",
    ]

    if error_message:
        parts.extend([
            "## Error to Investigate",
            f"```\n{error_message}\n```",
            ""
        ])

    commands = execution.get("commands", [])
    if commands:
        parts.append("## Commands to Run")
        for cmd in commands:
            parts.append(f"```bash\n{cmd}\n```")
        parts.append("")

    steps = execution.get("steps", [])
    if steps:
        parts.append("## Investigation Steps")
        for i, step in enumerate(steps, 1):
            parts.append(f"{i}. {step}")
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
        "**INVESTIGATE. FIND ROOT CAUSE. FIX.**"
    ])

    return "\n".join(parts)


def print_debugger_banner():
    print(f"""
{Style.YELLOW}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}🔍 DEBUGGER v{CONFIG.version}{Style.RESET}{Style.YELLOW}                                               ║
║   {Style.DIM}Error Investigation Agent{Style.RESET}{Style.YELLOW}                                       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


async def run_task_loop(args):
    budget = create_budget_tracker("DEBUGGER", LOGS_DIR)
    tasks_config = load_tasks()
    max_iterations = args.iterations

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = create_session_log(
        LOGS_DIR, "DEBUGGER", CONFIG.name, CONFIG.model,
        extra_info={"Max Iterations": max_iterations}
    )
    print(f"  {Style.DIM}📝 Log file: {log_file.name}{Style.RESET}\n")

    update_agent_section(
        agent_id="DEBUGGER",
        emoji="🔍",
        status=STATUS_ACTIVE,
        mission="Bug investigation",
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

            prompt = build_task_prompt(task, args.error)
            log_agent_action("DEBUGGER", f"Investigating {task.get('id')}", COMMS_PATH)

            try:
                client = create_agent_client(
                    project_dir=PROJECT_DIR,
                    model=CONFIG.model,
                    system_prompt=get_agent_system_prompt("DEBUGGER"),
                    allowed_tools=CONFIG.allowed_tools,
                    settings_filename=".claude_debugger_settings.json"
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
        print(f"\n\n🔍 DEBUGGER interrupted.")

    set_agent_status("DEBUGGER", STATUS_IDLE, COMMS_PATH)
    log_completion(log_file, "completed", max_iterations, total_tokens)

    print(f"""
{Style.GREEN}╔══════════════════════════════════════════════════════════════════════╗
║  ✅ DEBUGGER SESSION COMPLETE                                        ║
║  🪙 Tokens used: {total_tokens:<49} ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def parse_args():
    parser = argparse.ArgumentParser(description="DEBUGGER - Investigation Agent")
    parser.add_argument("-i", "--iterations", type=int, default=1)
    parser.add_argument("--task", type=str)
    parser.add_argument("--error", type=str, help="Error message to investigate")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main():
    setup_windows_utf8()
    args = parse_args()

    print_debugger_banner()

    if args.list:
        tasks = load_tasks().get("tasks", [])
        print(f"\n{Style.CYAN}Debugger Tasks ({len(tasks)}):{Style.RESET}")
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
        print("\n\n🔍 DEBUGGER interrupted.")
    except Exception as e:
        print_error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
