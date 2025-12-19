#!/usr/bin/env python3
"""
🤖 AUTOAGENTS - Agent Configuration & Visual Output Module
==========================================================

Reusable visual output components for all autonomous agents.
Import this module to get consistent formatting across all agents.

Usage:
    from agents.agent_config import Style, AgentVisuals, AGENTS
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import sys

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 STYLE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class Style:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'

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
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'


# ═══════════════════════════════════════════════════════════════════════════════
# 🤖 AGENT DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class AgentConfig:
    """Configuration for an autonomous agent."""
    id: str
    name: str
    model: str
    role: str
    expertise: list[str]
    emoji: str
    color: str
    personality: str


# Available agents
AGENTS = {
    "JARVIS1": AgentConfig(
        id="JARVIS1",
        name="JARVIS-1",
        model="claude-sonnet-4-20250514",
        role="Primary Development",
        expertise=["React Hooks", "TypeScript", "Component Architecture"],
        emoji="🔧",
        color=Style.CYAN,
        personality="Methodical, thorough, prefers simple solutions"
    ),
    "JARVIS2": AgentConfig(
        id="JARVIS2",
        name="JARVIS-2",
        model="claude-sonnet-4-20250514",
        role="Testing & QA",
        expertise=["Vitest", "Testing Library", "Coverage Analysis", "Bug Hunting"],
        emoji="🧪",
        color=Style.GREEN,
        personality="Skeptical, tests edge cases, questions assumptions"
    ),
    "JARVIS3": AgentConfig(
        id="JARVIS3",
        name="JARVIS-3",
        model="claude-sonnet-4-20250514",
        role="Backend & Integration",
        expertise=["Rust", "Axum", "SQLite", "API Design", "Performance"],
        emoji="⚙️",
        color=Style.YELLOW,
        personality="Performance-focused, thinks about scale"
    ),
    "JARVIS4": AgentConfig(
        id="JARVIS4",
        name="JARVIS-4",
        model="claude-sonnet-4-20250514",
        role="UI & Polish",
        expertise=["React", "CSS/Tailwind", "Animations", "UX", "Accessibility"],
        emoji="🎨",
        color=Style.MAGENTA,
        personality="Design-minded, user-focused, attention to detail"
    ),
    "CMDTV": AgentConfig(
        id="CMDTV",
        name="CMDTV",
        model="claude-opus-4-5-20250514",
        role="Orchestrator & Senior Review",
        expertise=["Architecture", "Code Review", "Complex Refactoring", "Visual Testing"],
        emoji="👁️",
        color=Style.RED,
        personality="Big-picture thinker, quality gatekeeper"
    ),
    "SENTINEL": AgentConfig(
        id="SENTINEL",
        name="SENTINEL-DEV",
        model="claude-sonnet-4-20250514",  # Sonnet 4 - OAuth compatible
        role="DevOps Guardian & Auto-Repair",
        expertise=[
            "Server Health Monitoring",
            "Build Pipeline Diagnosis",
            "Database Integrity",
            "Process Management",
            "Log Analysis",
            "Automated Recovery"
        ],
        emoji="🛡️",
        color=Style.RED,
        personality="Vigilant, proactive, fixes issues before escalation"
    ),
    "CONFIG_FRONTEND": AgentConfig(
        id="CONFIG_FRONTEND",
        name="CONFIG-FRONTEND",
        model="claude-sonnet-4-20250514",  # Sonnet 4 - OAuth compatible
        role="Frontend Developer & UI/UX Polish",
        expertise=[
            "React 19 Components",
            "Next.js 16 Pages & Layouts",
            "Tailwind CSS 4 Styling",
            "Framer Motion Animations",
            "Dashboard Design",
            "Responsive Design",
            "Accessibility (a11y)",
            "Performance Optimization",
            "Component Architecture",
            "Design Systems"
        ],
        emoji="🎨",
        color=Style.MAGENTA,
        personality="Design-obsessed, pixel-perfect, animation-savvy, user-focused"
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 EMOJI MAPPINGS
# ═══════════════════════════════════════════════════════════════════════════════

PRIORITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}

COMPLEXITY_EMOJI = {
    "hard": "🔥",
    "medium": "⚡",
    "easy": "✨",
}

STATUS_EMOJI = {
    "pending": "⏳",
    "in_progress": "🔄",
    "completed": "✅",
    "failed": "❌",
}

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

# SENTINEL-specific status emojis
SENTINEL_EMOJI = {
    "monitoring": "🔍",
    "healthy": "✅",
    "degraded": "⚠️",
    "error": "❌",
    "repairing": "🔧",
    "success": "✨",
    "escalating": "🚨",
    "waiting": "⏳",
    "shield": "🛡️",
    "idle": "😴",
    "active": "👁️",
}


# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 VISUAL OUTPUT CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class AgentVisuals:
    """Visual output helpers for agents."""

    @staticmethod
    def setup_windows_utf8():
        """Enable UTF-8 output on Windows."""
        if sys.platform == "win32":
            sys.stdout.reconfigure(encoding='utf-8')

    @staticmethod
    def banner(version: str = "2.1", subtitle: str = "Autonomous Coding with Claude Code SDK"):
        """Print the startup banner."""
        print(f"""
{Style.CYAN}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}🤖 AUTOAGENTS v{version}{Style.RESET}{Style.CYAN}                                               ║
║   {Style.DIM}{subtitle}{Style.RESET}{Style.CYAN}                         ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")

    @staticmethod
    def task_header(task: dict, model: str, max_iterations: int, project_dir: Path):
        """Print task information header."""
        priority = task.get("priority", "medium")
        complexity = task.get("complexity", "medium")
        priority_emoji = PRIORITY_EMOJI.get(priority, "⚪")
        complexity_emoji = COMPLEXITY_EMOJI.get(complexity, "⚡")

        print(f"""
{Style.MAGENTA}┌──────────────────────────────────────────────────────────────────────┐{Style.RESET}
{Style.MAGENTA}│{Style.RESET} {Style.BOLD}📋 TASK: {task['id']}{Style.RESET}
{Style.MAGENTA}│{Style.RESET} {Style.CYAN}{task['title']}{Style.RESET}
{Style.MAGENTA}├──────────────────────────────────────────────────────────────────────┤{Style.RESET}
{Style.MAGENTA}│{Style.RESET} {priority_emoji} Priority: {priority:<10} {complexity_emoji} Complexity: {complexity}
{Style.MAGENTA}│{Style.RESET} 🧠 Model: {model}
{Style.MAGENTA}│{Style.RESET} 🔄 Iterations: {max_iterations}
{Style.MAGENTA}│{Style.RESET} 📁 Project: {project_dir}
{Style.MAGENTA}└──────────────────────────────────────────────────────────────────────┘{Style.RESET}
""")

    @staticmethod
    def iteration_header(iteration: int, total: int):
        """Print iteration header with progress bar."""
        progress = "█" * iteration + "░" * (total - iteration)
        print(f"""
{Style.YELLOW}╭─────────────────────────────────────────────────────────────────────╮{Style.RESET}
{Style.YELLOW}│{Style.RESET} {Style.BOLD}🔄 ITERATION {iteration}/{total}{Style.RESET}  [{progress}]
{Style.YELLOW}╰─────────────────────────────────────────────────────────────────────╯{Style.RESET}
""")

    @staticmethod
    def tool_use(tool_name: str, detail: str = ""):
        """Print tool usage with emoji."""
        emoji = TOOL_EMOJI.get(tool_name, "🔧")
        detail_str = f" → {detail}" if detail else ""
        print(f"  {Style.BLUE}{emoji} {tool_name}{Style.DIM}{detail_str}{Style.RESET}")

    @staticmethod
    def tool_result(success: bool, error_msg: str = ""):
        """Print tool result."""
        if success:
            print(f"     {Style.GREEN}✅ Done{Style.RESET}")
        else:
            print(f"     {Style.RED}❌ Error{Style.RESET}")
            if error_msg:
                print(f"     {Style.DIM}{error_msg[:60]}{Style.RESET}")

    @staticmethod
    def thinking(text: str):
        """Print agent's thinking/reasoning."""
        if text.strip():
            print(f"  {Style.WHITE}💭 {text}{Style.RESET}")

    @staticmethod
    def info(text: str):
        """Print info message."""
        print(f"  {Style.CYAN}ℹ️ {text}{Style.RESET}")

    @staticmethod
    def warning(text: str):
        """Print warning message."""
        print(f"  {Style.YELLOW}⚠️ {text}{Style.RESET}")

    @staticmethod
    def error(text: str):
        """Print error message."""
        print(f"  {Style.RED}❌ {text}{Style.RESET}")

    @staticmethod
    def success(text: str):
        """Print success message."""
        print(f"  {Style.GREEN}✅ {text}{Style.RESET}")

    @staticmethod
    def queue_status(pending: int, in_progress: int, completed: int, failed: int):
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

    @staticmethod
    def success_banner(task_id: str, iterations: int):
        """Print success completion banner."""
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

    @staticmethod
    def failure_banner(task_id: str, reason: str = ""):
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

    @staticmethod
    def divider():
        """Print a divider line."""
        print(f"  {Style.DIM}{'─' * 66}{Style.RESET}")

    @staticmethod
    def agent_header(agent: AgentConfig):
        """Print agent identification header."""
        print(f"""
{agent.color}┌──────────────────────────────────────────────────────────────────────┐{Style.RESET}
{agent.color}│{Style.RESET} {agent.emoji} {Style.BOLD}{agent.name}{Style.RESET} - {agent.role}
{agent.color}│{Style.RESET} {Style.DIM}Expertise: {', '.join(agent.expertise)}{Style.RESET}
{agent.color}└──────────────────────────────────────────────────────────────────────┘{Style.RESET}
""")


# ═══════════════════════════════════════════════════════════════════════════════
# 🧪 TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Demo the visual components
    AgentVisuals.setup_windows_utf8()
    AgentVisuals.banner()

    # Show agent header
    agent = AGENTS["JARVIS1"]
    AgentVisuals.agent_header(agent)

    # Show sample task
    sample_task = {
        "id": "TASK-000",
        "title": "Sample Task for Demo",
        "priority": "critical",
        "complexity": "hard"
    }
    AgentVisuals.task_header(sample_task, "claude-sonnet-4-20250514", 5, Path("./demo"))

    # Show iteration
    AgentVisuals.iteration_header(2, 5)

    # Show tool usage
    AgentVisuals.thinking("I'll start by reading the file...")
    AgentVisuals.tool_use("Read", "component.tsx")
    AgentVisuals.tool_result(True)
    AgentVisuals.tool_use("Bash", "npm test")
    AgentVisuals.tool_result(False, "Test failed: assertion error")

    AgentVisuals.divider()

    # Show queue
    AgentVisuals.queue_status(5, 1, 0, 0)

    # Show success
    AgentVisuals.success_banner("TASK-000", 5)
