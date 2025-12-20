"""
Agent Registry & Factory
========================

Central registry for all 7 autonomous agents.
Provides agent configuration, instantiation, and discovery.

Agents:
- COMMANDER (👑) - Orchestrator via COMMS.md
- SENTINEL (🛡️) - DevOps health monitoring
- FRONTEND (🎨) - React/Next.js UI development
- BACKEND (⚙️) - Rust/Axum backend development
- ARCHITECT (🏛️) - Architecture and tech debt
- DEBUGGER (🔍) - Error investigation and fixing
- TESTER (🧪) - Testing and coverage
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ..lib.styles import Style


# Base directory for all agents
AGENTS_DIR = Path(__file__).parent


@dataclass
class AgentConfig:
    """
    Complete configuration for an autonomous agent.

    Loaded from config.json in each agent's folder.
    """

    id: str
    name: str
    version: str
    model: str
    emoji: str
    color: str
    color_ansi: str
    role: str
    personality: str
    expertise: list[str] = field(default_factory=list)
    token_budget: dict = field(default_factory=lambda: {
        "daily_limit": 10000,
        "per_task": 3000,
        "warning_threshold": 0.8
    })
    comms_section: str = ""
    allowed_tools: list[str] = field(default_factory=lambda: [
        "Read", "Write", "Edit", "Glob", "Grep", "Bash"
    ])
    forbidden_patterns: list[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.comms_section:
            self.comms_section = self.id


# The 7 Agents - Hardcoded defaults, can be overridden by config.json
AGENT_DEFAULTS = {
    "COMMANDER": {
        "id": "COMMANDER",
        "name": "Commander",
        "version": "1.0.0",
        "model": "claude-opus-4-5-20250514",
        "emoji": "👑",
        "color": "#FFD700",  # Gold
        "color_ansi": Style.YELLOW,
        "role": "Orchestrator - assigns tasks via COMMS.md, monitors agents",
        "personality": "Strategic, calm under pressure, big-picture thinker",
        "expertise": [
            "Task orchestration",
            "Agent coordination",
            "Priority management",
            "Conflict resolution",
            "Progress monitoring"
        ],
        "token_budget": {"daily_limit": 15000, "per_task": 5000, "warning_threshold": 0.8},
    },
    "SENTINEL": {
        "id": "SENTINEL",
        "name": "Sentinel",
        "version": "1.0.0",
        "model": "claude-sonnet-4-20250514",
        "emoji": "🛡️",
        "color": "#EF4444",  # Red
        "color_ansi": Style.RED,
        "role": "DevOps Guardian - health monitoring, auto-repair",
        "personality": "Vigilant, proactive, brutally honest about problems",
        "expertise": [
            "Server health monitoring",
            "Build pipeline diagnosis",
            "Database integrity",
            "Process management",
            "Log analysis",
            "Automated recovery"
        ],
        "token_budget": {"daily_limit": 10000, "per_task": 3000, "warning_threshold": 0.8},
    },
    "FRONTEND": {
        "id": "FRONTEND",
        "name": "Frontend",
        "version": "1.0.0",
        "model": "claude-sonnet-4-20250514",
        "emoji": "🎨",
        "color": "#A855F7",  # Magenta/Purple
        "color_ansi": Style.MAGENTA,
        "role": "Frontend Developer - React, Next.js, Tailwind, animations",
        "personality": "Design-obsessed, pixel-perfect, animation-savvy, user-focused",
        "expertise": [
            "React 19 Components",
            "Next.js 16 Pages & Layouts",
            "Tailwind CSS 4 Styling",
            "Framer Motion Animations",
            "Dashboard Design",
            "Responsive Design",
            "Accessibility (a11y)",
            "Component Architecture"
        ],
        "token_budget": {"daily_limit": 12000, "per_task": 4000, "warning_threshold": 0.8},
    },
    "BACKEND": {
        "id": "BACKEND",
        "name": "Backend",
        "version": "1.0.0",
        "model": "claude-sonnet-4-20250514",
        "emoji": "⚙️",
        "color": "#F59E0B",  # Amber
        "color_ansi": Style.YELLOW,
        "role": "Backend Developer - Rust, Axum, SQLite, Tauri commands",
        "personality": "Performance-focused, security-conscious, thinks about scale",
        "expertise": [
            "Rust programming",
            "Axum web framework",
            "SQLite databases",
            "Tauri 2.9 commands",
            "API design",
            "Data modeling",
            "Error handling",
            "Performance optimization"
        ],
        "token_budget": {"daily_limit": 12000, "per_task": 4000, "warning_threshold": 0.8},
    },
    "ARCHITECT": {
        "id": "ARCHITECT",
        "name": "Architect",
        "version": "1.0.0",
        "model": "claude-sonnet-4-20250514",
        "emoji": "🏛️",
        "color": "#3B82F6",  # Blue
        "color_ansi": Style.BLUE,
        "role": "Architect - folder structure, naming, tech debt, organization",
        "personality": "Methodical, organized, quality-focused, debt-averse",
        "expertise": [
            "Architecture design",
            "Folder organization",
            "Naming conventions",
            "Tech debt management",
            "Code consolidation",
            "Duplicate detection",
            "Conflict resolution",
            "Documentation standards"
        ],
        "token_budget": {"daily_limit": 8000, "per_task": 3000, "warning_threshold": 0.8},
    },
    "DEBUGGER": {
        "id": "DEBUGGER",
        "name": "Debugger",
        "version": "1.0.0",
        "model": "claude-sonnet-4-20250514",
        "emoji": "🔍",
        "color": "#F97316",  # Orange
        "color_ansi": Style.YELLOW,
        "role": "Debugger - error investigation, bug fixing, root cause analysis",
        "personality": "Curious, persistent, follows evidence, never guesses",
        "expertise": [
            "Error analysis",
            "Stack trace parsing",
            "Root cause investigation",
            "Bug reproduction",
            "Fix verification",
            "TypeScript errors",
            "Rust errors",
            "Runtime debugging"
        ],
        "token_budget": {"daily_limit": 10000, "per_task": 3000, "warning_threshold": 0.8},
    },
    "TESTER": {
        "id": "TESTER",
        "name": "Tester",
        "version": "1.0.0",
        "model": "claude-sonnet-4-20250514",
        "emoji": "🧪",
        "color": "#22C55E",  # Green
        "color_ansi": Style.GREEN,
        "role": "Tester - write tests, improve coverage, QA verification",
        "personality": "Skeptical, thorough, tests edge cases, questions assumptions",
        "expertise": [
            "Vitest testing",
            "React Testing Library",
            "Coverage analysis",
            "Test strategy",
            "Mocking & stubbing",
            "Integration tests",
            "E2E scenarios",
            "Bug hunting"
        ],
        "token_budget": {"daily_limit": 10000, "per_task": 3000, "warning_threshold": 0.8},
    },
}


def get_agent_dir(agent_id: str) -> Path:
    """
    Get the directory for an agent.

    Args:
        agent_id: Agent ID (e.g., "SENTINEL")

    Returns:
        Path to agent's folder
    """
    return AGENTS_DIR / agent_id.lower()


def get_agent_config(agent_id: str) -> AgentConfig:
    """
    Load agent configuration from config.json or use defaults.

    Args:
        agent_id: Agent ID (e.g., "SENTINEL")

    Returns:
        AgentConfig instance
    """
    agent_id = agent_id.upper()

    # Start with defaults
    if agent_id not in AGENT_DEFAULTS:
        raise ValueError(f"Unknown agent: {agent_id}. Valid: {list(AGENT_DEFAULTS.keys())}")

    config_data = AGENT_DEFAULTS[agent_id].copy()

    # Try to load config.json override
    config_file = get_agent_dir(agent_id) / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                file_config = json.load(f)
                config_data.update(file_config)
        except (json.JSONDecodeError, OSError):
            pass  # Use defaults on error

    return AgentConfig(**config_data)


def get_all_agents() -> dict[str, AgentConfig]:
    """
    Get configurations for all 7 agents.

    Returns:
        Dict of {agent_id: AgentConfig}
    """
    return {agent_id: get_agent_config(agent_id) for agent_id in AGENT_DEFAULTS}


def get_agent_by_role(role_keyword: str) -> Optional[AgentConfig]:
    """
    Find an agent by role keyword.

    Args:
        role_keyword: Keyword to search in role (case-insensitive)

    Returns:
        First matching AgentConfig, or None
    """
    role_lower = role_keyword.lower()
    for agent_id in AGENT_DEFAULTS:
        config = get_agent_config(agent_id)
        if role_lower in config.role.lower():
            return config
    return None


def get_agents_by_expertise(skill: str) -> list[AgentConfig]:
    """
    Find agents with a specific expertise.

    Args:
        skill: Skill to search for (case-insensitive)

    Returns:
        List of matching AgentConfigs
    """
    skill_lower = skill.lower()
    matches = []
    for agent_id in AGENT_DEFAULTS:
        config = get_agent_config(agent_id)
        for expertise in config.expertise:
            if skill_lower in expertise.lower():
                matches.append(config)
                break
    return matches


def list_agent_ids() -> list[str]:
    """Get list of all agent IDs."""
    return list(AGENT_DEFAULTS.keys())


def get_agent_system_prompt(agent_id: str) -> str:
    """
    Load agent's system prompt from prompts/system_prompt.md.

    Falls back to a generated prompt if file doesn't exist.

    Args:
        agent_id: Agent ID

    Returns:
        System prompt string
    """
    prompt_file = get_agent_dir(agent_id) / "prompts" / "system_prompt.md"

    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")

    # Generate default prompt from config
    config = get_agent_config(agent_id)
    return f"""# {config.emoji} {config.name} Agent

## Role
{config.role}

## Personality
{config.personality}

## Expertise
{chr(10).join(f"- {e}" for e in config.expertise)}

## Instructions
You are {config.name}, an autonomous coding agent. Your job is to complete tasks
assigned to you with precision and quality. Always:

1. Read files before modifying them
2. Update COMMS.md with your progress
3. Stay within your token budget
4. Document your changes
5. Verify your work compiles/passes tests

Be BRUTALLY HONEST about problems. Never hide issues.
"""


def get_agent_task_template(agent_id: str) -> str:
    """
    Load agent's task template from prompts/task_template.md.

    Args:
        agent_id: Agent ID

    Returns:
        Task template string (may contain {placeholders})
    """
    template_file = get_agent_dir(agent_id) / "prompts" / "task_template.md"

    if template_file.exists():
        return template_file.read_text(encoding="utf-8")

    # Default template
    return """# Task: {task_id}

## Problem
{problem}

## Goal
{goal}

## Files to Modify
{files}

## Verification
{verification}

---
Complete this task. Update COMMS.md with your progress.
"""


def print_agent_summary() -> None:
    """Print summary of all agents for CLI display."""
    from ..lib.output import print_divider

    print(f"\n{Style.CYAN}╔══════════════════════════════════════════════════════════════════════╗{Style.RESET}")
    print(f"{Style.CYAN}║{Style.RESET} {Style.BOLD}🤖 AUTONOMOUS AGENTS REGISTRY{Style.RESET}")
    print(f"{Style.CYAN}╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}\n")

    for agent_id, defaults in AGENT_DEFAULTS.items():
        config = get_agent_config(agent_id)
        daily = config.token_budget.get("daily_limit", 0)
        print(f"  {config.emoji} {Style.BOLD}{config.id:12}{Style.RESET} │ {config.role[:45]}")
        print(f"     {Style.DIM}Model: {config.model} │ Budget: {daily:,}/day{Style.RESET}")
        print_divider()


def save_agent_config(agent_id: str, config: AgentConfig) -> None:
    """
    Save agent configuration to config.json.

    Args:
        agent_id: Agent ID
        config: Configuration to save
    """
    agent_dir = get_agent_dir(agent_id)
    agent_dir.mkdir(parents=True, exist_ok=True)

    config_file = agent_dir / "config.json"
    config_data = {
        "id": config.id,
        "name": config.name,
        "version": config.version,
        "model": config.model,
        "emoji": config.emoji,
        "color": config.color,
        "color_ansi": config.color_ansi,
        "role": config.role,
        "personality": config.personality,
        "expertise": config.expertise,
        "token_budget": config.token_budget,
        "comms_section": config.comms_section,
        "allowed_tools": config.allowed_tools,
        "forbidden_patterns": config.forbidden_patterns,
    }

    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)


def ensure_agent_folders() -> dict[str, bool]:
    """
    Ensure all 7 agent folders exist with required structure.

    Creates: __init__.py, prompts/, tasks.json if missing.

    Returns:
        Dict of {agent_id: created_new}
    """
    results = {}

    for agent_id in AGENT_DEFAULTS:
        agent_dir = get_agent_dir(agent_id)
        created = not agent_dir.exists()

        # Create folder structure
        agent_dir.mkdir(parents=True, exist_ok=True)
        (agent_dir / "prompts").mkdir(exist_ok=True)

        # Create __init__.py if missing
        init_file = agent_dir / "__init__.py"
        if not init_file.exists():
            init_file.write_text(f'"""Agent: {agent_id}"""\n')

        # Create empty tasks.json if missing
        tasks_file = agent_dir / "tasks.json"
        if not tasks_file.exists():
            tasks_file.write_text('{"tasks": []}\n')

        # Create config.json if missing
        config_file = agent_dir / "config.json"
        if not config_file.exists():
            save_agent_config(agent_id, get_agent_config(agent_id))

        results[agent_id] = created

    return results
