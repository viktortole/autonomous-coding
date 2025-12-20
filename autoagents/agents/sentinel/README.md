# SENTINEL Agent

**ID:** SENTINEL
**Emoji:** 🛡️
**Color:** Red (#EF4444)
**Model:** claude-sonnet-4-20250514
**Daily Token Budget:** 10,000

## Role

The SENTINEL agent is the DevOps guardian for Control Station. It monitors system health, detects issues, and performs auto-repairs.

## Responsibilities

- Monitor dev server health (HTTP checks)
- Verify TypeScript compilation
- Run test suite and track failures
- Auto-repair crashed services
- Database health monitoring
- Visual verification of Tauri windows
- Log to COMMS.md for coordination

## Usage

```bash
# Single check
python -m autoagents.agents.sentinel.runner

# 5 iterations
python -m autoagents.agents.sentinel.runner -i 5

# Continuous monitoring
python -m autoagents.agents.sentinel.runner --continuous

# List health tasks
python -m autoagents.agents.sentinel.runner --list

# Deep health check
python -m autoagents.agents.sentinel.runner --deep
```

## Files

- `config.json` - Agent configuration
- `runner.py` - Main execution script
- `health_monitors.py` - Health check implementations
- `repair_workflows.py` - Auto-repair procedures
- `prompts/system_prompt.md` - System prompt
- `tasks.json` - Health check tasks

## COMMS.md Section

The SENTINEL updates the 🛡️ SENTINEL section in COMMS.md with:
- Current health status
- Recent repairs performed
- Active monitoring mode
- Session logs
