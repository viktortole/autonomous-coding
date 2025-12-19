# AUTOAGENTS - Autonomous Coding System

## Overview

AUTOAGENTS is an autonomous coding system that deploys agents via the Claude Code SDK.
The code engine lives in `autoagents/`, while each agent runs in its own workspace
so tasks, logs, and screenshots are isolated.

## Core Concepts

- Engine (shared code): `autoagents/`
- Workspace (agent state): `workspaces/<agent>/`
- Template (fresh workspace): `templates/agent_workspace/`

## Architecture

```
Engine: autoagents/  -->  Runner (task/frontend/sentinel)
                        |
                        v
Workspace: workspaces/<agent>/
  ├─ tasks/
  ├─ logs/
  └─ screenshots/
```

## Workspace Layout

```
workspaces/<agent>/
├─ tasks/
│  ├─ general.json
│  ├─ frontend.json
│  └─ sentinel.json
├─ config/
│  └─ agent.json
├─ logs/
└─ screenshots/
```

## Create a New Agent Workspace

```bash
cp -r templates/agent_workspace workspaces/agent_001
```

## Run an Agent

```bash
python -m autoagents.runners.task_runner --workspace workspaces/agent_001
python -m autoagents.runners.frontend_runner --workspace workspaces/agent_001 --module dashboard
python -m autoagents.runners.sentinel_runner --workspace workspaces/agent_001 --continuous
```

## Task Schema

Tasks are defined in JSON (see `tasks/schema/task_schema_v5.json`). Each task file
includes queues and status tracking.

## Notes

- Legacy scripts and root-level task files are archived under `archive/`.
- Use module entrypoints or wrappers in `scripts/` for CLI convenience.
