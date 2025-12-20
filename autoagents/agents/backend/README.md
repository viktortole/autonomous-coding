# BACKEND Agent

**ID:** BACKEND
**Emoji:** ⚙️
**Color:** Amber (#F59E0B)
**Model:** claude-sonnet-4-20250514
**Daily Token Budget:** 12,000

## Role

The BACKEND agent is an autonomous Rust/Axum/SQLite developer for Control Station's Tauri backend.

## Responsibilities

- Develop Rust backend services
- Implement Tauri commands
- Manage SQLite database operations
- Build Axum HTTP API endpoints
- Handle inter-process communication
- Ensure safe memory management
- Log to COMMS.md for coordination

## Usage

```bash
# Single task
python -m autoagents.agents.backend.runner

# 5 iterations
python -m autoagents.agents.backend.runner -i 5

# Specific task
python -m autoagents.agents.backend.runner --task BACKEND-001

# Continuous mode
python -m autoagents.agents.backend.runner --continuous

# List tasks
python -m autoagents.agents.backend.runner --list
```

## Files

- `config.json` - Agent configuration
- `runner.py` - Main execution script
- `prompts/system_prompt.md` - System prompt
- `tasks.json` - Backend tasks queue

## Key Directories

- `src-tauri/src/` - Rust source code
- `src-tauri/src/api/` - Axum HTTP API
- `src-tauri/Cargo.toml` - Rust dependencies

## COMMS.md Section

The BACKEND updates the ⚙️ BACKEND section in COMMS.md with:
- Current Rust work
- API endpoints added
- Database migrations
- Session logs
