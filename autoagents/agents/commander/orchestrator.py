#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COMMANDER Orchestrator - AI-Aware Agent Spawner with Prompt Engineering
========================================================================

The COMMANDER is the only agent you need to run. It acts as a PROMPT ENGINEER:

1. Analyzes each agent's task queue to understand complexity
2. CRAFTS OPTIMAL PROMPTS for each agent spawn (minimize tokens, maximize output)
3. Spawns agents with engineered context injection
4. Monitors progress and adjusts strategy
5. Manages token budgets intelligently

PROMPT ENGINEERING PRINCIPLES APPLIED:
- Front-load critical information
- Be specific, not vague
- Provide clear success criteria
- Limit scope to reduce token waste
- Use structured formats

Usage:
    python -m autoagents.agents.commander.runner              # Run orchestrator
    python -m autoagents.agents.commander.runner --once       # Single orchestration cycle
    python -m autoagents.agents.commander.runner --agents 3   # Max 3 concurrent agents
"""

import asyncio
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional
import time

from autoagents.lib.styles import Style
from autoagents.lib.output import print_info, print_warning, print_error, print_success
from autoagents.lib.comms import CommsManager

# Prompt Engineering Module
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
CONTROL_STATION = Path("C:/Users/ToleV/Desktop/TestingFolder/control-station")
COMMS_MD = AUTONOMOUS_CODING / "COMMS.md"

# Agent definitions with their priorities and default iterations
AGENT_CONFIGS = {
    "sentinel": {
        "name": "SENTINEL",
        "emoji": "🛡️",
        "priority": 1,  # Highest - health monitoring
        "default_iterations": 3,
        "min_interval_minutes": 10,
        "module": "autoagents.agents.sentinel.runner",
        "description": "DevOps health monitoring",
    },
    "frontend": {
        "name": "FRONTEND",
        "emoji": "🎨",
        "priority": 2,
        "default_iterations": 5,
        "min_interval_minutes": 15,
        "module": "autoagents.agents.frontend.runner",
        "description": "React/Next.js development",
    },
    "backend": {
        "name": "BACKEND",
        "emoji": "⚙️",
        "priority": 2,
        "default_iterations": 5,
        "min_interval_minutes": 15,
        "module": "autoagents.agents.backend.runner",
        "description": "Rust/Axum development",
    },
    "debugger": {
        "name": "DEBUGGER",
        "emoji": "🔍",
        "priority": 3,
        "default_iterations": 3,
        "min_interval_minutes": 20,
        "module": "autoagents.agents.debugger.runner",
        "description": "Bug investigation",
    },
    "tester": {
        "name": "TESTER",
        "emoji": "🧪",
        "priority": 3,
        "default_iterations": 3,
        "min_interval_minutes": 30,
        "module": "autoagents.agents.tester.runner",
        "description": "Test writing and QA",
    },
    "architect": {
        "name": "ARCHITECT",
        "emoji": "🏛️",
        "priority": 4,  # Lowest - runs less frequently
        "default_iterations": 2,
        "min_interval_minutes": 60,
        "module": "autoagents.agents.architect.runner",
        "description": "Architecture review",
    },
}


class AgentStatus(Enum):
    """Agent execution status."""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    COOLDOWN = "cooldown"


@dataclass
class AgentState:
    """State of a single agent."""
    id: str
    status: AgentStatus = AgentStatus.IDLE
    last_run: Optional[datetime] = None
    last_completion: Optional[datetime] = None
    process: Optional[subprocess.Popen] = None
    runs_today: int = 0
    tokens_today: int = 0
    pending_tasks: int = 0
    error_count: int = 0


@dataclass
class OrchestratorState:
    """Global orchestrator state."""
    agents: dict = field(default_factory=dict)
    cycle_count: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    total_agents_spawned: int = 0
    active_agents: int = 0
    max_concurrent: int = 2
    paused: bool = False
    # Prompt engineering tracking
    total_estimated_tokens: int = 0
    prompts_engineered: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# COMMS.MD INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

comms = CommsManager(COMMS_MD, agent_id="COMMANDER", emoji="👑")


def update_comms_status(state: OrchestratorState):
    """Update COMMANDER section in COMMS.md."""
    active_list = [
        f"{AGENT_CONFIGS[aid]['emoji']} {aid.upper()}"
        for aid, astate in state.agents.items()
        if astate.status == AgentStatus.RUNNING
    ]

    comms.update_section(
        status="🟢 Active" if not state.paused else "⏸️ Paused",
        mission="Orchestrating all agents",
        progress=[
            f"Cycle: {state.cycle_count}",
            f"Active agents: {', '.join(active_list) if active_list else 'None'}",
            f"Total spawned today: {state.total_agents_spawned}",
        ],
        log_entry=f"[{datetime.now().strftime('%H:%M')}] Cycle {state.cycle_count} - {state.active_agents} agents active"
    )


def read_agent_pending_tasks(agent_id: str) -> int:
    """Read pending task count from agent's tasks.json."""
    tasks_file = AGENTS_DIR / agent_id / "tasks.json"
    if not tasks_file.exists():
        return 0

    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check queue.pending or count tasks with status=pending
        queue = data.get("queue", {})
        if "pending" in queue:
            return len(queue["pending"])

        # Fallback: count tasks with pending status
        tasks = data.get("tasks", [])
        return sum(1 for t in tasks if t.get("status") == "pending")
    except Exception:
        return 0


def read_agent_tasks(agent_id: str) -> list[dict]:
    """Read full pending tasks list from agent's tasks.json for prompt engineering."""
    tasks_file = AGENTS_DIR / agent_id / "tasks.json"
    if not tasks_file.exists():
        return []

    try:
        with open(tasks_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        all_tasks = data.get("tasks", [])
        queue = data.get("queue", {})
        pending_ids = queue.get("pending", [])

        # Get pending tasks in priority order
        if pending_ids:
            pending_tasks = []
            for task_id in pending_ids:
                task = next((t for t in all_tasks if t.get("id") == task_id), None)
                if task:
                    pending_tasks.append(task)
            return pending_tasks

        # Fallback: filter by status
        return [t for t in all_tasks if t.get("status") == "pending"]
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT SPAWNING WITH PROMPT ENGINEERING
# ═══════════════════════════════════════════════════════════════════════════════

def spawn_agent_with_prompt_engineering(agent_id: str) -> tuple[Optional[subprocess.Popen], dict]:
    """
    Spawn an agent with PROMPT ENGINEERING intelligence.

    This is where COMMANDER acts as a prompt engineer:
    1. Read the agent's pending tasks
    2. Analyze task complexity
    3. Build an optimized prompt
    4. Create injection file for the agent
    5. Spawn with calculated iterations

    Returns:
        (process, context) - The spawned process and the engineering context
    """
    config = AGENT_CONFIGS.get(agent_id)
    if not config:
        print_error(f"Unknown agent: {agent_id}")
        return None, {}

    # Step 1: Read pending tasks
    tasks = read_agent_tasks(agent_id)

    # Step 2: Build spawn context with prompt engineering
    context = build_spawn_context(agent_id.upper(), tasks)

    # Step 3: Create injection file if we have a prompt
    injection_file = None
    if context.get("prompt"):
        injection_file = create_task_injection_file(agent_id, context)

    # Step 4: Get the spawn command with calculated iterations
    cmd, env_vars = get_spawn_command(agent_id, context, injection_file)

    # Display prompt engineering info
    complexity = context.get("complexity", "SIMPLE")
    iterations = context.get("iterations", config["default_iterations"])
    task_id = context.get("task_id", "exploration")
    est_tokens = context.get("estimated_tokens", 5000)

    print(f"\n  {config['emoji']} {Style.BOLD}PROMPT ENGINEERING for {config['name']}{Style.RESET}")
    print(f"     Task: {task_id}")
    print(f"     Complexity: {complexity}")
    print(f"     Iterations: {iterations} (calculated)")
    print(f"     Est. tokens: ~{est_tokens:,}")

    if injection_file:
        print(f"     Injection: {injection_file.name}")

    # Step 5: Spawn the process
    try:
        # Merge environment variables
        import os
        spawn_env = os.environ.copy()
        spawn_env.update(env_vars)

        process = subprocess.Popen(
            cmd,
            cwd=str(AUTONOMOUS_CODING),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1,
            env=spawn_env,
        )
        return process, context
    except Exception as e:
        print_error(f"Failed to spawn {agent_id}: {e}")
        return None, context


def spawn_agent(agent_id: str, iterations: int = None) -> Optional[subprocess.Popen]:
    """Legacy spawn function - wraps prompt engineering spawn."""
    process, _ = spawn_agent_with_prompt_engineering(agent_id)
    return process


def check_agent_process(agent_state: AgentState) -> bool:
    """Check if agent process is still running. Returns True if running."""
    if agent_state.process is None:
        return False

    poll = agent_state.process.poll()
    if poll is None:
        return True  # Still running

    # Process completed
    return False


def stream_agent_output(agent_state: AgentState, timeout: float = 0.1) -> list[str]:
    """Non-blocking read of agent output lines."""
    lines = []
    if agent_state.process and agent_state.process.stdout:
        try:
            import select
            # Windows doesn't support select on pipes, use a different approach
            while True:
                line = agent_state.process.stdout.readline()
                if not line:
                    break
                lines.append(line.rstrip())
        except Exception:
            pass
    return lines


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEDULING LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

def should_spawn_agent(agent_id: str, agent_state: AgentState) -> bool:
    """Determine if an agent should be spawned."""
    config = AGENT_CONFIGS[agent_id]

    # Don't spawn if already running
    if agent_state.status == AgentStatus.RUNNING:
        return False

    # Check cooldown
    if agent_state.last_completion:
        cooldown = timedelta(minutes=config["min_interval_minutes"])
        if datetime.now() - agent_state.last_completion < cooldown:
            return False

    # Check if agent has pending tasks
    pending = read_agent_pending_tasks(agent_id)
    agent_state.pending_tasks = pending

    # SENTINEL always runs (health monitoring)
    if agent_id == "sentinel":
        return True

    # Other agents need pending tasks
    return pending > 0


def get_next_agents_to_spawn(state: OrchestratorState, max_spawn: int = 1) -> list[str]:
    """Get list of agents to spawn based on priority and availability."""
    candidates = []

    for agent_id, config in AGENT_CONFIGS.items():
        agent_state = state.agents.get(agent_id)
        if agent_state and should_spawn_agent(agent_id, agent_state):
            candidates.append((agent_id, config["priority"], agent_state.pending_tasks))

    # Sort by priority (lower = higher priority), then by pending tasks (more = higher)
    candidates.sort(key=lambda x: (x[1], -x[2]))

    # Return top candidates up to max_spawn
    return [c[0] for c in candidates[:max_spawn]]


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ORCHESTRATION LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def print_orchestrator_banner():
    """Print orchestrator banner with prompt engineering focus."""
    print(f"""
{Style.YELLOW}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}👑 COMMANDER v2.0 - PROMPT ENGINEER{Style.RESET}{Style.YELLOW}                              ║
║   {Style.DIM}AI-Aware Agent Orchestration with Prompt Engineering{Style.RESET}{Style.YELLOW}               ║
║                                                                      ║
║   {Style.CYAN}• Analyzes tasks for complexity{Style.RESET}{Style.YELLOW}                                  ║
║   {Style.CYAN}• Crafts optimal prompts per agent{Style.RESET}{Style.YELLOW}                               ║
║   {Style.CYAN}• Minimizes tokens, maximizes output{Style.RESET}{Style.YELLOW}                             ║
║   {Style.CYAN}• Injects focused context{Style.RESET}{Style.YELLOW}                                        ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def print_status_table(state: OrchestratorState):
    """Print current status of all agents."""
    print(f"\n{Style.CYAN}┌{'─' * 70}┐{Style.RESET}")
    print(f"{Style.CYAN}│{Style.RESET} {Style.BOLD}AGENT STATUS{Style.RESET}" + " " * 57 + f"{Style.CYAN}│{Style.RESET}")
    print(f"{Style.CYAN}├{'─' * 70}┤{Style.RESET}")
    print(f"{Style.CYAN}│{Style.RESET} {'Agent':<12} {'Status':<12} {'Last Run':<12} {'Pending':<10} {'Runs':<8} {Style.CYAN}│{Style.RESET}")
    print(f"{Style.CYAN}├{'─' * 70}┤{Style.RESET}")

    for agent_id, config in AGENT_CONFIGS.items():
        agent_state = state.agents.get(agent_id)
        if not agent_state:
            continue

        status_str = agent_state.status.value
        status_color = {
            AgentStatus.IDLE: Style.DIM,
            AgentStatus.RUNNING: Style.GREEN,
            AgentStatus.COMPLETED: Style.CYAN,
            AgentStatus.FAILED: Style.RED,
            AgentStatus.COOLDOWN: Style.YELLOW,
        }.get(agent_state.status, Style.RESET)

        last_run = agent_state.last_run.strftime("%H:%M:%S") if agent_state.last_run else "-"

        print(f"{Style.CYAN}│{Style.RESET} {config['emoji']} {agent_id:<9} {status_color}{status_str:<12}{Style.RESET} {last_run:<12} {agent_state.pending_tasks:<10} {agent_state.runs_today:<8} {Style.CYAN}│{Style.RESET}")

    print(f"{Style.CYAN}└{'─' * 70}┘{Style.RESET}")


async def orchestration_loop(
    max_concurrent: int = 2,
    cycle_interval: int = 30,
    single_cycle: bool = False,
):
    """Main orchestration loop."""
    state = OrchestratorState(max_concurrent=max_concurrent)

    # Initialize agent states
    for agent_id in AGENT_CONFIGS:
        state.agents[agent_id] = AgentState(id=agent_id)

    print_info(f"Max concurrent agents: {max_concurrent}")
    print_info(f"Cycle interval: {cycle_interval} seconds")
    print_info(f"COMMS.md: {COMMS_MD}")
    print()

    # Initial COMMS.md update
    comms.log_event("orchestrator_start", {
        "max_concurrent": max_concurrent,
        "agents": list(AGENT_CONFIGS.keys()),
    })

    try:
        while True:
            state.cycle_count += 1

            print(f"\n{Style.YELLOW}{'═' * 70}{Style.RESET}")
            print(f"{Style.BOLD}👑 ORCHESTRATION CYCLE {state.cycle_count}{Style.RESET}")
            print(f"{Style.YELLOW}{'═' * 70}{Style.RESET}")

            # Update pending task counts
            for agent_id in AGENT_CONFIGS:
                agent_state = state.agents[agent_id]
                agent_state.pending_tasks = read_agent_pending_tasks(agent_id)

            # Check running agents
            for agent_id, agent_state in state.agents.items():
                if agent_state.status == AgentStatus.RUNNING:
                    if not check_agent_process(agent_state):
                        # Agent completed
                        exit_code = agent_state.process.returncode if agent_state.process else -1
                        agent_state.status = AgentStatus.COMPLETED if exit_code == 0 else AgentStatus.FAILED
                        agent_state.last_completion = datetime.now()
                        agent_state.process = None
                        state.active_agents -= 1

                        status_msg = "completed" if exit_code == 0 else f"failed (exit {exit_code})"
                        print(f"  {AGENT_CONFIGS[agent_id]['emoji']} {agent_id.upper()} {status_msg}")

            # Count active agents
            state.active_agents = sum(
                1 for a in state.agents.values()
                if a.status == AgentStatus.RUNNING
            )

            # Spawn new agents if we have capacity (with PROMPT ENGINEERING)
            available_slots = max_concurrent - state.active_agents
            if available_slots > 0:
                to_spawn = get_next_agents_to_spawn(state, available_slots)

                for agent_id in to_spawn:
                    agent_state = state.agents[agent_id]
                    config = AGENT_CONFIGS[agent_id]

                    # Use prompt engineering spawn
                    process, context = spawn_agent_with_prompt_engineering(agent_id)

                    if process:
                        agent_state.status = AgentStatus.RUNNING
                        agent_state.last_run = datetime.now()
                        agent_state.process = process
                        agent_state.runs_today += 1
                        state.active_agents += 1
                        state.total_agents_spawned += 1

                        # Track prompt engineering stats
                        if context.get("prompt"):
                            state.prompts_engineered += 1
                            state.total_estimated_tokens += context.get("estimated_tokens", 0)

                        print_success(f"Started {config['name']} (PID: {process.pid})")

            # Print status
            print_status_table(state)

            # Update COMMS.md
            update_comms_status(state)

            if single_cycle:
                print_info("Single cycle mode - exiting")
                break

            # Wait for next cycle
            print(f"\n  {Style.DIM}Next cycle in {cycle_interval} seconds... (Ctrl+C to stop){Style.RESET}")
            await asyncio.sleep(cycle_interval)

    except KeyboardInterrupt:
        print(f"\n\n{Style.YELLOW}👑 COMMANDER shutting down...{Style.RESET}")

        # Terminate running agents
        for agent_id, agent_state in state.agents.items():
            if agent_state.process and agent_state.status == AgentStatus.RUNNING:
                print(f"  Stopping {agent_id}...")
                agent_state.process.terminate()
                try:
                    agent_state.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    agent_state.process.kill()

        comms.log_event("orchestrator_shutdown", {
            "cycles": state.cycle_count,
            "total_spawned": state.total_agents_spawned,
        })

    # Final summary with prompt engineering stats
    print(f"""
{Style.GREEN}╔══════════════════════════════════════════════════════════════════════╗
║  👑 COMMANDER SESSION COMPLETE                                       ║
╠══════════════════════════════════════════════════════════════════════╣
║  {Style.BOLD}Orchestration{Style.RESET}{Style.GREEN}                                                        ║
║  🔄 Cycles: {state.cycle_count:<56} ║
║  🚀 Total agents spawned: {state.total_agents_spawned:<41} ║
║  ⏱️  Runtime: {str(datetime.now() - state.start_time).split('.')[0]:<53} ║
╠══════════════════════════════════════════════════════════════════════╣
║  {Style.BOLD}Prompt Engineering{Style.RESET}{Style.GREEN}                                                   ║
║  📝 Prompts engineered: {state.prompts_engineered:<43} ║
║  🪙 Est. tokens allocated: {state.total_estimated_tokens:<40,} ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def run_orchestrator(
    max_concurrent: int = 2,
    cycle_interval: int = 30,
    single_cycle: bool = False,
):
    """Entry point for orchestrator."""
    print_orchestrator_banner()
    asyncio.run(orchestration_loop(max_concurrent, cycle_interval, single_cycle))
