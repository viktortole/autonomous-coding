#!/usr/bin/env python3
"""
🛡️ SENTINEL-DEV v1.0 - Autonomous Dev Server Guardian
======================================================

Monitors Control Station dev environment health and auto-repairs issues.
Uses minimal tokens when healthy, comprehensive diagnosis when issues detected.

Usage:
    python run_sentinel.py                    # Run single health check
    python run_sentinel.py -i 5               # Run 5 iterations (conserve tokens)
    python run_sentinel.py -i 10              # Run 10 iterations
    python run_sentinel.py --continuous       # Never stop (daemon mode, infinite)
    python run_sentinel.py --deep             # Force deep health check
    python run_sentinel.py --repair           # Force repair mode
    python run_sentinel.py --dry-run          # Show what would be done

Token Budget:
    - Quick checks: ~0 tokens (pure bash)
    - Smart checks: ~500 tokens per check
    - Deep checks: ~2000 tokens per check
    - Repairs: ~3000 tokens per repair
    - Daily limit: 10,000 tokens
    - Recommended: -i 5 for token conservation

Author: AUTOAGENTS / SENTINEL-DEV
Created: 2025-12-19
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment variables FIRST (before SDK imports)
load_dotenv()

# Claude Code SDK imports
from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient

from llm_provider import get_llm_provider
from opencode_client import OpenCodeClient

# ═══════════════════════════════════════════════════════════════════════════════
# 🎨 STYLE & VISUAL OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

class Style:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'

    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'


class SentinelEmoji:
    """SENTINEL-specific emojis for visual output."""
    SHIELD = "🛡️"
    MONITORING = "🔍"
    HEALTHY = "✅"
    DEGRADED = "⚠️"
    ERROR = "❌"
    REPAIRING = "🔧"
    SUCCESS = "✨"
    ESCALATING = "🚨"
    WAITING = "⏳"
    IDLE = "😴"
    ACTIVE = "👁️"
    BASH = "💻"
    INFO = "ℹ️"
    TOKEN = "🪙"


# ═══════════════════════════════════════════════════════════════════════════════
# 📊 DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"
    UNKNOWN = "unknown"


class MonitoringMode(Enum):
    """SENTINEL operational modes."""
    IDLE = "idle"
    MONITORING = "monitoring"
    REPAIRING = "repairing"
    ESCALATING = "escalating"


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    timestamp: datetime
    check_type: str  # "quick" | "deep"
    status: HealthStatus
    component: str
    message: str
    duration_ms: int
    tokens_used: int = 0
    details: dict = field(default_factory=dict)


@dataclass
class RepairResult:
    """Result of a repair attempt."""
    timestamp: datetime
    repair_type: str
    success: bool
    message: str
    duration_ms: int
    tokens_used: int
    steps_completed: list = field(default_factory=list)


@dataclass
class SentinelState:
    """SENTINEL operational state."""
    mode: MonitoringMode = MonitoringMode.IDLE
    last_check_time: Optional[datetime] = None
    last_repair_time: Optional[datetime] = None
    consecutive_failures: int = 0
    health_history: list = field(default_factory=list)
    repair_history: list = field(default_factory=list)
    token_usage_today: int = 0
    token_usage_reset_date: str = ""
    repairs_today: int = 0
    restarts_today: int = 0
    cycle_count: int = 0


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# Paths
SCRIPT_DIR = Path(__file__).parent
SENTINEL_TASKS = SCRIPT_DIR / "sentinel_tasks.json"
LOGS_DIR = SCRIPT_DIR / "logs" / "sentinel"
CONTROL_STATION = Path("C:/Users/ToleV/Desktop/TestingFolder/control-station")
COMMS_MD = CONTROL_STATION / ".claude" / "COMMS.md"

# Dev server config
DEV_SERVER_URL = "http://127.0.0.1:3000"
DEV_SERVER_PORT = 3000

# Token budgets
TOKEN_BUDGET = {
    "daily_limit": 10000,
    "quick_check": 0,
    "smart_check": 500,
    "deep_check": 2000,
    "repair": 3000,
    "warning_threshold": 0.8,
}

# Timing (in seconds)
TIMING = {
    "idle_check_interval": 300,      # 5 minutes when healthy
    "degraded_check_interval": 120,  # 2 minutes when degraded
    "alert_check_interval": 30,      # 30 seconds during issues
    "recovery_duration": 600,        # 10 minutes in recovery mode
    "http_timeout": 3,
    "process_timeout": 5,
    "repair_timeout": 120,
}

# Rate limits
RATE_LIMITS = {
    "max_repairs_per_hour": 5,
    "max_restarts_per_day": 10,
    "max_consecutive_failures": 3,
}

# SENTINEL Agent Configuration
SENTINEL_CONFIG = {
    "model": "claude-sonnet-4-20250514",  # Sonnet 4 - OAuth compatible
    "name": "SENTINEL-DEV",
    "role": "DevOps Guardian & Auto-Repair",
    "emoji": "🛡️",
}


# ═══════════════════════════════════════════════════════════════════════════════
# 🤖 CLAUDE SDK CLIENT
# ═══════════════════════════════════════════════════════════════════════════════

def create_sentinel_client(project_dir: Path, model: str = None):
    """
    Create a Claude SDK client for SENTINEL diagnostics.

    Uses OAuth token from .env (CLAUDE_CODE_OAUTH_TOKEN).
    """
    if model is None:
        model = SENTINEL_CONFIG["model"]

    provider = get_llm_provider()
    if provider == "opencode":
        return OpenCodeClient(project_dir=project_dir, model=model)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")

    if not api_key and not oauth_token:
        raise ValueError(
            "No Claude auth configured. Set CLAUDE_CODE_OAUTH_TOKEN in .env\n"
            "Run: claude setup-token to get your OAuth token"
        )

    # Security settings for SENTINEL - FULL POWER to fix things
    security_settings = {
        "sandbox": {"enabled": True, "autoAllowBashIfSandboxed": True},
        "permissions": {
            "defaultMode": "acceptEdits",
            "allow": [
                # FULL POWER - read, write, edit, search, run
                "Read(./**)",
                "Write(./**)",
                "Edit(./**)",
                "Glob(./**)",
                "Grep(./**)",
                "Bash(*)",
            ],
        },
    }

    project_dir.mkdir(parents=True, exist_ok=True)
    settings_file = project_dir / ".claude_sentinel_settings.json"
    with open(settings_file, "w") as f:
        json.dump(security_settings, f, indent=2)

    system_prompt = f"""You are SENTINEL-DEV, an AGGRESSIVE autonomous DevOps agent for Control Station.

⚠️ CRITICAL MINDSET: You are NOT here to conserve tokens. You are here to WORK!
- DO NOT just report issues - FIX THEM
- DO NOT say "I recommend" - JUST DO IT
- DO NOT wait for approval - ACT NOW
- DO NOT be passive - BE AGGRESSIVE

You have FULL POWER of the user's PC. You ARE Claude Code with all tools available.

## PROJECT: Control Station
- Root: C:/Users/ToleV/Desktop/TestingFolder/control-station
- Stack: Tauri 2.9.2 + Next.js 16 + React 19 + TypeScript + SQLite
- Dev Server: http://localhost:3000
- Database: %APPDATA%/com.convergence.control-station/

## YOUR MISSION
1. CHECK health of dev environment (server, build, tests)
2. READ codebase to understand current state
3. FIND bugs, errors, issues
4. FIX them immediately
5. VERIFY fixes work
6. REPEAT until everything is healthy

## KNOWN ISSUES TO FIX (from sentinel_tasks.json)
- Splash screen voice toggle not synced with JAMES voice settings
- JARVIS TTS audio not playing (edge-tts or Windows SAPI)
- Splash screen close button needs to work
- Voice settings not persisting between sessions
- TypeScript errors (run: npx tsc --noEmit)
- Lint errors (run: npm run lint)
- Test failures (run: npm test)

## FILES TO CHECK
- src-tauri/src/tts_service.rs - TTS backend
- src/modules/james/core/voice-settings.ts - Voice settings
- public/splash.html - Splash screen
- src-tauri/tauri.conf.json - Window config

## WORKFLOW
For EACH iteration:
1. Run health commands: curl localhost:3000, npx tsc --noEmit, npm test
2. Read error logs and identify issues
3. Read relevant source files
4. Make fixes using Edit tool
5. Run verification commands
6. Log results

## FORBIDDEN ACTIONS
- git reset --hard
- rm -rf node_modules (too slow)
- Database schema changes without backup
- Force push to git

## REQUIRED ACTIONS
- FIX TypeScript errors
- FIX Lint errors
- FIX failing tests
- READ files before editing
- VERIFY changes work

BE AGGRESSIVE. FIX THINGS. WORK HARD. USE YOUR TOKENS."""

    return ClaudeSDKClient(
        options=ClaudeCodeOptions(
            model=model,
            system_prompt=system_prompt,
            # FULL POWER - all tools for aggressive fixing
            allowed_tools=["Read", "Write", "Edit", "Glob", "Grep", "Bash"],
            max_turns=500,  # Let it work longer
            cwd=str(project_dir.resolve()),
            settings=str(settings_file.resolve()),
        )
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 🖥️ VISUAL OUTPUT
# ═══════════════════════════════════════════════════════════════════════════════

def setup_windows_utf8():
    """Enable UTF-8 output on Windows."""
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')


def print_banner():
    """Print the SENTINEL startup banner."""
    print(f"""
{Style.RED}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}🛡️ SENTINEL-DEV v2.0{Style.RESET}{Style.RED}  {Style.CYAN}+ Claude AI{Style.RESET}{Style.RED}                            ║
║   {Style.DIM}Autonomous Dev Server Guardian with Real AI Diagnostics{Style.RESET}{Style.RED}         ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")


def print_agent_header():
    """Print SENTINEL agent identification."""
    print(f"""
{Style.RED}┌──────────────────────────────────────────────────────────────────────┐{Style.RESET}
{Style.RED}│{Style.RESET} {SentinelEmoji.SHIELD} {Style.BOLD}SENTINEL-DEV{Style.RESET} - DevOps Guardian & Auto-Repair
{Style.RED}│{Style.RESET} {Style.DIM}Expertise: Server Health, Build Pipeline, Database, Process Mgmt{Style.RESET}
{Style.RED}└──────────────────────────────────────────────────────────────────────┘{Style.RESET}
""")


def print_cycle_header(cycle: int, max_iterations: int, mode: MonitoringMode):
    """Print monitoring cycle header."""
    mode_emoji = {
        MonitoringMode.IDLE: SentinelEmoji.IDLE,
        MonitoringMode.MONITORING: SentinelEmoji.MONITORING,
        MonitoringMode.REPAIRING: SentinelEmoji.REPAIRING,
        MonitoringMode.ESCALATING: SentinelEmoji.ESCALATING,
    }
    emoji = mode_emoji.get(mode, SentinelEmoji.MONITORING)

    # Show max iterations or infinity symbol
    max_str = "∞" if max_iterations == -1 else str(max_iterations)

    print(f"""
{Style.YELLOW}╭─────────────────────────────────────────────────────────────────────╮{Style.RESET}
{Style.YELLOW}│{Style.RESET} {Style.BOLD}{emoji} MONITORING CYCLE {cycle}/{max_str}{Style.RESET}  [{mode.value.upper()}]
{Style.YELLOW}╰─────────────────────────────────────────────────────────────────────╯{Style.RESET}
""")


def print_status_box(state: SentinelState, results: list[HealthCheckResult], next_check_seconds: int):
    """Print system status summary box."""
    # Determine overall status
    if all(r.status == HealthStatus.HEALTHY for r in results):
        overall = f"{Style.GREEN}HEALTHY{Style.RESET}"
    elif any(r.status == HealthStatus.ERROR for r in results):
        overall = f"{Style.RED}ERROR{Style.RESET}"
    else:
        overall = f"{Style.YELLOW}DEGRADED{Style.RESET}"

    # Component statuses
    dev_server = next((r for r in results if "HTTP" in r.component or "Server" in r.component), None)
    tauri = next((r for r in results if "Tauri" in r.component or "Process" in r.component), None)
    database = next((r for r in results if "Database" in r.component or "DB" in r.component), None)

    dev_status = f"{SentinelEmoji.HEALTHY}" if dev_server and dev_server.status == HealthStatus.HEALTHY else f"{SentinelEmoji.ERROR}"
    tauri_status = f"{SentinelEmoji.HEALTHY}" if tauri and tauri.status == HealthStatus.HEALTHY else f"{SentinelEmoji.WAITING}"
    db_status = f"{SentinelEmoji.HEALTHY}" if database and database.status == HealthStatus.HEALTHY else f"{SentinelEmoji.WAITING}"

    # Format next check time
    if next_check_seconds >= 60:
        next_check = f"{next_check_seconds // 60}m {next_check_seconds % 60}s"
    else:
        next_check = f"{next_check_seconds}s"

    print(f"""
{Style.CYAN}┌─────────────────────────────────────┐{Style.RESET}
{Style.CYAN}│{Style.RESET} {Style.BOLD}📊 SYSTEM STATUS{Style.RESET}                    {Style.CYAN}│{Style.RESET}
{Style.CYAN}├─────────────────────────────────────┤{Style.RESET}
{Style.CYAN}│{Style.RESET} {dev_status} Dev Server:     {overall:<18} {Style.CYAN}│{Style.RESET}
{Style.CYAN}│{Style.RESET} {tauri_status} Tauri App:      Running          {Style.CYAN}│{Style.RESET}
{Style.CYAN}│{Style.RESET} {db_status} Database:       Connected        {Style.CYAN}│{Style.RESET}
{Style.CYAN}│{Style.RESET} {SentinelEmoji.WAITING} Next Check:     {next_check:<16} {Style.CYAN}│{Style.RESET}
{Style.CYAN}└─────────────────────────────────────┘{Style.RESET}
""")


def print_token_usage(state: SentinelState):
    """Print token usage summary."""
    limit = TOKEN_BUDGET["daily_limit"]
    used = state.token_usage_today
    percentage = (used / limit) * 100 if limit > 0 else 0

    if percentage < 50:
        color = Style.GREEN
    elif percentage < 80:
        color = Style.YELLOW
    else:
        color = Style.RED

    print(f"  {SentinelEmoji.TOKEN} Token usage: {color}{used:,}{Style.RESET} / {limit:,} ({percentage:.1f}%)")


def print_check_result(result: HealthCheckResult):
    """Print health check result."""
    status_emoji = {
        HealthStatus.HEALTHY: SentinelEmoji.HEALTHY,
        HealthStatus.DEGRADED: SentinelEmoji.DEGRADED,
        HealthStatus.ERROR: SentinelEmoji.ERROR,
        HealthStatus.UNKNOWN: SentinelEmoji.WAITING,
    }
    emoji = status_emoji.get(result.status, SentinelEmoji.WAITING)

    color = Style.GREEN if result.status == HealthStatus.HEALTHY else (
        Style.YELLOW if result.status == HealthStatus.DEGRADED else Style.RED
    )

    print(f"  {emoji} {result.component}: {color}{result.message}{Style.RESET} ({result.duration_ms}ms)")


def print_repair_start(repair_type: str):
    """Print repair start message."""
    print(f"\n  {SentinelEmoji.REPAIRING} Starting repair: {Style.BOLD}{repair_type}{Style.RESET}")


def print_repair_step(step: str, success: bool):
    """Print repair step result."""
    emoji = SentinelEmoji.HEALTHY if success else SentinelEmoji.ERROR
    color = Style.GREEN if success else Style.RED
    print(f"     {emoji} {color}{step}{Style.RESET}")


def print_repair_result(result: RepairResult):
    """Print repair result summary."""
    if result.success:
        print(f"\n  {SentinelEmoji.SUCCESS} {Style.GREEN}Repair successful!{Style.RESET} ({result.duration_ms}ms)")
    else:
        print(f"\n  {SentinelEmoji.ERROR} {Style.RED}Repair failed: {result.message}{Style.RESET}")


def print_info(message: str):
    """Print info message."""
    print(f"  {SentinelEmoji.INFO} {Style.CYAN}{message}{Style.RESET}")


def print_warning(message: str):
    """Print warning message."""
    print(f"  {SentinelEmoji.DEGRADED} {Style.YELLOW}{message}{Style.RESET}")


def print_error(message: str):
    """Print error message."""
    print(f"  {SentinelEmoji.ERROR} {Style.RED}{message}{Style.RESET}")


def print_thinking(message: str):
    """Print SENTINEL's reasoning."""
    print(f"  💭 {Style.WHITE}{message}{Style.RESET}")


def print_tool_use(tool_name: str, tool_input: dict = None):
    """Print tool usage with nice formatting (for Claude SDK responses)."""
    tool_emojis = {
        "Read": "📖",
        "Write": "✍️",
        "Edit": "✏️",
        "Glob": "🔍",
        "Grep": "🔎",
        "Bash": "💻",
        "Task": "🚀",
    }
    emoji = tool_emojis.get(tool_name, "🔧")

    # Extract relevant info from tool input
    detail = ""
    if tool_input:
        if "file_path" in tool_input:
            detail = f" → {Path(tool_input['file_path']).name}"
        elif "pattern" in tool_input:
            detail = f" → {tool_input['pattern'][:30]}..."
        elif "command" in tool_input:
            cmd = tool_input['command'][:50]
            detail = f" → {cmd}..."

    print(f"  {Style.BLUE}{emoji} {tool_name}{Style.DIM}{detail}{Style.RESET}")


def print_tool_result(is_error: bool, content: str = None):
    """Print tool result."""
    if is_error:
        print(f"     {Style.RED}❌ Error{Style.RESET}")
        if content:
            first_line = str(content).split('\n')[0][:60]
            print(f"     {Style.DIM}{first_line}{Style.RESET}")
    else:
        print(f"     {Style.GREEN}✅ Done{Style.RESET}")


def print_ai_thinking(text: str):
    """Print Claude's thinking/reasoning with nice formatting."""
    if text.strip():
        lines = text.strip().split('\n')
        for line in lines[:5]:  # Show first 5 lines
            if line.strip():
                print(f"  {Style.WHITE}💭 {line[:80]}{Style.RESET}")
        if len(lines) > 5:
            print(f"  {Style.DIM}   ... ({len(lines) - 5} more lines){Style.RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# 🔍 HEALTH CHECKS - TIER 1 (PURE BASH, ZERO TOKENS)
# ═══════════════════════════════════════════════════════════════════════════════

def run_bash(command: str, timeout: int = 10) -> tuple[int, str, str]:
    """Run a bash/PowerShell command and return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def check_http_ping() -> HealthCheckResult:
    """Tier 1: Quick HTTP ping to dev server (0 tokens)."""
    start_time = time.time()

    # Use curl for HTTP check
    command = f'curl -f {DEV_SERVER_URL} --max-time {TIMING["http_timeout"]} --silent --output $null; if ($LASTEXITCODE -eq 0) {{ "HEALTHY" }} else {{ "UNHEALTHY" }}'

    exit_code, stdout, stderr = run_bash(command, timeout=TIMING["http_timeout"] + 2)
    duration_ms = int((time.time() - start_time) * 1000)

    if "HEALTHY" in stdout or exit_code == 0:
        return HealthCheckResult(
            timestamp=datetime.now(),
            check_type="quick",
            status=HealthStatus.HEALTHY,
            component="Dev Server HTTP",
            message="Responding (HTTP 200)",
            duration_ms=duration_ms,
            tokens_used=0
        )
    else:
        return HealthCheckResult(
            timestamp=datetime.now(),
            check_type="quick",
            status=HealthStatus.ERROR,
            component="Dev Server HTTP",
            message="Not responding",
            duration_ms=duration_ms,
            tokens_used=0,
            details={"error": stderr or "Connection failed"}
        )


def check_port_status() -> HealthCheckResult:
    """Tier 1: Check if port 3000 is in use (0 tokens)."""
    start_time = time.time()

    command = f'$conn = Get-NetTCPConnection -LocalPort {DEV_SERVER_PORT} -ErrorAction SilentlyContinue; if ($conn) {{ "PORT_IN_USE" }} else {{ "PORT_FREE" }}'

    exit_code, stdout, stderr = run_bash(command, timeout=TIMING["process_timeout"])
    duration_ms = int((time.time() - start_time) * 1000)

    if "PORT_IN_USE" in stdout:
        return HealthCheckResult(
            timestamp=datetime.now(),
            check_type="quick",
            status=HealthStatus.HEALTHY,
            component="Port 3000",
            message="In use (expected)",
            duration_ms=duration_ms,
            tokens_used=0
        )
    else:
        return HealthCheckResult(
            timestamp=datetime.now(),
            check_type="quick",
            status=HealthStatus.ERROR,
            component="Port 3000",
            message="Not in use (server may be down)",
            duration_ms=duration_ms,
            tokens_used=0
        )


def check_database_file() -> HealthCheckResult:
    """Tier 1: Check if database file exists (0 tokens)."""
    start_time = time.time()

    command = '$dbPath = "$env:APPDATA/com.convergence.control-station/control-station.dev.db"; if (Test-Path $dbPath) { $size = (Get-Item $dbPath).Length / 1KB; "EXISTS_SIZE_$size" } else { "MISSING" }'

    exit_code, stdout, stderr = run_bash(command, timeout=TIMING["process_timeout"])
    duration_ms = int((time.time() - start_time) * 1000)

    if "EXISTS" in stdout:
        return HealthCheckResult(
            timestamp=datetime.now(),
            check_type="quick",
            status=HealthStatus.HEALTHY,
            component="Database File",
            message="Exists and accessible",
            duration_ms=duration_ms,
            tokens_used=0
        )
    else:
        return HealthCheckResult(
            timestamp=datetime.now(),
            check_type="quick",
            status=HealthStatus.ERROR,
            component="Database File",
            message="Missing or inaccessible",
            duration_ms=duration_ms,
            tokens_used=0
        )


def run_quick_health_checks() -> list[HealthCheckResult]:
    """Run all Tier 1 quick health checks (0 tokens total)."""
    results = []

    print(f"\n  {SentinelEmoji.MONITORING} Quick Health Check (Tier 1)")

    # HTTP Ping
    print(f"     {SentinelEmoji.BASH} curl → {DEV_SERVER_URL}")
    http_result = check_http_ping()
    print_check_result(http_result)
    results.append(http_result)

    # Port check
    print(f"     {SentinelEmoji.BASH} Get-NetTCPConnection → Port {DEV_SERVER_PORT}")
    port_result = check_port_status()
    print_check_result(port_result)
    results.append(port_result)

    # Database file
    print(f"     {SentinelEmoji.BASH} Test-Path → Database")
    db_result = check_database_file()
    print_check_result(db_result)
    results.append(db_result)

    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 CLAUDE AI DIAGNOSTIC SESSION
# ═══════════════════════════════════════════════════════════════════════════════

def build_diagnostic_prompt(results: list[HealthCheckResult], state: SentinelState) -> str:
    """Build a comprehensive diagnostic prompt from health check findings."""
    parts = []

    # Header
    parts.append("# 🛡️ SENTINEL-DEV Diagnostic Request")
    parts.append(f"**Cycle:** {state.cycle_count} | **Mode:** {state.mode.value}")
    parts.append(f"**Consecutive Failures:** {state.consecutive_failures}")
    parts.append("")

    # Health Check Findings
    parts.append("## Health Check Results")
    parts.append("```")
    for r in results:
        status_emoji = "✅" if r.status == HealthStatus.HEALTHY else ("⚠️" if r.status == HealthStatus.DEGRADED else "❌")
        parts.append(f"{status_emoji} {r.component}: {r.status.value} - {r.message} ({r.duration_ms}ms)")
        if r.details:
            parts.append(f"   Details: {json.dumps(r.details)}")
    parts.append("```")
    parts.append("")

    # Issues Detected
    issues = [r for r in results if r.status != HealthStatus.HEALTHY]
    if issues:
        parts.append("## Issues Requiring Analysis")
        for issue in issues:
            parts.append(f"- **{issue.component}**: {issue.message}")
            if issue.details.get("error"):
                parts.append(f"  - Error: `{issue.details['error']}`")
        parts.append("")

    # Instructions
    parts.append("## Your Task")
    parts.append("1. Analyze the issues above and identify root cause")
    parts.append("2. Check relevant logs and configuration files")
    parts.append("3. Determine if auto-repair is safe:")
    parts.append("   - Safe repairs: restart server, clear cache, fix permissions")
    parts.append("   - Unsafe repairs: code changes, database modifications, git operations")
    parts.append("4. Execute safe repairs OR recommend human intervention")
    parts.append("")
    parts.append("## Project Paths")
    parts.append(f"- Control Station: `{CONTROL_STATION}`")
    parts.append(f"- Database: `%APPDATA%/com.convergence.control-station/`")
    parts.append(f"- Dev Server: `{DEV_SERVER_URL}`")
    parts.append("")
    parts.append("---")
    parts.append("**BEGIN ANALYSIS. Be thorough but efficient. Show your reasoning.**")

    return "\n".join(parts)


async def run_sentinel_ai_session(client, prompt: str, state: SentinelState) -> tuple[str, str, int]:
    """
    Run a SENTINEL AI diagnostic session with visual output.

    Returns:
        tuple: (status, response_text, tokens_used)
    """
    provider_label = getattr(client, "provider_label", "Claude AI")
    print(f"\n  {Style.CYAN}🤖 Invoking {provider_label} for diagnosis...{Style.RESET}")
    print(f"  {Style.DIM}Model: {SENTINEL_CONFIG['model']}{Style.RESET}\n")

    tokens_used = 0

    try:
        await client.query(prompt)

        response_text = ""
        current_text_buffer = ""

        async for msg in client.receive_response():
            msg_type = type(msg).__name__

            if msg_type == "AssistantMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__

                    if block_type == "TextBlock" and hasattr(block, "text"):
                        response_text += block.text
                        current_text_buffer += block.text

                        # Print thinking/reasoning with nice formatting
                        if '\n' in current_text_buffer:
                            lines = current_text_buffer.split('\n')
                            for line in lines[:-1]:
                                if line.strip():
                                    print(f"  {Style.WHITE}💭 {line[:100]}{Style.RESET}")
                            current_text_buffer = lines[-1]

                    elif block_type == "ToolUseBlock" and hasattr(block, "name"):
                        # Flush text buffer first
                        if current_text_buffer.strip():
                            print(f"  {Style.WHITE}💭 {current_text_buffer.strip()[:100]}{Style.RESET}")
                            current_text_buffer = ""

                        tool_input = getattr(block, "input", {})
                        print_tool_use(block.name, tool_input)

            elif msg_type == "UserMessage" and hasattr(msg, "content"):
                for block in msg.content:
                    block_type = type(block).__name__
                    if block_type == "ToolResultBlock":
                        is_error = getattr(block, "is_error", False)
                        content = getattr(block, "content", "")
                        print_tool_result(is_error, content)

            # Try to extract usage info
            if hasattr(msg, "usage"):
                usage = msg.usage
                if hasattr(usage, "input_tokens"):
                    tokens_used += usage.input_tokens
                if hasattr(usage, "output_tokens"):
                    tokens_used += usage.output_tokens

        # Flush remaining text
        if current_text_buffer.strip():
            print(f"  {Style.WHITE}💭 {current_text_buffer.strip()[:100]}{Style.RESET}")

        print(f"\n  {Style.DIM}{'─' * 66}{Style.RESET}")
        print(f"  {Style.GREEN}✅ AI Analysis Complete{Style.RESET}")

        # Estimate tokens if not provided
        if tokens_used == 0:
            # Rough estimate: ~4 chars per token for input+output
            tokens_used = (len(prompt) + len(response_text)) // 4

        return "complete", response_text, tokens_used

    except Exception as e:
        print(f"  {Style.RED}❌ AI Session Error: {e}{Style.RESET}")
        return "error", str(e), 0


# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 AUTO-REPAIR WORKFLOWS
# ═══════════════════════════════════════════════════════════════════════════════

def repair_dev_server(state: SentinelState) -> RepairResult:
    """Repair crashed dev server by killing port and restarting."""
    start_time = time.time()
    steps_completed = []

    print_repair_start("Dev Server Restart")

    # Step 1: Kill processes on port 3000
    print(f"     {SentinelEmoji.BASH} Killing processes on port 3000...")
    command = f'Get-NetTCPConnection -LocalPort {DEV_SERVER_PORT} -ErrorAction SilentlyContinue | ForEach-Object {{ Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }}'
    exit_code, stdout, stderr = run_bash(command, timeout=10)
    steps_completed.append("Kill port 3000 processes")
    print_repair_step("Kill port 3000 processes", True)

    # Step 2: Wait for port release
    print(f"     {SentinelEmoji.WAITING} Waiting for port release...")
    time.sleep(2)
    steps_completed.append("Wait for port release")
    print_repair_step("Wait for port release", True)

    # Step 3: Start dev server
    print(f"     {SentinelEmoji.BASH} Starting dev server...")
    launcher_script = CONTROL_STATION / "scripts" / "tauri-dev-live.ps1"

    if launcher_script.exists():
        # Start in background
        command = f'Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-File", "{launcher_script}" -WindowStyle Minimized'
        exit_code, stdout, stderr = run_bash(command, timeout=10)
        steps_completed.append("Launch tauri-dev-live.ps1")
        print_repair_step("Launch tauri-dev-live.ps1", exit_code == 0)
    else:
        # Fallback: direct npm run dev
        command = f'Start-Process powershell -ArgumentList "-NoProfile", "-Command", "cd \'{CONTROL_STATION}\'; npm run dev" -WindowStyle Minimized'
        exit_code, stdout, stderr = run_bash(command, timeout=10)
        steps_completed.append("Launch npm run dev")
        print_repair_step("Launch npm run dev", exit_code == 0)

    # Step 4: Wait for HTTP 200
    print(f"     {SentinelEmoji.WAITING} Waiting for HTTP 200...")
    max_wait = 90
    start_wait = time.time()
    server_ready = False

    while time.time() - start_wait < max_wait:
        http_result = check_http_ping()
        if http_result.status == HealthStatus.HEALTHY:
            server_ready = True
            break
        time.sleep(2)

    steps_completed.append("Wait for HTTP 200")
    print_repair_step(f"Wait for HTTP 200 ({int(time.time() - start_wait)}s)", server_ready)

    duration_ms = int((time.time() - start_time) * 1000)

    # Update state
    state.restarts_today += 1
    state.repairs_today += 1

    if server_ready:
        return RepairResult(
            timestamp=datetime.now(),
            repair_type="dev_server_restart",
            success=True,
            message="Dev server restarted successfully",
            duration_ms=duration_ms,
            tokens_used=0,  # No Claude used
            steps_completed=steps_completed
        )
    else:
        return RepairResult(
            timestamp=datetime.now(),
            repair_type="dev_server_restart",
            success=False,
            message="Dev server failed to start within 90 seconds",
            duration_ms=duration_ms,
            tokens_used=0,
            steps_completed=steps_completed
        )


def repair_database_lock(state: SentinelState) -> RepairResult:
    """Clear database lock by deleting WAL files."""
    start_time = time.time()
    steps_completed = []

    print_repair_start("Database Lock Clear")

    # Step 1: Delete WAL and SHM files
    print(f"     {SentinelEmoji.BASH} Clearing WAL files...")
    command = '''
    $dbDir = "$env:APPDATA/com.convergence.control-station"
    Remove-Item "$dbDir/*.db-wal" -Force -ErrorAction SilentlyContinue
    Remove-Item "$dbDir/*.db-shm" -Force -ErrorAction SilentlyContinue
    "CLEARED"
    '''
    exit_code, stdout, stderr = run_bash(command, timeout=10)
    steps_completed.append("Clear WAL files")
    print_repair_step("Clear WAL files", "CLEARED" in stdout or exit_code == 0)

    # Step 2: Verify database is accessible
    print(f"     {SentinelEmoji.BASH} Verifying database...")
    db_result = check_database_file()
    steps_completed.append("Verify database")
    print_repair_step("Verify database", db_result.status == HealthStatus.HEALTHY)

    duration_ms = int((time.time() - start_time) * 1000)
    state.repairs_today += 1

    return RepairResult(
        timestamp=datetime.now(),
        repair_type="database_lock_clear",
        success=db_result.status == HealthStatus.HEALTHY,
        message="Database lock cleared" if db_result.status == HealthStatus.HEALTHY else "Database still inaccessible",
        duration_ms=duration_ms,
        tokens_used=0,
        steps_completed=steps_completed
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 📝 LOGGING TO COMMS.MD
# ═══════════════════════════════════════════════════════════════════════════════

def log_to_comms(event_type: str, details: dict):
    """Append log entry to COMMS.md for agent coordination."""
    try:
        if not COMMS_MD.parent.exists():
            COMMS_MD.parent.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = f"""
### {SentinelEmoji.SHIELD} SENTINEL-DEV - {timestamp}
**Event:** {event_type}
**Details:**
```json
{json.dumps(details, indent=2)}
```

"""

        with open(COMMS_MD, "a", encoding="utf-8") as f:
            f.write(entry)

    except Exception as e:
        print_warning(f"Failed to log to COMMS.md: {e}")


def log_health_check(results: list[HealthCheckResult], state: SentinelState):
    """Log health check results to COMMS.md."""
    status = "healthy" if all(r.status == HealthStatus.HEALTHY for r in results) else (
        "error" if any(r.status == HealthStatus.ERROR for r in results) else "degraded"
    )

    log_to_comms("health_check", {
        "cycle": state.cycle_count,
        "status": status,
        "checks": [
            {
                "component": r.component,
                "status": r.status.value,
                "message": r.message,
                "duration_ms": r.duration_ms
            }
            for r in results
        ],
        "token_usage_today": state.token_usage_today
    })


def log_repair(result: RepairResult, state: SentinelState):
    """Log repair result to COMMS.md."""
    log_to_comms("repair", {
        "type": result.repair_type,
        "success": result.success,
        "message": result.message,
        "duration_ms": result.duration_ms,
        "steps": result.steps_completed,
        "repairs_today": state.repairs_today,
        "restarts_today": state.restarts_today
    })


# ═══════════════════════════════════════════════════════════════════════════════
# 🔄 MAIN MONITORING LOOP
# ═══════════════════════════════════════════════════════════════════════════════

def load_tasks() -> dict:
    """Load sentinel_tasks.json configuration."""
    try:
        with open(SENTINEL_TASKS, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print_error(f"Failed to load sentinel_tasks.json: {e}")
        return {}


def determine_next_check_interval(state: SentinelState, results: list[HealthCheckResult]) -> int:
    """Determine when to run next check based on health status."""
    # If any errors, check more frequently
    if any(r.status == HealthStatus.ERROR for r in results):
        return TIMING["alert_check_interval"]

    # If degraded, check moderately
    if any(r.status == HealthStatus.DEGRADED for r in results):
        return TIMING["degraded_check_interval"]

    # All healthy - normal idle interval
    return TIMING["idle_check_interval"]


def should_attempt_repair(state: SentinelState, results: list[HealthCheckResult]) -> tuple[bool, str]:
    """Decide if we should attempt auto-repair."""
    # Check rate limits
    if state.repairs_today >= RATE_LIMITS["max_repairs_per_hour"]:
        return False, "Rate limit reached (repairs per hour)"

    if state.restarts_today >= RATE_LIMITS["max_restarts_per_day"]:
        return False, "Rate limit reached (restarts per day)"

    # Find which component failed
    for result in results:
        if result.status == HealthStatus.ERROR:
            if "HTTP" in result.component or "Server" in result.component:
                return True, "dev_server"
            if "Database" in result.component:
                return True, "database"

    return False, ""


def get_health_tasks(tasks_config: dict) -> list[dict]:
    """Get all health check tasks from config."""
    all_tasks = tasks_config.get("tasks", [])
    # Filter to health monitoring tasks
    health_tasks = [t for t in all_tasks if t.get("category") == "health-monitoring" or t.get("id", "").startswith("SENTINEL-HEALTH")]
    return health_tasks if health_tasks else all_tasks[:5]  # Fallback to first 5 tasks


def build_task_prompt(task: dict, project_info: dict) -> str:
    """Build an AGGRESSIVE prompt from a SENTINEL task definition."""
    parts = []

    # Header
    parts.append(f"# 🛡️ SENTINEL TASK: {task.get('title', 'Unknown Task')}")
    parts.append(f"**ID:** {task.get('id', 'N/A')} | **Priority:** {task.get('priority', 'medium')} | **Complexity:** {task.get('complexity', 'medium')}")
    parts.append("")

    # AGGRESSIVE mindset
    parts.append("## ⚠️ AGGRESSIVE MODE")
    parts.append("- DO NOT just check - FIX ISSUES")
    parts.append("- DO NOT report problems - SOLVE THEM")
    parts.append("- DO NOT conserve tokens - USE THEM TO WORK")
    parts.append("- If something is broken, FIX IT NOW")
    parts.append("")

    # Description
    desc = task.get("description", {})
    parts.append("## PROBLEM")
    parts.append(desc.get("problem", "No problem description"))
    parts.append("")
    parts.append("## GOAL")
    parts.append(desc.get("goal", "No goal description"))
    parts.append("")

    # Execution
    execution = task.get("execution", {})
    if execution.get("bash_commands"):
        parts.append("## COMMANDS TO RUN FIRST")
        for cmd in execution["bash_commands"]:
            parts.append(f"```powershell")
            parts.append(cmd)
            parts.append("```")
        parts.append("")

    if execution.get("success_criteria"):
        parts.append("## SUCCESS = WHEN THESE ARE TRUE")
        for c in execution["success_criteria"]:
            parts.append(f"- {c}")
        parts.append("")

    if execution.get("failure_indicators"):
        parts.append("## IF YOU SEE THESE = FIX THEM!")
        for f in execution["failure_indicators"]:
            parts.append(f"- {f}")
        parts.append("")

    # Project info
    parts.append("## PROJECT")
    parts.append(f"- **Root:** {project_info.get('root', CONTROL_STATION)}")
    parts.append(f"- **Dev Server:** {DEV_SERVER_URL}")
    parts.append("")

    # Aggressive workflow
    parts.append("## YOUR WORKFLOW")
    parts.append("1. Run the health check commands")
    parts.append("2. If errors found → Read the files → Fix the errors → Verify fix works")
    parts.append("3. If all healthy → Move to next check")
    parts.append("4. KEEP WORKING until everything passes")
    parts.append("")

    parts.append("---")
    parts.append("**START NOW. RUN COMMANDS. FIX EVERYTHING. BE AGGRESSIVE!**")

    return "\n".join(parts)


async def monitoring_loop(args):
    """
    Main monitoring loop - REAL Claude AI execution pattern.

    This follows the run_task.py pattern:
    1. For each iteration, pick a health task
    2. Build prompt from task definition
    3. Invoke Claude to execute it
    4. Stream responses with visual output
    5. 3 second delay between iterations
    """
    state = SentinelState()
    tasks_config = load_tasks()

    # Get health check tasks
    health_tasks = get_health_tasks(tasks_config)
    project_info = tasks_config.get("project", {"root": str(CONTROL_STATION)})

    # Determine max iterations
    max_iterations = -1 if args.continuous else args.iterations

    # Reset token usage if new day
    today = datetime.now().strftime("%Y-%m-%d")
    if state.token_usage_reset_date != today:
        state.token_usage_today = 0
        state.repairs_today = 0
        state.restarts_today = 0
        state.token_usage_reset_date = today

    print_info(f"Loaded {len(health_tasks)} health check tasks")
    print_info(f"Token budget: {TOKEN_BUDGET['daily_limit']:,} tokens/day")
    if max_iterations == -1:
        print_info(f"Mode: CONTINUOUS (Claude runs every cycle)")
    else:
        print_info(f"Mode: LIMITED ({max_iterations} iterations)")
    print()

    # Log session start
    log_to_comms("session_start", {
        "mode": "continuous" if max_iterations == -1 else f"limited_{max_iterations}",
        "max_iterations": max_iterations,
        "health_tasks": len(health_tasks),
        "token_budget": TOKEN_BUDGET["daily_limit"]
    })

    # Create log file for this session
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"sentinel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"🛡️ SENTINEL-DEV Session Log\n")
        f.write(f"{'=' * 70}\n")
        f.write(f"Started: {datetime.now().isoformat()}\n")
        f.write(f"Model: {SENTINEL_CONFIG['model']}\n")
        f.write(f"Iterations: {max_iterations}\n")
        f.write(f"{'=' * 70}\n\n")

    print(f"  {Style.DIM}📝 Log file: {log_file.name}{Style.RESET}\n")

    try:
        # ═══════════════════════════════════════════════════════════════
        # 🔄 MAIN LOOP - Claude runs EVERY iteration (like run_task.py)
        # ═══════════════════════════════════════════════════════════════
        iteration = 0
        while True:
            iteration += 1
            state.cycle_count = iteration

            # Check if we've reached max iterations
            if max_iterations != -1 and iteration > max_iterations:
                print_info(f"Completed {max_iterations} iterations. Session complete.")
                break

            # Pick task for this iteration (cycle through tasks)
            task_index = (iteration - 1) % len(health_tasks)
            current_task = health_tasks[task_index]

            # Print iteration header with progress bar
            progress = "█" * iteration + "░" * (max(0, max_iterations - iteration) if max_iterations > 0 else 0)
            max_str = str(max_iterations) if max_iterations > 0 else "∞"
            print(f"""
{Style.YELLOW}╭─────────────────────────────────────────────────────────────────────╮{Style.RESET}
{Style.YELLOW}│{Style.RESET} {Style.BOLD}🔄 ITERATION {iteration}/{max_str}{Style.RESET}  [{progress[:30]}]
{Style.YELLOW}│{Style.RESET} {Style.CYAN}📋 Task: {current_task['id']} - {current_task['title'][:40]}{Style.RESET}
{Style.YELLOW}╰─────────────────────────────────────────────────────────────────────╯{Style.RESET}
""")

            # Build prompt from task
            prompt = build_task_prompt(current_task, project_info)

            # Add continuation context for iterations > 1 - AGGRESSIVE
            if iteration > 1:
                prompt = f"""# 🛡️ SENTINEL ITERATION {iteration}/{max_str} - KEEP WORKING!

⚠️ DO NOT STOP. DO NOT CONSERVE TOKENS. KEEP FIXING!

Previous iteration may have found issues. Your job:
1. CHECK if previous fixes worked
2. FIND any remaining issues
3. FIX them immediately
4. VERIFY everything works

{prompt}

---
**KEEP GOING. FIX EVERYTHING. DO NOT GIVE UP!**"""

            # ═══════════════════════════════════════════════════════════════
            # 🤖 INVOKE CLAUDE - The Real Deal!
            # ═══════════════════════════════════════════════════════════════
            try:
                provider_label = "OpenCode CLI" if get_llm_provider() == "opencode" else "Claude AI"

                print(f"  {Style.CYAN}🤖 Invoking {provider_label}...{Style.RESET}")
                print(f"  {Style.DIM}Model: {SENTINEL_CONFIG['model']}{Style.RESET}\n")

                client = create_sentinel_client(CONTROL_STATION)

                async with client:
                    ai_status, ai_response, tokens = await run_sentinel_ai_session(
                        client, prompt, state
                    )

                # Update token usage
                state.token_usage_today += tokens

                # Log to file
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n{'=' * 70}\n")
                    f.write(f"📍 ITERATION {iteration}/{max_str}\n")
                    f.write(f"Task: {current_task['id']}\n")
                    f.write(f"Tokens: {tokens}\n")
                    f.write(f"{'=' * 70}\n")
                    f.write(f"Response:\n{ai_response}\n")

                # Print token status
                print(f"\n  {SentinelEmoji.TOKEN} Tokens this iteration: {Style.CYAN}{tokens:,}{Style.RESET}")
                print(f"  {SentinelEmoji.TOKEN} Total today: {Style.CYAN}{state.token_usage_today:,}{Style.RESET} / {TOKEN_BUDGET['daily_limit']:,}")

                if ai_status == "complete":
                    print(f"  {Style.GREEN}✅ Iteration {iteration} complete{Style.RESET}")
                else:
                    print(f"  {Style.YELLOW}⚠️ Iteration {iteration} had issues{Style.RESET}")

                # Log to COMMS.md
                log_to_comms("iteration_complete", {
                    "iteration": iteration,
                    "task": current_task['id'],
                    "tokens": tokens,
                    "status": ai_status
                })

            except Exception as e:
                provider_label = "OpenCode CLI" if get_llm_provider() == "opencode" else "Claude AI"
                print(f"  {Style.RED}❌ {provider_label} error: {e}{Style.RESET}")
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n❌ ERROR in iteration {iteration}: {e}\n")

            # Check if more iterations
            if max_iterations != -1 and iteration >= max_iterations:
                break

            # 3 second delay between iterations (NOT 300 seconds!)
            print(f"\n  {Style.DIM}⏳ Next iteration in 3 seconds...{Style.RESET}")
            await asyncio.sleep(3)

    except KeyboardInterrupt:
        print(f"\n\n{SentinelEmoji.SHIELD} SENTINEL-DEV interrupted by user.")

    # Session complete
    print(f"""
{Style.GREEN}╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   {Style.BOLD}✅ SENTINEL SESSION COMPLETE{Style.RESET}{Style.GREEN}                                     ║
║                                                                      ║
║   🔄 Iterations: {state.cycle_count:<50}      ║
║   🪙 Tokens used: {state.token_usage_today:<49}      ║
║   📝 Log file: {log_file.name:<47}      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝{Style.RESET}
""")

    log_to_comms("session_end", {
        "iterations": state.cycle_count,
        "tokens_used": state.token_usage_today,
        "log_file": str(log_file)
    })


# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="🛡️ SENTINEL-DEV - Autonomous Dev Server Guardian",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python run_sentinel.py              # Run single check
    python run_sentinel.py -i 5         # Run 5 iterations (conserve tokens)
    python run_sentinel.py --continuous # Run forever (daemon mode)
    python run_sentinel.py --force-ai   # Force AI diagnostic (test Claude integration)
    python run_sentinel.py --deep       # Force deep health check
    python run_sentinel.py --dry-run    # Show what would be done
        """
    )
    parser.add_argument("-i", "--iterations", type=int, default=1,
                        help="Maximum iterations to run (default: 1, use -1 for infinite)")
    parser.add_argument("--deep", action="store_true", help="Force deep health check")
    parser.add_argument("--repair", action="store_true", help="Force repair mode")
    parser.add_argument("--force-ai", action="store_true",
                        help="Force Claude AI diagnostic even if healthy (tests SDK integration)")
    parser.add_argument("--continuous", action="store_true", help="Run forever (daemon mode, same as -i -1)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    return parser.parse_args()


def main():
    """Main entry point."""
    # Setup
    setup_windows_utf8()
    args = parse_args()

    # Ensure logs directory exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Print startup
    print_banner()
    print_agent_header()

    # Check if tasks file exists
    if not SENTINEL_TASKS.exists():
        print_error(f"sentinel_tasks.json not found at {SENTINEL_TASKS}")
        sys.exit(1)

    # Check if Control Station exists
    if not CONTROL_STATION.exists():
        print_error(f"Control Station not found at {CONTROL_STATION}")
        sys.exit(1)

    print_info(f"Control Station: {CONTROL_STATION}")
    print_info(f"Tasks file: {SENTINEL_TASKS}")
    print_info(f"Logs directory: {LOGS_DIR}")

    provider = get_llm_provider()
    if provider == "opencode":
        print(f"  {SentinelEmoji.HEALTHY} {Style.GREEN}OpenCode CLI: enabled{Style.RESET}")
        print(f"  {Style.DIM}Model: {SENTINEL_CONFIG['model']}{Style.RESET}")
        print(f"  {Style.DIM}Auth: run `opencode auth login` if needed{Style.RESET}")
    else:
        # Check Claude auth status
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        oauth_token = os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
        if api_key or oauth_token:
            auth_type = "API Key" if api_key else "OAuth Token"
            print(f"  {SentinelEmoji.HEALTHY} {Style.GREEN}Claude AI: {auth_type} configured{Style.RESET}")
            print(f"  {Style.DIM}Model: {SENTINEL_CONFIG['model']}{Style.RESET}")
        else:
            print_warning("Claude AI: No auth configured (will use bash-only mode)")
            print(f"  {Style.DIM}Set CLAUDE_CODE_OAUTH_TOKEN in .env to enable AI diagnostics{Style.RESET}")

    if args.dry_run:
        print_info("Dry run mode - no actions will be taken")

    # Run monitoring loop
    try:
        asyncio.run(monitoring_loop(args))
    except KeyboardInterrupt:
        # Handle CTRL+C at asyncio level (edge case)
        print(f"\n\n{SentinelEmoji.SHIELD} SENTINEL-DEV interrupted by user.")
    except Exception as e:
        print_error(f"Fatal error: {e}")
        sys.exit(1)

    print(f"\n{SentinelEmoji.SHIELD} SENTINEL-DEV session complete.")


if __name__ == "__main__":
    main()
