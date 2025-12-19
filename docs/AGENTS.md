# 🤖 AUTOAGENTS - Autonomous Coding System

> **Version:** 2.1
> **Created:** 2025-12-19
> **Author:** AUTOAGENTS / CMDTV

---

## 📋 Overview

AUTOAGENTS is an autonomous coding system that deploys Claude Code agents to complete development tasks defined in `feature_list.json`. It uses the **Claude Code SDK** for Python.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTOAGENTS ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   feature_list.json ──► run_task.py ──► Claude Code SDK ──► Agent  │
│         │                    │                │              │      │
│         │                    │                │              ▼      │
│         │                    │                │         ┌────────┐  │
│         ▼                    ▼                ▼         │ JARVIS │  │
│   ┌──────────┐        ┌───────────┐    ┌──────────┐    │  1-4   │  │
│   │  Tasks   │        │  Visual   │    │  OAuth   │    └────────┘  │
│   │  Queue   │        │  Output   │    │  Auth    │         │      │
│   └──────────┘        └───────────┘    └──────────┘         ▼      │
│                                                        Control      │
│                                                        Station      │
│                                                        Project      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ File Structure

```
autonomous-coding/
├── 📜 run_task.py           # Main entry point (Claude Code SDK)
├── 📜 agent_launcher.py     # Legacy CLI launcher (deprecated)
├── 📋 feature_list.json     # Task definitions (v3.0 schema)
├── 🔐 .env                  # Authentication tokens
├── 📋 requirements.txt      # Python dependencies
├── 📖 AGENTS.md             # This documentation
├── 📖 OUTPUT_TEMPLATE.md    # Visual output standards
│
├── 📁 agents/               # Agent configurations
│   └── agent_config.py      # Agent visual config
│
├── 📁 prompts/              # Prompt templates
│   └── coding_prompt.md     # Default coding prompt
│
├── 📁 logs/                 # Execution logs
│   └── TASK-XXX_*.log       # Per-task logs
│
└── 📁 research/             # Research notes
```

---

## 🤖 Available Agents

| Agent | Model | Role | Expertise |
|-------|-------|------|-----------|
| **JARVIS1** | claude-sonnet-4 | Primary Development | React, TypeScript, Hooks |
| **JARVIS2** | claude-sonnet-4 | Testing & QA | Vitest, Coverage, Bug Hunting |
| **JARVIS3** | claude-sonnet-4 | Backend & Integration | Rust, Axum, SQLite, APIs |
| **JARVIS4** | claude-sonnet-4 | UI & Polish | CSS, Animations, UX |
| **CMDTV** | claude-opus-4 | Orchestrator | Architecture, Code Review |

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install claude-code-sdk python-dotenv
```

### 2. Configure Authentication
Create `.env` file:
```env
CLAUDE_CODE_OAUTH_TOKEN=sk-ant-oat01-...
# OR
ANTHROPIC_API_KEY=sk-ant-api03-...
```

### 3. Run a Task
```bash
# Run specific task
python run_task.py --task TASK-000 --max-iterations 5

# Run first pending task
python run_task.py --max-iterations 5

# List all tasks
python run_task.py --list
```

---

## 📊 Task Schema (v3.0)

Each task in `feature_list.json` has this structure:

```json
{
  "id": "TASK-000",
  "title": "Task Title",
  "category": "bugfix|feature|enhancement|reliability",
  "priority": "critical|high|medium|low",
  "status": "pending|in_progress|completed|failed",
  "agent": "JARVIS1",
  "complexity": "easy|medium|hard",
  "iterations": 3,
  "description": {
    "problem": "What's wrong",
    "goal": "What success looks like",
    "scope": "What to change",
    "user_impact": "Before → After"
  },
  "files": {
    "target": ["files to modify"],
    "context": ["files to read"],
    "tests": ["test files"],
    "forbidden": ["never touch"]
  },
  "knowledge": {
    "patterns_to_follow": ["do this"],
    "anti_patterns": ["don't do this"],
    "code_example": { "description": "", "code": "" }
  },
  "verification": {
    "commands": ["npx tsc --noEmit", "npm test"],
    "success_criteria": ["criteria list"]
  }
}
```

---

## 🎨 Visual Output Standards

All agents must follow the visual output template defined in `OUTPUT_TEMPLATE.md`.

### Key Elements:
- 🤖 Banner on startup
- 📋 Task cards with emojis
- 🔄 Progress bars for iterations
- 💭 Thought bubbles for reasoning
- 📖✍️✏️🔍💻 Tool-specific emojis
- ✅❌ Clear status indicators
- 📊 Queue status boxes

---

## 🔄 Iteration Strategy

| Iteration | Name | Focus |
|-----------|------|-------|
| 1 | Make It Work | Core functionality, happy path |
| 2 | Make It Right | Edge cases, error handling |
| 3+ | Make It Fast | Optimization, polish |

---

## 📝 Logs

All executions are logged to `logs/TASK-XXX_YYYYMMDD_HHMMSS.log`:

```
🤖 AUTOAGENTS LOG
======================================================================
Task: TASK-000 - Fix JAMES Vision Screenshot Threading Freeze
Started: 2025-12-19T03:57:10
Model: claude-sonnet-4-20250514
======================================================================

PROMPT:
[Full prompt sent to agent]

======================================================================
📍 ITERATION 1/5
======================================================================
Response:
[Agent's response and actions]
```

---

## 🎯 Project Context

**Target Project:** Control Station
**Location:** `C:/Users/ToleV/Desktop/TestingFolder/control-station`
**Stack:** Next.js 16, React 19, TypeScript 5, Tauri 2.9, Rust, SQLite, Axum

---

## ⚠️ Important Notes

1. **OAuth vs API Key**: Use `CLAUDE_CODE_OAUTH_TOKEN` for Claude Max subscription
2. **Max Iterations**: Keep to 5 or less to avoid long-running sessions
3. **Task Queue**: Tasks are processed from `queue.pending` array
4. **Status Updates**: Script auto-updates `feature_list.json` status

---

## 🔗 Related Files

- `feature_list.json` - Task definitions
- `run_task.py` - Main runner script
- `.env` - Authentication
- `logs/` - Execution history
