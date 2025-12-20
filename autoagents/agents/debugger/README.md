# DEBUGGER Agent

**ID:** DEBUGGER
**Emoji:** 🔍
**Color:** Orange (#F97316)
**Model:** claude-sonnet-4-20250514
**Daily Token Budget:** 10,000

## Role

The DEBUGGER agent specializes in finding and fixing bugs, investigating errors, and resolving issues in Control Station.

## Responsibilities

- Investigate error reports
- Analyze stack traces
- Fix TypeScript errors
- Resolve runtime bugs
- Debug React component issues
- Fix Rust panics
- Log to COMMS.md for coordination

## Usage

```bash
# Single investigation
python -m autoagents.agents.debugger.runner

# 5 iterations
python -m autoagents.agents.debugger.runner -i 5

# Specific bug
python -m autoagents.agents.debugger.runner --task BUG-001

# Continuous mode
python -m autoagents.agents.debugger.runner --continuous

# List known bugs
python -m autoagents.agents.debugger.runner --list
```

## Files

- `config.json` - Agent configuration
- `runner.py` - Main execution script
- `prompts/system_prompt.md` - System prompt
- `tasks.json` - Bug tracking queue

## Debugging Process

1. Read error logs and stack traces
2. Identify root cause
3. Locate affected files
4. Implement fix
5. Verify fix with tests
6. Update COMMS.md

## COMMS.md Section

The DEBUGGER updates the 🔍 DEBUGGER section in COMMS.md with:
- Active investigations
- Bugs fixed
- Root cause analysis
- Session logs
