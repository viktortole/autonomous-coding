"""
AI Response Streaming
=====================

Utilities for streaming and displaying AI responses from Claude SDK.
"""

from typing import Callable, Optional

from .styles import Style
from .output import print_tool_use, print_tool_result, print_thinking


async def stream_agent_response(
    client,
    prompt: str,
    on_thinking: Optional[Callable[[str], None]] = None,
    on_tool_use: Optional[Callable[[str, dict], None]] = None,
    on_tool_result: Optional[Callable[[bool, str], None]] = None,
) -> tuple[str, str, int]:
    """
    Run an agent session and stream responses with visual output.

    Args:
        client: Claude SDK client (must support query() and receive_response())
        prompt: The prompt to send
        on_thinking: Optional callback for thinking text (defaults to print_thinking)
        on_tool_use: Optional callback for tool use (defaults to print_tool_use)
        on_tool_result: Optional callback for tool results (defaults to print_tool_result)

    Returns:
        Tuple of (status, response_text, tokens_used)
        status: "complete" or "error"
        response_text: Full response text
        tokens_used: Estimated token count
    """
    # Default callbacks
    if on_thinking is None:
        on_thinking = lambda text: print_thinking(text) if text.strip() else None
    if on_tool_use is None:
        on_tool_use = print_tool_use
    if on_tool_result is None:
        on_tool_result = print_tool_result

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

                        # Stream thinking as lines complete
                        if '\n' in current_text_buffer:
                            lines = current_text_buffer.split('\n')
                            for line in lines[:-1]:
                                if line.strip():
                                    on_thinking(line)
                            current_text_buffer = lines[-1]

                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        # Flush text buffer before tool use
                        if current_text_buffer.strip():
                            on_thinking(current_text_buffer.strip())
                            current_text_buffer = ""

                        tool_input = getattr(block, "input", {})
                        on_tool_use(block.name, tool_input)

            elif msg_type == "UserMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__
                    if block_type == "ToolResultBlock":
                        is_error = getattr(block, "is_error", False)
                        content = getattr(block, "content", "")
                        on_tool_result(is_error, content)

            # Track token usage if available
            if hasattr(msg, "usage"):
                usage = msg.usage
                tokens_used += getattr(usage, "input_tokens", 0)
                tokens_used += getattr(usage, "output_tokens", 0)

        # Flush remaining text
        if current_text_buffer.strip():
            on_thinking(current_text_buffer.strip())

        # Estimate tokens if not provided
        if tokens_used == 0:
            tokens_used = (len(prompt) + len(response_text)) // 4

        print(f"\n  {Style.DIM}{'─' * 66}{Style.RESET}\n")
        return "complete", response_text, tokens_used

    except Exception as e:
        print(f"  {Style.RED}❌ AI Session Error: {e}{Style.RESET}")
        return "error", str(e), 0


async def run_single_query(client, prompt: str) -> tuple[str, str]:
    """
    Simplified query - returns just status and response.

    Args:
        client: Claude SDK client
        prompt: The prompt to send

    Returns:
        Tuple of (status, response_text)
    """
    status, response, _ = await stream_agent_response(client, prompt)
    return status, response


class QuietStreamHandler:
    """Stream handler that doesn't print output (for background tasks)."""

    def __init__(self):
        self.thinking_buffer = []
        self.tool_uses = []
        self.tool_results = []

    def on_thinking(self, text: str):
        self.thinking_buffer.append(text)

    def on_tool_use(self, tool_name: str, tool_input: dict):
        self.tool_uses.append({"name": tool_name, "input": tool_input})

    def on_tool_result(self, is_error: bool, content: str):
        self.tool_results.append({"is_error": is_error, "content": content})

    async def stream(self, client, prompt: str) -> tuple[str, str, int]:
        """Stream with quiet output."""
        return await stream_agent_response(
            client,
            prompt,
            on_thinking=self.on_thinking,
            on_tool_use=self.on_tool_use,
            on_tool_result=self.on_tool_result,
        )
