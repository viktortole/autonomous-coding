# ARCHITECT Agent

**ID:** ARCHITECT
**Emoji:** 🏛️
**Color:** Blue (#3B82F6)
**Model:** claude-sonnet-4-20250514
**Daily Token Budget:** 8,000

## Role

The ARCHITECT agent focuses on codebase organization, architecture decisions, tech debt management, and maintaining coding standards.

## Responsibilities

- Review and improve folder structure
- Identify and eliminate duplicate code
- Enforce naming conventions
- Manage tech debt backlog
- Document architectural decisions
- Review module boundaries
- Log to COMMS.md for coordination

## Usage

```bash
# Single analysis
python -m autoagents.agents.architect.runner

# 5 iterations
python -m autoagents.agents.architect.runner -i 5

# Specific task
python -m autoagents.agents.architect.runner --task ARCH-001

# Continuous mode
python -m autoagents.agents.architect.runner --continuous

# List tasks
python -m autoagents.agents.architect.runner --list
```

## Files

- `config.json` - Agent configuration
- `runner.py` - Main execution script
- `prompts/system_prompt.md` - System prompt
- `tasks.json` - Architecture tasks queue

## Focus Areas

- Module boundaries and dependencies
- Code duplication detection
- File naming conventions
- Folder organization
- Import structure
- Dead code elimination

## COMMS.md Section

The ARCHITECT updates the 🏛️ ARCHITECT section in COMMS.md with:
- Architecture reviews
- Refactoring proposals
- Tech debt items
- Session logs
