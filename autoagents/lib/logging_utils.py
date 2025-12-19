"""
Logging Utilities
=================

Session logging and file management for AUTOAGENTS.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional


def create_session_log(
    logs_dir: Path,
    prefix: str,
    agent_name: str,
    model: str,
    extra_info: Optional[dict] = None
) -> Path:
    """
    Create a new session log file.

    Args:
        logs_dir: Directory for log files
        prefix: Log file prefix (e.g., "TASK-001", "sentinel")
        agent_name: Name of the agent
        model: Model being used
        extra_info: Additional metadata to log

    Returns:
        Path to the created log file
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"{prefix}_{timestamp}.log"

    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"🤖 {agent_name} Session Log\n")
        f.write(f"{'=' * 70}\n")
        f.write(f"Started: {datetime.now().isoformat()}\n")
        f.write(f"Model: {model}\n")
        if extra_info:
            for key, value in extra_info.items():
                f.write(f"{key}: {value}\n")
        f.write(f"{'=' * 70}\n\n")

    return log_file


def log_iteration(
    log_file: Path,
    iteration: int,
    max_iterations: int | str,
    response: str,
    tokens: int = 0,
    prompt: str = ""
):
    """
    Append iteration output to log file.

    Args:
        log_file: Path to the log file
        iteration: Current iteration number
        max_iterations: Total iterations (or "continuous")
        response: Agent's response text
        tokens: Tokens used in this iteration
        prompt: Prompt sent (optional, logged on first iteration)
    """
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 70}\n")
        f.write(f"📍 ITERATION {iteration}/{max_iterations}\n")
        f.write(f"Time: {datetime.now().isoformat()}\n")
        if tokens > 0:
            f.write(f"Tokens: {tokens}\n")
        f.write(f"{'=' * 70}\n")

        if prompt and iteration == 1:
            f.write(f"\nPROMPT:\n{prompt}\n")
            f.write(f"\n{'─' * 70}\n")

        f.write(f"\nResponse:\n{response}\n")


def log_completion(
    log_file: Path,
    status: str,
    total_iterations: int,
    total_tokens: int,
    summary: str = ""
):
    """
    Log session completion.

    Args:
        log_file: Path to the log file
        status: Final status (completed, failed, interrupted)
        total_iterations: Total iterations run
        total_tokens: Total tokens used
        summary: Optional summary message
    """
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 70}\n")
        f.write(f"SESSION COMPLETE\n")
        f.write(f"{'=' * 70}\n")
        f.write(f"Status: {status}\n")
        f.write(f"Total Iterations: {total_iterations}\n")
        f.write(f"Total Tokens: {total_tokens}\n")
        f.write(f"Ended: {datetime.now().isoformat()}\n")
        if summary:
            f.write(f"\nSummary:\n{summary}\n")


def get_log_path(logs_dir: Path, task_id: str) -> Path:
    """
    Get the most recent log file for a task.

    Args:
        logs_dir: Directory containing log files
        task_id: Task ID to search for

    Returns:
        Path to the most recent log file, or None if not found
    """
    pattern = f"{task_id}_*.log"
    log_files = sorted(logs_dir.glob(pattern), reverse=True)
    return log_files[0] if log_files else None
