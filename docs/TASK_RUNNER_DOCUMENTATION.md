# TASK RUNNER Agent Documentation

**Created:** 2025-12-20
**Session:** CMDTV Session (ULTRATHINK)
**Author:** Claude Opus 4.5 + ToleV
**Purpose:** Complete documentation of the General Task Runner autonomous agent system

---

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [task_runner.py](#task_runnerpy)
4. [general.json](#generaljson)
5. [How Everything Works Together](#how-everything-works-together)
6. [Iteration Strategy](#iteration-strategy)
7. [Honest Assessment](#honest-assessment)
8. [Recommended Improvements](#recommended-improvements)
9. [Updates Log](#updates-log)

---

## Overview

```
TASK RUNNER = General-Purpose Autonomous Coding Agent

It does 3 things:
1. Loads tasks from JSON configuration files
2. Picks the next pending task from the queue
3. Runs Claude AI in a loop to implement features/fixes
```

### Quick Start

```bash
# Run first pending task (1 iteration by default)
python -m autoagents.runners.task_runner

# Run specific task
python -m autoagents.runners.task_runner --task TASK-001

# Run 5 iterations
python -m autoagents.runners.task_runner --max-iterations 5

# List all tasks
python -m autoagents.runners.task_runner --list

# Use custom tasks file
python -m autoagents.runners.task_runner --tasks-file my-tasks.json
```

---

## File Structure

```
autonomous-coding/
├── autoagents/
│   ├── runners/
│   │   └── task_runner.py       (Main runner - ~420 lines)
│   └── lib/
│       ├── client.py            (Claude API client)
│       ├── streaming.py         (Response streaming)
│       ├── output.py            (Pretty printing)
│       ├── logging_utils.py     (Session logging)
│       └── workspace.py         (Path resolution)
└── tasks/
    └── general.json             (Task definitions - ~1000 lines)
```

---

## task_runner.py

### What It Is

```
task_runner.py = A generic task executor that works with any task JSON file

It does 3 things:
1. Load tasks from JSON (general.json by default)
2. Pick next pending task from queue
3. Run Claude AI with context to implement the task
```

### Code Structure (Top to Bottom)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 1-50: IMPORTS & SETUP                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  • Load environment variables (.env)                                            │
│  • Import shared library utilities (styles, output, client, streaming)          │
│  • Set default model: claude-sonnet-4-20250514                                  │
│  • Set default tasks file: general.json                                         │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 49-107: DATA MANAGEMENT                                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  load_tasks(tasks_file: Path) -> dict                                           │
│      Load task definitions from JSON file                                       │
│                                                                                 │
│  save_tasks(data: dict, tasks_file: Path) -> None                              │
│      Save updated task definitions                                              │
│                                                                                 │
│  get_pending_task(data: dict) -> dict | None                                   │
│      Get first task from queue.pending array                                    │
│                                                                                 │
│  get_task_by_id(data: dict, task_id: str) -> dict | None                       │
│      Find specific task by ID                                                   │
│                                                                                 │
│  update_task_status(data, task_id, status, tasks_file)                         │
│      Move task between queues (pending → in_progress → completed/failed)       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 109-176: PROMPT BUILDING                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  build_task_prompt(task: dict, project: dict) -> str                           │
│      Converts a task object into a comprehensive Claude prompt                  │
│                                                                                 │
│  Prompt includes:                                                               │
│  ├── Task title, ID, priority, complexity                                      │
│  ├── Problem description                                                        │
│  ├── Goal to achieve                                                            │
│  ├── Target files to modify                                                     │
│  ├── Context files to read                                                      │
│  ├── Patterns to follow / anti-patterns to avoid                               │
│  ├── Verification commands                                                      │
│  └── Project context (root path, stack)                                        │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 178-254: TASK RUNNER                                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  async def run_task(task, project, model, max_iterations, workspace):          │
│      Main execution loop for a single task                                      │
│                                                                                 │
│      1. Print task header                                                       │
│      2. Build initial prompt from task definition                               │
│      3. Create session log file                                                 │
│      4. Loop through iterations:                                                │
│         - Iteration 1: Full task prompt                                         │
│         - Iteration 2+: "Continue working" prompt                               │
│         - Create Claude client                                                  │
│         - Stream AI response                                                    │
│         - Log output to file                                                    │
│         - 3 second delay between iterations                                     │
│      5. Return success/failure                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 256-300: LIST TASKS                                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│  def list_tasks(data: dict) -> None                                            │
│      Pretty print all tasks with status emojis                                  │
│                                                                                 │
│      Status emojis:                                                             │
│      ⏳ pending | 🔄 in_progress | ✅ completed | ❌ failed                      │
│                                                                                 │
│      Priority colors:                                                           │
│      🔴 critical | 🟡 high | 🔵 medium | 🟢 low                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 302-419: MAIN ENTRY POINT                                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│  parse_args() -> argparse.Namespace                                            │
│      Parse CLI arguments: --task, --max-iterations, --model, --list            │
│                                                                                 │
│  async def main():                                                              │
│      1. Setup Windows UTF-8                                                     │
│      2. Print banner                                                            │
│      3. Load tasks from JSON                                                    │
│      4. Handle --list flag                                                      │
│      5. Get task (specific or next pending)                                     │
│      6. Mark task as in_progress                                                │
│      7. Run the task                                                            │
│      8. Update final status (completed/failed)                                  │
│      9. Print success/failure banner                                            │
│      10. Show queue status                                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### The Flow (Visual)

```
    ┌──────────────────┐
    │   python -m      │
    │   task_runner    │
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │  Load general    │
    │     .json        │
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │  Get next task   │
    │  from queue      │
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │  Mark task as    │
    │  "in_progress"   │
    └────────┬─────────┘
             ↓
    ╔══════════════════╗
    ║   ITERATION      ║◄─────────────────────────────┐
    ║   LOOP           ║                              │
    ╚════════╤═════════╝                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  Build prompt    │  ← Task details + project   │
    │  from task       │    context + instructions    │
    └────────┬─────────┘                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  Create Claude   │  ← claude-sonnet-4          │
    │  API client      │                              │
    └────────┬─────────┘                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  Stream AI       │  ← Claude reads files,      │
    │  response        │    writes code, runs tests   │
    └────────┬─────────┘                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  Log iteration   │                              │
    │  to file         │                              │
    └────────┬─────────┘                              │
             ↓                                        │
        ┌────┴────┐                                   │
        │ More    │                                   │
        │ iters?  │                                   │
        └────┬────┘                                   │
         YES │ NO                                     │
             │                                        │
    ┌────────┴────────┐                               │
    │  Sleep 3 sec    ├───────────────────────────────┘
    └─────────────────┘
             ↓
    ┌──────────────────┐
    │  Mark task as    │
    │  "completed" or  │
    │  "failed"        │
    └──────────────────┘
```

### Key Functions

| Function | What It Does |
|----------|--------------|
| `load_tasks()` | Reads task definitions from JSON file |
| `get_pending_task()` | Returns first task in queue.pending |
| `update_task_status()` | Moves task between queues, saves JSON |
| `build_task_prompt()` | Converts task object to Claude prompt |
| `run_task()` | Main async loop - runs Claude for N iterations |
| `list_tasks()` | Pretty-prints all tasks with status emojis |

### Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  task_runner.py in ONE SENTENCE:                                                │
│                                                                                 │
│  "A simple loop that loads tasks from JSON, picks the next pending one,         │
│   builds a prompt with all context, and runs Claude to implement it"            │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## general.json

### What It Is

```
general.json = The task queue and definitions for general coding work

It contains:
1. Project metadata (name, root, stack, gold standard)
2. Agent definitions (JARVIS1-4, CMDTV with roles)
3. Global rules (forbidden patterns, required checks)
4. Task definitions (rich context for each task)
5. Queue management (pending, in_progress, completed, failed)
6. Iteration strategy (Make It Work → Make It Right → Make It Fast)
```

### File Size & Structure Overview

```
general.json = ~1000 lines (~30 KB)

┌─────────────────────────────────────────────────────────────────────────────────┐
│  SECTION                          LINES        PURPOSE                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  _schema                          1-10         Version, author, philosophy      │
│  agent_protocol                   11-58        Pre-flight, checkpoints, tools   │
│  project                          59-108       Control Station details          │
│  agents                           109-171      JARVIS1-4, CMDTV definitions     │
│  global_rules                     172-203      Forbidden patterns, code rules   │
│  tasks[]                          204-963      Array of task definitions        │
│  queue                            964-978      pending, in_progress, completed  │
│  iteration_strategy               979-997      3-phase iteration approach       │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Section 1: _schema

```json
{
  "_schema": {
    "version": "3.0.0",
    "name": "AUTOAGENTS Task Intelligence System",
    "description": "Ultimate task definitions engineered for Claude Code autonomous agents",
    "philosophy": "Every task gives the agent COMPLETE context to succeed autonomously"
  }
}
```

### Section 2: agent_protocol

```json
{
  "agent_protocol": {
    "pre_flight": [
      "1. Read this entire task definition thoroughly",
      "2. Read all context files listed before writing ANY code",
      "3. Run verification.pre_checks commands to understand current state",
      "4. If anything is unclear, STOP and document the question",
      "5. Enter Plan Mode for tasks marked complexity: hard"
    ],
    "thinking_mode": {
      "default": "ULTRATHINK",
      "trigger_phrases": [
        "Think step-by-step about this problem",
        "What could go wrong here?",
        "What's the simplest solution that works?"
      ]
    },
    "checkpoints": {
      "after_reading": "Summarize what you understand before coding",
      "after_implementation": "Run all verification commands",
      "before_completion": "Self-assess against quality_rubric"
    },
    "tools_available": {
      "claude_code": ["Task", "Glob", "Grep", "Read", "Edit", "Write", "Bash"],
      "workflows": ["Plan Mode for complex tasks", "TodoWrite for tracking"]
    }
  }
}
```

### Section 3: project

```json
{
  "project": {
    "name": "Control Station",
    "root": "C:/Users/ToleV/Desktop/TestingFolder/control-station",
    "stack": ["Next.js 16", "React 19", "TypeScript 5", "Tauri 2.9", "Rust", "SQLite", "Axum"],
    "architecture": {
      "frontend": "src/modules/* - Feature modules",
      "backend": "src-tauri/src/* - Rust backend",
      "shared": "src/services/* - Shared services"
    },
    "gold_standard": {
      "module": "src/modules/alarm",
      "why": "Perfect separation of concerns, proper hooks, full test coverage"
    },
    "commands": {
      "dev": "npm run dev",
      "test": "npm test",
      "typecheck": "npx tsc --noEmit"
    }
  }
}
```

### Section 4: agents

```json
{
  "agents": {
    "JARVIS1": { "role": "Primary Development", "expertise": ["React Hooks", "TypeScript"] },
    "JARVIS2": { "role": "Testing & QA", "expertise": ["Vitest", "Bug Hunting"] },
    "JARVIS3": { "role": "Backend & Integration", "expertise": ["Rust", "Axum", "SQLite"] },
    "JARVIS4": { "role": "UI & Polish", "expertise": ["React", "CSS/Tailwind", "Animations"] },
    "CMDTV": { "role": "Orchestrator & Senior Review", "model": "claude-opus-4-5-20250514" }
  }
}
```

### Section 5: global_rules

```json
{
  "global_rules": {
    "forbidden_patterns": [
      "src/modules/alarm/** - Gold standard, never modify",
      ".claude/AGENTLOGGER.json - Multi-agent coordination file",
      "package-lock.json - Auto-generated"
    ],
    "required_before_completion": [
      "npx tsc --noEmit - Must show 0 errors",
      "npm run lint - Must pass",
      "npm test - Related tests must pass"
    ],
    "code_patterns": {
      "hooks": "Extract ALL logic to custom hooks, components are UI-only",
      "imports": "Use barrel exports (index.ts) and absolute paths (@/)",
      "testing": "Co-locate tests in __tests__ folders",
      "cleanup": "ALL useEffect hooks with subscriptions MUST have cleanup"
    }
  }
}
```

### Section 6: tasks[] - Task Structure

Each task follows this comprehensive structure:

```json
{
  "id": "TASK-001",
  "title": "Add Error Boundaries to Module Manager",
  "category": "reliability",
  "priority": "high",
  "status": "pending",
  "agent": "JARVIS1",
  "complexity": "medium",
  "iterations": 2,

  "description": {
    "problem": "Module Manager crashes the entire app when a module fails",
    "goal": "Wrap modules in error boundaries with friendly error UI",
    "scope": "Add ErrorBoundary component to ModuleManager",
    "user_impact": "White screen → Error message with retry option"
  },

  "thinking_prompts": [
    "What are all the ways a module could fail to load?",
    "How should the error UI look?",
    "How do we allow users to retry?"
  ],

  "files": {
    "target": ["src/modules/module-manager/components/ErrorBoundary.tsx"],
    "context": ["src/modules/alarm/components/AlarmManager.tsx"],
    "tests": ["src/modules/module-manager/__tests__/ErrorBoundary.test.tsx"],
    "forbidden": ["src/modules/alarm/**"]
  },

  "knowledge": {
    "gold_standard": { "file": "...", "learn": "..." },
    "patterns_to_follow": ["React Error Boundary class pattern", "..."],
    "anti_patterns": ["Don't catch errors in functional components", "..."],
    "code_example": { "description": "...", "code": "..." }
  },

  "verification": {
    "pre_checks": ["npm test -- --grep ModuleManager"],
    "commands": ["npx tsc --noEmit", "npm test", "npm run build"],
    "success_criteria": ["ErrorBoundary catches render errors", "..."],
    "manual_test": ["Throw error in module, verify UI shows", "..."]
  },

  "architecture": {
    "module": "module-manager",
    "layer": "frontend",
    "data_flow": "ModuleManager → ErrorBoundary → Module"
  },

  "intelligence": {
    "notes": "React 18+ has improved error boundary support",
    "known_issues": ["Error boundaries don't catch event handler errors"],
    "tips": ["Start simple, add features incrementally"],
    "estimated_minutes": 45
  },

  "quality_rubric": {
    "functionality": "Error boundary catches render errors",
    "code_quality": "Clean TypeScript, follows project patterns",
    "testing": "Unit tests cover error catching and retry"
  },

  "rollback": {
    "if_breaks": "Revert ModuleManager.tsx, delete ErrorBoundary.tsx",
    "git_command": "git checkout HEAD -- src/modules/module-manager/"
  }
}
```

### Section 7: queue

```json
{
  "queue": {
    "pending": ["TASK-001", "TASK-002", "TASK-003", "TASK-004", "TASK-005"],
    "in_progress": [],
    "completed": ["TASK-000"],
    "failed": []
  }
}
```

### Section 8: iteration_strategy

```json
{
  "iteration_strategy": {
    "iteration_1": {
      "name": "Make It Work",
      "focus": "Core functionality, happy path only",
      "skip": "Edge cases, polish, optimization"
    },
    "iteration_2": {
      "name": "Make It Right",
      "focus": "Edge cases, error handling, code quality",
      "skip": "Performance optimization"
    },
    "iteration_3": {
      "name": "Make It Fast",
      "focus": "Performance, optimization, polish",
      "skip": "Nothing - final pass"
    }
  }
}
```

### Current Tasks

| ID | Title | Priority | Status | Est. Time |
|----|-------|----------|--------|-----------|
| TASK-000 | Fix JAMES Vision Screenshot Threading Freeze | critical | ✅ completed | 90 min |
| TASK-001 | Add Error Boundaries to Module Manager | high | ⏳ pending | 45 min |
| TASK-002 | Implement Alert Sound Notifications | medium | ⏳ pending | 60 min |
| TASK-003 | Add Keyboard Shortcuts to Device Control | low | ⏳ pending | 30 min |
| TASK-004 | Implement Activity Log Export Feature | medium | ⏳ pending | 75 min |
| TASK-005 | Add System Monitor Performance Graphs | low | ⏳ pending | 180 min |

### Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  general.json in ONE SENTENCE:                                                  │
│                                                                                 │
│  "A comprehensive task queue with rich context - problem statements, files,     │
│   patterns, verification steps, and quality rubrics - so agents can work        │
│   autonomously without asking questions"                                        │
└─────────────────────────────────────────────────────────────────────────────────┘

Key insight: Each task contains EVERYTHING an agent needs to succeed:
             What to do, why, how, what files, what patterns, how to verify.
```

---

## How Everything Works Together

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         THE TASK RUNNER SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   YOU RUN:                                                                      │
│   python -m autoagents.runners.task_runner -i 5                                │
│                                                                                 │
│                              ↓                                                  │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  task_runner.py (The Executor)                                          │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │  1. Loads general.json (tasks + project context)                        │  │
│   │  2. Picks first pending task from queue                                 │  │
│   │  3. Builds comprehensive prompt from task definition                    │  │
│   │  4. Runs Claude API for N iterations                                    │  │
│   │  5. Updates queue status when done                                      │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                              ↓                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  general.json (The Task Queue)                                          │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │  • Project knowledge (Control Station stack, modules, paths)            │  │
│   │  • 6 task definitions (with full context)                               │  │
│   │  • Queue management (pending → in_progress → completed)                 │  │
│   │  • Global rules (forbidden patterns, required checks)                   │  │
│   │  • Iteration strategy (Work → Right → Fast)                             │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                              ↓                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  Claude AI (The Worker)                                                  │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │  • Reads context files (gold standard, patterns)                        │  │
│   │  • Implements the feature/fix                                           │  │
│   │  • Runs verification commands                                           │  │
│   │  • Self-assesses against quality rubric                                 │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### One-Liner Summary of Each File

| File | Purpose |
|------|---------|
| `task_runner.py` | **The executor** - loads tasks, runs Claude, updates queue |
| `general.json` | **The brain** - tasks, context, rules, verification |

---

## Iteration Strategy

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      THREE-PHASE ITERATION STRATEGY                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ITERATION 1: MAKE IT WORK                                                     │
│   ┌──────────────────────────────────────────────────────────────────────────┐ │
│   │  Focus: Core functionality, happy path only                              │ │
│   │  Skip:  Edge cases, polish, optimization                                 │ │
│   │  Goal:  Get something working end-to-end                                 │ │
│   └──────────────────────────────────────────────────────────────────────────┘ │
│                              ↓                                                  │
│   ITERATION 2: MAKE IT RIGHT                                                    │
│   ┌──────────────────────────────────────────────────────────────────────────┐ │
│   │  Focus: Edge cases, error handling, code quality                         │ │
│   │  Skip:  Performance optimization                                         │ │
│   │  Goal:  Handle all scenarios, clean code                                 │ │
│   └──────────────────────────────────────────────────────────────────────────┘ │
│                              ↓                                                  │
│   ITERATION 3: MAKE IT FAST                                                     │
│   ┌──────────────────────────────────────────────────────────────────────────┐ │
│   │  Focus: Performance, optimization, polish                                │ │
│   │  Skip:  Nothing - final pass                                             │ │
│   │  Goal:  Ship-ready, optimized code                                       │ │
│   └──────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│   WHY THIS WORKS:                                                               │
│   • Iteration 1 finds fundamental issues early                                 │
│   • Iteration 2 hardens the solution                                           │
│   • Iteration 3 polishes for production                                        │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Honest Assessment

### What's GOOD

| Aspect | Why It's Good |
|--------|---------------|
| **Rich task definitions** | Every task has problem, goal, files, patterns, verification |
| **Queue management** | Clean pending → in_progress → completed flow |
| **Iteration strategy** | Work → Right → Fast prevents over-engineering early |
| **Gold standard reference** | Tasks reference alarm module as example |
| **Verification commands** | Every task knows how to verify itself |
| **Quality rubric** | Tasks self-assess against clear criteria |
| **Rollback instructions** | Every task has git command to undo changes |

### What's INCOMPLETE or NEEDS WORK

| Issue | Impact | Severity |
|-------|--------|----------|
| **No COMMS.md integration** | Doesn't log to shared agent log | Medium |
| **No token tracking** | No budget or daily limits | Low |
| **Simple system prompt** | Just "expert developer fixing bugs" | Low |
| **No screenshot capability** | Can't visually verify UI changes | Medium |
| **No exploration mode** | Stops if queue is empty | Low |

### What's UNCLEAR

1. Does the 3-second delay between iterations help or hurt?
2. Should failed tasks be retried automatically?
3. How should agents coordinate when running multiple task_runners?

---

## Recommended Improvements

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  RECOMMENDED IMPROVEMENTS (in order of priority)                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  1. ⏳ ADD COMMS.MD LOGGING (PENDING)                                           │
│     └── Log session start/end to COMMS.md                                      │
│     └── Other agents can see what task_runner is working on                    │
│                                                                                 │
│  2. ⏳ ADD TOKEN TRACKING (PENDING)                                             │
│     └── Track daily token usage like frontend_runner                           │
│     └── Warn when approaching budget                                           │
│                                                                                 │
│  3. ⏳ ADD EXPLORATION MODE (PENDING)                                           │
│     └── When queue is empty, explore codebase for improvements                 │
│     └── Like frontend_runner's "EXPLORE-{iteration}" tasks                     │
│                                                                                 │
│  4. ⏳ IMPROVE SYSTEM PROMPT (PENDING)                                          │
│     └── Include ULTRATHINK protocol                                            │
│     └── Add project context from general.json                                  │
│                                                                                 │
│  5. ⏳ ADD CONTEXT INJECTION (PENDING)                                          │
│     └── Read COMMS.md, CLAUDE.md before starting                               │
│     └── Follow project conventions                                             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Session Information

**Documented by:** CMDTV (Claude Opus 4.5)
**Date:** 2025-12-20
**Session:** ULTRATHINK Mode - Agent Documentation

This documentation was created during a session where:
- task_runner.py was analyzed (420 lines)
- general.json was analyzed (1000 lines)
- Both files were documented with visual diagrams
- All code patterns and data structures were explained

---

## Updates Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-20 | CMDTV | Initial documentation created |

---

*End of TASK RUNNER Agent Documentation*
