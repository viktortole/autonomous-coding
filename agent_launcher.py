#!/usr/bin/env python3
"""
AUTOAGENTS v2.0 - Autonomous Agent Launcher
Deploys Claude Code agents based on feature_list.json v3.0 tasks.

Usage:
    python agent_launcher.py                    # Run all pending tasks
    python agent_launcher.py -i 5               # Run with 5 iterations per task
    python agent_launcher.py --task TASK-001    # Run specific task
    python agent_launcher.py --list             # List all tasks
    python agent_launcher.py --status           # Show queue status
    python agent_launcher.py --dry-run          # Preview without executing
"""

import json
import subprocess
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

# Paths - uses feature_list.json in same directory as this script
SCRIPT_DIR = Path(__file__).parent
FEATURE_LIST = SCRIPT_DIR / "feature_list.json"
LOGS_DIR = SCRIPT_DIR / "logs"
ENV_FILE = SCRIPT_DIR / ".env"


def load_env_file() -> dict:
    """Load environment variables from .env file."""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'


def log(msg: str, color: str = ""):
    """Print colored log message."""
    print(f"{color}{msg}{Colors.END}" if color else msg)


def load_feature_list() -> dict:
    """Load the feature_list.json file."""
    log(f"[INFO] Loading: {FEATURE_LIST}", Colors.CYAN)
    if not FEATURE_LIST.exists():
        log(f"[ERROR] feature_list.json not found at {FEATURE_LIST}", Colors.RED)
        sys.exit(1)
    with open(FEATURE_LIST, "r", encoding="utf-8") as f:
        data = json.load(f)
    log(f"[OK] Loaded {len(data.get('tasks', []))} tasks", Colors.GREEN)
    return data


def save_feature_list(data: dict) -> None:
    """Save updated feature_list.json."""
    with open(FEATURE_LIST, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    log(f"[OK] Updated feature_list.json", Colors.GREEN)


def get_task_by_id(data: dict, task_id: str) -> Optional[dict]:
    """Find a task by its ID."""
    for task in data.get("tasks", []):
        if task["id"] == task_id:
            return task
    return None


def update_task_status(data: dict, task_id: str, status: str) -> None:
    """Update task status in feature_list.json."""
    for task in data.get("tasks", []):
        if task["id"] == task_id:
            task["status"] = status
            task["last_updated"] = datetime.now().isoformat()
            break

    # Update queue
    queue = data.get("queue", {})
    for q in ["pending", "in_progress", "completed", "failed"]:
        if task_id in queue.get(q, []):
            queue[q].remove(task_id)

    if status in queue:
        queue[status].append(task_id)

    save_feature_list(data)


def build_claude_prompt(task: dict, agent_config: dict, project: dict, global_rules: dict) -> str:
    """
    Build a comprehensive prompt from v3.0 task structure.
    This extracts ALL useful information to give Claude maximum context.
    """
    parts = []

    # Header
    parts.append(f"# TASK: {task['title']}")
    parts.append(f"**ID:** {task['id']} | **Agent:** {task['agent']} | **Priority:** {task.get('priority', 'medium')} | **Complexity:** {task.get('complexity', 'medium')}")
    parts.append("")

    # Agent mode
    parts.append(f"## AGENT MODE: {agent_config.get('mode', 'ULTRATHINK')}")
    parts.append(f"Role: {agent_config.get('role', 'Developer')}")
    parts.append(f"Expertise: {', '.join(agent_config.get('expertise', []))}")
    parts.append("")

    # Description
    desc = task.get("description", {})
    parts.append("## PROBLEM")
    parts.append(desc.get("problem", "No problem description"))
    parts.append("")
    parts.append("## GOAL")
    parts.append(desc.get("goal", "No goal description"))
    parts.append("")
    parts.append("## SCOPE")
    parts.append(desc.get("scope", "No scope defined"))
    if desc.get("user_impact"):
        parts.append(f"\n**User Impact:** {desc['user_impact']}")
    parts.append("")

    # Thinking prompts
    if task.get("thinking_prompts"):
        parts.append("## THINK ABOUT THESE FIRST")
        for prompt in task["thinking_prompts"]:
            parts.append(f"- {prompt}")
        parts.append("")

    # Files
    files = task.get("files", {})
    if files:
        parts.append("## FILES")
        if files.get("target"):
            parts.append("**TARGET (modify these):**")
            for f in files["target"]:
                parts.append(f"  - {f}")
        if files.get("context"):
            parts.append("**CONTEXT (read for understanding):**")
            for f in files["context"]:
                parts.append(f"  - {f}")
        if files.get("tests"):
            parts.append("**TESTS:**")
            for f in files["tests"]:
                parts.append(f"  - {f}")
        if files.get("forbidden"):
            parts.append("**FORBIDDEN (never touch):**")
            for f in files["forbidden"]:
                parts.append(f"  - {f}")
        parts.append("")

    # Knowledge
    knowledge = task.get("knowledge", {})
    if knowledge:
        parts.append("## KNOWLEDGE")
        if knowledge.get("gold_standard"):
            gs = knowledge["gold_standard"]
            parts.append(f"**Gold Standard:** {gs.get('file', 'N/A')}")
            parts.append(f"  Learn: {gs.get('learn', 'N/A')}")
        if knowledge.get("patterns_to_follow"):
            parts.append("**DO THIS:**")
            for p in knowledge["patterns_to_follow"]:
                parts.append(f"  [OK] {p}")
        if knowledge.get("anti_patterns"):
            parts.append("**DON'T DO THIS:**")
            for p in knowledge["anti_patterns"]:
                parts.append(f"  [NO] {p}")
        if knowledge.get("code_example"):
            ex = knowledge["code_example"]
            parts.append(f"\n**Code Example ({ex.get('description', 'Example')}):**")
            parts.append("```")
            parts.append(ex.get("code", ""))
            parts.append("```")
        parts.append("")

    # Verification
    verification = task.get("verification", {})
    if verification:
        parts.append("## VERIFICATION")
        if verification.get("commands"):
            parts.append("**Run these commands:**")
            for cmd in verification["commands"]:
                parts.append(f"  $ {cmd}")
        if verification.get("success_criteria"):
            parts.append("**Success Criteria:**")
            for c in verification["success_criteria"]:
                parts.append(f"  - {c}")
        parts.append("")

    # Intelligence
    intel = task.get("intelligence", {})
    if intel:
        parts.append("## INTELLIGENCE")
        if intel.get("notes"):
            parts.append(f"**Notes:** {intel['notes']}")
        if intel.get("known_issues"):
            parts.append("**Known Issues:**")
            for issue in intel["known_issues"]:
                parts.append(f"  [!] {issue}")
        if intel.get("tips"):
            parts.append("**Tips:**")
            for tip in intel["tips"]:
                parts.append(f"  [TIP] {tip}")
        parts.append("")

    # Quality Rubric
    rubric = task.get("quality_rubric", {})
    if rubric:
        parts.append("## QUALITY RUBRIC (self-assess before completing)")
        for key, value in rubric.items():
            parts.append(f"  - {key}: {value}")
        parts.append("")

    # Project context
    parts.append("## PROJECT CONTEXT")
    parts.append(f"**Project:** {project.get('name', 'Unknown')}")
    parts.append(f"**Stack:** {', '.join(project.get('stack', []))}")
    parts.append(f"**Root:** {project.get('root', 'Unknown')}")
    parts.append("")

    # Global rules reminder
    parts.append("## GLOBAL RULES")
    parts.append("**Required before completion:**")
    for rule in global_rules.get("required_before_completion", []):
        parts.append(f"  - {rule}")
    parts.append("")

    # Final instruction
    parts.append("---")
    parts.append("**BEGIN WORK. Read all context files first. ULTRATHINK. Execute with precision.**")

    return "\n".join(parts)


def run_claude_agent(
    task: dict,
    project: dict,
    agents: dict,
    global_rules: dict,
    iterations: int = 1,
    dry_run: bool = False
) -> bool:
    """
    Run Claude Code CLI for a specific task.
    """
    task_id = task["id"]
    agent_name = task.get("agent", "JARVIS1")
    agent_config = agents.get(agent_name, {})
    model = agent_config.get("model", "claude-sonnet-4-20250514")
    working_dir = project.get("root", os.getcwd())

    # Use Claude Code's built-in OAuth (from Claude Max subscription)
    # Don't override with API key - let Claude Code use its stored session
    subprocess_env = os.environ.copy()

    # Remove any ANTHROPIC_API_KEY that might interfere with OAuth
    if "ANTHROPIC_API_KEY" in subprocess_env:
        del subprocess_env["ANTHROPIC_API_KEY"]

    log(f"[OK] Using Claude Code's built-in OAuth (Claude Max)", Colors.GREEN)

    # Build the comprehensive prompt
    prompt = build_claude_prompt(task, agent_config, project, global_rules)

    # Ensure logs directory exists
    LOGS_DIR.mkdir(exist_ok=True)
    log_file = LOGS_DIR / f"{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    log(f"\n{'='*70}", Colors.HEADER)
    log(f"  AUTOAGENTS - Deploying {agent_name} for {task_id}", Colors.BOLD)
    log(f"{'='*70}", Colors.HEADER)
    log(f"  Title:      {task['title']}", Colors.CYAN)
    log(f"  Model:      {model}", Colors.CYAN)
    log(f"  Iterations: {iterations}", Colors.CYAN)
    log(f"  Complexity: {task.get('complexity', 'medium')}", Colors.CYAN)
    log(f"  Working:    {working_dir}", Colors.CYAN)
    log(f"  Log:        {log_file}", Colors.CYAN)
    log(f"{'='*70}\n", Colors.HEADER)

    # Save full prompt to log
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"TASK: {task_id} - {task['title']}\n")
        f.write(f"Started: {datetime.now().isoformat()}\n")
        f.write(f"Agent: {agent_name} | Model: {model}\n")
        f.write(f"{'='*70}\n\n")
        f.write("FULL PROMPT:\n")
        f.write(prompt)
        f.write(f"\n\n{'='*70}\n\n")

    for i in range(iterations):
        log(f"[Iteration {i+1}/{iterations}]", Colors.YELLOW)

        # Build claude command
        if i == 0:
            current_prompt = prompt
        else:
            current_prompt = f"""Continue working on {task_id}: {task['title']}

This is iteration {i+1} of {iterations}.

## ITERATION FOCUS
- Iteration 1: Make it work (core functionality)
- Iteration 2: Make it right (edge cases, error handling)
- Iteration 3+: Make it fast (optimization, polish)

## CHECKLIST
1. Review what was done in previous iteration
2. Run verification commands to check current state
3. Address any remaining issues
4. Self-assess against quality rubric
5. If complete, summarize changes made

**Continue improving. ULTRATHINK.**"""

        # Claude Code CLI: claude -p "prompt" (positional arg, -p means print mode)
        cmd = [
            "claude",
            "--model", model,
            "-p",  # Print mode (non-interactive)
            current_prompt  # Prompt as positional argument
        ]

        if dry_run:
            log(f"[DRY RUN] Would execute in: {working_dir}", Colors.YELLOW)
            log(f"[DRY RUN] Command: claude --model {model} --print -p '...'", Colors.YELLOW)
            log(f"\n[DRY RUN] Prompt preview ({len(prompt)} chars):\n", Colors.CYAN)
            # Handle Windows encoding issues
            preview = prompt[:1500] + "\n..." if len(prompt) > 1500 else prompt
            try:
                print(preview)
            except UnicodeEncodeError:
                print(preview.encode('ascii', 'replace').decode('ascii'))
            return True

        try:
            log(f"  Running claude CLI...", Colors.CYAN)
            result = subprocess.run(
                cmd,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=60 * 60,  # 60 minute timeout
                env=subprocess_env  # Pass environment with OAuth token
            )

            # Log output
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n{'='*70}\n")
                f.write(f"ITERATION {i+1}/{iterations}\n")
                f.write(f"{'='*70}\n")
                f.write(f"STDOUT:\n{result.stdout}\n")
                if result.stderr:
                    f.write(f"STDERR:\n{result.stderr}\n")
                f.write(f"Return Code: {result.returncode}\n")

            if result.returncode != 0:
                log(f"  [WARN] Non-zero exit code: {result.returncode}", Colors.YELLOW)
                if i == iterations - 1:
                    return False
            else:
                log(f"  [OK] Iteration {i+1} completed", Colors.GREEN)

        except subprocess.TimeoutExpired:
            log(f"[ERROR] Timeout after 60 minutes", Colors.RED)
            return False
        except FileNotFoundError:
            log("[ERROR] 'claude' CLI not found. Is Claude Code installed?", Colors.RED)
            log("        Run: npm install -g @anthropic-ai/claude-code", Colors.YELLOW)
            return False
        except Exception as e:
            log(f"[ERROR] {type(e).__name__}: {e}", Colors.RED)
            return False

    log(f"\n[SUCCESS] {task_id} completed with {iterations} iterations", Colors.GREEN)
    return True


def list_tasks(data: dict) -> None:
    """Display all tasks in a table format."""
    tasks = data.get("tasks", [])
    if not tasks:
        log("[INFO] No tasks defined in feature_list.json", Colors.YELLOW)
        return

    log(f"\n{'ID':<12} {'Status':<12} {'Agent':<10} {'Priority':<10} {'Complexity':<10} Title", Colors.BOLD)
    log("-" * 90)
    for task in tasks:
        status = task.get('status', 'pending')
        color = Colors.GREEN if status == 'completed' else Colors.YELLOW if status == 'in_progress' else ""
        log(f"{task['id']:<12} {status:<12} {task.get('agent', 'N/A'):<10} {task.get('priority', 'medium'):<10} {task.get('complexity', 'medium'):<10} {task['title'][:35]}", color)


def show_status(data: dict) -> None:
    """Show queue status summary."""
    queue = data.get("queue", {})
    log("\n[QUEUE STATUS]", Colors.BOLD)
    log(f"  Pending:     {len(queue.get('pending', []))}", Colors.YELLOW)
    log(f"  In Progress: {len(queue.get('in_progress', []))}", Colors.CYAN)
    log(f"  Completed:   {len(queue.get('completed', []))}", Colors.GREEN)
    log(f"  Failed:      {len(queue.get('failed', []))}", Colors.RED)


def main():
    parser = argparse.ArgumentParser(
        description="AUTOAGENTS v2.0 - Deploy Claude Code agents for autonomous coding",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
    python agent_launcher.py -i 5               # Run all pending with 5 iterations
    python agent_launcher.py --task TASK-001    # Run specific task
    python agent_launcher.py --list             # List all tasks
    python agent_launcher.py --dry-run -i 3     # Preview without executing

Config file: {FEATURE_LIST}
        """
    )
    parser.add_argument("-i", "--iterations", type=int, default=None,
                        help="Number of iterations per task (default: from task config)")
    parser.add_argument("--task", type=str, help="Run a specific task by ID")
    parser.add_argument("--list", action="store_true", help="List all tasks")
    parser.add_argument("--status", action="store_true", help="Show queue status")
    parser.add_argument("--dry-run", action="store_true", help="Preview commands without executing")

    args = parser.parse_args()

    log(f"\n{'='*70}", Colors.HEADER)
    log(f"  AUTOAGENTS v2.0 - Autonomous Agent Launcher", Colors.BOLD)
    log(f"{'='*70}\n", Colors.HEADER)

    # Load feature list
    data = load_feature_list()
    project = data.get("project", {})
    agents = data.get("agents", {})
    global_rules = data.get("global_rules", {})

    # Handle info commands
    if args.list:
        list_tasks(data)
        return

    if args.status:
        show_status(data)
        return

    # Determine tasks to run
    if args.task:
        task = get_task_by_id(data, args.task)
        if not task:
            log(f"[ERROR] Task {args.task} not found", Colors.RED)
            sys.exit(1)
        tasks_to_run = [task]
    else:
        # Run all pending tasks
        pending_ids = data.get("queue", {}).get("pending", [])
        tasks_to_run = [t for t in data.get("tasks", []) if t["id"] in pending_ids]

    if not tasks_to_run:
        log("[INFO] No pending tasks to run", Colors.YELLOW)
        show_status(data)
        return

    log(f"[AUTOAGENTS] Starting deployment of {len(tasks_to_run)} task(s)\n", Colors.GREEN)

    # Process each task
    for task in tasks_to_run:
        task_id = task["id"]
        iterations = args.iterations or task.get("iterations", 3)

        # Update status to in_progress
        if not args.dry_run:
            update_task_status(data, task_id, "in_progress")
            data = load_feature_list()  # Reload after update

        # Run the agent
        success = run_claude_agent(
            task=task,
            project=project,
            agents=agents,
            global_rules=global_rules,
            iterations=iterations,
            dry_run=args.dry_run
        )

        # Update final status
        if not args.dry_run:
            final_status = "completed" if success else "failed"
            update_task_status(data, task_id, final_status)
            data = load_feature_list()  # Reload after update

    log(f"\n{'='*70}", Colors.HEADER)
    log(f"  AUTOAGENTS - Deployment Complete", Colors.BOLD)
    log(f"{'='*70}", Colors.HEADER)
    show_status(load_feature_list())


if __name__ == "__main__":
    main()
