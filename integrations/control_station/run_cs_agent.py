#!/usr/bin/env python3
"""
Control Station Agent Runner
=============================

This script is invoked by Control Station's Tauri backend (agent_manager.rs)
to spawn autonomous coding agents using the Claude Code SDK.

Interface matches what agent_manager.rs expects:
    python run_cs_agent.py --iterations N --model MODEL

The task description comes via stdin (first line).

Part of AUTOAGENTS - Control Station Integration
"""

import argparse
import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Ensure repo root is in path for imports
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv

# Load environment variables
load_dotenv(REPO_ROOT / ".env")

try:
    from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient
except ImportError:
    print("ERROR: claude_code_sdk not installed. Run: pip install claude-code-sdk>=0.0.25", file=sys.stderr)
    sys.exit(1)


# ============================================================================
# CONFIGURATION
# ============================================================================

from autoagents.lib.workspace import resolve_workspace

# Project root (autonomous-coding repo)
PROJECT_ROOT = REPO_ROOT

# Agent working directory
WORKING_DIR = PROJECT_ROOT

# Workspace-resolved log directory
WORKSPACE = resolve_workspace()
LOGS_DIR = WORKSPACE.logs_dir
LOGS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================================
# VISUAL OUTPUT
# ============================================================================

class Style:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'


def emit(message: str, emoji: str = ""):
    """Emit a message (sent to Tauri via stdout)."""
    prefix = f"{emoji} " if emoji else ""
    print(f"{prefix}{message}", flush=True)


def emit_status(status: str, details: str = ""):
    """Emit a status update."""
    detail_str = f" - {details}" if details else ""
    print(f"[STATUS] {status}{detail_str}", flush=True)


def emit_tool(tool_name: str, detail: str = ""):
    """Emit tool usage."""
    tool_emoji = {
        "Read": "📖",
        "Write": "✍️",
        "Edit": "✏️",
        "Glob": "🔍",
        "Grep": "🔎",
        "Bash": "💻",
        "Task": "🚀",
    }.get(tool_name, "🔧")
    detail_str = f" → {detail}" if detail else ""
    print(f"  {tool_emoji} {tool_name}{detail_str}", flush=True)


def emit_thinking(text: str):
    """Emit agent thinking/reasoning."""
    if text.strip():
        # Truncate long thoughts
        display_text = text[:200] + "..." if len(text) > 200 else text
        print(f"  💭 {display_text}", flush=True)


def emit_error(message: str):
    """Emit an error."""
    print(f"  ❌ ERROR: {message}", flush=True)


def emit_success(message: str):
    """Emit success."""
    print(f"  ✅ {message}", flush=True)


# ============================================================================
# AGENT SESSION
# ============================================================================

async def run_agent_session(task_prompt: str, model: str, max_iterations: int):
    """Run an agent session with the given prompt."""

    emit_status("Starting", f"Model: {model}, Iterations: {max_iterations}")

    # Create client with options
    options = ClaudeCodeOptions(
        max_turns=max_iterations,
        model=model,
        allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash", "Task"],
        cwd=str(WORKING_DIR),
    )

    iteration = 0
    total_tokens = 0

    async with ClaudeSDKClient(options) as client:
        emit_status("Connected", "Claude Code SDK ready")

        # Send the task prompt
        emit_status("Sending", "Task prompt to agent")
        await client.query(task_prompt)

        # Process responses
        async for message in client.receive_response():
            msg_type = type(message).__name__

            if msg_type == "AssistantMessage":
                iteration += 1
                emit_status("Iteration", f"{iteration}/{max_iterations}")

                for block in message.content:
                    block_type = type(block).__name__

                    if block_type == "TextBlock":
                        # Agent is thinking/responding
                        emit_thinking(block.text[:300] if hasattr(block, 'text') else "")

                    elif block_type == "ToolUseBlock":
                        # Agent is using a tool
                        tool_name = getattr(block, 'name', 'Unknown')
                        tool_input = getattr(block, 'input', {})

                        # Extract relevant detail from input
                        detail = ""
                        if isinstance(tool_input, dict):
                            if 'file_path' in tool_input:
                                detail = Path(tool_input['file_path']).name
                            elif 'pattern' in tool_input:
                                detail = tool_input['pattern'][:50]
                            elif 'command' in tool_input:
                                detail = tool_input['command'][:50]

                        emit_tool(tool_name, detail)

            elif msg_type == "ToolResultMessage":
                # Tool completed
                is_error = getattr(message, 'is_error', False)
                if is_error:
                    emit_error("Tool execution failed")
                else:
                    print("     ✅ Done", flush=True)

            elif msg_type == "SystemMessage":
                # System message (session info)
                pass

            # Track token usage if available
            if hasattr(message, 'usage'):
                usage = message.usage
                if hasattr(usage, 'output_tokens'):
                    total_tokens += usage.output_tokens

    emit_status("Completed", f"Total iterations: {iteration}, Tokens: {total_tokens}")
    return iteration, total_tokens


# ============================================================================
# MAIN
# ============================================================================

def create_log_file(task_description: str) -> Path:
    """Create a log file for this session."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize task description for filename
    safe_name = "".join(c if c.isalnum() or c in "- " else "_" for c in task_description[:30])
    log_file = LOGS_DIR / f"cs_agent_{timestamp}_{safe_name}.log"
    return log_file


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Control Station Agent Runner")
    parser.add_argument("--iterations", type=int, default=5, help="Maximum iterations")
    parser.add_argument("--model", type=str, default="claude-sonnet-4-20250514", help="Model to use")
    parser.add_argument("--task", type=str, default="", help="Task description for the agent")
    args = parser.parse_args()

    # Configure stdout for UTF-8 (Windows compatibility)
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    # Print startup banner
    print(f"""
{Style.CYAN}╔══════════════════════════════════════════════════════════════════════╗
║  🤖 Control Station Agent - Claude Code SDK                          ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""", flush=True)

    emit_status("Initializing", f"Model: {args.model}")
    emit_status("WorkingDir", str(WORKING_DIR))

    # Build task prompt from CLI argument
    try:
        if args.task:
            # Task provided via CLI from Tauri backend
            task_prompt = f"""# AUTONOMOUS CODING AGENT

You are an autonomous coding agent for Control Station.

## PROJECT
- **Path:** {WORKING_DIR}
- **Stack:** Next.js 16, React 19, TypeScript, Tauri 2.9, Rust, SQLite

## YOUR TASK
{args.task}

## RULES
1. Read files before modifying them
2. Run `npx tsc --noEmit` to check for TypeScript errors
3. Run `npm run build` to verify builds pass
4. Fix issues incrementally - one at a time
5. Report what you find and fix

BEGIN WORK.
"""
            emit_status("Task", args.task[:60] + "..." if len(args.task) > 60 else args.task)
        else:
            # No task provided - use default analysis task
            task_prompt = f"""# AUTONOMOUS CODING AGENT

You are an autonomous coding agent for Control Station.

## PROJECT
- **Path:** {WORKING_DIR}
- **Stack:** Next.js 16, React 19, TypeScript, Tauri 2.9, Rust, SQLite

## YOUR TASK
Analyze the current state of the project and look for any TypeScript errors,
broken tests, or issues that need attention. Fix any critical issues you find.

## RULES
1. Read files before modifying them
2. Run `npx tsc --noEmit` to check for TypeScript errors
3. Run `npm run build` to verify builds pass
4. Fix issues incrementally - one at a time
5. Report what you find and fix

BEGIN WORK.
"""
            emit_status("Task", "Default: Autonomous code analysis and fixes")

        # Run the agent
        iterations, tokens = await run_agent_session(
            task_prompt=task_prompt,
            model=args.model,
            max_iterations=args.iterations
        )

        # Success banner
        print(f"""
{Style.GREEN}╔══════════════════════════════════════════════════════════════════════╗
║  ✅ AGENT SESSION COMPLETED                                          ║
╠══════════════════════════════════════════════════════════════════════╣
║  Iterations: {iterations:<5}  |  Tokens: {tokens:<10}                        ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""", flush=True)

    except KeyboardInterrupt:
        emit_status("Interrupted", "Agent stopped by user")
        sys.exit(130)
    except Exception as e:
        emit_error(f"Agent failed: {e}")
        print(f"""
{Style.RED}╔══════════════════════════════════════════════════════════════════════╗
║  ❌ AGENT SESSION FAILED                                             ║
╠══════════════════════════════════════════════════════════════════════╣
║  Error: {str(e)[:60]:<60} ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""", flush=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
