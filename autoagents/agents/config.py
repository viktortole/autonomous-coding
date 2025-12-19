"""
Agent Configuration
===================

Definitions for all autonomous coding agents.
"""

from dataclasses import dataclass
from typing import Optional

from ..lib.styles import Style


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
        model="claude-sonnet-4-20250514",
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
        model="claude-sonnet-4-20250514",
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


def get_agent(agent_id: str) -> Optional[AgentConfig]:
    """
    Get an agent by ID.

    Args:
        agent_id: The agent ID (e.g., "JARVIS1", "SENTINEL")

    Returns:
        AgentConfig or None if not found
    """
    return AGENTS.get(agent_id.upper())


def list_agents() -> list[AgentConfig]:
    """Get all available agents."""
    return list(AGENTS.values())


def get_agent_by_role(role: str) -> Optional[AgentConfig]:
    """
    Find an agent by role keyword.

    Args:
        role: Role keyword to search for (case-insensitive)

    Returns:
        First matching AgentConfig or None
    """
    role_lower = role.lower()
    for agent in AGENTS.values():
        if role_lower in agent.role.lower():
            return agent
    return None
