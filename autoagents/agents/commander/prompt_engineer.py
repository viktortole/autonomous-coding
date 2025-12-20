#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMMANDER Prompt Engineering Module
====================================

The COMMANDER acts as a prompt engineer, crafting optimal prompts for each agent.
This module contains the intelligence for:

1. Analyzing tasks to determine complexity and scope
2. Building focused, efficient prompts that minimize tokens
3. Injecting just-enough context for the agent to succeed
4. Using prompt engineering best practices for AI agents

Prompt Engineering Principles Applied:
- Be specific, not vague
- Front-load critical information
- Use structured formats (numbered lists, headers)
- Provide clear success criteria
- Limit scope to reduce token waste
- Use imperative mood ("Do X" not "You should X")
"""

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class TaskComplexity(Enum):
    """Task complexity levels - determines iterations and token budget."""
    TRIVIAL = 1      # Single file, small change: 1-2 iterations
    SIMPLE = 2       # Few files, clear scope: 2-3 iterations
    MODERATE = 3     # Multiple files, some exploration: 3-4 iterations
    COMPLEX = 4      # Many files, needs investigation: 4-5 iterations
    EPIC = 5         # Large refactor, multi-step: 5+ iterations


@dataclass
class TaskAnalysis:
    """Analysis of a task for prompt engineering."""
    task_id: str
    title: str
    complexity: TaskComplexity
    estimated_iterations: int
    estimated_tokens: int
    key_files: list[str]
    success_criteria: list[str]
    context_needed: list[str]
    anti_patterns: list[str]  # What NOT to do


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT ENGINEERING TEMPLATES
# ═══════════════════════════════════════════════════════════════════════════════

# Core prompt structure - minimal, focused, efficient
AGENT_PROMPT_TEMPLATE = """# {emoji} {agent_name} - {task_title}

## MISSION (Read First)
{mission_statement}

## SCOPE (Stay Focused)
{scope}

## SUCCESS =
{success_criteria}

## FILES
{files}

## FORBIDDEN
{anti_patterns}

## EXECUTE NOW
{execution_steps}
"""

# Per-agent prompt engineering strategies
AGENT_STRATEGIES = {
    "SENTINEL": {
        "style": "diagnostic",
        "focus": "health checks first, repairs second",
        "token_multiplier": 0.8,  # SENTINEL is efficient
        "prompt_additions": [
            "Run checks BEFORE attempting fixes",
            "If healthy, report and STOP - don't invent problems",
            "Log all findings to COMMS.md",
        ],
    },
    "FRONTEND": {
        "style": "visual",
        "focus": "one component at a time",
        "token_multiplier": 1.0,
        "prompt_additions": [
            "Read the component file FIRST",
            "Make surgical edits, not rewrites",
            "Run npx tsc --noEmit after changes",
        ],
    },
    "BACKEND": {
        "style": "systems",
        "focus": "API endpoints and data flow",
        "token_multiplier": 1.0,
        "prompt_additions": [
            "Check Cargo.toml for dependencies",
            "Follow Rust idioms (Result, Option)",
            "Run cargo check after changes",
        ],
    },
    "ARCHITECT": {
        "style": "analytical",
        "focus": "patterns and organization",
        "token_multiplier": 0.7,  # ARCHITECT thinks more, codes less
        "prompt_additions": [
            "Analyze before proposing changes",
            "Document findings in COMMS.md",
            "Prefer small refactors over big rewrites",
        ],
    },
    "DEBUGGER": {
        "style": "investigative",
        "focus": "root cause, not symptoms",
        "token_multiplier": 0.9,
        "prompt_additions": [
            "Read error messages CAREFULLY",
            "Find the SOURCE, not the symptom",
            "Verify fix doesn't break other tests",
        ],
    },
    "TESTER": {
        "style": "skeptical",
        "focus": "edge cases and coverage",
        "token_multiplier": 1.1,  # Tests need more tokens
        "prompt_additions": [
            "Check existing tests before writing new ones",
            "Test edge cases, not just happy path",
            "Run npm test after adding tests",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# TASK ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_task(task: dict, agent_id: str) -> TaskAnalysis:
    """
    Analyze a task to determine optimal prompting strategy.

    This is where prompt engineering intelligence lives.
    """
    task_id = task.get("id", "UNKNOWN")
    title = task.get("title", "Untitled Task")

    # Extract file information (handle both dict and list formats)
    files = task.get("files", {})
    if isinstance(files, dict):
        target_files = files.get("target", [])
        context_files = files.get("context", [])
    elif isinstance(files, list):
        target_files = files
        context_files = []
    else:
        target_files = []
        context_files = []

    # Determine complexity based on signals
    complexity = TaskComplexity.SIMPLE

    # More files = more complexity
    total_files = len(target_files) + len(context_files)
    if total_files > 5:
        complexity = TaskComplexity.COMPLEX
    elif total_files > 2:
        complexity = TaskComplexity.MODERATE

    # Check for complexity keywords
    title_lower = title.lower()
    if any(kw in title_lower for kw in ["refactor", "redesign", "overhaul", "migrate"]):
        complexity = TaskComplexity.COMPLEX
    elif any(kw in title_lower for kw in ["fix", "update", "add", "remove"]):
        complexity = TaskComplexity.SIMPLE
    elif any(kw in title_lower for kw in ["investigate", "analyze", "debug"]):
        complexity = TaskComplexity.MODERATE

    # Priority affects complexity perception
    priority = task.get("priority", "medium")
    if priority == "critical":
        complexity = TaskComplexity(min(complexity.value + 1, 5))

    # Calculate iterations based on complexity and agent
    base_iterations = {
        TaskComplexity.TRIVIAL: 1,
        TaskComplexity.SIMPLE: 2,
        TaskComplexity.MODERATE: 3,
        TaskComplexity.COMPLEX: 4,
        TaskComplexity.EPIC: 5,
    }[complexity]

    # Agent-specific adjustments
    strategy = AGENT_STRATEGIES.get(agent_id.upper(), {})
    token_mult = strategy.get("token_multiplier", 1.0)

    estimated_iterations = max(1, int(base_iterations * token_mult))
    estimated_tokens = estimated_iterations * 2000  # ~2K tokens per iteration

    # Extract success criteria
    success_criteria = task.get("acceptance_criteria", [])
    if not success_criteria:
        desc = task.get("description", {})
        if isinstance(desc, dict):
            goal = desc.get("goal", "")
            if goal:
                success_criteria = [goal]
        elif isinstance(desc, str):
            success_criteria = [desc[:100]]

    # Determine what context is needed
    context_needed = []
    if "component" in title_lower or "ui" in title_lower:
        context_needed.append("Component structure and props")
    if "api" in title_lower or "endpoint" in title_lower:
        context_needed.append("API route handlers")
    if "test" in title_lower:
        context_needed.append("Existing test patterns")
    if "style" in title_lower or "css" in title_lower:
        context_needed.append("Tailwind configuration")

    # Common anti-patterns to avoid
    anti_patterns = [
        "Don't rewrite entire files",
        "Don't add unnecessary dependencies",
        "Don't break existing tests",
    ]

    return TaskAnalysis(
        task_id=task_id,
        title=title,
        complexity=complexity,
        estimated_iterations=estimated_iterations,
        estimated_tokens=estimated_tokens,
        key_files=target_files[:5],  # Limit to 5 files
        success_criteria=success_criteria[:3],  # Limit to 3 criteria
        context_needed=context_needed,
        anti_patterns=anti_patterns,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT CONSTRUCTION
# ═══════════════════════════════════════════════════════════════════════════════

def build_agent_prompt(
    agent_id: str,
    agent_emoji: str,
    task: dict,
    analysis: TaskAnalysis,
    iteration: int = 1,
) -> str:
    """
    Build an optimized prompt for an agent.

    Prompt Engineering Applied:
    1. Front-load the mission (what to do)
    2. Constrain the scope (what NOT to do)
    3. Define success clearly (when to stop)
    4. Provide just-enough context (minimize tokens)
    5. Use imperative mood (direct commands)
    """
    strategy = AGENT_STRATEGIES.get(agent_id.upper(), {})

    # Build mission statement - ONE clear sentence
    desc = task.get("description", {})
    if isinstance(desc, dict):
        problem = desc.get("problem", "")
        goal = desc.get("goal", "")
        mission = goal if goal else problem
    else:
        mission = str(desc)[:200]

    if not mission:
        mission = analysis.title

    # Build scope - what to focus on
    scope_items = [f"Focus: {strategy.get('focus', 'Complete the task')}"]
    scope_items.append(f"Complexity: {analysis.complexity.name}")
    scope_items.append(f"Target iterations: {analysis.estimated_iterations}")
    scope = "\n".join(f"- {s}" for s in scope_items)

    # Build success criteria - numbered for clarity
    if analysis.success_criteria:
        success = "\n".join(f"{i+1}. {c}" for i, c in enumerate(analysis.success_criteria))
    else:
        success = "1. Task completed without errors\n2. Changes verified"

    # Build files section - prioritized
    if analysis.key_files:
        files = "\n".join(f"- `{f}`" for f in analysis.key_files)
    else:
        files = "_No specific files - explore as needed_"

    # Build anti-patterns - what to avoid
    anti = "\n".join(f"- {a}" for a in analysis.anti_patterns)

    # Build execution steps - agent-specific
    exec_steps = strategy.get("prompt_additions", [])
    if iteration > 1:
        exec_steps.insert(0, f"This is iteration {iteration} - CONTINUE from where you left off")
    execution = "\n".join(f"{i+1}. {s}" for i, s in enumerate(exec_steps))

    # Construct final prompt
    prompt = AGENT_PROMPT_TEMPLATE.format(
        emoji=agent_emoji,
        agent_name=agent_id.upper(),
        task_title=analysis.title[:50],
        mission_statement=mission[:300],
        scope=scope,
        success_criteria=success,
        files=files,
        anti_patterns=anti,
        execution_steps=execution if execution else "1. Read files\n2. Make changes\n3. Verify",
    )

    return prompt.strip()


def build_spawn_context(agent_id: str, tasks: list[dict]) -> dict:
    """
    Build context object to pass to spawned agent.

    Returns dict with:
    - prompt: The engineered prompt
    - iterations: Recommended iterations
    - task_id: Primary task ID
    - flags: Additional CLI flags
    """
    if not tasks:
        return {
            "prompt": None,
            "iterations": 2,
            "task_id": None,
            "flags": [],
        }

    # Get highest priority task
    task = tasks[0]
    for t in tasks:
        if t.get("priority") == "critical":
            task = t
            break
        elif t.get("priority") == "high" and task.get("priority") != "critical":
            task = t

    # Analyze the task
    analysis = analyze_task(task, agent_id)

    # Get agent config for emoji
    agent_emoji = {
        "SENTINEL": "🛡️",
        "FRONTEND": "🎨",
        "BACKEND": "⚙️",
        "ARCHITECT": "🏛️",
        "DEBUGGER": "🔍",
        "TESTER": "🧪",
    }.get(agent_id.upper(), "🤖")

    # Build the prompt
    prompt = build_agent_prompt(agent_id, agent_emoji, task, analysis)

    return {
        "prompt": prompt,
        "iterations": analysis.estimated_iterations,
        "task_id": analysis.task_id,
        "complexity": analysis.complexity.name,
        "estimated_tokens": analysis.estimated_tokens,
        "flags": [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PROMPT INJECTION INTO AGENT SPAWN
# ═══════════════════════════════════════════════════════════════════════════════

def create_task_injection_file(agent_id: str, context: dict) -> Optional[Path]:
    """
    Create a temporary file with the engineered prompt.
    The agent runner will read this and use it as the first prompt.

    Returns path to the injection file.
    """
    if not context.get("prompt"):
        return None

    agents_dir = Path(__file__).parent.parent
    injection_dir = agents_dir.parent.parent / ".commander_injections"
    injection_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{agent_id.lower()}_{timestamp}.md"
    filepath = injection_dir / filename

    # Write the engineered prompt
    content = f"""# COMMANDER TASK INJECTION
# Agent: {agent_id}
# Task: {context.get('task_id', 'N/A')}
# Complexity: {context.get('complexity', 'UNKNOWN')}
# Generated: {datetime.now().isoformat()}

{context['prompt']}
"""

    filepath.write_text(content, encoding="utf-8")
    return filepath


def get_spawn_command(
    agent_id: str,
    context: dict,
    injection_file: Optional[Path] = None,
) -> tuple[list[str], dict]:
    """
    Get the command and environment for spawning an agent.

    Returns:
        (command_args, env_vars)
    """
    import sys

    module = f"autoagents.agents.{agent_id.lower()}.runner"
    iterations = context.get("iterations", 3)

    cmd = [sys.executable, "-m", module, "-i", str(iterations)]

    # Add task-specific flags
    if context.get("task_id"):
        cmd.extend(["--task", context["task_id"]])

    for flag in context.get("flags", []):
        cmd.append(flag)

    # Environment variables for prompt injection
    env = {}
    if injection_file:
        env["COMMANDER_INJECTION"] = str(injection_file)

    env["COMMANDER_MANAGED"] = "1"
    env["COMMANDER_COMPLEXITY"] = context.get("complexity", "SIMPLE")
    env["COMMANDER_TOKENS"] = str(context.get("estimated_tokens", 5000))

    return cmd, env
