"""
LLM provider selection helpers.
"""

import os


def get_llm_provider() -> str:
    """
    Resolve which LLM provider to use.

    Supported values (case-insensitive):
    - claude (default)
    - opencode (alias: codex)
    """
    provider = os.environ.get("LLM_PROVIDER", "claude").strip().lower()
    if provider in {"opencode", "codex", "openai-codex"}:
        return "opencode"
    return "claude"
