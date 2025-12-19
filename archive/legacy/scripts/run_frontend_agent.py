#!/usr/bin/env python3
"""
🎨 CONFIG-FRONTEND v1.0 - Autonomous Frontend Developer Agent
==============================================================

Works on Control Station frontend: dashboard module look, feel, animations,
behavior, and overall UX polish. Uses Opus 4.5 for maximum intelligence.

Usage:
    python run_frontend_agent.py                    # Run single task
    python run_frontend_agent.py -i 5               # Run 5 iterations
    python run_frontend_agent.py --continuous       # Never stop
    python run_frontend_agent.py --task TASK-ID     # Run specific task
    python run_frontend_agent.py --module dashboard # Focus on module

Author: AUTOAGENTS / CONFIG-FRONTEND
Created: 2025-12-19
"""

import argparse
import asyncio
import base64
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

# Claude Code SDK imports
from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient

from llm_provider import get_llm_provider
from opencode_client import OpenCodeClient

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 STYLE & VISUAL OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

class Style:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'

    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    BG_MAGENTA = '\033[45m'


class FrontendEmoji:
    """Frontend agent emojis."""
    PALETTE = "🎨"
    COMPONENT = "🧩"
    ANIMATION = "✨"
    RESPONSIVE = "📱"
    ACCESSIBILITY = "♿"
    PERFORMANCE = "⚡"
    DESIGN = "🎯"
    SUCCESS = "✅"
    ERROR = "❌"
    WORKING = "🔨"
    THINKING = "💭"
    TOOL = "🔧"
    CODE = "💻"
    STYLE = "💅"
    INFO = "ℹ️"
    WARNING = "⚠️"
    CAMERA = "📸"
    EYE = "👁️"


# ═══════════════════════════════════════════════════════════════════════════════
# 📸 SCREENSHOT CAPTURE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

# Screenshot storage
SCRIPT_DIR = Path(__file__).parent
SCREENSHOTS_DIR = SCRIPT_DIR / "screenshots" / "frontend"


def capture_tauri_window_screenshot(window_title: str = "Control Station") -> Optional[Path]:
    """
    Capture a screenshot of the Tauri app window using PowerShell.

    Returns the path to the saved screenshot or None if capture failed.
    """
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = SCREENSHOTS_DIR / f"dashboard_{timestamp}.png"

    # PowerShell script to capture a specific window
    ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Find the window
$process = Get-Process | Where-Object {{ $_.MainWindowTitle -like "*{window_title}*" }} | Select-Object -First 1

if ($process -eq $null) {{
    Write-Host "WINDOW_NOT_FOUND"
    exit 1
}}

# Get window handle and rect
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
    public int Left;
    public int Top;
    public int Right;
    public int Bottom;
}}
"@

$hwnd = $process.MainWindowHandle
$rect = New-Object RECT
[Win32]::GetWindowRect($hwnd, [ref]$rect) | Out-Null

# Bring window to foreground
[Win32]::SetForegroundWindow($hwnd) | Out-Null
Start-Sleep -Milliseconds 200

# Calculate dimensions
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top

if ($width -le 0 -or $height -le 0) {{
    Write-Host "INVALID_DIMENSIONS"
    exit 1
}}

# Capture the screen region
$bitmap = New-Object System.Drawing.Bitmap($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, [System.Drawing.Size]::new($width, $height))

# Save the image
$bitmap.Save("{str(screenshot_path).replace(chr(92), '/')}")
$graphics.Dispose()
$bitmap.Dispose()

Write-Host "SUCCESS"
'''

    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8',
            errors='replace'
        )

        if "SUCCESS" in result.stdout and screenshot_path.exists():
            return screenshot_path
        elif "WINDOW_NOT_FOUND" in result.stdout:
            print(f"  {FrontendEmoji.WARNING} {Style.YELLOW}Control Station window not found{Style.RESET}")
            return None
        else:
            print(f"  {FrontendEmoji.ERROR} {Style.RED}Screenshot failed: {result.stderr[:100]}{Style.RESET}")
            return None

    except subprocess.TimeoutExpired:
        print(f"  {FrontendEmoji.ERROR} {Style.RED}Screenshot timeout{Style.RESET}")
        return None
    except Exception as e:
        print(f"  {FrontendEmoji.ERROR} {Style.RED}Screenshot error: {e}{Style.RESET}")
        return None


def capture_full_screen_screenshot() -> Optional[Path]:
    """
    Capture a full screen screenshot as fallback.

    Returns the path to the saved screenshot or None if capture failed.
    """
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = SCREENSHOTS_DIR / f"fullscreen_{timestamp}.png"

    ps_script = f'''
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bitmap.Save("{str(screenshot_path).replace(chr(92), '/')}")
$graphics.Dispose()
$bitmap.Dispose()
Write-Host "SUCCESS"
'''

    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=10,
            encoding='utf-8',
            errors='replace'
        )

        if "SUCCESS" in result.stdout and screenshot_path.exists():
            return screenshot_path
        return None
    except Exception as e:
        print(f"  {FrontendEmoji.ERROR} {Style.RED}Fullscreen screenshot error: {e}{Style.RESET}")
        return None


def get_latest_screenshot() -> Optional[Path]:
    """Get the most recent screenshot from the screenshots directory."""
    if not SCREENSHOTS_DIR.exists():
        return None

    screenshots = list(SCREENSHOTS_DIR.glob("*.png"))
    if not screenshots:
        return None

    return max(screenshots, key=lambda p: p.stat().st_mtime)


def build_visual_review_prompt(screenshot_path: Path) -> str:
    """Build a prompt for visual review of the screenshot."""
    return f"""# 📸 VISUAL REVIEW OF DASHBOARD

I have captured a screenshot of the Control Station dashboard at:
`{screenshot_path}`

**USE THE READ TOOL TO VIEW THIS IMAGE**, then provide BRUTALLY HONEST feedback:

## ANALYZE THESE ASPECTS:

### 1. VISUAL HIERARCHY
- Is the most important info immediately visible?
- Is there clear visual flow?
- Are headings and sections distinct?

### 2. SPACING & ALIGNMENT
- Is spacing consistent?
- Are elements properly aligned?
- Any cramped or too-sparse areas?

### 3. COLOR & CONTRAST
- Is text readable?
- Do colors work well together?
- Is dark mode executed well?

### 4. ANIMATIONS & POLISH
- Do animations feel smooth?
- Any jarring transitions?
- Loading states visible?

### 5. RESPONSIVE CONCERNS
- Would this work on smaller screens?
- Any overflow risks?

### 6. ACCESSIBILITY
- Sufficient contrast?
- Interactive elements visible?
- Focus states apparent?

## BE BRUTALLY HONEST
- What looks GOOD? (brief)
- What looks BAD? (detailed)
- What needs IMMEDIATE fixing?
- Rate overall polish: 1-10

After reviewing, IDENTIFY specific files and lines that need changes.
Then IMPLEMENT the fixes using Edit tool.
"""


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

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
# 🔧 CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Paths (SCRIPT_DIR already defined in screenshot section above)
FRONTEND_TASKS = SCRIPT_DIR / "frontend_tasks.json"
LOGS_DIR = SCRIPT_DIR / "logs" / "frontend"
CONTROL_STATION = Path("C:/Users/ToleV/Desktop/TestingFolder/control-station")
COMMS_MD = CONTROL_STATION / ".claude" / "COMMS.md"

# Module paths
MODULES = {
    "dashboard": CONTROL_STATION / "src" / "modules" / "dashboard",
    "focusguardian": CONTROL_STATION / "src" / "modules" / "focusguardian",
    "roadmap": CONTROL_STATION / "src" / "modules" / "roadmap",
    "alarm": CONTROL_STATION / "src" / "modules" / "alarm",
    "gamification": CONTROL_STATION / "src" / "modules" / "gamification",
    "james": CONTROL_STATION / "src" / "modules" / "james",
}

# Agent configuration
FRONTEND_CONFIG = {
    "model": "claude-sonnet-4-20250514",  # Sonnet 4 - OAuth compatible
    "name": "CONFIG-FRONTEND",
    "role": "Frontend Developer & UI/UX Polish",
    "emoji": "🎨",
}

# Token budgets
TOKEN_BUDGET = {
    "daily_limit": 50000,  # Frontend work needs more tokens
    "per_task": 10000,
    "warning_threshold": 0.8,
}


# ═══════════════════════════════════════════════════════════════════════════════
# 🤖 CLAUDE SDK CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

def create_frontend_client(project_dir: Path, module: str = "dashboard"):
    """Create LLM client for frontend work."""
    model = FRONTEND_CONFIG["model"]

    provider = get_llm_provider()
    if provider == "opencode":
        return OpenCodeClient(project_dir=project_dir, model=model)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")

    if not api_key and not oauth_token:
        raise ValueError(
            "No Claude auth configured. Set CLAUDE_CODE_OAUTH_TOKEN in .env\n"
            "Run: claude setup-token to get your OAuth token"
        )

    # Full power security settings
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
    settings_file = project_dir / ".claude_frontend_settings.json"
    with open(settings_file, "w") as f:
        json.dump(security_settings, f, indent=2)

    module_path = MODULES.get(module, MODULES["dashboard"])

    system_prompt = f"""You are CONFIG-FRONTEND, an ELITE autonomous frontend developer agent for Control Station.

⚠️ CRITICAL MINDSET: You are a SENIOR frontend developer with 15+ years experience.
- You WRITE CODE, not just analyze
- You IMPLEMENT features, not just plan
- You FIX issues immediately, not just report
- You have IMPECCABLE taste in design and UX

## YOUR EXPERTISE
- React 19 (hooks, suspense, server components)
- Next.js 16 (App Router, layouts, loading states)
- TypeScript 5.5 (strict mode, generics, utility types)
- Tailwind CSS 4 (dark mode, responsive, animations)
- Framer Motion 12 (enter/exit, gestures, layout)
- Recharts (data visualization)
- Radix UI (accessible primitives)
- @dnd-kit (drag and drop)

## CURRENT FOCUS: {module.upper()} MODULE
- Path: {module_path}
- Goal: Make it BEAUTIFUL, SMOOTH, ACCESSIBLE, PERFORMANT

## PROJECT CONTEXT
- Root: C:/Users/ToleV/Desktop/TestingFolder/control-station
- Stack: Tauri 2.9.2 + Next.js 16 + React 19 + TypeScript
- Styling: Tailwind CSS 4 + custom-enhancements.css
- Animations: Framer Motion + CSS transitions
- Theme: Dark mode primary, glassmorphism, depth shadows

## DESIGN SYSTEM
- Colors: Brand purple-blue gradient, category-specific accents
- Spacing: Tailwind scale (gap-4, p-6, etc.)
- Borders: border-white/10, hover:border-white/20
- Shadows: depth-1 to depth-4, shadow-premium
- Radius: rounded-2xl for cards, rounded-xl for elements
- Glass: glass-effect, glass-effect-strong

## ANIMATION STANDARDS
- Entrance: opacity 0→1, y 20→0, stagger 0.1s
- Duration: 200-500ms for micro, 500-1000ms for page
- Easing: ease-out for enter, ease-in for exit
- Performance: will-change, transform only, no layout thrash

## YOUR WORKFLOW
1. READ the task and understand requirements
2. EXPLORE the current code (Read, Glob, Grep)
3. IDENTIFY what needs improvement
4. IMPLEMENT changes (Edit, Write)
5. VERIFY with TypeScript (npx tsc --noEmit)
6. TEST visually if possible
7. ITERATE until perfect

## QUALITY STANDARDS
- NO placeholder code - real implementations only
- NO console.logs left behind
- NO unused imports
- NO TypeScript errors
- NO accessibility violations
- ALWAYS use semantic HTML
- ALWAYS add hover/focus states
- ALWAYS test responsive behavior
- ALWAYS consider loading states
- ALWAYS handle empty states

## FILES TO KNOW
Dashboard key files:
- dashboard-view.tsx (765 lines) - Main bento grid layout
- premium-stat-card.tsx - Reusable stat cards
- productivity-charts.tsx - Recharts visualizations
- gamification-card.tsx - Achievement display
- workspace-preview-cards.tsx - Module navigation
- useDashboardSections.ts - Section order/collapse state

Shared styling:
- src/app/globals.css - Global styles
- src/app/custom-enhancements.css - Glass, depth, glow effects
- tailwind.config.ts - Tailwind configuration

BE AGGRESSIVE. WRITE BEAUTIFUL CODE. SHIP POLISHED UI."""

    return ClaudeSDKClient(
        options=ClaudeCodeOptions(
            model=model,
            system_prompt=system_prompt,
            allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
            max_turns=500,
            cwd=str(project_dir.resolve()),
            settings=str(settings_file.resolve()),
        )
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 🖥️ VISUAL OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

def setup_windows_utf8():
    """Enable UTF-8 output on Windows."""
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')


def print_banner():
    """Print startup banner."""
    print(f"""
{Style.MAGENTA}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}🎨 CONFIG-FRONTEND v1.0{Style.RESET}{Style.MAGENTA}                                          ║
║   {Style.DIM}Autonomous Frontend Developer + UI/UX Polish{Style.RESET}{Style.MAGENTA}                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def print_agent_header():
    """Print agent identification."""
    print(f"""
{Style.MAGENTA}┌──────────────────────────────────────────────────────────────────────┐{Style.RESET}
{Style.MAGENTA}│{Style.RESET} {FrontendEmoji.PALETTE} {Style.BOLD}CONFIG-FRONTEND{Style.RESET} - Frontend Developer & UI/UX Polish
{Style.MAGENTA}│{Style.RESET} {Style.DIM}Expertise: React 19, Next.js 16, Tailwind CSS 4, Framer Motion{Style.RESET}
{Style.MAGENTA}└──────────────────────────────────────────────────────────────────────┘{Style.RESET}
""")


def print_iteration_header(iteration: int, max_iterations: int, module: str, task_title: str):
    """Print iteration header."""
    max_str = "∞" if max_iterations == -1 else str(max_iterations)
    progress = "█" * iteration + "░" * (max(0, max_iterations - iteration) if max_iterations > 0 else 0)

    print(f"""
{Style.YELLOW}╭─────────────────────────────────────────────────────────────────────╮{Style.RESET}
{Style.YELLOW}│{Style.RESET} {Style.BOLD}🔄 ITERATION {iteration}/{max_str}{Style.RESET}  [{progress[:30]}]
{Style.YELLOW}│{Style.RESET} {Style.CYAN}📦 Module: {module.upper()}{Style.RESET}
{Style.YELLOW}│{Style.RESET} {Style.CYAN}📋 Task: {task_title[:50]}{Style.RESET}
{Style.YELLOW}╰─────────────────────────────────────────────────────────────────────╯{Style.RESET}
""")


def print_tool_use(tool_name: str, tool_input: dict = None):
    """Print tool usage."""
    tool_emojis = {
        "Read": "📖",
        "Write": "✍️",
        "Edit": "✏️",
        "Glob": "🔍",
        "Grep": "🔎",
        "Bash": "💻",
    }
    emoji = tool_emojis.get(tool_name, "🔧")

    detail = ""
    if tool_input:
        if "file_path" in tool_input:
            detail = f" → {Path(tool_input['file_path']).name}"
        elif "pattern" in tool_input:
            detail = f" → {tool_input['pattern'][:30]}..."
        elif "command" in tool_input:
            cmd = tool_input['command'][:50]
            detail = f" → {cmd}..."

    print(f"  {Style.BLUE}{emoji} {tool_name}{Style.DIM}{detail}{Style.RESET}")


def print_tool_result(is_error: bool, content: str = None):
    """Print tool result."""
    if is_error:
        print(f"     {Style.RED}❌ Error{Style.RESET}")
        if content:
            first_line = str(content).split('\n')[0][:60]
            print(f"     {Style.DIM}{first_line}{Style.RESET}")
    else:
        print(f"     {Style.GREEN}✅ Done{Style.RESET}")


def print_info(message: str):
    """Print info message."""
    print(f"  {FrontendEmoji.INFO} {Style.CYAN}{message}{Style.RESET}")


def print_warning(message: str):
    """Print warning message."""
    print(f"  {FrontendEmoji.WARNING} {Style.YELLOW}{message}{Style.RESET}")


def print_error(message: str):
    """Print error message."""
    print(f"  {FrontendEmoji.ERROR} {Style.RED}{message}{Style.RESET}")


def print_success(message: str):
    """Print success message."""
    print(f"  {FrontendEmoji.SUCCESS} {Style.GREEN}{message}{Style.RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# 📝 TASK MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def load_tasks() -> dict:
    """Load frontend_tasks.json configuration."""
    try:
        with open(FRONTEND_TASKS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load frontend_tasks.json: {e}")
        return {"tasks": [], "queue": {"pending": []}}


def save_tasks(tasks_config: dict):
    """Save frontend_tasks.json."""
    try:
        with open(FRONTEND_TASKS, "w", encoding="utf-8") as f:
            json.dump(tasks_config, f, indent=2)
    except Exception as e:
        print_error(f"Failed to save frontend_tasks.json: {e}")


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

    # Remove from all queues
    for q in ["pending", "in_progress", "completed", "failed"]:
        if task_id in queue.get(q, []):
            queue[q].remove(task_id)

    # Add to new queue
    if status not in queue:
        queue[status] = []
    queue[status].append(task_id)

    # Update task status
    for task in tasks_config.get("tasks", []):
        if task["id"] == task_id:
            task["status"] = status
            break

    tasks_config["queue"] = queue
    save_tasks(tasks_config)


# ═══════════════════════════════════════════════════════════════════════════════
# 📝 LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

def log_to_comms(event_type: str, details: dict):
    """Log to COMMS.md for agent coordination."""
    try:
        if not COMMS_MD.parent.exists():
            COMMS_MD.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = f"""
### {FrontendEmoji.PALETTE} CONFIG-FRONTEND - {timestamp}
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
# 🤖 AI SESSION
# ═══════════════════════════════════════════════════════════════════════════════

def build_task_prompt(task: dict, module: str) -> str:
    """Build comprehensive prompt from task definition."""
    parts = []

    # Header
    parts.append(f"# 🎨 FRONTEND TASK: {task.get('title', 'Unknown Task')}")
    parts.append(f"**ID:** {task.get('id', 'N/A')} | **Priority:** {task.get('priority', 'medium')} | **Module:** {module.upper()}")
    parts.append("")

    # Aggressive mindset
    parts.append("## ⚠️ EXECUTION MODE: SHIP IT")
    parts.append("- WRITE real code, not pseudocode")
    parts.append("- IMPLEMENT the feature completely")
    parts.append("- FIX any issues you encounter")
    parts.append("- VERIFY with TypeScript (npx tsc --noEmit)")
    parts.append("- DO NOT leave TODOs - finish the work")
    parts.append("")

    # Description
    desc = task.get("description", {})
    parts.append("## PROBLEM")
    parts.append(desc.get("problem", task.get("title", "No description")))
    parts.append("")
    parts.append("## GOAL")
    parts.append(desc.get("goal", "Improve the UI/UX"))
    parts.append("")
    parts.append("## SCOPE")
    parts.append(desc.get("scope", f"Focus on {module} module"))
    parts.append("")

    # Files
    files = task.get("files", {})
    if files.get("target"):
        parts.append("## TARGET FILES (modify these)")
        for f in files["target"]:
            parts.append(f"- `{f}`")
        parts.append("")

    if files.get("context"):
        parts.append("## CONTEXT FILES (read for understanding)")
        for f in files["context"]:
            parts.append(f"- `{f}`")
        parts.append("")

    # Acceptance criteria
    acceptance = task.get("acceptance_criteria", [])
    if acceptance:
        parts.append("## ACCEPTANCE CRITERIA")
        for ac in acceptance:
            parts.append(f"- {ac}")
        parts.append("")

    # Design specs
    design = task.get("design", {})
    if design:
        parts.append("## DESIGN SPECIFICATIONS")
        for key, value in design.items():
            parts.append(f"- **{key}**: {value}")
        parts.append("")

    # Verification
    verification = task.get("verification", {})
    if verification.get("commands"):
        parts.append("## VERIFICATION COMMANDS")
        for cmd in verification["commands"]:
            parts.append(f"```bash")
            parts.append(cmd)
            parts.append("```")
        parts.append("")

    # Workflow
    parts.append("## YOUR WORKFLOW")
    parts.append("1. Read target files to understand current state")
    parts.append("2. Read context files for patterns")
    parts.append("3. Plan your changes")
    parts.append("4. Implement using Edit tool")
    parts.append("5. Run: npx tsc --noEmit")
    parts.append("6. Fix any TypeScript errors")
    parts.append("7. Verify the UI looks good")
    parts.append("")

    parts.append("---")
    parts.append("**START NOW. READ FILES. WRITE CODE. SHIP BEAUTIFUL UI!**")

    return "\n".join(parts)


async def run_frontend_session(client, prompt: str, state: FrontendState) -> tuple[str, str, int]:
    """Run frontend AI session with visual output."""
    provider_label = getattr(client, "provider_label", "Claude AI")
    print(f"\n  {Style.CYAN}🤖 Invoking {provider_label}...{Style.RESET}")
    print(f"  {Style.DIM}Model: {FRONTEND_CONFIG['model']}{Style.RESET}\n")

    tokens_used = 0

    try:
        await client.query(prompt)

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

                        if '\n' in current_text_buffer:
                            lines = current_text_buffer.split('\n')
                            for line in lines[:-1]:
                                if line.strip():
                                    print(f"  {Style.WHITE}💭 {line[:100]}{Style.RESET}")
                            current_text_buffer = lines[-1]

                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        if current_text_buffer.strip():
                            print(f"  {Style.WHITE}💭 {current_text_buffer.strip()[:100]}{Style.RESET}")
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

            if hasattr(msg, "usage"):
                usage = msg.usage
                if hasattr(usage, "input_tokens"):
                    tokens_used += usage.input_tokens
                if hasattr(usage, "output_tokens"):
                    tokens_used += usage.output_tokens

        if current_text_buffer.strip():
            print(f"  {Style.WHITE}💭 {current_text_buffer.strip()[:100]}{Style.RESET}")

        print(f"\n  {Style.DIM}{'─' * 66}{Style.RESET}")
        print(f"  {Style.GREEN}✅ AI Session Complete{Style.RESET}")

        if tokens_used == 0:
            tokens_used = (len(prompt) + len(response_text)) // 4

        return "complete", response_text, tokens_used

    except Exception as e:
        print(f"  {Style.RED}❌ AI Session Error: {e}{Style.RESET}")
        return "error", str(e), 0


# ═══════════════════════════════════════════════════════════════════════════════
# 🔄 MAIN LOOP
# ═══════════════════════════════════════════════════════════════════════════════

async def frontend_loop(args):
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
    if max_iterations == -1:
        print_info(f"Mode: CONTINUOUS (Opus 4.5 runs every cycle)")
    else:
        print_info(f"Mode: LIMITED ({max_iterations} iterations)")
    print()

    # Log session start
    log_to_comms("session_start", {
        "module": args.module,
        "mode": "continuous" if max_iterations == -1 else f"limited_{max_iterations}",
        "max_iterations": max_iterations,
    })

    # Create log file
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"frontend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"🎨 CONFIG-FRONTEND Session Log\n")
        f.write(f"{'=' * 70}\n")
        f.write(f"Started: {datetime.now().isoformat()}\n")
        f.write(f"Model: {FRONTEND_CONFIG['model']}\n")
        f.write(f"Module: {args.module}\n")
        f.write(f"{'=' * 70}\n\n")

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
                    # Create ad-hoc exploration task
                    current_task = {
                        "id": f"EXPLORE-{iteration}",
                        "title": f"Explore and improve {args.module} module",
                        "module": args.module,
                        "priority": "medium",
                        "description": {
                            "problem": f"The {args.module} module may need UI/UX improvements",
                            "goal": f"Find and fix issues in {args.module}, improve animations, polish UI",
                            "scope": f"Focus on {args.module} components"
                        },
                        "files": {
                            "target": [f"src/modules/{args.module}/**/*.tsx"],
                            "context": ["src/app/globals.css", "src/app/custom-enhancements.css"]
                        },
                        "acceptance_criteria": [
                            "No TypeScript errors",
                            "Smooth animations",
                            "Consistent styling",
                            "Good loading states"
                        ],
                        "verification": {
                            "commands": ["npx tsc --noEmit"]
                        }
                    }

            state.current_task = current_task["id"]

            # Print iteration header
            print_iteration_header(iteration, max_iterations, args.module, current_task["title"])

            # ═══════════════════════════════════════════════════════════════
            # 📸 SCREENSHOT CAPTURE (if enabled)
            # ═══════════════════════════════════════════════════════════════
            screenshot_path = None
            if args.screenshot or args.visual_review:
                print(f"\n  {FrontendEmoji.CAMERA} {Style.CYAN}Capturing dashboard screenshot...{Style.RESET}")

                # Try to capture Tauri window first, fallback to fullscreen
                screenshot_path = capture_tauri_window_screenshot("Control Station")
                if not screenshot_path:
                    print(f"  {FrontendEmoji.WARNING} {Style.YELLOW}Tauri window not found, trying fullscreen...{Style.RESET}")
                    screenshot_path = capture_full_screen_screenshot()

                if screenshot_path:
                    print(f"  {FrontendEmoji.SUCCESS} {Style.GREEN}Screenshot saved: {screenshot_path.name}{Style.RESET}")
                    # Log screenshot
                    with open(log_file, "a", encoding="utf-8") as f:
                        f.write(f"\n📸 Screenshot captured: {screenshot_path}\n")
                else:
                    print(f"  {FrontendEmoji.WARNING} {Style.YELLOW}Screenshot capture failed - continuing without visual review{Style.RESET}")

            # Mark task in progress
            if current_task["id"] in tasks_config.get("queue", {}).get("pending", []):
                mark_task_status(tasks_config, current_task["id"], "in_progress")

            # Build prompt
            prompt = build_task_prompt(current_task, args.module)

            # Add visual review section if screenshot was captured
            if screenshot_path and screenshot_path.exists():
                visual_prompt = build_visual_review_prompt(screenshot_path)
                prompt = f"""{visual_prompt}

---

# AFTER VISUAL REVIEW, WORK ON THIS TASK:

{prompt}"""

            # Add continuation context
            if iteration > 1:
                prompt = f"""# 🎨 FRONTEND ITERATION {iteration} - KEEP POLISHING!

Continue improving the {args.module.upper()} module. Previous iteration made progress.

Your job now:
1. CHECK if previous changes are working
2. FIND remaining issues or opportunities
3. IMPLEMENT more improvements
4. VERIFY everything compiles

{prompt}

---
**KEEP GOING. MAKE IT BEAUTIFUL. SHIP POLISHED UI!**"""

            # Run AI session
            try:
                client = create_frontend_client(CONTROL_STATION, args.module)

                async with client:
                    ai_status, ai_response, tokens = await run_frontend_session(
                        client, prompt, state
                    )

                state.token_usage_today += tokens

                # Log to file
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n{'=' * 70}\n")
                    f.write(f"📍 ITERATION {iteration}\n")
                    f.write(f"Task: {current_task['id']}\n")
                    f.write(f"Tokens: {tokens}\n")
                    f.write(f"{'=' * 70}\n")
                    f.write(f"Response:\n{ai_response}\n")

                print(f"\n  🪙 Tokens this iteration: {Style.CYAN}{tokens:,}{Style.RESET}")
                print(f"  🪙 Total today: {Style.CYAN}{state.token_usage_today:,}{Style.RESET} / {TOKEN_BUDGET['daily_limit']:,}")

                if ai_status == "complete":
                    print_success(f"Iteration {iteration} complete")
                    if current_task["id"].startswith("EXPLORE-"):
                        pass  # Don't track exploration tasks
                    else:
                        mark_task_status(tasks_config, current_task["id"], "completed")
                        state.tasks_completed += 1
                else:
                    print_warning(f"Iteration {iteration} had issues")

                log_to_comms("iteration_complete", {
                    "iteration": iteration,
                    "task": current_task["id"],
                    "tokens": tokens,
                    "status": ai_status
                })

            except Exception as e:
                provider_label = "OpenCode CLI" if get_llm_provider() == "opencode" else "Claude AI"
                print_error(f"{provider_label} error: {e}")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n❌ ERROR in iteration {iteration}: {e}\n")

            if max_iterations != -1 and iteration >= max_iterations:
                break

            # 5 second delay between iterations
            print(f"\n  {Style.DIM}⏳ Next iteration in 5 seconds...{Style.RESET}")
            await asyncio.sleep(5)

    except KeyboardInterrupt:
        print(f"\n\n{FrontendEmoji.PALETTE} CONFIG-FRONTEND interrupted by user.")

    # Session complete
    print(f"""
{Style.GREEN}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}✅ FRONTEND SESSION COMPLETE{Style.RESET}{Style.GREEN}                                     ║
║                                                                      ║
║   🔄 Iterations: {state.iteration_count:<50}      ║
║   ✅ Tasks completed: {state.tasks_completed:<46}      ║
║   🪙 Tokens used: {state.token_usage_today:<49}      ║
║   📝 Log file: {log_file.name:<47}      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")

    log_to_comms("session_end", {
        "iterations": state.iteration_count,
        "tasks_completed": state.tasks_completed,
        "tokens_used": state.token_usage_today,
        "log_file": str(log_file)
    })


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="🎨 CONFIG-FRONTEND - Autonomous Frontend Developer Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_frontend_agent.py                         # Run single iteration on dashboard
    python run_frontend_agent.py -i 5                    # Run 5 iterations
    python run_frontend_agent.py --continuous            # Run forever
    python run_frontend_agent.py --screenshot            # Capture & analyze dashboard visually
    python run_frontend_agent.py --visual-review -i 3    # Visual review + 3 iterations
    python run_frontend_agent.py --module focusguardian  # Work on different module
    python run_frontend_agent.py --task FRONTEND-001     # Run specific task
        """
    )
    parser.add_argument("-i", "--iterations", type=int, default=1,
                        help="Maximum iterations to run (default: 1)")
    parser.add_argument("--module", type=str, default="dashboard",
                        choices=["dashboard", "focusguardian", "roadmap", "alarm", "gamification", "james"],
                        help="Module to focus on (default: dashboard)")
    parser.add_argument("--task", type=str, default=None,
                        help="Specific task ID to run")
    parser.add_argument("--continuous", action="store_true",
                        help="Run forever (daemon mode)")
    parser.add_argument("--screenshot", action="store_true",
                        help="Capture and analyze dashboard screenshots each iteration")
    parser.add_argument("--visual-review", action="store_true",
                        help="Start with visual review of current dashboard state")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done")
    return parser.parse_args()


def main():
    """Main entry point."""
    setup_windows_utf8()
    args = parse_args()

    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    print_banner()
    print_agent_header()

    if not FRONTEND_TASKS.exists():
        print_warning(f"frontend_tasks.json not found - will use exploration mode")

    if not CONTROL_STATION.exists():
        print_error(f"Control Station not found at {CONTROL_STATION}")
        sys.exit(1)

    print_info(f"Control Station: {CONTROL_STATION}")
    print_info(f"Module: {args.module}")
    print_info(f"Logs: {LOGS_DIR}")

    provider = get_llm_provider()
    if provider == "opencode":
        print(f"  {FrontendEmoji.SUCCESS} {Style.GREEN}OpenCode CLI: enabled{Style.RESET}")
        print(f"  {Style.DIM}Model: {FRONTEND_CONFIG['model']}{Style.RESET}")
        print(f"  {Style.DIM}Auth: run `opencode auth login` if needed{Style.RESET}")
    else:
        # Check Claude auth
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
        if api_key or oauth_token:
            auth_type = "API Key" if api_key else "OAuth Token"
            print(f"  {FrontendEmoji.SUCCESS} {Style.GREEN}Claude AI: {auth_type} configured{Style.RESET}")
            print(f"  {Style.DIM}Model: {FRONTEND_CONFIG['model']} (Opus 4.5){Style.RESET}")
        else:
            print_error("Claude AI: No auth configured")
            print(f"  {Style.DIM}Set CLAUDE_CODE_OAUTH_TOKEN in .env{Style.RESET}")
            sys.exit(1)

    if args.dry_run:
        print_info("Dry run mode - no actions will be taken")
        return

    try:
        asyncio.run(frontend_loop(args))
    except KeyboardInterrupt:
        print(f"\n\n{FrontendEmoji.PALETTE} CONFIG-FRONTEND interrupted by user.")
    except Exception as e:
        print_error(f"Fatal error: {e}")
        sys.exit(1)

    print(f"\n{FrontendEmoji.PALETTE} CONFIG-FRONTEND session complete.")


if __name__ == "__main__":
    main()
