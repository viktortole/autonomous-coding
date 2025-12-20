# TESTER Agent

**ID:** TESTER
**Emoji:** 🧪
**Color:** Green (#22C55E)
**Model:** claude-sonnet-4-20250514
**Daily Token Budget:** 10,000

## Role

The TESTER agent focuses on writing tests, improving test coverage, and ensuring quality assurance for Control Station.

## Responsibilities

- Write unit tests (Vitest)
- Improve test coverage
- Create integration tests
- Write E2E tests
- Fix flaky tests
- Maintain test utilities
- Log to COMMS.md for coordination

## Usage

```bash
# Single session
python -m autoagents.agents.tester.runner

# 5 iterations
python -m autoagents.agents.tester.runner -i 5

# Focus on module
python -m autoagents.agents.tester.runner --module dashboard

# Continuous mode
python -m autoagents.agents.tester.runner --continuous

# List tasks
python -m autoagents.agents.tester.runner --list
```

## Files

- `config.json` - Agent configuration
- `runner.py` - Main execution script
- `prompts/system_prompt.md` - System prompt
- `tasks.json` - Testing tasks queue

## Testing Framework

- **Unit Tests:** Vitest
- **Test Location:** Colocated in `__tests__/` folders
- **Coverage Target:** 80%+
- **Current Stats:** 2583 tests, 100% passing

## COMMS.md Section

The TESTER updates the 🧪 TESTER section in COMMS.md with:
- Tests written
- Coverage changes
- Failing tests fixed
- Session logs
