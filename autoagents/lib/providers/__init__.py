"""
LLM Provider Selection
======================

Supports Claude SDK (default) and OpenCode CLI (fallback).
"""

import os


def get_llm_provider() -> str:
    """
    Determine which LLM provider to use.

    Priority:
    1. CLAUDE_CODE_OAUTH_TOKEN -> "claude"
    2. ANTHROPIC_API_KEY -> "claude"
    3. OPENCODE_API_KEY -> "opencode"
    4. Default -> "claude"

    Returns:
        "claude" or "opencode"
    """
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return "claude"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    if os.environ.get("OPENCODE_API_KEY"):
        return "opencode"
    return "claude"


__all__ = ["get_llm_provider"]
