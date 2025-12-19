#!/usr/bin/env python3
"""
🤖 AUTOAGENTS Task Runner v2.1 - Claude Code SDK
================================================

Runs autonomous coding agents on tasks defined in feature_list.json.

Usage:
    python run_task.py                         # Run first pending task
    python run_task.py --task TASK-000         # Run specific task
    python run_task.py --max-iterations 5      # Limit iterations
    python run_task.py --list                  # List all tasks
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient

from llm_provider import get_llm_provider
from opencode_client import OpenCodeClient

# Paths
SCRIPT_DIR = Path(__file__).parent
FEATURE_LIST = SCRIPT_DIR / "feature_list.json"
PROMPTS_DIR = SCRIPT_DIR / "prompts"
LOGS_DIR = SCRIPT_DIR / "logs"

# Default model
DEFAULT_MODEL = "claude-sonnet-4-20250514"

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 VISUAL OUTPUT HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

class Style:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Backgrounds
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'


def print_banner():
    """Print the startup banner."""
    banner = f"""
{Style.CYAN}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}🤖 AUTOAGENTS v2.1{Style.RESET}{Style.CYAN}                                               ║
║   {Style.DIM}Autonomous Coding with Claude Code SDK{Style.RESET}{Style.CYAN}                         ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
"""
    print(banner)


def print_task_header(task: dict, model: str, max_iterations: int, project_dir: Path):
    """Print task information header."""
    priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(task.get("priority", "medium"), "⚪")
    complexity_emoji = {"hard": "🔥", "medium": "⚡", "easy": "✨"}.get(task.get("complexity", "medium"), "⚡")

    print(f"""
{Style.MAGENTA}┌──────────────────────────────────────────────────────────────────────┐{Style.RESET}
{Style.MAGENTA}│{Style.RESET} {Style.BOLD}📋 TASK: {task['id']}{Style.RESET}
{Style.MAGENTA}│{Style.RESET} {Style.CYAN}{task['title']}{Style.RESET}
{Style.MAGENTA}├──────────────────────────────────────────────────────────────────────┤{Style.RESET}
{Style.MAGENTA}│{Style.RESET} {priority_emoji} Priority: {task.get('priority', 'medium'):<10} {complexity_emoji} Complexity: {task.get('complexity', 'medium')}
{Style.MAGENTA}│{Style.RESET} 🧠 Model: {model}
{Style.MAGENTA}│{Style.RESET} 🔄 Iterations: {max_iterations}
{Style.MAGENTA}│{Style.RESET} 📁 Project: {project_dir}
{Style.MAGENTA}└──────────────────────────────────────────────────────────────────────┘{Style.RESET}
""")


def print_iteration_header(iteration: int, total: int):
    """Print iteration header."""
    progress = "█" * iteration + "░" * (total - iteration)
    print(f"""
{Style.YELLOW}╭─────────────────────────────────────────────────────────────────────╮{Style.RESET}
{Style.YELLOW}│{Style.RESET} {Style.BOLD}🔄 ITERATION {iteration}/{total}{Style.RESET}  [{progress}]
{Style.YELLOW}╰─────────────────────────────────────────────────────────────────────╯{Style.RESET}
""")


def print_tool_use(tool_name: str, tool_input: dict = None):
    """Print tool usage with nice formatting."""
    tool_emojis = {
        "Read": "📖",
        "Write": "✍️",
        "Edit": "✏️",
        "Glob": "🔍",
        "Grep": "🔎",
        "Bash": "💻",
        "Task": "🚀",
    }
    emoji = tool_emojis.get(tool_name, "🔧")

    # Extract relevant info from tool input
    detail = ""
    if tool_input:
        if "file_path" in tool_input:
            detail = f" → {Path(tool_input['file_path']).name}"
        elif "pattern" in tool_input:
            detail = f" → {tool_input['pattern'][:30]}..."
        elif "command" in tool_input:
            cmd = tool_input['command'][:40]
            detail = f" → {cmd}..."

    print(f"  {Style.BLUE}{emoji} {tool_name}{Style.DIM}{detail}{Style.RESET}")


def print_tool_result(is_error: bool, content: str = None):
    """Print tool result."""
    if is_error:
        print(f"     {Style.RED}❌ Error{Style.RESET}")
        if content:
            # Show first line of error
            first_line = str(content).split('\n')[0][:60]
            print(f"     {Style.DIM}{first_line}{Style.RESET}")
    else:
        print(f"     {Style.GREEN}✅ Done{Style.RESET}")


def print_thinking(text: str):
    """Print agent's thinking/reasoning."""
    if text.strip():
        # Clean up and truncate long text
        lines = text.strip().split('\n')
        for line in lines[:5]:  # Show first 5 lines
            if line.strip():
                print(f"  {Style.DIM}💭 {line[:80]}{Style.RESET}")
        if len(lines) > 5:
            print(f"  {Style.DIM}   ... ({len(lines) - 5} more lines){Style.RESET}")


def print_success(task_id: str, iterations: int):
    """Print success message."""
    print(f"""
{Style.GREEN}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}✅ TASK COMPLETED SUCCESSFULLY{Style.RESET}{Style.GREEN}                                  ║
║                                                                      ║
║   📋 Task: {task_id:<52}       ║
║   🔄 Iterations: {iterations:<48}       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def print_failure(task_id: str, reason: str = ""):
    """Print failure message."""
    print(f"""
{Style.RED}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}❌ TASK FAILED{Style.RESET}{Style.RED}                                                    ║
║                                                                      ║
║   📋 Task: {task_id:<52}       ║
║   💬 {reason[:54]:<54}       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def print_queue_status(data: dict):
    """Print queue status summary."""
    queue = data.get("queue", {})
    pending = len(queue.get("pending", []))
    in_progress = len(queue.get("in_progress", []))
    completed = len(queue.get("completed", []))
    failed = len(queue.get("failed", []))

    print(f"""
{Style.CYAN}┌─────────────────────────────────────┐{Style.RESET}
{Style.CYAN}│{Style.RESET} {Style.BOLD}📊 QUEUE STATUS{Style.RESET}                      {Style.CYAN}│{Style.RESET}
{Style.CYAN}├─────────────────────────────────────┤{Style.RESET}
{Style.CYAN}│{Style.RESET} ⏳ Pending:     {Style.YELLOW}{pending:<18}{Style.RESET} {Style.CYAN}│{Style.RESET}
{Style.CYAN}│{Style.RESET} 🔄 In Progress: {Style.BLUE}{in_progress:<18}{Style.RESET} {Style.CYAN}│{Style.RESET}
{Style.CYAN}│{Style.RESET} ✅ Completed:   {Style.GREEN}{completed:<18}{Style.RESET} {Style.CYAN}│{Style.RESET}
{Style.CYAN}│{Style.RESET} ❌ Failed:      {Style.RED}{failed:<18}{Style.RESET} {Style.CYAN}│{Style.RESET}
{Style.CYAN}└─────────────────────────────────────┘{Style.RESET}
""")


# ═══════════════════════════════════════════════════════════════════════════════
# 📋 DATA MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def load_feature_list() -> dict:
    """Load the feature_list.json file."""
    if not FEATURE_LIST.exists():
        print(f"{Style.RED}❌ Error: feature_list.json not found at {FEATURE_LIST}{Style.RESET}")
        return {}
    with open(FEATURE_LIST, "r", encoding="utf-8") as f:
        return json.load(f)


def save_feature_list(data: dict) -> None:
    """Save updated feature_list.json."""
    with open(FEATURE_LIST, "w", encoding="utf-8") as f:
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
    """Update task status in feature_list.json."""
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

    save_feature_list(data)


# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 PROMPT BUILDING
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
# 🔌 CLAUDE SDK CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

def create_client(project_dir: Path, model: str):
    """Create an LLM client (Claude SDK or OpenCode CLI)."""
    provider = get_llm_provider()
    if provider == "opencode":
        return OpenCodeClient(project_dir=project_dir, model=model)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")

    if not api_key and not oauth_token:
        raise ValueError(
            "No auth configured. Set ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN in .env"
        )

    # Security settings
    security_settings = {
        "sandbox": {"enabled": True, "autoAllowBashIfSandboxed": True},
        "permissions": {
            "defaultMode": "acceptEdits",
            "allow": [
                "Read(./**)",
                "Write(./**)",
                "Edit(./**)",
                "Glob(./**)",
                "Grep(./**)",
                "Bash(*)",
            ],
        },
    }

    project_dir.mkdir(parents=True, exist_ok=True)
    settings_file = project_dir / ".claude_settings.json"
    with open(settings_file, "w") as f:
        json.dump(security_settings, f, indent=2)

    return ClaudeSDKClient(
        options=ClaudeCodeOptions(
            model=model,
            system_prompt="You are an expert developer fixing bugs and implementing features. Think step by step and explain your reasoning.",
            allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
            max_turns=500,
            cwd=str(project_dir.resolve()),
            settings=str(settings_file.resolve()),
        )
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 AGENT SESSION
# ═══════════════════════════════════════════════════════════════════════════════

async def run_agent_session(client, message: str) -> tuple[str, str]:
    """Run a single agent session with pretty output."""
    provider_label = getattr(client, "provider_label", "Claude Agent SDK")
    print(f"  {Style.CYAN}🚀 Sending prompt to {provider_label}...{Style.RESET}\n")

    try:
        await client.query(message)

        response_text = ""
        current_text_buffer = ""

        async for msg in client.receive_response():
            msg_type = type(msg).__name__

            if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "TextBlock" and hasattr(block, "text"):
                        response_text += block.text
                        current_text_buffer += block.text

                        # Print thinking/reasoning with nice formatting
                        if '\n' in current_text_buffer:
                            lines = current_text_buffer.split('\n')
                            for line in lines[:-1]:
                                if line.strip():
                                    print(f"  {Style.WHITE}💭 {line}{Style.RESET}")
                            current_text_buffer = lines[-1]

                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        # Flush text buffer first
                        if current_text_buffer.strip():
                            print(f"  {Style.WHITE}💭 {current_text_buffer.strip()}{Style.RESET}")
                            current_text_buffer = ""

                        tool_input = getattr(block, "input", {})
                        print_tool_use(block.name, tool_input)

            elif msg_type == "UserMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__
                    if block_type == "ToolResultBlock":
                        is_error = getattr(block, "is_error", False)
                        content = getattr(block, "content", "")
                        print_tool_result(is_error, content)

        # Flush remaining text
        if current_text_buffer.strip():
            print(f"  {Style.WHITE}💭 {current_text_buffer.strip()}{Style.RESET}")

        print(f"\n  {Style.DIM}{'─' * 66}{Style.RESET}\n")
        return "continue", response_text

    except Exception as e:
        print(f"  {Style.RED}❌ Error during agent session: {e}{Style.RESET}")
        return "error", str(e)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 TASK RUNNER
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
    log_file = LOGS_DIR / f"{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"🤖 AUTOAGENTS LOG\n")
        f.write(f"{'=' * 70}\n")
        f.write(f"Task: {task_id} - {task['title']}\n")
        f.write(f"Started: {datetime.now().isoformat()}\n")
        f.write(f"Model: {model}\n")
        f.write(f"{'=' * 70}\n\n")
        f.write("PROMPT:\n")
        f.write(prompt)
        f.write(f"\n\n{'=' * 70}\n\n")

    print(f"  {Style.DIM}📝 Log file: {log_file.name}{Style.RESET}\n")

    # Run iterations
    for i in range(max_iterations):
        print_iteration_header(i + 1, max_iterations)

        client = create_client(project_dir, model)

        if i == 0:
            current_prompt = prompt
        else:
            current_prompt = f"""Continue working on {task_id}: {task['title']}

This is iteration {i+1} of {max_iterations}.

## 📋 CHECKLIST
1. Check what was done in previous iteration
2. Run verification commands
3. Fix any remaining issues
4. If complete, commit changes

**Continue improving. Show your reasoning.**"""

        async with client:
            status, response = await run_agent_session(client, current_prompt)

        # Log output
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n{'=' * 70}\n")
            f.write(f"📍 ITERATION {i+1}/{max_iterations}\n")
            f.write(f"{'=' * 70}\n")
            f.write(f"Response:\n{response}\n")

        if status == "error":
            print(f"  {Style.RED}⚠️ Error in iteration {i+1}{Style.RESET}")
            if i == max_iterations - 1:
                return False
        else:
            print(f"  {Style.GREEN}✅ Iteration {i+1} complete{Style.RESET}")

        # Small delay between iterations
        if i < max_iterations - 1:
            print(f"\n  {Style.DIM}⏳ Next iteration in 3 seconds...{Style.RESET}")
            await asyncio.sleep(3)

    return True


# ═══════════════════════════════════════════════════════════════════════════════
# 📋 LIST TASKS
# ═══════════════════════════════════════════════════════════════════════════════

def list_tasks(data: dict) -> None:
    """Display all tasks with nice formatting."""
    tasks = data.get("tasks", [])
    if not tasks:
        print(f"  {Style.YELLOW}⚠️ No tasks defined{Style.RESET}")
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

    print_queue_status(data)


# ═══════════════════════════════════════════════════════════════════════════════
# 🎬 MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="🤖 AUTOAGENTS Task Runner - Claude Code SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_task.py                         # Run first pending task
  python run_task.py --task TASK-000         # Run specific task
  python run_task.py --max-iterations 5      # Limit iterations
  python run_task.py --list                  # List all tasks
        """,
    )

    parser.add_argument("--task", type=str, help="Run a specific task by ID")
    parser.add_argument("--max-iterations", type=int, default=5, help="Max iterations (default: 5)")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Model to use (default: {DEFAULT_MODEL})")
    parser.add_argument("--list", action="store_true", help="List all tasks")

    return parser.parse_args()


async def main() -> None:
    """Main entry point."""
    args = parse_args()

    # Print banner
    print_banner()

    # Load feature list
    data = load_feature_list()
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
            print(f"  {Style.RED}❌ Error: Task {args.task} not found{Style.RESET}")
            return
    else:
        task = get_pending_task(data)
        if not task:
            print(f"  {Style.YELLOW}⚠️ No pending tasks to run{Style.RESET}")
            print_queue_status(data)
            return

    # Update status to in_progress
    update_task_status(data, task["id"], "in_progress")
    print(f"  {Style.CYAN}📋 Task {task['id']} marked as in_progress{Style.RESET}")

    # Run the task
    try:
        success = await run_task(task, project, args.model, args.max_iterations)

        # Update final status
        final_status = "completed" if success else "failed"
        data = load_feature_list()  # Reload
        update_task_status(data, task["id"], final_status)

        if success:
            print_success(task["id"], args.max_iterations)
        else:
            print_failure(task["id"], "Task did not complete successfully")

    except KeyboardInterrupt:
        print(f"\n\n  {Style.YELLOW}⚠️ Interrupted by user{Style.RESET}")
        data = load_feature_list()
        update_task_status(data, task["id"], "pending")
        print(f"  {Style.DIM}Task returned to pending queue{Style.RESET}")

    except Exception as e:
        print(f"\n  {Style.RED}💥 Fatal error: {e}{Style.RESET}")
        data = load_feature_list()
        update_task_status(data, task["id"], "failed")
        print_failure(task["id"], str(e)[:50])
        raise

    # Final status
    print_queue_status(load_feature_list())


if __name__ == "__main__":
    # Enable UTF-8 output on Windows
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')

    asyncio.run(main())
