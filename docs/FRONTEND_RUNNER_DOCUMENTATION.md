# FRONTEND RUNNER Agent Documentation

**Created:** 2025-12-20
**Session:** CMDTV Session (ULTRATHINK)
**Author:** Claude Opus 4.5 + ToleV
**Purpose:** Complete documentation of the CONFIG-FRONTEND autonomous agent system

---

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [frontend_runner.py](#frontend_runnerpy)
4. [frontend.json](#frontendjson)
5. [Unique Features](#unique-features)
6. [How Everything Works Together](#how-everything-works-together)
7. [Honest Assessment](#honest-assessment)
8. [Recommended Improvements](#recommended-improvements)
9. [Updates Log](#updates-log)

---

## Overview

```
CONFIG-FRONTEND = Specialized Frontend Developer + UI/UX Polish Agent

It does 4 things:
1. Focuses on a specific module (dashboard, focusguardian, james, etc.)
2. Captures screenshots of the Tauri app for visual review
3. Runs Claude AI to implement UI improvements
4. Auto-creates exploration tasks when queue is empty
```

### Quick Start

```bash
# Single iteration on dashboard
python -m autoagents.runners.frontend_runner

# 5 iterations
python -m autoagents.runners.frontend_runner -i 5

# Focus on specific module
python -m autoagents.runners.frontend_runner --module focusguardian

# Run forever (continuous mode)
python -m autoagents.runners.frontend_runner --continuous

# Capture screenshot before each iteration
python -m autoagents.runners.frontend_runner --screenshot

# Visual review mode (start with screenshot analysis)
python -m autoagents.runners.frontend_runner --visual-review

# Run specific task
python -m autoagents.runners.frontend_runner --task FRONTEND-DASH-007

# List pending tasks
python -m autoagents.runners.frontend_runner --list

# Dry run (show what would be done)
python -m autoagents.runners.frontend_runner --dry-run
```

---

## File Structure

```
autonomous-coding/
├── autoagents/
│   ├── runners/
│   │   └── frontend_runner.py   (Main runner - 600 lines)
│   ├── agents/
│   │   └── emojis.py            (FRONTEND_EMOJI, TOOL_EMOJI)
│   └── lib/
│       ├── client.py            (Claude API client)
│       ├── streaming.py         (Response streaming)
│       ├── output.py            (Pretty printing)
│       ├── logging_utils.py     (Session logging)
│       └── workspace.py         (Path resolution)
└── tasks/
    └── frontend.json            (Task definitions - 2200+ lines)
```

---

## frontend_runner.py

### What It Is

```
frontend_runner.py = A specialized agent for UI/UX development

Unlike task_runner.py, it has:
1. Module focus (--module dashboard)
2. Screenshot capture capability
3. Token budget tracking
4. Exploration mode when queue empty
5. Visual review workflow
```

### Code Structure (Top to Bottom)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 1-50: IMPORTS & SETUP                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  • Load environment variables (.env)                                            │
│  • Import shared library utilities                                              │
│  • Import FRONTEND_EMOJI for pretty output                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 47-88: CONFIGURATION                                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  CONTROL_STATION = Path("C:/Users/ToleV/Desktop/TestingFolder/control-station") │
│                                                                                 │
│  MODULES = {                                                                    │
│      "dashboard":    src/modules/dashboard,                                     │
│      "focusguardian": src/modules/focusguardian,                               │
│      "roadmap":      src/modules/roadmap,                                       │
│      "alarm":        src/modules/alarm,                                         │
│      "gamification": src/modules/gamification,                                  │
│      "james":        src/modules/james                                          │
│  }                                                                              │
│                                                                                 │
│  FRONTEND_CONFIG = {                                                            │
│      "model": "claude-sonnet-4-20250514",                                       │
│      "name": "CONFIG-FRONTEND",                                                 │
│      "role": "Frontend Developer & UI/UX Polish"                                │
│  }                                                                              │
│                                                                                 │
│  TOKEN_BUDGET = {                                                               │
│      "daily_limit": 50000,     ← 50K tokens/day                                │
│      "per_task": 10000,        ← Max 10K per task                              │
│      "warning_threshold": 0.8  ← Warn at 80%                                   │
│  }                                                                              │
│                                                                                 │
│  @dataclass                                                                     │
│  class FrontendState:                                                           │
│      current_module: str = "dashboard"                                          │
│      current_task: Optional[str] = None                                         │
│      iteration_count: int = 0                                                   │
│      tasks_completed: int = 0                                                   │
│      tasks_failed: int = 0                                                      │
│      token_usage_today: int = 0                                                 │
│      files_modified: list                                                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 89-174: SCREENSHOT CAPTURE (Unique Feature!)                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│  def capture_tauri_window_screenshot(workspace, window_title):                  │
│      """Capture a screenshot of the Tauri app window using PowerShell."""      │
│                                                                                 │
│      Uses PowerShell with:                                                      │
│      • System.Windows.Forms for window finding                                  │
│      • System.Drawing for screenshot capture                                    │
│      • Win32 API calls (GetWindowRect, SetForegroundWindow)                    │
│                                                                                 │
│      Returns: Path to saved screenshot or None                                  │
│                                                                                 │
│      ┌─────────────────────────────────────────────────────────────────────┐   │
│      │  PowerShell Script Flow:                                            │   │
│      │  1. Find process with "Control Station" in title                    │   │
│      │  2. Get window handle (MainWindowHandle)                            │   │
│      │  3. Get window dimensions (GetWindowRect)                           │   │
│      │  4. Bring window to foreground (SetForegroundWindow)                │   │
│      │  5. Wait 200ms for window to activate                               │   │
│      │  6. Capture screenshot to Bitmap                                    │   │
│      │  7. Save as PNG to logs/screenshots/frontend/                       │   │
│      └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 176-238: TASK MANAGEMENT                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  load_tasks(tasks_file: Path) -> dict                                           │
│  save_tasks(tasks_config: dict, tasks_file: Path)                              │
│  get_next_task(tasks_config: dict, module: str) -> dict | None                 │
│      ← Filters by module (only dashboard tasks if --module dashboard)          │
│  get_task_by_id(tasks_config: dict, task_id: str) -> dict | None               │
│  mark_task_status(tasks_config, task_id, status, tasks_file)                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 240-333: PROMPT BUILDING                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  def get_system_prompt(module: str) -> str                                      │
│      Returns specialized frontend developer persona:                            │
│      • Expert in React 19, Next.js 16, TypeScript 5.5                          │
│      • Expert in Tailwind CSS 4, Framer Motion 12                              │
│      • Current focus module and path                                            │
│      • Quality standards (no placeholder code, no TS errors)                   │
│                                                                                 │
│  def build_task_prompt(task: dict, module: str) -> str                         │
│      Builds frontend-specific prompt with:                                      │
│      • Task title, ID, priority, module                                         │
│      • Execution mode: "SHIP IT"                                               │
│      • Problem and goal                                                         │
│      • Target and context files                                                 │
│      • Acceptance criteria                                                      │
│      • "START NOW. READ FILES. WRITE CODE. SHIP BEAUTIFUL UI!"                 │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 335-520: MAIN LOOP                                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  def print_frontend_banner()                                                    │
│      Pretty ASCII art banner with 🎨 emoji                                      │
│                                                                                 │
│  def print_iteration_header(iteration, max_iterations, module, task_title)     │
│      Shows progress bar, module, and current task                              │
│                                                                                 │
│  async def frontend_loop(args, workspace, tasks_file):                         │
│      Main execution loop with:                                                  │
│      1. Initialize FrontendState                                                │
│      2. Reset token usage on new day                                            │
│      3. Create session log file                                                 │
│      4. Loop:                                                                   │
│         a. Get next task (filtered by module)                                   │
│         b. If no task → create exploration task                                │
│         c. Capture screenshot (if --screenshot or --visual-review)             │
│         d. Build prompt with visual context                                     │
│         e. Run Claude AI                                                        │
│         f. Track tokens                                                         │
│         g. Update task status                                                   │
│         h. 5 second delay                                                       │
│      5. Print session summary                                                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                   ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 522-600: ENTRY POINT                                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  def parse_args():                                                              │
│      -i, --iterations (default: 1)                                              │
│      --module (default: dashboard, choices: all MODULES)                       │
│      --task (specific task ID)                                                  │
│      --continuous (run forever)                                                 │
│      --screenshot (capture before each iteration)                              │
│      --visual-review (start with visual analysis)                              │
│      --dry-run (show what would be done)                                        │
│      --list (list pending tasks)                                                │
│      --workspace (override workspace root)                                      │
│                                                                                 │
│  def main():                                                                    │
│      1. Setup Windows UTF-8                                                     │
│      2. Print banner                                                            │
│      3. Handle --list                                                           │
│      4. Validate Control Station exists                                         │
│      5. Run frontend_loop()                                                     │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### The Flow (Visual)

```
    ┌──────────────────┐
    │   python -m      │
    │   frontend_runner│
    │   --module dash  │
    │   -i 5           │
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │  Load frontend   │
    │     .json        │
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │  Filter tasks by │
    │  --module        │
    └────────┬─────────┘
             ↓
    ╔══════════════════╗
    ║   MAIN LOOP      ║◄─────────────────────────────┐
    ╚════════╤═════════╝                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  Get next task   │                              │
    │  (or create      │                              │
    │  EXPLORE task)   │                              │
    └────────┬─────────┘                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  📸 Capture      │  ← PowerShell screenshot    │
    │  screenshot?     │    of Tauri window           │
    └────────┬─────────┘                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  Build prompt    │  ← Include screenshot path  │
    │  with visual     │    for Claude to Read        │
    │  context         │                              │
    └────────┬─────────┘                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  Run Claude AI   │  ← Sonnet 4 with tools      │
    │  with tools      │    Read, Edit, Write, Bash   │
    └────────┬─────────┘                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  Track tokens    │  ← 50K daily limit          │
    │  Log iteration   │                              │
    └────────┬─────────┘                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  Sleep 5 sec     ├──────────────────────────────┘
    │  (next iter)     │
    └──────────────────┘
```

### Key Functions

| Function | What It Does |
|----------|--------------|
| `capture_tauri_window_screenshot()` | PowerShell script to capture app window |
| `get_next_task()` | Gets next pending task, filtered by module |
| `get_system_prompt()` | Returns frontend-specialized Claude prompt |
| `build_task_prompt()` | Converts task to prompt with visual context |
| `frontend_loop()` | Main async loop with token tracking |
| `print_frontend_banner()` | Pretty 🎨 ASCII art banner |

### Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  frontend_runner.py in ONE SENTENCE:                                           │
│                                                                                 │
│  "A specialized frontend agent that focuses on a single module, captures       │
│   screenshots for visual review, tracks token usage, and auto-creates          │
│   exploration tasks when the queue is empty"                                    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## frontend.json

### What It Is

```
frontend.json = The task queue for UI/UX improvements

It contains:
1. Project metadata (Control Station focus)
2. Agent instructions (mindset, workflow, quality bar)
3. 50+ frontend tasks organized by category
4. Queue management (pending, in_progress, completed)
```

### File Size & Structure Overview

```
frontend.json = ~2200 lines (~70 KB)

┌─────────────────────────────────────────────────────────────────────────────────┐
│  SECTION                          PURPOSE                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│  version, agent, created          Metadata                                      │
│  project                          Control Station details                       │
│  agent_instructions               Mindset, workflow, quality bar                │
│  queue                            pending, in_progress, completed, failed       │
│  tasks[]                          50+ task definitions                          │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Section 1: agent_instructions

```json
{
  "agent_instructions": {
    "mindset": "You are a SENIOR frontend developer. IMPLEMENT, don't just analyze. SHIP code.",
    "workflow": [
      "1. Read the screenshot with Read tool - analyze visual state",
      "2. Read target files to understand current code",
      "3. Identify specific issues or improvements",
      "4. IMPLEMENT changes using Edit tool",
      "5. Run npx tsc --noEmit to verify",
      "6. If errors, fix them immediately",
      "7. Move to next task"
    ],
    "quality_bar": [
      "No TypeScript errors",
      "No unused imports",
      "No console.logs",
      "Consistent styling patterns",
      "Smooth animations (60fps)",
      "Accessible (keyboard + screen reader)"
    ]
  }
}
```

### Section 2: queue

```json
{
  "queue": {
    "pending": [
      "FRONTEND-DASH-023", "FRONTEND-DASH-024", "FRONTEND-DASH-025",
      "FRONTEND-COMP-001", "FRONTEND-COMP-002",
      "FRONTEND-ANIM-001", "FRONTEND-ANIM-002",
      "FRONTEND-PERF-001", "FRONTEND-A11Y-001",
      "FRONTEND-FIX-001", "FRONTEND-FIX-002"
      // ... 28 total pending
    ],
    "in_progress": [
      "FRONTEND-DASH-003", "FRONTEND-DASH-007", "FRONTEND-DASH-008"
      // ... 14 total in progress
    ],
    "completed": [
      "FRONTEND-DASH-001", "FRONTEND-DASH-002", "FRONTEND-DASH-005"
      // ... 8 total completed
    ],
    "failed": []
  }
}
```

### Task Categories

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND TASK CATEGORIES                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   DASH (35 tasks) - Dashboard UI                                                │
│   ├── FRONTEND-DASH-001: Enhance Hero Section Animations                       │
│   ├── FRONTEND-DASH-007: Mobile Responsive Layout Fix                          │
│   ├── FRONTEND-DASH-008: Accessibility Focus States                            │
│   └── ... skeleton loading, charts, cards, empty states                        │
│                                                                                 │
│   COMP (5 tasks) - Components                                                   │
│   ├── FRONTEND-COMP-001: Reusable Card Component                               │
│   ├── FRONTEND-COMP-002: Button System Standardization                         │
│   └── ... modal, tooltip, badge components                                      │
│                                                                                 │
│   ANIM (3 tasks) - Animations                                                   │
│   ├── FRONTEND-ANIM-001: Page Transition System                                │
│   ├── FRONTEND-ANIM-002: Micro-interactions Library                            │
│   └── FRONTEND-ANIM-003: Loading Animation System                              │
│                                                                                 │
│   PERF (2 tasks) - Performance                                                  │
│   ├── FRONTEND-PERF-001: Bundle Size Optimization                              │
│   └── FRONTEND-PERF-002: Image Lazy Loading                                    │
│                                                                                 │
│   A11Y (2 tasks) - Accessibility                                                │
│   ├── FRONTEND-A11Y-001: Screen Reader Compatibility                           │
│   └── FRONTEND-A11Y-002: Keyboard Navigation Audit                             │
│                                                                                 │
│   FIX (3 tasks) - Bug Fixes                                                     │
│   ├── FRONTEND-FIX-001: Chart Rendering Glitch                                 │
│   ├── FRONTEND-FIX-002: Mobile Menu Overlap                                    │
│   └── FRONTEND-FIX-003: Theme Switching Flicker                                │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Queue Status Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND QUEUE STATUS                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   ⏳ PENDING:     28 tasks waiting to be picked up                              │
│   🔄 IN PROGRESS: 14 tasks currently being worked on                            │
│   ✅ COMPLETED:    8 tasks finished successfully                                │
│   ❌ FAILED:       0 tasks (none failed yet)                                    │
│                                                                                 │
│   TOTAL:          50 tasks defined                                              │
│                                                                                 │
│   Completion Rate: 16% (8/50)                                                   │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Example Task: FRONTEND-DASH-007

```json
{
  "id": "FRONTEND-DASH-007",
  "title": "Mobile Responsive Layout Fix",
  "module": "dashboard",
  "category": "responsive",
  "priority": "critical",
  "complexity": "hard",
  "status": "in_progress",
  "iterations": 3,

  "description": {
    "problem": "Dashboard may have horizontal scroll, small touch targets, cramped cards on mobile",
    "goal": "Perfect single-column layout on mobile, 44px+ touch targets, readable text",
    "scope": "All dashboard components",
    "user_impact": "Dashboard usable on phones and tablets"
  },

  "files": {
    "target": [
      "src/modules/dashboard/components/dashboard-view.tsx",
      "src/modules/dashboard/components/premium-stat-card.tsx",
      "src/modules/dashboard/components/workspace-preview-cards.tsx",
      "src/modules/dashboard/components/productivity-charts.tsx"
    ],
    "context": ["tailwind.config.ts"]
  },

  "implementation": {
    "steps": [
      "Audit all components at 375px width (iPhone SE)",
      "Fix any horizontal overflow (check for fixed widths)",
      "Ensure grid collapses: grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
      "Increase touch targets to 44px minimum",
      "Test chart container widths are 100%"
    ],
    "breakpoints": {
      "mobile": "< 640px: Single column, full width",
      "tablet": "640-1024px: 2 columns",
      "desktop": "> 1024px: 4 column bento grid"
    }
  },

  "acceptance_criteria": [
    "No horizontal scroll at any breakpoint",
    "All touch targets >= 44px",
    "Text readable without zooming (16px+ body)",
    "Cards stack properly on mobile",
    "Charts resize without breaking"
  ],

  "verification": {
    "commands": ["npx tsc --noEmit"],
    "manual": ["Test at 375px, 768px, 1024px, 1440px widths"]
  }
}
```

---

## Unique Features

### 1. Screenshot Capture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        SCREENSHOT CAPTURE SYSTEM                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   capture_tauri_window_screenshot(workspace, window_title)                      │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  PowerShell Script:                                                      │  │
│   │                                                                          │  │
│   │  1. Find process with "Control Station" in title                         │  │
│   │     Get-Process | Where-Object { $_.MainWindowTitle -like "*..." }      │  │
│   │                                                                          │  │
│   │  2. Get window handle                                                    │  │
│   │     $hwnd = $process.MainWindowHandle                                   │  │
│   │                                                                          │  │
│   │  3. Use Win32 API to get window dimensions                              │  │
│   │     [Win32]::GetWindowRect($hwnd, [ref]$rect)                           │  │
│   │                                                                          │  │
│   │  4. Bring window to foreground                                          │  │
│   │     [Win32]::SetForegroundWindow($hwnd)                                 │  │
│   │                                                                          │  │
│   │  5. Capture screenshot                                                   │  │
│   │     $graphics.CopyFromScreen($rect.Left, $rect.Top, ...)               │  │
│   │                                                                          │  │
│   │  6. Save to PNG                                                          │  │
│   │     logs/screenshots/frontend/dashboard_20251220_143052.png             │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
│   Usage in prompt:                                                              │
│   "Screenshot at: `{path}`. USE THE READ TOOL TO VIEW THIS IMAGE."             │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 2. Module Focus

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          MODULE FOCUS SYSTEM                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   --module dashboard   → Only FRONTEND-DASH-* tasks                            │
│   --module focusguardian → Only tasks for focusguardian module                 │
│   --module james       → Only tasks for james module                           │
│                                                                                 │
│   MODULES = {                                                                   │
│       "dashboard":    "src/modules/dashboard",                                  │
│       "focusguardian": "src/modules/focusguardian",                            │
│       "roadmap":      "src/modules/roadmap",                                    │
│       "alarm":        "src/modules/alarm",                                      │
│       "gamification": "src/modules/gamification",                               │
│       "james":        "src/modules/james"                                       │
│   }                                                                             │
│                                                                                 │
│   System prompt includes:                                                       │
│   "## CURRENT FOCUS: DASHBOARD MODULE                                          │
│    - Path: C:/.../control-station/src/modules/dashboard                        │
│    - Goal: Make it BEAUTIFUL, SMOOTH, ACCESSIBLE, PERFORMANT"                  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 3. Exploration Mode

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        EXPLORATION MODE                                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   When queue is empty for a module, frontend_runner creates:                    │
│                                                                                 │
│   {                                                                             │
│       "id": "EXPLORE-{iteration}",                                              │
│       "title": "Explore and improve {module} module",                           │
│       "module": "{module}",                                                     │
│       "description": {                                                          │
│           "problem": "The {module} module may need UI/UX improvements",        │
│           "goal": "Find and fix issues in {module}"                            │
│       },                                                                        │
│       "files": {                                                                │
│           "target": ["src/modules/{module}/**/*.tsx"]                          │
│       },                                                                        │
│       "acceptance_criteria": [                                                  │
│           "No TypeScript errors",                                               │
│           "Smooth animations"                                                   │
│       ]                                                                         │
│   }                                                                             │
│                                                                                 │
│   This allows the agent to continue working even without predefined tasks!     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4. Token Budget Tracking

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        TOKEN BUDGET SYSTEM                                       │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   TOKEN_BUDGET = {                                                              │
│       "daily_limit": 50000,        ← Max 50K tokens per day                    │
│       "per_task": 10000,           ← Max 10K per individual task               │
│       "warning_threshold": 0.8     ← Warn when 80% used                        │
│   }                                                                             │
│                                                                                 │
│   After each iteration:                                                         │
│   print(f"🪙 Tokens this iteration: {tokens:,}")                               │
│   print(f"🪙 Total today: {state.token_usage_today:,} / 50,000")               │
│                                                                                 │
│   Token reset happens at midnight (new day):                                   │
│   if state.token_usage_reset_date != today:                                    │
│       state.token_usage_today = 0                                              │
│       state.token_usage_reset_date = today                                     │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## How Everything Works Together

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     THE FRONTEND RUNNER SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   YOU RUN:                                                                      │
│   python -m autoagents.runners.frontend_runner --module dashboard -i 5         │
│                                                                                 │
│                              ↓                                                  │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  frontend_runner.py (Specialized Frontend Agent)                        │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │  1. Loads frontend.json (50+ UI tasks)                                  │  │
│   │  2. Filters tasks by --module (dashboard only)                          │  │
│   │  3. Optionally captures screenshot via PowerShell                       │  │
│   │  4. Builds prompt with visual context                                   │  │
│   │  5. Runs Claude with specialized frontend system prompt                 │  │
│   │  6. Tracks token usage (50K/day budget)                                 │  │
│   │  7. Auto-creates exploration tasks when queue empty                     │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                              ↓                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  frontend.json (The UI Task Queue)                                      │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │  • 50+ frontend tasks (DASH, COMP, ANIM, PERF, A11Y, FIX)              │  │
│   │  • Rich implementation steps and acceptance criteria                    │  │
│   │  • Module assignments for task filtering                                │  │
│   │  • Queue management (28 pending, 14 in progress, 8 completed)          │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                              ↓                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  Claude AI (The Frontend Expert)                                        │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │  • Views screenshot with Read tool                                      │  │
│   │  • Analyzes visual state of UI                                          │  │
│   │  • Implements React/TypeScript/Tailwind code                           │  │
│   │  • Runs npx tsc --noEmit to verify                                      │  │
│   │  • Ships polished, accessible UI                                        │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Comparison: frontend_runner vs task_runner

| Feature | task_runner.py | frontend_runner.py |
|---------|----------------|-------------------|
| **Focus** | General coding tasks | UI/UX development only |
| **Module Filter** | ❌ No | ✅ Yes (`--module`) |
| **Screenshot** | ❌ No | ✅ Yes (`--screenshot`) |
| **Token Tracking** | ❌ No | ✅ 50K/day budget |
| **Exploration Mode** | ❌ No | ✅ Auto-creates tasks |
| **Visual Review** | ❌ No | ✅ `--visual-review` |
| **Continuous Mode** | ❌ No | ✅ `--continuous` |
| **System Prompt** | Generic developer | Frontend specialist |
| **Delay** | 3 seconds | 5 seconds |

---

## Honest Assessment

### What's GOOD

| Aspect | Why It's Good |
|--------|---------------|
| **Screenshot capture** | Can visually verify UI changes |
| **Module focus** | Concentrates work on one area |
| **Token tracking** | Prevents runaway costs |
| **Exploration mode** | Never sits idle, always improving |
| **Rich task definitions** | 50+ tasks with detailed implementation steps |
| **Continuous mode** | Can run overnight |
| **Specialized system prompt** | Frontend-specific expertise |

### What's INCOMPLETE or NEEDS WORK

| Issue | Impact | Severity |
|-------|--------|----------|
| **No COMMS.md integration** | Other agents don't see activity | Medium |
| **Screenshot requires Tauri running** | Can't capture if app not open | Low |
| **Many tasks stuck in "in_progress"** | 14 tasks never completed | Medium |
| **No visual diff** | Can't compare before/after | Low |
| **No MCP Puppeteer integration** | Limited to window capture only | Low |

### What's UNCLEAR

1. Why are 14 tasks stuck in "in_progress"? Were they abandoned?
2. Does the screenshot capture work reliably on all monitors?
3. How should visual-review mode interact with actual task work?

---

## Recommended Improvements

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  RECOMMENDED IMPROVEMENTS (in order of priority)                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  1. ⏳ ADD COMMS.MD LOGGING (PENDING)                                           │
│     └── Log frontend session start/end                                         │
│     └── Track files modified                                                    │
│                                                                                 │
│  2. ⏳ CLEAN UP IN_PROGRESS TASKS (PENDING)                                     │
│     └── Review 14 stuck tasks                                                   │
│     └── Move abandoned ones back to pending                                     │
│                                                                                 │
│  3. ⏳ ADD BEFORE/AFTER SCREENSHOTS (PENDING)                                   │
│     └── Capture before making changes                                          │
│     └── Capture after for visual comparison                                    │
│     └── Log both paths for review                                              │
│                                                                                 │
│  4. ⏳ ADD CONTEXT INJECTION (PENDING)                                          │
│     └── Read COMMS.md before starting                                          │
│     └── Check if other agents are working on same files                        │
│                                                                                 │
│  5. ⏳ INTEGRATE MCP PUPPETEER (OPTIONAL)                                       │
│     └── Use Puppeteer for more reliable screenshots                            │
│     └── Can capture specific elements, not just window                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Commands Reference

```bash
# ═══════════════════════════════════════════════════════════════════════════════
# FRONTEND RUNNER QUICK COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

# Basic usage
python -m autoagents.runners.frontend_runner                    # 1 iteration
python -m autoagents.runners.frontend_runner -i 5               # 5 iterations
python -m autoagents.runners.frontend_runner --continuous       # Run forever

# Module focus
python -m autoagents.runners.frontend_runner --module dashboard      # Default
python -m autoagents.runners.frontend_runner --module focusguardian
python -m autoagents.runners.frontend_runner --module james
python -m autoagents.runners.frontend_runner --module roadmap
python -m autoagents.runners.frontend_runner --module gamification

# Visual features
python -m autoagents.runners.frontend_runner --screenshot       # Capture before each
python -m autoagents.runners.frontend_runner --visual-review    # Start with analysis

# Specific task
python -m autoagents.runners.frontend_runner --task FRONTEND-DASH-007

# Utilities
python -m autoagents.runners.frontend_runner --list             # Show pending tasks
python -m autoagents.runners.frontend_runner --dry-run          # Show what would happen
```

---

## Session Information

**Documented by:** CMDTV (Claude Opus 4.5)
**Date:** 2025-12-20
**Session:** ULTRATHINK Mode - Agent Documentation

This documentation was created during a session where:
- frontend_runner.py was analyzed (600 lines)
- frontend.json was analyzed (2200+ lines)
- Both files were documented with visual diagrams
- All unique features (screenshots, module focus, exploration) were explained

---

## Updates Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-20 | CMDTV | Initial documentation created |

---

*End of FRONTEND RUNNER Agent Documentation*
