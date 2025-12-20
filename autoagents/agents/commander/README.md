# COMMANDER Agent - Agent Orchestrator

**ID:** COMMANDER
**Emoji:** 👑
**Color:** Gold (#FFD700)
**Model:** claude-opus-4-5-20251101 (AI mode only)
**Daily Token Budget:** 15,000 (AI mode only)

## Overview

The COMMANDER is the **ONLY agent you need to run**. It automatically:
1. Spawns other agents as subprocesses
2. Monitors their progress via COMMS.md
3. Manages token budgets across all agents
4. Keeps the system running autonomously

## Quick Start

```bash
# Just run this - it handles everything
python -m autoagents.agents.commander.runner

# Or after pip install
commander
```

## Usage Modes

### Orchestrator Mode (Default)

Spawns and monitors all other agents automatically:

```bash
# Start orchestrating (runs forever until Ctrl+C)
python -m autoagents.agents.commander.runner

# Max 3 concurrent agents (default: 2)
python -m autoagents.agents.commander.runner --agents 3

# 60 second cycle interval (default: 30)
python -m autoagents.agents.commander.runner --interval 60

# Single cycle then exit
python -m autoagents.agents.commander.runner --once

# Show status and exit
python -m autoagents.agents.commander.runner --status
```

### AI Mode (Legacy)

Uses Claude Opus 4.5 to make orchestration decisions:

```bash
# 5 AI orchestration cycles
python -m autoagents.agents.commander.runner --ai -i 5

# With focus area
python -m autoagents.agents.commander.runner --ai --focus "fix build errors"
```

## Agent Priorities

| Priority | Agent | Default Iterations | Min Interval |
|----------|-------|-------------------|--------------|
| 1 (High) | 🛡️ SENTINEL | 3 | 10 min |
| 2 | 🎨 FRONTEND | 5 | 15 min |
| 2 | ⚙️ BACKEND | 5 | 15 min |
| 3 | 🔍 DEBUGGER | 3 | 20 min |
| 3 | 🧪 TESTER | 3 | 30 min |
| 4 (Low) | 🏛️ ARCHITECT | 2 | 60 min |

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                     COMMANDER ORCHESTRATOR                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Every 30 seconds:                                                  │
│  1. Read COMMS.md → Check agent statuses                           │
│  2. Check each agent's tasks.json → Count pending tasks            │
│  3. Find completed agents → Mark as available                      │
│  4. Calculate available slots → (max_concurrent - running)         │
│  5. Select agents to spawn → By priority + pending tasks           │
│  6. Spawn subprocess → python -m autoagents.agents.X.runner -i N   │
│  7. Update COMMS.md → Log spawned agents                           │
│  8. Repeat...                                                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Files

- `config.json` - Agent configuration
- `runner.py` - Main entry point
- `orchestrator.py` - Spawning and monitoring logic
- `prompts/system_prompt.md` - System prompt (AI mode)
- `tasks.json` - Task queue (AI mode)

## Configuration

Modify `orchestrator.py` AGENT_CONFIGS to customize:
- `priority` - Lower = spawned first
- `default_iterations` - How many iterations per spawn
- `min_interval_minutes` - Cooldown between spawns

## COMMS.md Integration

The COMMANDER updates its section in COMMS.md with:
- Current status (Active/Paused)
- List of running agents
- Cycle count and runtime
- Session log entries

## Example Session

```
👑 COMMANDER ORCHESTRATOR v1.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

══════════════════════════════════════════════════════════════════════
👑 ORCHESTRATION CYCLE 1
══════════════════════════════════════════════════════════════════════

  🛡️ Spawning SENTINEL with 3 iterations...
  ✅ Started SENTINEL (PID: 12345)

  🎨 Spawning FRONTEND with 5 iterations...
  ✅ Started FRONTEND (PID: 12346)

┌──────────────────────────────────────────────────────────────────────┐
│ AGENT STATUS                                                         │
├──────────────────────────────────────────────────────────────────────┤
│ Agent        Status       Last Run     Pending    Runs               │
├──────────────────────────────────────────────────────────────────────┤
│ 🛡️ sentinel   running      14:30:00     5          1                  │
│ 🎨 frontend   running      14:30:01     28         1                  │
│ ⚙️ backend    idle         -            3          0                  │
│ 🔍 debugger   idle         -            0          0                  │
│ 🧪 tester     idle         -            2          0                  │
│ 🏛️ architect  idle         -            1          0                  │
└──────────────────────────────────────────────────────────────────────┘

  Next cycle in 30 seconds... (Ctrl+C to stop)
```
