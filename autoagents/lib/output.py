"""
Visual Output Functions
=======================

Reusable visual output components for all autonomous agents.
"""

import sys
from pathlib import Path
from typing import Optional

from .styles import Style


def setup_windows_utf8():
    """Enable UTF-8 output on Windows."""
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')


def print_banner(
    version: str = "2.1",
    title: str = "AUTOAGENTS",
    subtitle: str = "Autonomous Coding with Claude Code SDK"
):
    """Print the startup banner."""
    print(f"""
{Style.CYAN}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}🤖 {title} v{version}{Style.RESET}{Style.CYAN}                                               ║
║   {Style.DIM}{subtitle}{Style.RESET}{Style.CYAN}                         ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def print_tool_use(tool_name: str, tool_input: Optional[dict] = None):
    """
    Print tool usage with emoji.

    Args:
        tool_name: Name of the tool being used
        tool_input: Optional input parameters for the tool
    """
    TOOL_EMOJI = {
        "Read": "📖",
        "Write": "✍️",
        "Edit": "✏️",
        "Glob": "🔍",
        "Grep": "🔎",
        "Bash": "💻",
        "Task": "🚀",
        "WebFetch": "🌐",
        "WebSearch": "🔍",
    }
    emoji = TOOL_EMOJI.get(tool_name, "🔧")

    detail = ""
    if tool_input and isinstance(tool_input, dict):
        if "file_path" in tool_input:
            detail = f" → {Path(tool_input['file_path']).name}"
        elif "pattern" in tool_input:
            pattern = str(tool_input['pattern'])
            detail = f" → {pattern[:30]}..." if len(pattern) > 30 else f" → {pattern}"
        elif "command" in tool_input:
            cmd = str(tool_input['command'])
            detail = f" → {cmd[:40]}..." if len(cmd) > 40 else f" → {cmd}"
        elif "query" in tool_input:
            query = str(tool_input['query'])
            detail = f" → {query[:40]}..." if len(query) > 40 else f" → {query}"

    print(f"  {Style.BLUE}{emoji} {tool_name}{Style.DIM}{detail}{Style.RESET}")


def print_tool_result(is_error: bool, content: str = ""):
    """
    Print tool result.

    Args:
        is_error: Whether the tool execution failed
        content: Optional content to display (truncated for errors)
    """
    if is_error:
        print(f"     {Style.RED}❌ Error{Style.RESET}")
        if content:
            error_line = str(content).split('\n')[0][:60]
            print(f"     {Style.DIM}{error_line}{Style.RESET}")
    else:
        print(f"     {Style.GREEN}✅ Done{Style.RESET}")


def print_thinking(text: str):
    """Print agent's thinking/reasoning."""
    if text.strip():
        truncated = text[:100] + "..." if len(text) > 100 else text
        print(f"  {Style.WHITE}💭 {truncated}{Style.RESET}")


def print_iteration_header(iteration: int, total: int, task_id: str = ""):
    """Print iteration header with progress bar."""
    progress = "█" * iteration + "░" * (total - iteration)
    task_str = f" - {task_id}" if task_id else ""
    print(f"""
{Style.YELLOW}╭─────────────────────────────────────────────────────────────────────╮{Style.RESET}
{Style.YELLOW}│{Style.RESET} {Style.BOLD}🔄 ITERATION {iteration}/{total}{Style.RESET}{task_str}  [{progress}]
{Style.YELLOW}╰─────────────────────────────────────────────────────────────────────╯{Style.RESET}
""")


def print_task_header(
    task: dict,
    model: str,
    max_iterations: int,
    project_dir: Path
):
    """Print task information header."""
    PRIORITY_EMOJI = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
    COMPLEXITY_EMOJI = {"hard": "🔥", "medium": "⚡", "easy": "✨"}

    priority = task.get("priority", "medium")
    complexity = task.get("complexity", "medium")
    priority_emoji = PRIORITY_EMOJI.get(priority, "⚪")
    complexity_emoji = COMPLEXITY_EMOJI.get(complexity, "⚡")

    print(f"""
{Style.MAGENTA}┌──────────────────────────────────────────────────────────────────────┐{Style.RESET}
{Style.MAGENTA}│{Style.RESET} {Style.BOLD}📋 TASK: {task.get('id', 'N/A')}{Style.RESET}
{Style.MAGENTA}│{Style.RESET} {Style.CYAN}{task.get('title', 'Untitled')}{Style.RESET}
{Style.MAGENTA}├──────────────────────────────────────────────────────────────────────┤{Style.RESET}
{Style.MAGENTA}│{Style.RESET} {priority_emoji} Priority: {priority:<10} {complexity_emoji} Complexity: {complexity}
{Style.MAGENTA}│{Style.RESET} 🧠 Model: {model}
{Style.MAGENTA}│{Style.RESET} 🔄 Iterations: {max_iterations}
{Style.MAGENTA}│{Style.RESET} 📁 Project: {project_dir}
{Style.MAGENTA}└──────────────────────────────────────────────────────────────────────┘{Style.RESET}
""")


def print_queue_status(pending: int, in_progress: int, completed: int, failed: int):
    """Print queue status box."""
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


def print_success_banner(task_id: str, iterations: int = 0, message: str = ""):
    """Print success completion banner."""
    msg_display = message if message else f"Task: {task_id}"
    print(f"""
{Style.GREEN}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}✅ TASK COMPLETED SUCCESSFULLY{Style.RESET}{Style.GREEN}                                  ║
║                                                                      ║
║   📋 {msg_display:<58}       ║
║   🔄 Iterations: {iterations:<48}       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def print_failure_banner(task_id: str, reason: str = ""):
    """Print failure banner."""
    reason_display = reason[:54] if reason else "Unknown error"
    print(f"""
{Style.RED}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}❌ TASK FAILED{Style.RESET}{Style.RED}                                                    ║
║                                                                      ║
║   📋 Task: {task_id:<52}       ║
║   💬 {reason_display:<54}       ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def print_info(text: str):
    """Print info message."""
    print(f"  {Style.CYAN}ℹ️ {text}{Style.RESET}")


def print_warning(text: str):
    """Print warning message."""
    print(f"  {Style.YELLOW}⚠️ {text}{Style.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"  {Style.RED}❌ {text}{Style.RESET}")


def print_success(text: str):
    """Print success message."""
    print(f"  {Style.GREEN}✅ {text}{Style.RESET}")


def print_divider():
    """Print a divider line."""
    print(f"  {Style.DIM}{'─' * 66}{Style.RESET}")


def print_agent_header(name: str, role: str, expertise: list, emoji: str, color: str):
    """Print agent identification header."""
    print(f"""
{color}┌──────────────────────────────────────────────────────────────────────┐{Style.RESET}
{color}│{Style.RESET} {emoji} {Style.BOLD}{name}{Style.RESET} - {role}
{color}│{Style.RESET} {Style.DIM}Expertise: {', '.join(expertise[:4])}{Style.RESET}
{color}└──────────────────────────────────────────────────────────────────────┘{Style.RESET}
""")
