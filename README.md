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
# List all tasks
python -m autoagents.runners.task_runner --list

# Run first pending task
python -m autoagents.runners.task_runner

# Run specific task
python -m autoagents.runners.task_runner --task TASK-001

# Run with custom iterations
python -m autoagents.runners.task_runner --task TASK-001 --max-iterations 3
```

## Available Agents

| Agent | Role | Command |
|-------|------|---------|
| **Task Runner** | General task execution | `python -m autoagents.runners.task_runner` |
| **Frontend** | UI/UX development | `python -m autoagents.runners.frontend_runner` |
| **Sentinel** | DevOps health monitoring | `python -m autoagents.runners.sentinel_runner` |
| **CS Agent** | Control Station integration | `python -m autoagents.runners.cs_agent_runner` |

## Project Structure

```
autoagents/
├── lib/                    # Shared utilities
│   ├── styles.py           # Terminal colors
│   ├── output.py           # Visual output functions
│   ├── client.py           # Claude SDK client factory
│   ├── streaming.py        # AI response streaming
│   ├── logging_utils.py    # Session logging
│   └── security.py         # Bash security hooks
├── agents/                 # Agent configurations
│   ├── config.py           # Agent definitions
│   ├── emojis.py           # Emoji mappings
│   └── sentinel/           # SENTINEL-specific modules
└── runners/                # Entry point scripts
    ├── task_runner.py      # General task runner
    ├── frontend_runner.py  # Frontend agent
    └── sentinel_runner.py  # Health monitoring
```

## Task Files

Tasks are defined in JSON files in the `tasks/` directory:

| File | Purpose |
|------|---------|
| `tasks/general.json` | General development tasks |
| `tasks/frontend.json` | Frontend/UI tasks |
| `tasks/sentinel.json` | Health monitoring tasks |

## Configuration

### Environment Variables

Set in `.env` file:

```bash
# Authentication (at least one required)
ANTHROPIC_API_KEY=your_api_key
# OR
CLAUDE_CODE_OAUTH_TOKEN=your_oauth_token

# Optional: Webhook for progress notifications
PROGRESS_N8N_WEBHOOK_URL=https://your-webhook-url
```

### Agent Models

Default model: `claude-sonnet-4-20250514`

Available agents use different models:
- **JARVIS1-4**: Sonnet 4 (general development)
- **CMDTV**: Opus 4.5 (senior review)
- **SENTINEL**: Sonnet 4 (health monitoring)
- **CONFIG_FRONTEND**: Sonnet 4 (UI/UX)

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=autoagents

# Run specific test file
pytest tests/test_lib/test_styles.py
```

## Usage Examples

### Task Runner

```bash
# List tasks
python -m autoagents.runners.task_runner --list

# Run task with specific model
python -m autoagents.runners.task_runner --task TASK-001 --model claude-opus-4-5-20250514

# Use custom tasks file
python -m autoagents.runners.task_runner --tasks-file ./my-tasks.json
```

### Frontend Agent

```bash
# Run on dashboard module
python -m autoagents.runners.frontend_runner --module dashboard

# Run with visual review
python -m autoagents.runners.frontend_runner --visual-review

# Continuous mode
python -m autoagents.runners.frontend_runner --continuous
```

### Sentinel (Health Monitor)

```bash
# Quick health check
python -m autoagents.runners.sentinel_runner -i 1

# Continuous monitoring
python -m autoagents.runners.sentinel_runner --continuous

# Deep diagnostics
python -m autoagents.runners.sentinel_runner --deep
```

## Backward Compatibility

Legacy scripts at the root level still work:

```bash
python run_task.py --list
python run_frontend_agent.py --module dashboard
python run_sentinel.py --continuous
```

## Logs

Session logs are saved to `logs/`:
- Task logs: `logs/TASK-XXX_YYYYMMDD_HHMMSS.log`
- Frontend logs: `logs/frontend/frontend_YYYYMMDD_HHMMSS.log`
- Sentinel logs: `logs/sentinel/sentinel_YYYYMMDD_HHMMSS.log`

## License

MIT
