# SENTINEL-DEV Agent Documentation

**Created:** 2025-12-20
**Session:** CMDTV Session 4 (ULTRATHINK)
**Author:** Claude Opus 4.5 + ToleV
**Purpose:** Complete documentation of the SENTINEL autonomous agent system

---

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [sentinel_runner.py](#sentinel_runnerpy)
4. [health_monitors.py](#health_monitorspy)
5. [repair_workflows.py](#repair_workflowspy)
6. [sentinel.json](#sentineljson)
   - [NEW: context_injection](#new-section-7-context_injection-added-2025-12-20)
   - [NEW: agent_coordination_protocol](#new-section-8-agent_coordination_protocol-added-2025-12-20)
7. [How Everything Works Together](#how-everything-works-together)
8. [Honest Assessment](#honest-assessment)
9. [Recommended Improvements](#recommended-improvements)
10. [Updates Log](#updates-log)

---

## Overview

```
SENTINEL-DEV = Autonomous DevOps Guardian for Control Station

It does 3 things:
1. Monitors health (is dev server alive? TypeScript OK? Database working?)
2. Auto-repairs issues (restart crashed server, clear cache, fix DB locks)
3. Calls Claude AI for deeper analysis when needed
```

### Quick Start

```bash
# Single check (1 iteration)
python -m autoagents.runners.sentinel_runner

# 5 iterations
python -m autoagents.runners.sentinel_runner -i 5

# Run forever (continuous monitoring)
python -m autoagents.runners.sentinel_runner --continuous

# Force deep analysis with Claude
python -m autoagents.runners.sentinel_runner --deep
```

---

## File Structure

```
autonomous-coding/
├── autoagents/
│   ├── runners/
│   │   └── sentinel_runner.py    (Main runner - 22KB)
│   ├── agents/
│   │   └── sentinel/
│   │       ├── __init__.py
│   │       ├── health_monitors.py (Health checks - tiered)
│   │       └── repair_workflows.py (Auto-repair procedures)
│   └── lib/
│       ├── client.py             (Claude API client)
│       ├── streaming.py          (Response streaming)
│       └── output.py             (Pretty printing)
└── tasks/
    └── sentinel.json             (Config + tasks - 68KB)
```

---

## sentinel_runner.py

### What It Is

```
sentinel_runner.py = The "brain" that orchestrates SENTINEL agent

It does 3 things:
1. Runs health checks (is dev server alive?)
2. Auto-repairs issues (restart crashed server)
3. Calls Claude AI for deeper analysis
```

### Code Structure (Top to Bottom)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 1-50: IMPORTS & SETUP                                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  • Load environment variables (.env)                                            │
│  • Import HealthMonitor and RepairWorkflow classes                              │
│  • Import styling/output helpers                                                │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 51-82: CONFIGURATION                                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│  SENTINEL_CONFIG = {                                                            │
│      "model": "claude-sonnet-4-20250514",   ← Which Claude model               │
│      "name": "SENTINEL-DEV",                                                    │
│      "role": "DevOps Guardian"                                                  │
│  }                                                                              │
│                                                                                 │
│  TOKEN_BUDGET = {                                                               │
│      "daily_limit": 10000,    ← Max tokens per day                             │
│      "quick_check": 0,        ← Tier 1 = free                                  │
│      "deep_check": 2000       ← Tier 3 = expensive                             │
│  }                                                                              │
│                                                                                 │
│  RATE_LIMITS = {                                                                │
│      "max_repairs_per_hour": 5,    ← Don't spam restarts                       │
│      "max_restarts_per_day": 10                                                │
│  }                                                                              │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 112-134: LOG TO COMMS.MD                                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│  def log_to_comms(event_type, details):                                         │
│      """Writes entries to .claude/COMMS.md so other agents can see"""          │
│                                                                                 │
│      # Example output in COMMS.md:                                              │
│      # ### 🛡️ SENTINEL-DEV - 2025-12-20 03:00:00                               │
│      # **Event:** session_start                                                 │
│      # **Details:** {"mode": "limited_5", "health_tasks": 6}                   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 164-203: SYSTEM PROMPT FOR CLAUDE                                        │
├─────────────────────────────────────────────────────────────────────────────────┤
│  def get_system_prompt():                                                       │
│      """Tells Claude WHO it is and HOW to behave"""                            │
│                                                                                 │
│      Key instructions:                                                          │
│      • "You are SENTINEL-DEV, an AGGRESSIVE autonomous DevOps agent"           │
│      • "DO NOT just report issues - FIX THEM"                                  │
│      • "DO NOT wait for approval - ACT NOW"                                    │
│      • "You have FULL POWER of the user's PC"                                  │
│                                                                                 │
│      Forbidden actions:                                                         │
│      • git reset --hard                                                         │
│      • rm -rf node_modules                                                      │
└─────────────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│  LINES 287-400: MAIN MONITORING LOOP                                            │
├─────────────────────────────────────────────────────────────────────────────────┤
│  async def monitoring_loop(args, workspace, tasks_file):                        │
│      """The heart of SENTINEL - runs forever or N iterations"""                │
│                                                                                 │
│      1. Load tasks from sentinel.json                                           │
│      2. Initialize HealthMonitor() and RepairWorkflow()                        │
│      3. Log session_start to COMMS.md                                          │
│                                                                                 │
│      while True:                                                                │
│          # Step A: Run quick health checks (FREE - 0 tokens)                   │
│          quick_results = health_monitor.run_tier1_checks()                     │
│                                                                                 │
│          # Step B: Check for failures                                           │
│          for result in quick_results:                                           │
│              if result.status == HealthStatus.ERROR:                           │
│                  # Try auto-repair                                              │
│                  repair_workflow.execute_workflow("dev_server_restart")        │
│                                                                                 │
│          # Step C: Call Claude for deeper analysis (COSTS TOKENS)              │
│          response = await stream_agent_response(client, prompt)                │
│                                                                                 │
│          # Step D: Wait before next iteration                                  │
│          await asyncio.sleep(300)  # 5 minutes                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### The Flow (Visual)

```
    ┌──────────────────┐
    │   START SENTINEL │
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │  Load sentinel   │
    │     .json        │
    └────────┬─────────┘
             ↓
    ┌──────────────────┐
    │  Log to COMMS.md │
    │  "session_start" │
    └────────┬─────────┘
             ↓
    ╔══════════════════╗
    ║   MAIN LOOP      ║◄─────────────────────────────┐
    ╚════════╤═════════╝                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  Tier 1 Checks   │  ← FREE (0 tokens)          │
    │  • HTTP ping     │                              │
    │  • Port 3000     │                              │
    │  • Database      │                              │
    └────────┬─────────┘                              │
             ↓                                        │
        ┌────┴────┐                                   │
        │ Healthy? │                                  │
        └────┬────┘                                   │
         YES │ NO                                     │
             ↓                                        │
    ┌──────────────────┐                              │
    │   AUTO-REPAIR    │  ← Kill port, restart       │
    │  dev_server      │                              │
    └────────┬─────────┘                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  Call Claude AI  │  ← COSTS TOKENS             │
    │  for analysis    │                              │
    └────────┬─────────┘                              │
             ↓                                        │
    ┌──────────────────┐                              │
    │  Sleep 5 min     │                              │
    │  (or next iter)  ├──────────────────────────────┘
    └──────────────────┘
```

### Key Functions

| Function | What It Does |
|----------|--------------|
| `log_to_comms()` | Writes to COMMS.md so other agents see SENTINEL's activity |
| `get_system_prompt()` | Returns the "personality" prompt for Claude |
| `build_task_prompt()` | Converts a task from JSON into a Claude prompt |
| `monitoring_loop()` | Main async loop - runs health checks + Claude |
| `print_sentinel_banner()` | Pretty ASCII art header |
| `print_cycle_header()` | Shows "ITERATION 1/5" progress |

### Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  sentinel_runner.py in ONE SENTENCE:                                           │
│                                                                                 │
│  "A loop that checks if Control Station is healthy, auto-repairs if broken,    │
│   and calls Claude AI for deeper analysis - all while respecting token limits" │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## health_monitors.py

### What It Is

```
health_monitors.py = The "doctor" that diagnoses Control Station's health

It does 3 things:
1. Defines WHAT to check (HTTP, ports, database, TypeScript)
2. Runs PowerShell commands to check health
3. Returns HEALTHY / DEGRADED / ERROR status
```

### The Tiered System (KEY CONCEPT)

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        WHY TIERS? → SAVE TOKENS!                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   TIER 1: BASH ONLY          TIER 2: SMART           TIER 3: DEEP              │
│   ┌──────────────────┐       ┌──────────────────┐    ┌──────────────────┐      │
│   │  0 tokens        │       │  ~500 tokens     │    │  ~2000 tokens    │      │
│   │  Just run cmd    │       │  Light analysis  │    │  Full Claude AI  │      │
│   │  Check output    │       │  Pattern match   │    │  Deep diagnosis  │      │
│   └──────────────────┘       └──────────────────┘    └──────────────────┘      │
│                                                                                 │
│   Examples:                  Examples:               Examples:                  │
│   • curl localhost:3000      • npx tsc --noEmit     • Analyze error logs       │
│   • Check port 3000          • Check TypeScript     • Root cause analysis      │
│   • File exists?             • Parse output         • Suggest fixes            │
│                                                                                 │
│   Run EVERY time             Run occasionally       Run only when needed       │
│   (every 5 min)              (every 30 min)         (on escalation)            │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Data Classes

```python
class HealthStatus(Enum):
    HEALTHY = "healthy"      # ✅ All good
    DEGRADED = "degraded"    # ⚠️ Working but slow/issues
    ERROR = "error"          # ❌ Broken
    UNKNOWN = "unknown"      # ❓ Couldn't determine

class CheckTier(Enum):
    TIER_1_BASH = 1    # Free - just PowerShell
    TIER_2_SMART = 2   # ~500 tokens
    TIER_3_DEEP = 3    # ~2000 tokens

@dataclass
class HealthCheckConfig:
    id: str                    # "SENTINEL-HEALTH-001"
    name: str                  # "Dev Server HTTP Ping"
    tier: CheckTier            # TIER_1_BASH
    component: str             # "Dev Server HTTP"
    command: str               # "curl localhost:3000"
    success_patterns: list     # ["HEALTHY", "200"]
    failure_patterns: list     # ["UNHEALTHY", "refused"]
    on_failure_escalate_to: str  # "SENTINEL-REPAIR-001"

@dataclass
class HealthCheckResult:
    config: HealthCheckConfig  # Which check was run
    status: HealthStatus       # HEALTHY / ERROR
    message: str               # "Check passed"
    stdout: str                # Command output
```

### The Predefined Checks

```python
CHECKS = {
    # TIER 1: FREE (0 tokens)
    "http_ping": HealthCheckConfig(
        id="SENTINEL-HEALTH-001",
        command='curl -f http://127.0.0.1:3000',
        success_patterns=["HEALTHY"],
        failure_patterns=["Connection refused"],
        on_failure_escalate_to="SENTINEL-REPAIR-001",
    ),

    "port_status": HealthCheckConfig(
        id="SENTINEL-HEALTH-006",
        command='Get-NetTCPConnection -LocalPort 3000',
        success_patterns=["PORT_IN_USE"],
        failure_patterns=["PORT_FREE"],
    ),

    "database_file": HealthCheckConfig(
        id="SENTINEL-HEALTH-005",
        command='Test-Path $env:APPDATA/com.convergence.control-station/*.db',
        success_patterns=["EXISTS"],
        failure_patterns=["MISSING"],
    ),

    # TIER 2: SMART (~500 tokens)
    "typescript_check": HealthCheckConfig(
        id="SENTINEL-HEALTH-004",
        tier=CheckTier.TIER_2_SMART,
        command='npx tsc --noEmit',
        failure_patterns=["error TS"],
        token_budget=500,
    ),

    # TIER 3: DEEP (~2000 tokens)
    "full_health_api": HealthCheckConfig(
        id="SENTINEL-DIAG-001",
        tier=CheckTier.TIER_3_DEEP,
        command='curl http://127.0.0.1:3000/api/health',
        token_budget=2000,
    ),
}
```

### The Flow

```
    ┌─────────────────────────────────────────────────────────────────┐
    │  sentinel_runner.py calls:                                      │
    │  health_monitor.run_tier1_checks()                              │
    └─────────────────────────────────┬───────────────────────────────┘
                                      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  For each TIER_1 check in CHECKS:                               │
    │  ├── http_ping                                                  │
    │  ├── port_status                                                │
    │  ├── database_file                                              │
    │  └── build_cache                                                │
    └─────────────────────────────────┬───────────────────────────────┘
                                      ↓
                            ┌─────────┴─────────┐
                            │  execute_check()  │
                            └─────────┬─────────┘
                                      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  run_bash(command)                                              │
    │  └── powershell -Command "curl localhost:3000"                  │
    └─────────────────────────────────┬───────────────────────────────┘
                                      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  Check output against patterns:                                 │
    │  ├── success_patterns: ["HEALTHY", "200"]                       │
    │  └── failure_patterns: ["refused", "error"]                     │
    └─────────────────────────────────┬───────────────────────────────┘
                                      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  Return HealthCheckResult:                                      │
    │  ├── status: HEALTHY ✅  or  ERROR ❌                           │
    │  ├── message: "Check passed"                                    │
    │  └── stdout: "HTTP/1.1 200 OK"                                  │
    └─────────────────────────────────────────────────────────────────┘
```

### Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  health_monitors.py in ONE SENTENCE:                                           │
│                                                                                 │
│  "A dictionary of health checks that run PowerShell commands and return        │
│   HEALTHY or ERROR based on pattern matching - organized by token cost tiers"  │
└─────────────────────────────────────────────────────────────────────────────────┘

Key insight: Tier 1 checks are FREE (no Claude API calls)
             They run first to avoid wasting tokens on simple checks
```

---

## repair_workflows.py

### What It Is

```
repair_workflows.py = The "mechanic" that fixes broken things

It does 3 things:
1. Defines REPAIR PROCEDURES (step-by-step fixes)
2. Executes PowerShell commands to fix issues
3. Verifies the fix worked
```

### When Is It Called?

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          TRIGGER FLOW                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   health_monitors.py                     repair_workflows.py                    │
│   ┌──────────────────┐                   ┌──────────────────┐                  │
│   │  http_ping       │                   │  dev_server_     │                  │
│   │  returns ERROR   │ ──escalates to──► │  restart         │                  │
│   │                  │                   │                  │                  │
│   │  on_failure_     │                   │  Kills port 3000 │                  │
│   │  escalate_to:    │                   │  Restarts npm    │                  │
│   │  "REPAIR-001"    │                   │  Waits for 200   │                  │
│   └──────────────────┘                   └──────────────────┘                  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### The Safety System

```python
class RepairWorkflow:

    # FORBIDDEN ACTIONS - Will NEVER run these
    FORBIDDEN_ACTIONS = [
        "git reset --hard",      # Could lose work
        "rm -rf node_modules",   # Too slow, breaks things
        "npm install",           # Too slow
        "Delete source files"    # Dangerous
    ]

    # SAFE TO KILL - Only these processes can be terminated
    SAFE_TO_KILL_PROCESSES = [
        "node",
        "npm",
        "next-server",
        "control-station"
    ]

    # RATE LIMITS - Prevent repair spam
    RATE_LIMITS = {
        "max_repairs_per_hour": 5,
        "max_restarts_per_day": 10
    }
```

### The Predefined Workflows

```python
WORKFLOWS = {
    # WORKFLOW 1: Restart Dev Server
    "dev_server_restart": RepairConfig(
        id="SENTINEL-REPAIR-001",
        name="Restart Crashed Next.js Dev Server",
        steps=[
            RepairStep(name="Kill port 3000 processes", required=False),
            RepairStep(name="Wait for port release"),
            RepairStep(name="Start dev server"),
            RepairStep(name="Wait for HTTP 200"),
        ]
    ),

    # WORKFLOW 2: Clear Build Cache
    "build_cache_clear": RepairConfig(
        id="SENTINEL-REPAIR-003",
        name="Clear Next.js Build Cache",
        steps=[
            RepairStep(name="Stop dev server", required=False),
            RepairStep(name="Delete .next directory"),
            RepairStep(name="Verify deletion"),
        ]
    ),

    # WORKFLOW 3: Fix Database Lock
    "database_lock_clear": RepairConfig(
        id="SENTINEL-REPAIR-004",
        name="Fix Database Lock with WAL Checkpoint",
        steps=[
            RepairStep(name="Stop Control Station processes"),
            RepairStep(name="Wait for handles to release"),
            RepairStep(name="Delete WAL files"),
            RepairStep(name="Verify database accessible"),
        ]
    ),
}
```

### The Flow

```
    ┌─────────────────────────────────────────────────────────────────┐
    │  sentinel_runner.py detects ERROR from health check            │
    │  Calls: repair_workflow.execute_workflow("dev_server_restart") │
    └─────────────────────────────────┬───────────────────────────────┘
                                      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  Check rate limits:                                             │
    │  • repairs_this_hour < 5?  ✅                                   │
    │  • restarts_today < 10?    ✅                                   │
    └─────────────────────────────────┬───────────────────────────────┘
                                      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  STEP 1: Kill port 3000 processes                               │
    │  ├── Command: Get-NetTCPConnection | Stop-Process               │
    │  ├── required: false (OK if nothing to kill)                    │
    │  └── Result: ✅ or ⏭️ skipped                                   │
    └─────────────────────────────────┬───────────────────────────────┘
                                      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  STEP 2: Wait for port release                                  │
    │  ├── Command: Start-Sleep -Seconds 2                            │
    │  └── Result: ✅                                                  │
    └─────────────────────────────────┬───────────────────────────────┘
                                      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  STEP 3: Start dev server                                       │
    │  ├── Command: Start-Process "tauri-dev-live.ps1"                │
    │  └── Result: ✅                                                  │
    └─────────────────────────────────┬───────────────────────────────┘
                                      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  STEP 4: Wait for HTTP 200                                      │
    │  ├── Command: Loop until localhost:3000 returns 200             │
    │  ├── Timeout: 90 seconds                                        │
    │  └── Result: ✅ "SERVER_READY" or ❌ "TIMEOUT"                  │
    └─────────────────────────────────┬───────────────────────────────┘
                                      ↓
    ┌─────────────────────────────────────────────────────────────────┐
    │  Return RepairResult:                                           │
    │  ├── status: SUCCESS ✅                                         │
    │  ├── steps_completed: ["Kill", "Wait", "Start", "Verify"]      │
    │  ├── steps_failed: []                                           │
    │  └── message: "Dev server restarted successfully"               │
    └─────────────────────────────────────────────────────────────────┘
```

### Step Failure Handling

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        WHAT HAPPENS WHEN A STEP FAILS?                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   on_failure: "stop"                                                            │
│   ┌──────────────────┐                                                         │
│   │  Step fails      │ ──► Abort entire workflow                               │
│   │  required: true  │     Return FAILED status                                │
│   └──────────────────┘                                                         │
│                                                                                 │
│   on_failure: "continue"                                                        │
│   ┌──────────────────┐                                                         │
│   │  Step fails      │ ──► Log failure, keep going                             │
│   │  required: false │     Try next step anyway                                │
│   └──────────────────┘                                                         │
│                                                                                 │
│   on_failure: "retry"                                                           │
│   ┌──────────────────┐                                                         │
│   │  Step fails      │ ──► Try again (up to max_retries)                       │
│   │  max_retries: 3  │     Then continue or stop                               │
│   └──────────────────┘                                                         │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  repair_workflows.py in ONE SENTENCE:                                          │
│                                                                                 │
│  "A collection of multi-step PowerShell procedures that fix common issues      │
│   like crashed servers, stale caches, and locked databases - with safety       │
│   limits to prevent repair spam"                                               │
└─────────────────────────────────────────────────────────────────────────────────┘

Key insight: Repairs are AUTOMATIC but RATE-LIMITED
             Max 5 repairs/hour, max 10 restarts/day
             Some actions are FORBIDDEN (git reset, rm -rf node_modules)
```

---

## sentinel.json

### What It Is

```
sentinel.json = The "brain configuration" - everything SENTINEL needs to know

It contains:
1. Philosophy & rules (ULTRATHINK, brutal honesty)
2. Project knowledge (Control Station stack, modules, paths)
3. Task definitions (what to check, how to verify)
4. Agent personality (how to behave)
```

### File Size & Structure Overview

```
sentinel.json = 68 KB (~1800 lines)

┌─────────────────────────────────────────────────────────────────────────────────┐
│  SECTION                          LINES        PURPOSE                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│  _schema                          1-10         Version, author, philosophy      │
│  ultrathink_protocol              11-83        Rules, brutal honesty, visual    │
│  pc_environment                   85-113       User paths, Windows info         │
│  project                          115-233      Control Station full details     │
│  critical_files                   235-299      Important file paths             │
│  commands                         301-337      npm run dev, build, test         │
│  agents                           339-369      SENTINEL agent definition        │
│  sentinel_protocol                371-403      Token budgets, safety rules      │
│  tasks[]                          405-1800     Array of task definitions        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Section 1: _schema

```json
{
  "_schema": {
    "version": "4.0.0",
    "name": "SENTINEL-DEV Autonomous Guardian System",
    "description": "BRUTALLY HONEST dev environment health monitoring",
    "philosophy": "Act like a real human: look at screenshots, verify visually, never assume - CHECK!"
  }
}
```

### Section 2: ultrathink_protocol

```json
{
  "ultrathink_protocol": {
    "mode": "ULTRATHINK",
    "rules": [
      "⚠️ Let's be fucking real. DO NOT restrain. DO NOT hold back.",
      "Think HARD and activate ULTRATHINK for ALL checks",
      "Be your own supervisor, be your own critique, be BRUTALLY HONEST",
      "Never trust assumptions - VERIFY EVERYTHING",
      "Take screenshots and LOOK at them like a real human would"
    ],
    "brutal_honesty": {
      "enabled": true,
      "behavior": [
        "Report issues even if they seem minor",
        "Don't hide failures to make things look good",
        "Call out any suspicious behavior"
      ]
    },
    "visual_verification": {
      "required": true,
      "method": "Take screenshots using MCP Puppeteer",
      "what_to_check": [
        "Splash screen actually displays (not 404)",
        "Dashboard loads with real data",
        "All modules render correctly"
      ]
    }
  }
}
```

### Section 3: pc_environment

```json
{
  "pc_environment": {
    "user": "ToleV",
    "platform": "Windows 11",
    "machine": "TOLESPC",
    "paths": {
      "control_station": "C:/Users/ToleV/Desktop/TestingFolder/control-station",
      "autonomous_coding": "C:/Users/ToleV/Desktop/TestingFolder/autonomous-coding",
      "database_dir": "C:/Users/ToleV/AppData/Roaming/com.convergence.control-station"
    }
  }
}
```

### Section 4: project

```json
{
  "project": {
    "name": "Control Station",
    "version": "2.0.0",
    "status": "Active Development (~70% complete)",
    "stack": {
      "frontend": { "framework": "Next.js 16", "ui": "React 19", "language": "TypeScript 5" },
      "desktop": { "framework": "Tauri 2.9.2", "backend_lang": "Rust", "database": "SQLite" },
      "testing": { "total_tests": 2583, "passing": 2583, "failing": 0 }
    },
    "modules": {
      "alarm": { "status": "100% ✅", "tests": 660, "notes": "Gold standard" },
      "james": { "status": "50% 🔄", "priority": "#1" },
      "focus-guardian": { "status": "65% 🔄", "priority": "#2" }
    }
  }
}
```

### Section 5: sentinel_protocol (Safety)

```json
{
  "sentinel_protocol": {
    "token_budget": {
      "daily_limit": 10000,
      "quick_check": 0,
      "deep_check": 1500,
      "repair": 2000
    },
    "rate_limits": {
      "max_repairs_per_hour": 5,
      "max_restarts_per_day": 10
    },
    "safety": {
      "forbidden_actions": [
        "git reset --hard",
        "rm -rf node_modules",
        "Touch src/modules/alarm/** (gold standard)"
      ]
    }
  }
}
```

### Section 6: tasks[]

```json
{
  "tasks": [
    {
      "id": "SENTINEL-VISUAL-001",
      "title": "Visual Verification: Splash Screen Check",
      "category": "visual-verification",
      "priority": "critical",
      "description": {
        "problem": "Previous 404 splash screen issue may recur",
        "goal": "VISUALLY verify splash screen displays correctly"
      },
      "visual_verification": {
        "required": true,
        "what_to_look_for": ["Control Station logo", "Loading progress bar"]
      }
    },
    {
      "id": "SENTINEL-HEALTH-001",
      "title": "Dev Server Health Check",
      "category": "health-monitoring",
      "execution": {
        "bash_commands": ["curl -f http://127.0.0.1:3000"],
        "success_criteria": ["HTTP 200 response"]
      }
    }
  ]
}
```

### Summary

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  sentinel.json in ONE SENTENCE:                                                │
│                                                                                 │
│  "A 68KB configuration file that gives SENTINEL complete knowledge of          │
│   Control Station - paths, stack, modules, commands, safety rules, and         │
│   30+ task definitions for what to check and how to verify it"                 │
└─────────────────────────────────────────────────────────────────────────────────┘

The JSON is the "memory" - everything SENTINEL needs to know about YOUR project.
The Python files are the "logic" - how to use that knowledge.
```

### NEW: Section 7: context_injection (Added 2025-12-20)

```json
{
  "context_injection": {
    "description": "SENTINEL MUST read these files at session start",
    "required_reads": [
      {
        "file": ".claude/COMMS.md",
        "purpose": "See what other agents have done, active tasks, blockers",
        "when": "ALWAYS at session start, before any health checks",
        "what_to_extract": [
          "Recent agent sessions (last 24h)",
          "Active blockers or warnings",
          "Files recently modified by other agents",
          "Tasks completed or in progress"
        ]
      },
      {
        "file": ".claude/CLAUDE.md",
        "purpose": "Project rules, standards, ULTRATHINK protocol",
        "when": "First run only, cache the rules"
      },
      {
        "file": ".claude/context/STATUS.md",
        "purpose": "Current build status, test results, known issues"
      }
    ],
    "required_writes": [
      {
        "file": ".claude/COMMS.md",
        "purpose": "Log SENTINEL activities for other agents to see",
        "when": "Session start, after repairs, session end"
      }
    ]
  }
}
```

### NEW: Section 8: agent_coordination_protocol (Added 2025-12-20)

```json
{
  "agent_coordination_protocol": {
    "description": "How SENTINEL coordinates with other agents (CMDTV, JARVIS1-5)",
    "rules": [
      "READ COMMS.md FIRST - understand what other agents did",
      "DON'T repair something another agent is actively working on",
      "LOG all repairs to COMMS.md so others know what changed",
      "ESCALATE complex issues instead of auto-repairing",
      "NEVER modify files another agent just changed (check git status)",
      "RESPECT gold standard modules (alarm) - read-only for all agents"
    ],
    "conflict_avoidance": {
      "check_git_status": true,
      "check_file_locks": true,
      "check_recent_commits": "Don't undo commits from last 1 hour",
      "active_session_detection": "Check COMMS.md for active agent sessions"
    },
    "handoff_protocol": {
      "when_to_handoff": [
        "TypeScript error requires code changes (not SENTINEL's job)",
        "Test failure requires code fix (escalate to CMDTV/JARVIS)",
        "UI issue found that needs React changes",
        "Database schema issue (requires human approval)"
      ],
      "how_to_handoff": [
        "1. Document issue in COMMS.md with full details",
        "2. Tag recommended agent (CMDTV for complex, JARVIS for routine)",
        "3. Include file paths, error messages, reproduction steps",
        "4. Mark as NEEDS_ATTENTION in COMMS.md"
      ]
    }
  }
}
```

---

## How Everything Works Together

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         THE SENTINEL SYSTEM                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│   YOU RUN:                                                                      │
│   python -m autoagents.runners.sentinel_runner -i 5                            │
│                                                                                 │
│                              ↓                                                  │
│                                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  sentinel_runner.py (The Orchestrator)                                  │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │  1. Loads sentinel.json (project knowledge + tasks)                     │  │
│   │  2. Creates HealthMonitor() and RepairWorkflow()                        │  │
│   │  3. Loops through iterations:                                           │  │
│   │     a. Run FREE health checks (Tier 1)                                  │  │
│   │     b. If ERROR → trigger auto-repair                                   │  │
│   │     c. Call Claude API for deeper analysis                              │  │
│   │     d. Log to COMMS.md                                                  │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                              ↓                                                  │
│            ┌─────────────────┴─────────────────┐                               │
│            ↓                                   ↓                                │
│   ┌─────────────────────┐           ┌─────────────────────┐                    │
│   │  health_monitors.py │           │  repair_workflows.py│                    │
│   │  ─────────────────  │           │  ──────────────────│                    │
│   │  • Tier 1: curl,    │   ERROR   │  • Kill port 3000  │                    │
│   │    port, db checks  │ ────────► │  • Restart server  │                    │
│   │  • Tier 2: tsc      │           │  • Clear cache     │                    │
│   │  • Tier 3: deep AI  │           │  • Fix DB locks    │                    │
│   │                     │           │                     │                    │
│   │  Returns: HEALTHY   │           │  Returns: SUCCESS   │                    │
│   │           or ERROR  │           │           or FAILED │                    │
│   └─────────────────────┘           └─────────────────────┘                    │
│                              ↑                                                  │
│                              │                                                  │
│   ┌─────────────────────────────────────────────────────────────────────────┐  │
│   │  sentinel.json (The Brain/Memory)                                       │  │
│   │  ─────────────────────────────────────────────────────────────────────  │  │
│   │  • Project knowledge (Control Station stack, modules, paths)            │  │
│   │  • 30+ task definitions (what to check)                                 │  │
│   │  • Safety rules (forbidden actions, rate limits)                        │  │
│   │  • Agent personality (ULTRATHINK, brutal honesty)                       │  │
│   └─────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### One-Liner Summary of Each File

| File | Purpose |
|------|---------|
| `sentinel_runner.py` | **Main loop** - orchestrates checks, repairs, Claude calls |
| `health_monitors.py` | **The doctor** - runs PowerShell commands, returns HEALTHY/ERROR |
| `repair_workflows.py` | **The mechanic** - multi-step fixes (restart server, clear cache) |
| `sentinel.json` | **The brain** - all knowledge about Control Station + tasks |

---

## Honest Assessment

### What's GOOD

| Aspect | Why It's Good |
|--------|---------------|
| **Tiered checks** | Tier 1 = FREE, saves tokens for when you actually need Claude |
| **Auto-repair** | Server crashes → automatically restarts, no human needed |
| **Rate limits** | Won't spam 100 restarts, has daily/hourly limits |
| **Safety rules** | Forbidden actions prevent catastrophic mistakes |
| **Logs to COMMS.md** | Other agents can see what SENTINEL did |
| **Comprehensive JSON** | Has ALL project knowledge in one place |

### What's INCOMPLETE or BROKEN

| Issue | Impact | Severity | Status |
|-------|--------|----------|--------|
| **Outdated test counts** | JSON says 1192, reality is 2583 | Medium | ✅ FIXED 2025-12-20 |
| **Visual verification not working** | Claims to use Puppeteer but no actual integration | High | ⏳ Pending |
| **No COMMS.md reading** | SENTINEL writes to COMMS but doesn't READ it | Medium | ✅ FIXED 2025-12-20 |
| **No CLAUDE.md context** | Doesn't follow project conventions | Medium | ✅ FIXED 2025-12-20 |
| **Tasks are mostly stubs** | Many tasks have commands but no real verification | Medium | ⏳ Pending |

### What's UNCLEAR

1. Does Claude actually get called and respond?
2. Are the PowerShell commands all Windows-compatible?
3. What happens when SENTINEL finds a REAL bug - does it fix code?
4. How does iteration cycling work - repeat or progress?

---

## Recommended Improvements

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  RECOMMENDED IMPROVEMENTS (in order of priority)                                │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  1. ✅ UPDATE sentinel.json (COMPLETED 2025-12-20)                              │
│     └── ✅ Fixed test counts (1192 → 2583)                                     │
│     └── ✅ Verified all file paths are correct                                 │
│                                                                                 │
│  2. ✅ ADD CONTEXT INJECTION (COMPLETED 2025-12-20)                             │
│     └── ✅ Added context_injection section                                     │
│     └── ✅ SENTINEL reads COMMS.md before acting                               │
│     └── ✅ SENTINEL follows CLAUDE.md rules                                    │
│                                                                                 │
│  3. ✅ ADD AGENT COORDINATION (COMPLETED 2025-12-20)                            │
│     └── ✅ Added agent_coordination_protocol section                           │
│     └── ✅ Handoff protocol for complex issues                                 │
│     └── ✅ Conflict avoidance with other agents                                │
│                                                                                 │
│  4. ⏳ VERIFY CLAUDE API WORKS (PENDING)                                        │
│     └── Test that stream_agent_response() actually works                       │
│     └── Check OAuth token is valid                                             │
│                                                                                 │
│  5. ⏳ ADD VISUAL VERIFICATION (PENDING)                                        │
│     └── Integrate MCP Puppeteer for real screenshots                           │
│     └── Or use system screenshots via PowerShell                               │
│                                                                                 │
│  6. ⏳ IMPROVE TASK DEFINITIONS (PENDING)                                       │
│     └── Make tasks more specific with real verification                        │
│     └── Add tasks for things that actually break                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Session Information

**Documented by:** CMDTV (Claude Opus 4.5)
**Date:** 2025-12-20
**Session:** ULTRATHINK Mode - Codebase Stabilization
**Commit:** 549c3c9

This documentation was created during a session where:
- 12 test failures were fixed (now 2583 passing)
- SENTINEL agent was analyzed and documented
- All 4 core files were explained with visual diagrams

---

## Updates Log

| Date | Author | Changes |
|------|--------|---------|
| 2025-12-20 | CMDTV | Initial documentation created |
| 2025-12-20 | CMDTV | Updated sentinel.json test counts (1192 → 2583) |
| 2025-12-20 | CMDTV | Added context_injection section to sentinel.json |
| 2025-12-20 | CMDTV | Added agent_coordination_protocol section |
| 2025-12-20 | CMDTV | Added agent_pool with CMDTV, JARVIS1-5 |
| 2025-12-20 | CMDTV | Updated documentation with new sections |

---

*End of SENTINEL Agent Documentation*
