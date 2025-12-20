# FRONTEND Agent

**ID:** FRONTEND
**Emoji:** 🎨
**Color:** Magenta (#A855F7)
**Model:** claude-sonnet-4-20250514
**Daily Token Budget:** 12,000

## Role

The FRONTEND agent is an autonomous frontend developer specializing in React, Next.js, TypeScript, and Tailwind CSS development for Control Station.

## Responsibilities

- Develop and polish React components
- Implement Framer Motion animations
- Fix UI/UX issues
- Ensure TypeScript compliance
- Visual review via screenshots
- Maintain accessibility standards
- Log to COMMS.md for coordination

## Usage

```bash
# Single task
python -m autoagents.agents.frontend.runner

# 5 iterations
python -m autoagents.agents.frontend.runner -i 5

# Focus on specific module
python -m autoagents.agents.frontend.runner --module dashboard

# With screenshot capture
python -m autoagents.agents.frontend.runner --screenshot

# Continuous mode
python -m autoagents.agents.frontend.runner --continuous

# List pending tasks
python -m autoagents.agents.frontend.runner --list
```

## Files

- `config.json` - Agent configuration
- `runner.py` - Main execution script
- `prompts/system_prompt.md` - System prompt
- `tasks.json` - Frontend tasks queue

## Modules

- dashboard - Main dashboard view
- focusguardian - Focus tracking module
- roadmap - Project roadmap
- alarm - Alarm system (gold standard - read only)
- james - AI assistant module

## COMMS.md Section

The FRONTEND updates the 🎨 FRONTEND section in COMMS.md with:
- Current module focus
- Tasks completed
- Files modified
- Session logs
