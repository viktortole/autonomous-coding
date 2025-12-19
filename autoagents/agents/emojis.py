"""
Emoji Mappings for AUTOAGENTS
=============================

Centralized emoji definitions for consistent visual output.
"""

# Task priority levels
PRIORITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
}

# Task complexity levels
COMPLEXITY_EMOJI = {
    "hard": "🔥",
    "medium": "⚡",
    "easy": "✨",
}

# Task status
STATUS_EMOJI = {
    "pending": "⏳",
    "in_progress": "🔄",
    "completed": "✅",
    "failed": "❌",
}

# Tool usage icons
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

# SENTINEL-specific status
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

# Frontend agent icons
FRONTEND_EMOJI = {
    "palette": "🎨",
    "component": "🧩",
    "animation": "✨",
    "camera": "📸",
    "responsive": "📱",
    "accessibility": "♿",
}

# Module icons
MODULE_EMOJI = {
    "dashboard": "📊",
    "focusguardian": "🎯",
    "missions": "🚀",
    "roadmap": "🗺️",
    "auth": "🔐",
    "settings": "⚙️",
}


def get_priority_emoji(priority: str) -> str:
    """Get emoji for priority level."""
    return PRIORITY_EMOJI.get(priority.lower(), "⚪")


def get_complexity_emoji(complexity: str) -> str:
    """Get emoji for complexity level."""
    return COMPLEXITY_EMOJI.get(complexity.lower(), "⚡")


def get_status_emoji(status: str) -> str:
    """Get emoji for status."""
    return STATUS_EMOJI.get(status.lower(), "❓")


def get_tool_emoji(tool_name: str) -> str:
    """Get emoji for tool."""
    return TOOL_EMOJI.get(tool_name, "🔧")
