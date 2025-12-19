# AUTOAGENTS - Autonomous Coding Agents

Autonomous coding agents using Claude Code SDK for Control Station development.

## Installation

```bash
# Install with pip (editable mode)
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# List tasks
python -m autoagents.runners.task_runner --list

# Run first pending task
python -m autoagents.runners.task_runner

# Run specific task
python -m autoagents.runners.task_runner --task TASK-001

# Run with custom iterations
python -m autoagents.runners.task_runner --task TASK-001 --max-iterations 3
```

## Project Structure

```
autonomous-coding/
├─ autoagents/                     # Shared engine (code only)
│  ├─ lib/                         # Client, logging, streaming, security
│  ├─ agents/                      # Agent configs + sentinel modules
│  └─ runners/                     # Task/front/sentinel runners
├─ templates/
│  └─ agent_workspace/             # Clean workspace template (tasks/logs/config)
├─ workspaces/                     # One isolated workspace per agent
├─ scripts/                        # Convenience CLI wrappers
├─ integrations/
│  └─ control_station/             # Control Station runner
├─ tasks/                          # Shared baseline task sets
├─ prompts/                        # Prompt templates
├─ docs/                           # Documentation
└─ archive/                        # Legacy code for reference
```

## Task Files

Tasks live in JSON files inside each workspace. The root `tasks/` directory is the
baseline template that gets copied into each new workspace.

```
workspaces/<agent>/tasks/
├─ general.json
├─ frontend.json
└─ sentinel.json
```

## Workspaces (Isolated Agent State)

```bash
# Create a new workspace (copy template)
cp -r templates/agent_workspace workspaces/agent_001

# Run using that workspace (tasks/logs/screenshots are isolated)
python -m autoagents.runners.task_runner --workspace workspaces/agent_001
python -m autoagents.runners.frontend_runner --workspace workspaces/agent_001 --module dashboard
python -m autoagents.runners.sentinel_runner --workspace workspaces/agent_001 --continuous
```

## Available Agents

| Agent | Role | Command |
|-------|------|---------|
| Task Runner | General task execution | `python -m autoagents.runners.task_runner` |
| Frontend | UI/UX development | `python -m autoagents.runners.frontend_runner` |
| Sentinel | DevOps health monitoring | `python -m autoagents.runners.sentinel_runner` |
| CS Agent | Control Station integration | `python integrations/control_station/run_cs_agent.py` |

## Configuration

Set environment variables in `.env`:

```bash
# Authentication (at least one required)
ANTHROPIC_API_KEY=your_api_key
# OR
CLAUDE_CODE_OAUTH_TOKEN=your_oauth_token

# Optional: Webhook for progress notifications
PROGRESS_N8N_WEBHOOK_URL=https://your-webhook-url
```

## Testing

```bash
pytest
pytest --cov=autoagents
pytest tests/test_lib/test_styles.py
```

## Backward Compatibility

Legacy scripts are archived. Use module entrypoints or the wrappers in `scripts/` if
you want `python scripts/run_task.py` style usage.

## Logs

Session logs are saved inside each workspace under `logs/`:

- Task logs: `logs/TASK-XXX_YYYYMMDD_HHMMSS.log`
- Frontend logs: `logs/frontend/frontend_YYYYMMDD_HHMMSS.log`
- Sentinel logs: `logs/sentinel/sentinel_YYYYMMDD_HHMMSS.log`

## License

MIT
