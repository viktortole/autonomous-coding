#!/usr/bin/env python3
"""
AUTOAGENTS Task Runner v2.1
===========================

Runs autonomous coding agents on tasks defined in JSON task files.

Usage:
    python -m autoagents.runners.task_runner                    # Run first pending task
    python -m autoagents.runners.task_runner --task TASK-000    # Run specific task
    python -m autoagents.runners.task_runner --max-iterations 5 # Limit iterations
    python -m autoagents.runners.task_runner --list             # List all tasks
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import from shared library
from ..lib.styles import Style
from ..lib.output import (
    setup_windows_utf8,
    print_banner,
    print_task_header,
    print_iteration_header,
    print_queue_status,
    print_success_banner,
    print_failure_banner,
)
from ..lib.client import create_agent_client
from ..lib.streaming import stream_agent_response
from ..lib.logging_utils import create_session_log, log_iteration


# Paths
SCRIPT_DIR = Path(__file__).parent.parent.parent
TASKS_DIR = SCRIPT_DIR / "tasks"
LOGS_DIR = SCRIPT_DIR / "logs"

# Default settings
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_TASKS_FILE = "general.json"


# ═══════════════════════════════════════════════════════════════════════════════
# DATA MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def load_tasks(tasks_file: Path = None) -> dict:
    """Load task definitions from JSON file."""
    if tasks_file is None:
        tasks_file = TASKS_DIR / DEFAULT_TASKS_FILE

    # Fallback to old location if new doesn't exist
    if not tasks_file.exists():
        old_location = SCRIPT_DIR / "feature_list.json"
        if old_location.exists():
            tasks_file = old_location

    if not tasks_file.exists():
        print(f"{Style.RED}Error: Tasks file not found: {tasks_file}{Style.RESET}")
        return {}

    with open(tasks_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tasks(data: dict, tasks_file: Path = None) -> None:
    """Save updated task definitions."""
    if tasks_file is None:
        tasks_file = TASKS_DIR / DEFAULT_TASKS_FILE

    # Fallback to old location if new doesn't exist
    if not tasks_file.exists():
        old_location = SCRIPT_DIR / "feature_list.json"
        if old_location.exists():
            tasks_file = old_location

    with open(tasks_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_pending_task(data: dict) -> dict | None:
    """Get the first pending task."""
    pending_ids = data.get("queue", {}).get("pending", [])
    if not pending_ids:
        return None

    task_id = pending_ids[0]
    for task in data.get("tasks", []):
        if task["id"] == task_id:
            return task
    return None


def get_task_by_id(data: dict, task_id: str) -> dict | None:
    """Find a task by its ID."""
    for task in data.get("tasks", []):
        if task["id"] == task_id:
            return task
    return None


def update_task_status(data: dict, task_id: str, status: str) -> None:
    """Update task status in data and save."""
    for task in data.get("tasks", []):
        if task["id"] == task_id:
            task["status"] = status
            task["last_updated"] = datetime.now().isoformat()
            break

    queue = data.get("queue", {})
    for q in ["pending", "in_progress", "completed", "failed"]:
        if task_id in queue.get(q, []):
            queue[q].remove(task_id)

    if status in queue:
        queue[status].append(task_id)

    save_tasks(data)


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT BUILDING
# ═══════════════════════════════════════════════════════════════════════════════

def build_task_prompt(task: dict, project: dict) -> str:
    """Build comprehensive prompt from task definition."""
    parts = []

    # Header
    parts.append(f"# TASK: {task['title']}")
    parts.append(f"**ID:** {task['id']} | **Priority:** {task.get('priority', 'medium')} | **Complexity:** {task.get('complexity', 'medium')}")
    parts.append("")

    # Description
    desc = task.get("description", {})
    parts.append("## PROBLEM")
    parts.append(desc.get("problem", "No problem description"))
    parts.append("")
    parts.append("## GOAL")
    parts.append(desc.get("goal", "No goal description"))
    parts.append("")

    # Files
    files = task.get("files", {})
    if files:
        parts.append("## FILES")
        if files.get("target"):
            parts.append("**MODIFY THESE:**")
            for f in files["target"]:
                parts.append(f"  - {f}")
        if files.get("context"):
            parts.append("**READ FOR CONTEXT:**")
            for f in files["context"]:
                parts.append(f"  - {f}")
        parts.append("")

    # Knowledge
    knowledge = task.get("knowledge", {})
    if knowledge.get("patterns_to_follow"):
        parts.append("## DO THIS:")
        for p in knowledge["patterns_to_follow"]:
            parts.append(f"  - {p}")
        parts.append("")
    if knowledge.get("anti_patterns"):
        parts.append("## DON'T DO THIS:")
        for p in knowledge["anti_patterns"]:
            parts.append(f"  - {p}")
        parts.append("")

    # Verification
    verification = task.get("verification", {})
    if verification.get("commands"):
        parts.append("## VERIFICATION COMMANDS (run these when done):")
        for cmd in verification["commands"]:
            parts.append(f"  $ {cmd}")
        parts.append("")

    # Project context
    parts.append("## PROJECT")
    parts.append(f"**Root:** {project.get('root', 'Unknown')}")
    parts.append(f"**Stack:** {', '.join(project.get('stack', []))}")
    parts.append("")

    parts.append("---")
    parts.append("**BEGIN WORK. Read context files first. Execute with precision.**")

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# TASK RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

async def run_task(task: dict, project: dict, model: str, max_iterations: int) -> bool:
    """Run a task with the Claude SDK."""
    task_id = task["id"]
    project_dir = Path(project.get("root", "."))

    # Print task header
    print_task_header(task, model, max_iterations, project_dir)

    # Build prompt
    prompt = build_task_prompt(task, project)

    # Create log file
    LOGS_DIR.mkdir(exist_ok=True)
    log_file = create_session_log(
        LOGS_DIR, task_id, "AUTOAGENTS", model,
        {"Task": task["title"], "Iterations": max_iterations}
    )

    print(f"  {Style.DIM}Log: {log_file.name}{Style.RESET}\n")

    # Run iterations
    for i in range(max_iterations):
        print_iteration_header(i + 1, max_iterations, task_id)

        # Build prompt for this iteration
        if i == 0:
            current_prompt = prompt
        else:
            current_prompt = f"""Continue working on {task_id}: {task['title']}

This is iteration {i+1} of {max_iterations}.

## CHECKLIST
1. Check what was done in previous iteration
2. Run verification commands
3. Fix any remaining issues
4. If complete, commit changes

**Continue improving. Show your reasoning.**"""

        # Create client and run session
        client = create_agent_client(
            project_dir=project_dir,
            model=model,
            system_prompt="You are an expert developer fixing bugs and implementing features. Think step by step and explain your reasoning.",
        )

        async with client:
            status, response, tokens = await stream_agent_response(client, current_prompt)

        # Log output
        log_iteration(log_file, i + 1, max_iterations, response, tokens, prompt if i == 0 else "")

        if status == "error":
            print(f"  {Style.RED}Error in iteration {i+1}{Style.RESET}")
            if i == max_iterations - 1:
                return False
        else:
            print(f"  {Style.GREEN}Iteration {i+1} complete{Style.RESET}")

        # Small delay between iterations
        if i < max_iterations - 1:
            print(f"\n  {Style.DIM}Next iteration in 3 seconds...{Style.RESET}")
            await asyncio.sleep(3)

    return True


# ═══════════════════════════════════════════════════════════════════════════════
# LIST TASKS
# ═══════════════════════════════════════════════════════════════════════════════

def list_tasks(data: dict) -> None:
    """Display all tasks with nice formatting."""
    tasks = data.get("tasks", [])
    if not tasks:
        print(f"  {Style.YELLOW}No tasks defined{Style.RESET}")
        return

    status_emoji = {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "failed": "❌"
    }

    priority_color = {
        "critical": Style.RED,
        "high": Style.YELLOW,
        "medium": Style.CYAN,
        "low": Style.GREEN
    }

    print(f"\n{Style.BOLD}{'ID':<12} {'Status':<14} {'Priority':<12} Title{Style.RESET}")
    print(f"{Style.DIM}{'─' * 70}{Style.RESET}")

    for task in tasks:
        status = task.get('status', 'pending')
        priority = task.get('priority', 'medium')
        emoji = status_emoji.get(status, "⚪")
        color = priority_color.get(priority, Style.WHITE)

        print(f"{task['id']:<12} {emoji} {status:<11} {color}{priority:<10}{Style.RESET} {task['title'][:35]}")

    # Show queue status
    queue = data.get("queue", {})
    print_queue_status(
        pending=len(queue.get("pending", [])),
        in_progress=len(queue.get("in_progress", [])),
        completed=len(queue.get("completed", [])),
        failed=len(queue.get("failed", []))
    )


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="AUTOAGENTS Task Runner - Claude Code SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m autoagents.runners.task_runner                    # Run first pending task
  python -m autoagents.runners.task_runner --task TASK-000    # Run specific task
  python -m autoagents.runners.task_runner --max-iterations 5 # Limit iterations
  python -m autoagents.runners.task_runner --list             # List all tasks
        """,
    )

    parser.add_argument("--task", type=str, help="Run a specific task by ID")
    parser.add_argument("--max-iterations", type=int, default=5, help="Max iterations (default: 5)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--list", action="store_true", help="List all tasks")
    parser.add_argument("--tasks-file", type=str, help="Path to tasks JSON file")

    return parser.parse_args()


async def main() -> None:
    """Main entry point."""
    setup_windows_utf8()
    args = parse_args()

    # Print banner
    print_banner()

    # Load tasks
    tasks_file = Path(args.tasks_file) if args.tasks_file else None
    data = load_tasks(tasks_file)
    if not data:
        return

    project = data.get("project", {})

    # Handle --list
    if args.list:
        list_tasks(data)
        return

    # Get task to run
    if args.task:
        task = get_task_by_id(data, args.task)
        if not task:
            print(f"  {Style.RED}Error: Task {args.task} not found{Style.RESET}")
            return
    else:
        task = get_pending_task(data)
        if not task:
            print(f"  {Style.YELLOW}No pending tasks to run{Style.RESET}")
            queue = data.get("queue", {})
            print_queue_status(
                pending=len(queue.get("pending", [])),
                in_progress=len(queue.get("in_progress", [])),
                completed=len(queue.get("completed", [])),
                failed=len(queue.get("failed", []))
            )
            return

    # Update status to in_progress
    update_task_status(data, task["id"], "in_progress")
    print(f"  {Style.CYAN}Task {task['id']} marked as in_progress{Style.RESET}")

    # Run the task
    try:
        success = await run_task(task, project, args.model, args.max_iterations)

        # Update final status
        final_status = "completed" if success else "failed"
        data = load_tasks(tasks_file)  # Reload
        update_task_status(data, task["id"], final_status)

        if success:
            print_success_banner(task["id"], args.max_iterations)
        else:
            print_failure_banner(task["id"], "Task did not complete successfully")

    except KeyboardInterrupt:
        print(f"\n\n  {Style.YELLOW}Interrupted by user{Style.RESET}")
        data = load_tasks(tasks_file)
        update_task_status(data, task["id"], "pending")
        print(f"  {Style.DIM}Task returned to pending queue{Style.RESET}")

    except Exception as e:
        print(f"\n  {Style.RED}Fatal error: {e}{Style.RESET}")
        data = load_tasks(tasks_file)
        update_task_status(data, task["id"], "failed")
        print_failure_banner(task["id"], str(e)[:50])
        raise

    # Final status
    queue = load_tasks(tasks_file).get("queue", {})
    print_queue_status(
        pending=len(queue.get("pending", [])),
        in_progress=len(queue.get("in_progress", [])),
        completed=len(queue.get("completed", [])),
        failed=len(queue.get("failed", []))
    )


def run():
    """Entry point for console script."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
