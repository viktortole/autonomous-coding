#!/usr/bin/env python3
"""
FRONTEND Agent Runner - Autonomous Frontend Developer Agent

Migrated to agents/ folder structure.
Works on Control Station frontend: dashboard module look, feel, animations.

Usage:
    python -m autoagents.agents.frontend.runner                    # Run single task
    python -m autoagents.agents.frontend.runner -i 5               # Run 5 iterations
    python -m autoagents.agents.frontend.runner --continuous       # Never stop
    python -m autoagents.agents.frontend.runner --module dashboard # Focus on module
"""

import argparse
import asyncio
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
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
from autoagents.lib.comms import CommsManager
from autoagents.lib.budget import TokenBudget
from autoagents.agents.emojis import FRONTEND_EMOJI, TOOL_EMOJI
from autoagents.lib.workspace import resolve_workspace, WorkspacePaths


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION - Load from config.json
# ═══════════════════════════════════════════════════════════════════════════════

AGENT_DIR = Path(__file__).parent
CONFIG_FILE = AGENT_DIR / "config.json"
TASKS_FILE = AGENT_DIR / "tasks.json"

def load_config() -> dict:
    """Load agent configuration from config.json."""
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load config: {e}")
        return {}

CONFIG = load_config()

CONTROL_STATION = Path("C:/Users/ToleV/Desktop/TestingFolder/control-station")
COMMS_MD = CONTROL_STATION / ".claude" / "COMMS.md"

MODULES = {
    "dashboard": CONTROL_STATION / "src" / "modules" / "dashboard",
    "focusguardian": CONTROL_STATION / "src" / "modules" / "focusguardian",
    "roadmap": CONTROL_STATION / "src" / "modules" / "roadmap",
    "alarm": CONTROL_STATION / "src" / "modules" / "alarm",
    "gamification": CONTROL_STATION / "src" / "modules" / "gamification",
    "james": CONTROL_STATION / "src" / "modules" / "james",
}

FRONTEND_CONFIG = {
    "model": CONFIG.get("model", "claude-sonnet-4-20250514"),
    "name": CONFIG.get("name", "FRONTEND"),
    "role": CONFIG.get("role", "Frontend Developer & UI/UX Polish"),
    "emoji": CONFIG.get("emoji", "🎨"),
}

TOKEN_BUDGET_CONFIG = CONFIG.get("token_budget", {})
TOKEN_BUDGET = {
    "daily_limit": TOKEN_BUDGET_CONFIG.get("daily_limit", 12000),
    "per_task": TOKEN_BUDGET_CONFIG.get("per_task", 3000),
    "warning_threshold": TOKEN_BUDGET_CONFIG.get("warning_threshold", 0.8),
}


@dataclass
class FrontendState:
    """Agent operational state."""
    current_module: str = "dashboard"
    current_task: Optional[str] = None
    iteration_count: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    token_usage_today: int = 0
    token_usage_reset_date: str = ""
    files_modified: list = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════════════════
# COMMS.MD INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

comms = CommsManager(COMMS_MD, agent_id="FRONTEND", emoji="🎨")


def log_to_comms(event_type: str, details: dict):
    """Append log entry to COMMS.md for agent coordination."""
    comms.log_event(event_type, details)


# ═══════════════════════════════════════════════════════════════════════════════
# SCREENSHOT CAPTURE (Frontend-specific feature)
# ═══════════════════════════════════════════════════════════════════════════════

def capture_tauri_window_screenshot(
    workspace: WorkspacePaths,
    window_title: str = "Control Station",
) -> Optional[Path]:
    """Capture a screenshot of the Tauri app window using PowerShell."""
    screenshots_dir = workspace.screenshots_dir / "frontend"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = screenshots_dir / f"dashboard_{timestamp}.png"

    ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$process = Get-Process | Where-Object {{ $_.MainWindowTitle -like "*{window_title}*" }} | Select-Object -First 1

if ($process -eq $null) {{
    Write-Host "WINDOW_NOT_FOUND"
    exit 1
}}

Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {{
    [DllImport("user32.dll")]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
}}
public struct RECT {{
    public int Left; public int Top; public int Right; public int Bottom;
}}
"@

$hwnd = $process.MainWindowHandle
$rect = New-Object RECT
[Win32]::GetWindowRect($hwnd, [ref]$rect) | Out-Null
[Win32]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Milliseconds 200

$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top

if ($width -le 0 -or $height -le 0) {{
    Write-Host "INVALID_DIMENSIONS"
    exit 1
}}

$bitmap = New-Object System.Drawing.Bitmap($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, [System.Drawing.Size]::new($width, $height))
$bitmap.Save("{str(screenshot_path).replace(chr(92), '/')}")
$graphics.Dispose()
$bitmap.Dispose()
Write-Host "SUCCESS"
'''

    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, text=True, timeout=10,
            encoding='utf-8', errors='replace'
        )

        if "SUCCESS" in result.stdout and screenshot_path.exists():
            return screenshot_path
        elif "WINDOW_NOT_FOUND" in result.stdout:
            print_warning("Control Station window not found")
            return None
        else:
            print_error(f"Screenshot failed: {result.stderr[:100]}")
            return None

    except subprocess.TimeoutExpired:
        print_error("Screenshot timeout")
        return None
    except Exception as e:
        print_error(f"Screenshot error: {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# TASK MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def load_tasks() -> dict:
    """Load frontend tasks from local tasks.json."""
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load tasks: {e}")
        return {"tasks": [], "queue": {"pending": []}}


def save_tasks(tasks_config: dict):
    """Save frontend tasks."""
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks_config, f, indent=2)
    except Exception as e:
        print_error(f"Failed to save tasks: {e}")


def get_next_task(tasks_config: dict, module: str = None) -> Optional[dict]:
    """Get next pending task, optionally filtered by module."""
    all_tasks = tasks_config.get("tasks", [])
    pending = tasks_config.get("queue", {}).get("pending", [])

    for task_id in pending:
        task = next((t for t in all_tasks if t["id"] == task_id), None)
        if task:
            if module and task.get("module") != module:
                continue
            return task
    return None


def get_task_by_id(tasks_config: dict, task_id: str) -> Optional[dict]:
    """Get specific task by ID."""
    all_tasks = tasks_config.get("tasks", [])
    return next((t for t in all_tasks if t["id"] == task_id), None)


def mark_task_status(tasks_config: dict, task_id: str, status: str):
    """Update task status in queue."""
    queue = tasks_config.get("queue", {})

    for q in ["pending", "in_progress", "completed", "failed"]:
        if task_id in queue.get(q, []):
            queue[q].remove(task_id)

    if status not in queue:
        queue[status] = []
    queue[status].append(task_id)

    for task in tasks_config.get("tasks", []):
        if task["id"] == task_id:
            task["status"] = status
            break

    tasks_config["queue"] = queue
    save_tasks(tasks_config)


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT BUILDING
# ═══════════════════════════════════════════════════════════════════════════════

def get_system_prompt(module: str) -> str:
    """Get system prompt for frontend agent."""
    # Try to load from prompts/system_prompt.md
    prompt_file = AGENT_DIR / "prompts" / "system_prompt.md"
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")

    module_path = MODULES.get(module, MODULES["dashboard"])

    return f"""You are FRONTEND, an ELITE autonomous frontend developer agent for Control Station.

## YOUR EXPERTISE
- React 19 (hooks, suspense, server components)
- Next.js 16 (App Router, layouts, loading states)
- TypeScript 5.5 (strict mode, generics, utility types)
- Tailwind CSS 4 (dark mode, responsive, animations)
- Framer Motion 12 (enter/exit, gestures, layout)

## CURRENT FOCUS: {module.upper()} MODULE
- Path: {module_path}
- Goal: Make it BEAUTIFUL, SMOOTH, ACCESSIBLE, PERFORMANT

## PROJECT CONTEXT
- Root: C:/Users/ToleV/Desktop/TestingFolder/control-station
- Stack: Tauri 2.9.2 + Next.js 16 + React 19 + TypeScript
- Styling: Tailwind CSS 4 + custom-enhancements.css
- Animations: Framer Motion + CSS transitions
- Theme: Dark mode primary, glassmorphism, depth shadows

## WORKFLOW
1. READ the task and understand requirements
2. EXPLORE the current code (Read, Glob, Grep)
3. IDENTIFY what needs improvement
4. IMPLEMENT changes (Edit, Write)
5. VERIFY with TypeScript (npx tsc --noEmit)

## QUALITY STANDARDS
- NO placeholder code - real implementations only
- NO TypeScript errors
- ALWAYS use semantic HTML
- ALWAYS add hover/focus states

BE AGGRESSIVE. WRITE BEAUTIFUL CODE. SHIP POLISHED UI."""


def build_task_prompt(task: dict, module: str) -> str:
    """Build comprehensive prompt from task definition."""
    parts = [
        f"# {FRONTEND_EMOJI['palette']} FRONTEND TASK: {task.get('title', 'Unknown Task')}",
        f"**ID:** {task.get('id', 'N/A')} | **Priority:** {task.get('priority', 'medium')} | **Module:** {module.upper()}",
        "",
        "## EXECUTION MODE: SHIP IT",
        "- WRITE real code, not pseudocode",
        "- IMPLEMENT the feature completely",
        "- VERIFY with TypeScript (npx tsc --noEmit)",
        "",
    ]

    desc = task.get("description", {})
    parts.extend([
        "## PROBLEM",
        desc.get("problem", task.get("title", "No description")),
        "",
        "## GOAL",
        desc.get("goal", "Improve the UI/UX"),
        "",
    ])

    files = task.get("files", {})
    if files.get("target"):
        parts.append("## TARGET FILES")
        for f in files["target"]:
            parts.append(f"- `{f}`")
        parts.append("")

    if files.get("context"):
        parts.append("## CONTEXT FILES")
        for f in files["context"]:
            parts.append(f"- `{f}`")
        parts.append("")

    acceptance = task.get("acceptance_criteria", [])
    if acceptance:
        parts.append("## ACCEPTANCE CRITERIA")
        for ac in acceptance:
            parts.append(f"- {ac}")
        parts.append("")

    parts.extend([
        "---",
        "**START NOW. READ FILES. WRITE CODE. SHIP BEAUTIFUL UI!**"
    ])

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def print_frontend_banner():
    """Print frontend-specific banner."""
    print(f"""
{Style.MAGENTA}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}🎨 FRONTEND v2.1{Style.RESET}{Style.MAGENTA}                                                ║
║   {Style.DIM}Autonomous Frontend Developer + UI/UX Polish{Style.RESET}{Style.MAGENTA}                      ║
║   {Style.DIM}Now using agents/ folder structure{Style.RESET}{Style.MAGENTA}                                ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def print_iteration_header(iteration: int, max_iterations: int, module: str, task_title: str):
    """Print iteration header."""
    max_str = "∞" if max_iterations == -1 else str(max_iterations)
    progress = "█" * min(iteration, 30) + "░" * max(0, min(30, max_iterations) - iteration) if max_iterations > 0 else ""

    print(f"""
{Style.YELLOW}╭─────────────────────────────────────────────────────────────────────╮{Style.RESET}
{Style.YELLOW}│{Style.RESET} {Style.BOLD}🔄 ITERATION {iteration}/{max_str}{Style.RESET}  [{progress[:30]}]
{Style.YELLOW}│{Style.RESET} {Style.CYAN}📦 Module: {module.upper()}{Style.RESET}
{Style.YELLOW}│{Style.RESET} {Style.CYAN}📋 Task: {task_title[:50]}{Style.RESET}
{Style.YELLOW}╰─────────────────────────────────────────────────────────────────────╯{Style.RESET}
""")


async def frontend_loop(args, workspace: WorkspacePaths):
    """Main frontend development loop."""
    state = FrontendState()
    state.current_module = args.module

    tasks_config = load_tasks()
    max_iterations = -1 if args.continuous else args.iterations

    # Reset token usage if new day
    today = datetime.now().strftime("%Y-%m-%d")
    if state.token_usage_reset_date != today:
        state.token_usage_today = 0
        state.token_usage_reset_date = today

    print_info(f"Module focus: {args.module.upper()}")
    print_info(f"Token budget: {TOKEN_BUDGET['daily_limit']:,} tokens/day")
    print_info(f"Mode: {'CONTINUOUS' if max_iterations == -1 else f'LIMITED ({max_iterations} iterations)'}")
    print()

    # Log session start to COMMS.md
    log_to_comms("session_start", {
        "module": args.module,
        "mode": "continuous" if max_iterations == -1 else f"limited_{max_iterations}",
        "token_budget": TOKEN_BUDGET["daily_limit"]
    })

    # Create log file
    logs_dir = workspace.logs_dir / "frontend"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = create_session_log(
        logs_dir, "FRONTEND", FRONTEND_CONFIG["name"], FRONTEND_CONFIG["model"],
        extra_info={"Module": args.module}
    )
    print(f"  {Style.DIM}📝 Log file: {log_file.name}{Style.RESET}\n")

    try:
        iteration = 0
        while True:
            iteration += 1
            state.iteration_count = iteration

            if max_iterations != -1 and iteration > max_iterations:
                print_info(f"Completed {max_iterations} iterations. Session complete.")
                break

            # Get next task
            if args.task:
                current_task = get_task_by_id(tasks_config, args.task)
                if not current_task:
                    print_error(f"Task {args.task} not found")
                    break
            else:
                current_task = get_next_task(tasks_config, args.module)
                if not current_task:
                    print_warning(f"No pending tasks for {args.module}. Creating exploration task...")
                    current_task = {
                        "id": f"EXPLORE-{iteration}",
                        "title": f"Explore and improve {args.module} module",
                        "module": args.module,
                        "priority": "medium",
                        "description": {
                            "problem": f"The {args.module} module may need UI/UX improvements",
                            "goal": f"Find and fix issues in {args.module}",
                            "scope": f"Focus on {args.module} components"
                        },
                        "files": {
                            "target": [f"src/modules/{args.module}/**/*.tsx"],
                            "context": ["src/app/globals.css"]
                        },
                        "acceptance_criteria": ["No TypeScript errors", "Smooth animations"],
                        "verification": {"commands": ["npx tsc --noEmit"]}
                    }

            state.current_task = current_task["id"]
            print_iteration_header(iteration, max_iterations, args.module, current_task["title"])

            # Screenshot capture (if enabled)
            screenshot_path = None
            if args.screenshot or args.visual_review:
                print(f"\n  {FRONTEND_EMOJI['camera']} {Style.CYAN}Capturing dashboard screenshot...{Style.RESET}")
                screenshot_path = capture_tauri_window_screenshot(workspace, "Control Station")
                if screenshot_path:
                    print_success(f"Screenshot saved: {screenshot_path.name}")

            # Mark task in progress
            if current_task["id"] in tasks_config.get("queue", {}).get("pending", []):
                mark_task_status(tasks_config, current_task["id"], "in_progress")

            # Build prompt
            prompt = build_task_prompt(current_task, args.module)

            if screenshot_path and screenshot_path.exists():
                prompt = f"""# 📸 VISUAL REVIEW
Screenshot at: `{screenshot_path}`
USE THE READ TOOL TO VIEW THIS IMAGE, then provide feedback.

---

{prompt}"""

            if iteration > 1:
                prompt = f"""# {FRONTEND_EMOJI['palette']} FRONTEND ITERATION {iteration} - KEEP POLISHING!
Continue improving the {args.module.upper()} module.

{prompt}"""

            # Run AI session
            try:
                system_prompt = get_system_prompt(args.module)
                client = create_agent_client(
                    project_dir=CONTROL_STATION,
                    model=FRONTEND_CONFIG["model"],
                    system_prompt=system_prompt,
                    allowed_tools=CONFIG.get("allowed_tools", ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]),
                    settings_filename=".claude_frontend_settings.json"
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
                    if not current_task["id"].startswith("EXPLORE-"):
                        mark_task_status(tasks_config, current_task["id"], "completed")
                        state.tasks_completed += 1
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

            print(f"\n  {Style.DIM}⏳ Next iteration in 5 seconds...{Style.RESET}")
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        print(f"\n\n{FRONTEND_EMOJI['palette']} FRONTEND interrupted by user.")

    # Session complete
    log_completion(log_file, "completed", state.iteration_count, state.token_usage_today)

    print(f"""
{Style.GREEN}╔══════════════════════════════════════════════════════════════════════╗
║  ✅ FRONTEND SESSION COMPLETE                                        ║
║  🔄 Iterations: {state.iteration_count:<52} ║
║  ✅ Tasks completed: {state.tasks_completed:<47} ║
║  🪙 Tokens used: {state.token_usage_today:<50} ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")

    log_to_comms("session_end", {
        "iterations": state.iteration_count,
        "tasks_completed": state.tasks_completed,
        "tokens_used": state.token_usage_today,
        "log_file": str(log_file)
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="FRONTEND - Autonomous Frontend Developer Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m autoagents.agents.frontend.runner                     # Single iteration
    python -m autoagents.agents.frontend.runner -i 5                # 5 iterations
    python -m autoagents.agents.frontend.runner --continuous        # Run forever
    python -m autoagents.agents.frontend.runner --screenshot        # Visual review
    python -m autoagents.agents.frontend.runner --module dashboard  # Focus on module
        """
    )
    parser.add_argument("-i", "--iterations", type=int, default=1, help="Max iterations (default: 1)")
    parser.add_argument("--module", type=str, default="dashboard",
                        choices=list(MODULES.keys()), help="Module to focus on")
    parser.add_argument("--task", type=str, default=None, help="Specific task ID")
    parser.add_argument("--continuous", action="store_true", help="Run forever")
    parser.add_argument("--screenshot", action="store_true", help="Capture screenshots")
    parser.add_argument("--visual-review", action="store_true", help="Start with visual review")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--list", action="store_true", help="List pending tasks")
    parser.add_argument("--workspace", type=str, help="Workspace root (tasks/logs live here)")
    return parser.parse_args()


def main():
    """Main entry point."""
    setup_windows_utf8()
    args = parse_args()
    workspace = resolve_workspace(args.workspace)

    print_frontend_banner()

    if args.list:
        tasks_config = load_tasks()
        pending = tasks_config.get("queue", {}).get("pending", [])
        all_tasks = tasks_config.get("tasks", [])
        print(f"\n{Style.CYAN}Pending Tasks ({len(pending)}):{Style.RESET}")
        for task_id in pending[:10]:
            task = next((t for t in all_tasks if t["id"] == task_id), None)
            if task:
                print(f"  - {task['id']}: {task['title'][:60]}")
        return

    if not TASKS_FILE.exists():
        print_warning("Frontend tasks file not found - will use exploration mode")

    if not CONTROL_STATION.exists():
        print_error(f"Control Station not found at {CONTROL_STATION}")
        sys.exit(1)

    print_info(f"Control Station: {CONTROL_STATION}")
    print_info(f"Module: {args.module}")
    print_info(f"Model: {FRONTEND_CONFIG['model']}")

    if args.dry_run:
        print_info("Dry run mode - no actions will be taken")
        return

    try:
        asyncio.run(frontend_loop(args, workspace))
    except KeyboardInterrupt:
        print(f"\n\n{FRONTEND_EMOJI['palette']} FRONTEND interrupted by user.")
    except Exception as e:
        print_error(f"Fatal error: {e}")
        sys.exit(1)


def run():
    """Entry point for pyproject.toml scripts."""
    main()


if __name__ == "__main__":
    main()
