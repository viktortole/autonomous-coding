#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMMANDER Budget-Based Orchestration
=====================================

Simple interface: Run COMMANDER with an iteration budget.
COMMANDER intelligently distributes iterations across agents.

Usage:
    python -m autoagents.agents.commander.runner --budget 10

What happens:
1. COMMANDER reads ALL agents' pending tasks
2. Analyzes complexity and priority of each
3. Creates a spawn plan that fits within budget
4. Executes the plan, spawning agents with calculated iterations
5. Stops when budget is exhausted
6. Reports on what was accomplished

Budget Distribution Algorithm:
- Higher priority agents get preference
- More pending tasks = more iterations
- Complex tasks get more iterations
- Critical priority tasks get bonus iterations
"""

import json
import subprocess
import sys
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from autoagents.lib.styles import Style
from autoagents.lib.output import print_info, print_warning, print_error, print_success
from autoagents.lib.comms import CommsManager

from autoagents.agents.commander.prompt_engineer import (
    analyze_task,
    build_spawn_context,
    create_task_injection_file,
    get_spawn_command,
    TaskComplexity,
)


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

AGENTS_DIR = Path(__file__).parent.parent
AUTONOMOUS_CODING = AGENTS_DIR.parent.parent
COMMS_MD = AUTONOMOUS_CODING / "COMMS.md"

# Agent priority and limits
AGENT_CONFIG = {
    "sentinel": {"priority": 1, "emoji": "🛡️", "max_iters": 3, "min_iters": 1},
    "frontend": {"priority": 2, "emoji": "🎨", "max_iters": 5, "min_iters": 2},
    "backend":  {"priority": 2, "emoji": "⚙️", "max_iters": 5, "min_iters": 2},
    "debugger": {"priority": 3, "emoji": "🔍", "max_iters": 4, "min_iters": 1},
    "tester":   {"priority": 3, "emoji": "🧪", "max_iters": 4, "min_iters": 1},
    "architect":{"priority": 4, "emoji": "🏛️", "max_iters": 2, "min_iters": 1},
}

# Complexity to iteration mapping
COMPLEXITY_ITERS = {
    TaskComplexity.TRIVIAL: 1,
    TaskComplexity.SIMPLE: 2,
    TaskComplexity.MODERATE: 3,
    TaskComplexity.COMPLEX: 4,
    TaskComplexity.EPIC: 5,
}


@dataclass
class AgentAllocation:
    """Planned allocation for an agent."""
    agent_id: str
    emoji: str
    iterations: int
    task_id: str
    task_title: str
    complexity: str
    priority_score: float
    reason: str


@dataclass
class BudgetPlan:
    """Complete budget distribution plan."""
    total_budget: int
    allocated: int
    remaining: int
    allocations: list[AgentAllocation] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


@dataclass
class BudgetState:
    """Runtime state for budget-based orchestration."""
    plan: BudgetPlan
    started: datetime = field(default_factory=datetime.now)
    completed_agents: list[str] = field(default_factory=list)
    failed_agents: list[str] = field(default_factory=list)
    iterations_used: int = 0
    estimated_tokens: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# TASK READING
# ═══════════════════════════════════════════════════════════════════════════════

def read_agent_tasks(agent_id: str) -> list[dict]:
    """Read pending tasks from agent's tasks.json."""
    tasks_file = AGENTS_DIR / agent_id / "tasks.json"
    if not tasks_file.exists():
        return []

    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        all_tasks = data.get("tasks", [])
        queue = data.get("queue", {})
        pending_ids = queue.get("pending", [])

        if pending_ids:
            pending = []
            for task_id in pending_ids:
                task = next((t for t in all_tasks if t.get("id") == task_id), None)
                if task:
                    pending.append(task)
            return pending

        return [t for t in all_tasks if t.get("status") == "pending"]
    except Exception:
        return []


def get_highest_priority_task(tasks: list[dict]) -> Optional[dict]:
    """Get the highest priority task from a list."""
    if not tasks:
        return None

    # Priority order: critical > high > medium > low
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}

    sorted_tasks = sorted(
        tasks,
        key=lambda t: priority_order.get(t.get("priority", "medium"), 2)
    )
    return sorted_tasks[0]


# ═══════════════════════════════════════════════════════════════════════════════
# BUDGET DISTRIBUTION ALGORITHM
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_agent_score(agent_id: str, tasks: list[dict]) -> tuple[float, dict]:
    """
    Calculate priority score for an agent.

    Score = (1 / priority) * pending_tasks * complexity_mult * priority_bonus

    Returns:
        (score, analysis_info)
    """
    if not tasks:
        return 0.0, {"reason": "No pending tasks"}

    config = AGENT_CONFIG.get(agent_id, {"priority": 5})
    priority = config["priority"]

    # Get highest priority task for analysis
    top_task = get_highest_priority_task(tasks)
    analysis = analyze_task(top_task, agent_id.upper())

    # Base score from task count and complexity
    task_count = len(tasks)
    complexity_mult = {
        TaskComplexity.TRIVIAL: 0.5,
        TaskComplexity.SIMPLE: 1.0,
        TaskComplexity.MODERATE: 1.5,
        TaskComplexity.COMPLEX: 2.0,
        TaskComplexity.EPIC: 2.5,
    }.get(analysis.complexity, 1.0)

    # Priority bonus for critical/high tasks
    priority_bonus = 1.0
    if top_task.get("priority") == "critical":
        priority_bonus = 3.0
    elif top_task.get("priority") == "high":
        priority_bonus = 2.0

    # Calculate score (lower agent priority number = higher score)
    score = (1.0 / priority) * min(task_count, 10) * complexity_mult * priority_bonus

    info = {
        "task_count": task_count,
        "top_task_id": top_task.get("id"),
        "top_task_title": top_task.get("title", "")[:40],
        "complexity": analysis.complexity.name,
        "priority_bonus": priority_bonus,
        "estimated_iters": analysis.estimated_iterations,
    }

    return score, info


def create_budget_plan(total_budget: int) -> BudgetPlan:
    """
    Create a plan for distributing iteration budget across agents.

    Algorithm:
    1. Score all agents based on task priority and complexity
    2. Sort by score (highest first)
    3. Allocate iterations proportionally, respecting min/max limits
    4. Continue until budget exhausted
    """
    plan = BudgetPlan(total_budget=total_budget, allocated=0, remaining=total_budget)

    # Gather agent scores
    agent_scores = []
    for agent_id, config in AGENT_CONFIG.items():
        tasks = read_agent_tasks(agent_id)
        score, info = calculate_agent_score(agent_id, tasks)

        if score > 0:
            agent_scores.append({
                "agent_id": agent_id,
                "score": score,
                "info": info,
                "config": config,
            })
        else:
            plan.skipped.append(f"{config['emoji']} {agent_id}: {info.get('reason', 'No tasks')}")

    # Sort by score (highest first)
    agent_scores.sort(key=lambda x: x["score"], reverse=True)

    # Distribute budget
    remaining = total_budget

    for agent_data in agent_scores:
        if remaining <= 0:
            plan.skipped.append(
                f"{agent_data['config']['emoji']} {agent_data['agent_id']}: Budget exhausted"
            )
            continue

        agent_id = agent_data["agent_id"]
        config = agent_data["config"]
        info = agent_data["info"]

        # Calculate iterations for this agent
        # Use the prompt engineer's estimate, but respect limits
        ideal_iters = info.get("estimated_iters", 2)
        min_iters = config["min_iters"]
        max_iters = config["max_iters"]

        # Clamp to limits and remaining budget
        iters = max(min_iters, min(ideal_iters, max_iters, remaining))

        if iters > 0:
            allocation = AgentAllocation(
                agent_id=agent_id,
                emoji=config["emoji"],
                iterations=iters,
                task_id=info.get("top_task_id", ""),
                task_title=info.get("top_task_title", ""),
                complexity=info.get("complexity", "SIMPLE"),
                priority_score=agent_data["score"],
                reason=f"{info['task_count']} tasks, {info['complexity']} complexity",
            )
            plan.allocations.append(allocation)
            remaining -= iters

    plan.allocated = total_budget - remaining
    plan.remaining = remaining

    return plan


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY - DOPAMINE-BOOSTING VISUAL OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

def print_budget_banner(budget: int):
    """Print epic budget mode banner."""
    print(f"""
{Style.YELLOW}
    ██████╗ ██████╗ ███╗   ███╗███╗   ███╗ █████╗ ███╗   ██╗██████╗ ███████╗██████╗
   ██╔════╝██╔═══██╗████╗ ████║████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝██╔══██╗
   ██║     ██║   ██║██╔████╔██║██╔████╔██║███████║██╔██╗ ██║██║  ██║█████╗  ██████╔╝
   ██║     ██║   ██║██║╚██╔╝██║██║╚██╔╝██║██╔══██║██║╚██╗██║██║  ██║██╔══╝  ██╔══██╗
   ╚██████╗╚██████╔╝██║ ╚═╝ ██║██║ ╚═╝ ██║██║  ██║██║ ╚████║██████╔╝███████╗██║  ██║
    ╚═════╝ ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝ ╚══════╝╚═╝  ╚═╝
{Style.RESET}
{Style.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Style.RESET}
{Style.CYAN}║{Style.RESET}  👑 {Style.BOLD}AUTONOMOUS AGENT ORCHESTRATOR{Style.RESET}                                          {Style.CYAN}║{Style.RESET}
{Style.CYAN}║{Style.RESET}  {Style.DIM}Budget Mode v2.0 - Intelligent Task Distribution{Style.RESET}                         {Style.CYAN}║{Style.RESET}
{Style.CYAN}╠══════════════════════════════════════════════════════════════════════════════╣{Style.RESET}
{Style.CYAN}║{Style.RESET}                                                                              {Style.CYAN}║{Style.RESET}
{Style.CYAN}║{Style.RESET}  💰 {Style.BOLD}ITERATION BUDGET:{Style.RESET} {Style.GREEN}{budget:>3}{Style.RESET} iterations                                       {Style.CYAN}║{Style.RESET}
{Style.CYAN}║{Style.RESET}                                                                              {Style.CYAN}║{Style.RESET}
{Style.CYAN}║{Style.RESET}  {Style.DIM}The COMMANDER will analyze all agent tasks, calculate priority{Style.RESET}           {Style.CYAN}║{Style.RESET}
{Style.CYAN}║{Style.RESET}  {Style.DIM}scores, and distribute iterations for maximum efficiency.{Style.RESET}                {Style.CYAN}║{Style.RESET}
{Style.CYAN}║{Style.RESET}                                                                              {Style.CYAN}║{Style.RESET}
{Style.CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def print_thinking(message: str):
    """Print a thinking/reasoning message."""
    print(f"  {Style.MAGENTA}🧠 THINKING:{Style.RESET} {Style.DIM}{message}{Style.RESET}")


def print_decision(message: str):
    """Print a decision message."""
    print(f"  {Style.GREEN}⚡ DECISION:{Style.RESET} {message}")


def print_budget_plan(plan: BudgetPlan):
    """Print the budget distribution plan with reasoning."""
    print(f"""
{Style.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Style.RESET}
{Style.CYAN}║{Style.RESET}  🧠 {Style.BOLD}COMMANDER ANALYSIS COMPLETE{Style.RESET}                                            {Style.CYAN}║{Style.RESET}
{Style.CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")

    # Show reasoning
    print_thinking("Scanned all 6 agent task queues...")
    print_thinking(f"Found {len(plan.allocations)} agents with pending work")
    print_thinking("Calculating priority scores based on task complexity and urgency...")
    print()

    # Budget summary with visual bar
    used_pct = (plan.allocated / plan.total_budget * 100) if plan.total_budget > 0 else 0
    bar_len = 40
    filled = int(bar_len * plan.allocated / plan.total_budget) if plan.total_budget > 0 else 0
    bar = f"{Style.GREEN}{'█' * filled}{Style.RESET}{Style.DIM}{'░' * (bar_len - filled)}{Style.RESET}"

    print(f"  {Style.BOLD}📊 BUDGET ALLOCATION{Style.RESET}")
    print(f"  ┌{'─' * 50}┐")
    print(f"  │ [{bar}] │")
    print(f"  └{'─' * 50}┘")
    print(f"  {Style.GREEN}✓ Allocated:{Style.RESET} {plan.allocated}/{plan.total_budget} iterations ({used_pct:.0f}%)")
    if plan.remaining > 0:
        print(f"  {Style.DIM}○ Remaining: {plan.remaining} iterations{Style.RESET}")
    print()

    # Spawn plan with cards
    if plan.allocations:
        print(f"  {Style.BOLD}🚀 SPAWN QUEUE{Style.RESET}")
        print(f"  {Style.CYAN}{'─' * 72}{Style.RESET}")

        for i, alloc in enumerate(plan.allocations, 1):
            task_short = alloc.task_title[:35] + ".." if len(alloc.task_title) > 37 else alloc.task_title
            complexity_color = {
                "TRIVIAL": Style.DIM,
                "SIMPLE": Style.GREEN,
                "MODERATE": Style.YELLOW,
                "COMPLEX": Style.MAGENTA,
                "EPIC": Style.RED,
            }.get(alloc.complexity, Style.RESET)

            print(f"  {Style.CYAN}│{Style.RESET} {i}. {alloc.emoji} {Style.BOLD}{alloc.agent_id.upper():<10}{Style.RESET} ───────────────────────────────────────────────")
            print(f"  {Style.CYAN}│{Style.RESET}    📋 Task: {task_short}")
            print(f"  {Style.CYAN}│{Style.RESET}    🔄 Iterations: {Style.BOLD}{alloc.iterations}{Style.RESET}  │  {complexity_color}◆ {alloc.complexity}{Style.RESET}  │  Score: {alloc.priority_score:.1f}")
            print(f"  {Style.CYAN}│{Style.RESET}    {Style.DIM}└─ {alloc.reason}{Style.RESET}")
            print(f"  {Style.CYAN}│{Style.RESET}")

        print(f"  {Style.CYAN}{'─' * 72}{Style.RESET}")

    # Skipped agents
    if plan.skipped:
        print(f"\n  {Style.DIM}⏸️  DEFERRED (insufficient budget):{Style.RESET}")
        for skip in plan.skipped:
            print(f"     {Style.DIM}└─ {skip}{Style.RESET}")


def print_execution_progress(state: BudgetState, current: int, total: int):
    """Print execution progress with visual bar."""
    pct = int((current / total) * 100) if total > 0 else 0
    bar_len = 40
    filled = int(bar_len * current / total) if total > 0 else 0
    bar = f"{Style.GREEN}{'█' * filled}{Style.RESET}{Style.DIM}{'░' * (bar_len - filled)}{Style.RESET}"

    completed = len(state.completed_agents)
    failed = len(state.failed_agents)

    print(f"""
{Style.CYAN}┌──────────────────────────────────────────────────────────────────────────────┐{Style.RESET}
{Style.CYAN}│{Style.RESET}  📈 {Style.BOLD}EXECUTION PROGRESS{Style.RESET}                                                      {Style.CYAN}│{Style.RESET}
{Style.CYAN}│{Style.RESET}  [{bar}] {pct:>3}%    {Style.CYAN}│{Style.RESET}
{Style.CYAN}│{Style.RESET}                                                                              {Style.CYAN}│{Style.RESET}
{Style.CYAN}│{Style.RESET}  🔄 Iterations: {current}/{total}  │  ✅ Completed: {completed}  │  ❌ Failed: {failed}            {Style.CYAN}│{Style.RESET}
{Style.CYAN}└──────────────────────────────────────────────────────────────────────────────┘{Style.RESET}""")


def print_agent_spawn_card(allocation: AgentAllocation, status: str = "starting"):
    """Print a card for agent spawn status."""
    status_icons = {
        "starting": f"{Style.YELLOW}⏳ STARTING{Style.RESET}",
        "running": f"{Style.CYAN}🔄 RUNNING{Style.RESET}",
        "success": f"{Style.GREEN}✅ SUCCESS{Style.RESET}",
        "failed": f"{Style.RED}❌ FAILED{Style.RESET}",
    }
    status_display = status_icons.get(status, status)

    print(f"""
{Style.YELLOW}┌──────────────────────────────────────────────────────────────────────────────┐{Style.RESET}
{Style.YELLOW}│{Style.RESET}  {allocation.emoji} {Style.BOLD}SPAWNING: {allocation.agent_id.upper()}{Style.RESET}                                                   {Style.YELLOW}│{Style.RESET}
{Style.YELLOW}├──────────────────────────────────────────────────────────────────────────────┤{Style.RESET}
{Style.YELLOW}│{Style.RESET}  📋 Task:       {allocation.task_title[:50]:<50}      {Style.YELLOW}│{Style.RESET}
{Style.YELLOW}│{Style.RESET}  🔄 Iterations: {allocation.iterations:<5}  │  ◆ Complexity: {allocation.complexity:<10}             {Style.YELLOW}│{Style.RESET}
{Style.YELLOW}│{Style.RESET}  📊 Status:     {status_display:<50}      {Style.YELLOW}│{Style.RESET}
{Style.YELLOW}└──────────────────────────────────────────────────────────────────────────────┘{Style.RESET}""")


def print_final_report(state: BudgetState):
    """Print epic final budget execution report."""
    duration = datetime.now() - state.started
    duration_str = str(duration).split('.')[0]
    remaining = state.plan.total_budget - state.iterations_used

    # Calculate efficiency
    efficiency = (state.iterations_used / state.plan.total_budget * 100) if state.plan.total_budget > 0 else 0
    success_rate = (len(state.completed_agents) / (len(state.completed_agents) + len(state.failed_agents)) * 100) if (len(state.completed_agents) + len(state.failed_agents)) > 0 else 0

    # Status color based on success
    if len(state.failed_agents) == 0:
        border_color = Style.GREEN
        status_msg = "🎉 ALL AGENTS COMPLETED SUCCESSFULLY"
    elif len(state.completed_agents) > len(state.failed_agents):
        border_color = Style.YELLOW
        status_msg = "⚠️  PARTIAL SUCCESS - SOME AGENTS FAILED"
    else:
        border_color = Style.RED
        status_msg = "❌ EXECUTION HAD ISSUES"

    print(f"""

{border_color}╔══════════════════════════════════════════════════════════════════════════════╗{Style.RESET}
{border_color}║{Style.RESET}                                                                              {border_color}║{Style.RESET}
{border_color}║{Style.RESET}     👑 {Style.BOLD}COMMANDER SESSION COMPLETE{Style.RESET}                                          {border_color}║{Style.RESET}
{border_color}║{Style.RESET}     {status_msg:<60}        {border_color}║{Style.RESET}
{border_color}║{Style.RESET}                                                                              {border_color}║{Style.RESET}
{border_color}╠══════════════════════════════════════════════════════════════════════════════╣{Style.RESET}
{border_color}║{Style.RESET}  {Style.BOLD}💰 BUDGET SUMMARY{Style.RESET}                                                        {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  ┌────────────────────────────────────────────────────────────────────────┐  {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  │  📊 Total Budget:     {state.plan.total_budget:>5} iterations                                 │  {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  │  ✅ Iterations Used:  {state.iterations_used:>5} iterations                                 │  {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  │  💰 Budget Remaining: {remaining:>5} iterations                                 │  {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  │  📈 Efficiency:       {efficiency:>5.1f}%                                           │  {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  └────────────────────────────────────────────────────────────────────────┘  {border_color}║{Style.RESET}
{border_color}╠══════════════════════════════════════════════════════════════════════════════╣{Style.RESET}
{border_color}║{Style.RESET}  {Style.BOLD}🤖 AGENT PERFORMANCE{Style.RESET}                                                     {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  ┌────────────────────────────────────────────────────────────────────────┐  {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  │  🚀 Completed:        {len(state.completed_agents):>5} agents                                     │  {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  │  ❌ Failed:           {len(state.failed_agents):>5} agents                                     │  {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  │  📊 Success Rate:     {success_rate:>5.1f}%                                           │  {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  └────────────────────────────────────────────────────────────────────────┘  {border_color}║{Style.RESET}
{border_color}╠══════════════════════════════════════════════════════════════════════════════╣{Style.RESET}
{border_color}║{Style.RESET}  {Style.BOLD}📊 RESOURCE USAGE{Style.RESET}                                                        {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  ┌────────────────────────────────────────────────────────────────────────┐  {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  │  🪙 Est. Tokens Used: {state.estimated_tokens:>10,}                                    │  {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  │  ⏱️  Session Duration: {duration_str:<15}                                   │  {border_color}║{Style.RESET}
{border_color}║{Style.RESET}  └────────────────────────────────────────────────────────────────────────┘  {border_color}║{Style.RESET}
{border_color}╚══════════════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def spawn_agent_for_budget(allocation: AgentAllocation) -> tuple[subprocess.Popen, dict]:
    """Spawn an agent with the allocated iterations."""
    agent_id = allocation.agent_id

    # Read tasks and build context
    tasks = read_agent_tasks(agent_id)
    context = build_spawn_context(agent_id.upper(), tasks)

    # Override iterations with our allocation
    context["iterations"] = allocation.iterations

    # Create injection file
    injection_file = None
    if context.get("prompt"):
        injection_file = create_task_injection_file(agent_id, context)

    # Get spawn command
    cmd, env_vars = get_spawn_command(agent_id, context, injection_file)

    # Override iterations in command
    for i, arg in enumerate(cmd):
        if arg == "-i" and i + 1 < len(cmd):
            cmd[i + 1] = str(allocation.iterations)
            break

    # Print visual spawn card
    print_agent_spawn_card(allocation, "starting")
    print_thinking(f"Crafting optimized prompt for {agent_id.upper()}...")
    print_thinking(f"Injecting task context: {allocation.task_id}")
    print_decision(f"Allocating {allocation.iterations} iterations based on {allocation.complexity} complexity")

    try:
        spawn_env = os.environ.copy()
        spawn_env.update(env_vars)

        # Don't capture stdout - let agent output flow directly to terminal
        # This gives real-time visibility into what agents are doing
        process = subprocess.Popen(
            cmd,
            cwd=str(AUTONOMOUS_CODING),
            env=spawn_env,
        )

        print(f"  {Style.GREEN}✓ Agent spawned successfully (PID: {process.pid}){Style.RESET}")
        print(f"\n{Style.CYAN}{'─' * 78}{Style.RESET}")
        print(f"  {Style.BOLD}📺 LIVE AGENT OUTPUT:{Style.RESET}")
        print(f"{Style.CYAN}{'─' * 78}{Style.RESET}\n")
        return process, context

    except Exception as e:
        print_error(f"Failed to spawn {agent_id}: {e}")
        return None, context


def run_budget_orchestration(budget: int, dry_run: bool = False):
    """
    Run budget-based orchestration.

    Args:
        budget: Total iteration budget to distribute
        dry_run: If True, just show the plan without executing
    """
    print_budget_banner(budget)

    # Create the plan with visual thinking
    print(f"\n{Style.CYAN}{'─' * 78}{Style.RESET}")
    print(f"  {Style.BOLD}🔍 PHASE 1: TASK ANALYSIS{Style.RESET}")
    print(f"{Style.CYAN}{'─' * 78}{Style.RESET}")
    print_thinking("Scanning agent task queues...")
    plan = create_budget_plan(budget)
    print_budget_plan(plan)

    if not plan.allocations:
        print_warning("No agents to spawn - all tasks completed or no pending work!")
        return

    if dry_run:
        print(f"""
{Style.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗{Style.RESET}
{Style.CYAN}║{Style.RESET}  {Style.DIM}🔒 DRY RUN MODE - Plan displayed but NOT executed{Style.RESET}                         {Style.CYAN}║{Style.RESET}
{Style.CYAN}║{Style.RESET}  {Style.DIM}Remove --dry-run flag to execute the plan{Style.RESET}                                  {Style.CYAN}║{Style.RESET}
{Style.CYAN}╚══════════════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")
        return

    # Ask for confirmation with visual prompt
    print(f"""
{Style.YELLOW}╔══════════════════════════════════════════════════════════════════════════════╗{Style.RESET}
{Style.YELLOW}║{Style.RESET}  ⚡ {Style.BOLD}READY TO EXECUTE{Style.RESET}                                                        {Style.YELLOW}║{Style.RESET}
{Style.YELLOW}║{Style.RESET}                                                                              {Style.YELLOW}║{Style.RESET}
{Style.YELLOW}║{Style.RESET}  The COMMANDER will now spawn {len(plan.allocations)} agents with {plan.allocated} total iterations.       {Style.YELLOW}║{Style.RESET}
{Style.YELLOW}║{Style.RESET}                                                                              {Style.YELLOW}║{Style.RESET}
{Style.YELLOW}║{Style.RESET}  {Style.DIM}Press ENTER to begin execution or Ctrl+C to abort...{Style.RESET}                    {Style.YELLOW}║{Style.RESET}
{Style.YELLOW}╚══════════════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")

    try:
        input()
    except KeyboardInterrupt:
        print(f"\n  {Style.YELLOW}⏹️  Execution cancelled by user.{Style.RESET}")
        return

    # Execute the plan
    state = BudgetState(plan=plan)
    comms = CommsManager(COMMS_MD, agent_id="COMMANDER", emoji="👑")

    comms.log_event("budget_orchestration_start", {
        "budget": budget,
        "allocated": plan.allocated,
        "agents": [a.agent_id for a in plan.allocations],
    })

    print(f"""
{Style.GREEN}{'═' * 78}{Style.RESET}
  {Style.BOLD}🚀 PHASE 2: AGENT EXECUTION{Style.RESET}
{Style.GREEN}{'═' * 78}{Style.RESET}
""")

    try:
        for i, allocation in enumerate(plan.allocations):
            print(f"\n{Style.CYAN}{'─' * 78}{Style.RESET}")
            print(f"  {Style.BOLD}AGENT {i + 1}/{len(plan.allocations)}{Style.RESET}")
            print(f"{Style.CYAN}{'─' * 78}{Style.RESET}")

            print_execution_progress(state, state.iterations_used, plan.allocated)

            process, context = spawn_agent_for_budget(allocation)

            if process:
                # Wait for completion with status
                print(f"\n  {Style.DIM}⏳ Waiting for {allocation.agent_id.upper()} to complete...{Style.RESET}")
                process.wait()

                exit_code = process.returncode
                if exit_code == 0:
                    state.completed_agents.append(allocation.agent_id)
                    print(f"\n  {Style.GREEN}{'─' * 40}{Style.RESET}")
                    print(f"  {Style.GREEN}✅ {allocation.emoji} {allocation.agent_id.upper()} COMPLETED SUCCESSFULLY{Style.RESET}")
                    print(f"  {Style.GREEN}{'─' * 40}{Style.RESET}")
                else:
                    state.failed_agents.append(allocation.agent_id)
                    print(f"\n  {Style.RED}{'─' * 40}{Style.RESET}")
                    print(f"  {Style.RED}❌ {allocation.emoji} {allocation.agent_id.upper()} FAILED (exit code {exit_code}){Style.RESET}")
                    print(f"  {Style.RED}{'─' * 40}{Style.RESET}")

                state.iterations_used += allocation.iterations
                state.estimated_tokens += context.get("estimated_tokens", 0)

            else:
                state.failed_agents.append(allocation.agent_id)
                print(f"\n  {Style.RED}❌ Failed to spawn {allocation.agent_id.upper()}{Style.RESET}")

    except KeyboardInterrupt:
        print(f"\n\n  {Style.YELLOW}⏹️  Execution interrupted by user{Style.RESET}")

    # Final report
    comms.log_event("budget_orchestration_end", {
        "iterations_used": state.iterations_used,
        "completed": state.completed_agents,
        "failed": state.failed_agents,
        "estimated_tokens": state.estimated_tokens,
    })

    print_final_report(state)
