"""
Claude SDK Client Creation
==========================

Universal client factory for creating Claude SDK clients with security settings.
"""

import json
import os
from pathlib import Path
from typing import Optional

from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient

from .providers import get_llm_provider


# Default tools available to agents
DEFAULT_TOOLS = ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]


def create_agent_client(
    project_dir: Path,
    model: str,
    system_prompt: str = "You are an expert developer. Think step by step and explain your reasoning.",
    allowed_tools: Optional[list[str]] = None,
    max_turns: int = 500,
    mcp_servers: Optional[dict] = None,
    hooks: Optional[dict] = None,
    settings_filename: str = ".claude_settings.json",
) -> ClaudeSDKClient:
    """
    Create a Claude SDK client with security settings.

    Args:
        project_dir: Working directory for the agent
        model: Claude model to use (e.g., "claude-sonnet-4-20250514")
        system_prompt: System prompt for the agent
        allowed_tools: List of allowed tools (default: Read, Write, Edit, Glob, Grep, Bash)
        max_turns: Maximum conversation turns
        mcp_servers: Optional MCP server configurations
        hooks: Optional security hooks (e.g., bash_security_hook)
        settings_filename: Name of the settings file to create

    Returns:
        Configured ClaudeSDKClient

    Raises:
        ValueError: If no authentication is configured
    """
    # Check for OpenCode fallback
    provider = get_llm_provider()
    if provider == "opencode":
        from .providers.opencode import OpenCodeClient
        return OpenCodeClient(project_dir=project_dir, model=model)

    # Validate auth
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")

    if not api_key and not oauth_token:
        raise ValueError(
            "No Claude auth configured. Set ANTHROPIC_API_KEY or CLAUDE_CODE_OAUTH_TOKEN in .env"
        )

    # Default tools
    if allowed_tools is None:
        allowed_tools = DEFAULT_TOOLS.copy()

    # Security settings - restrict file operations to project directory
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

    # Ensure project directory exists
    project_dir.mkdir(parents=True, exist_ok=True)

    # Write settings file
    settings_file = project_dir / settings_filename
    with open(settings_file, "w") as f:
        json.dump(security_settings, f, indent=2)

    # Build options
    options = ClaudeCodeOptions(
        model=model,
        system_prompt=system_prompt,
        allowed_tools=allowed_tools,
        max_turns=max_turns,
        cwd=str(project_dir.resolve()),
        settings=str(settings_file.resolve()),
    )

    # Add optional MCP servers
    if mcp_servers:
        options.mcp_servers = mcp_servers

    # Add optional hooks
    if hooks:
        options.hooks = hooks

    return ClaudeSDKClient(options=options)


def create_frontend_client(
    project_dir: Path,
    model: str = "claude-sonnet-4-20250514",
) -> ClaudeSDKClient:
    """Create a client configured for frontend development."""
    return create_agent_client(
        project_dir=project_dir,
        model=model,
        system_prompt=(
            "You are a senior frontend developer specializing in React 19, Next.js 16, "
            "TypeScript, and Tailwind CSS. Focus on clean, accessible, responsive UI/UX."
        ),
        settings_filename=".claude_frontend_settings.json",
    )


def create_sentinel_client(
    project_dir: Path,
    model: str = "claude-sonnet-4-20250514",
) -> ClaudeSDKClient:
    """Create a client configured for DevOps health monitoring."""
    return create_agent_client(
        project_dir=project_dir,
        model=model,
        system_prompt=(
            "You are SENTINEL-DEV, a DevOps guardian agent. Your role is to monitor "
            "dev environment health, diagnose issues, and perform safe automated repairs. "
            "Be BRUTALLY HONEST about problems. Never hide issues."
        ),
        settings_filename=".claude_sentinel_settings.json",
    )
