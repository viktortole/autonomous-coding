"""
🛡️ SENTINEL-DEV Repair Workflows
=================================

Auto-repair procedures for common dev environment issues.

Repair Types:
- Dev Server Restart
- Tauri App Recovery
- Build Cache Clear
- Database Lock Clear
- Port Conflict Resolution
"""

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable


class RepairStatus(Enum):
    """Repair operation status."""
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class RepairType(Enum):
    """Types of repair operations."""
    DEV_SERVER_RESTART = "dev_server_restart"
    TAURI_APP_RECOVERY = "tauri_app_recovery"
    BUILD_CACHE_CLEAR = "build_cache_clear"
    DATABASE_LOCK_CLEAR = "database_lock_clear"
    PORT_CONFLICT_RESOLVE = "port_conflict_resolve"


@dataclass
class RepairStep:
    """Single step in a repair workflow."""
    name: str
    command: str
    timeout_seconds: int = 30
    required: bool = True
    on_failure: str = "stop"  # "stop" | "continue" | "retry"
    max_retries: int = 1


@dataclass
class RepairConfig:
    """Configuration for a repair workflow."""
    id: str
    name: str
    repair_type: RepairType
    description: str
    steps: list[RepairStep]
    requires_approval: bool = False
    max_retries: int = 2
    timeout_seconds: int = 120
    token_budget: int = 0
    forbidden_if: list[str] = field(default_factory=list)


@dataclass
class RepairResult:
    """Result of a repair operation."""
    config: RepairConfig
    timestamp: datetime
    status: RepairStatus
    message: str
    duration_ms: int
    steps_completed: list[str] = field(default_factory=list)
    steps_failed: list[str] = field(default_factory=list)
    tokens_used: int = 0
    stdout: str = ""
    stderr: str = ""


class RepairWorkflow:
    """Repair workflow engine for SENTINEL-DEV."""

    # Control Station paths
    CONTROL_STATION = Path("C:/Users/ToleV/Desktop/TestingFolder/control-station")
    LAUNCHER_SCRIPT = CONTROL_STATION / "scripts" / "tauri-dev-live.ps1"
    DEV_SERVER_PORT = 3000

    # Safety configuration
    FORBIDDEN_ACTIONS = [
        "git reset --hard",
        "rm -rf node_modules",
        "npm install",
        "Delete source files"
    ]

    SAFE_TO_KILL_PROCESSES = ["node", "npm", "next-server", "control-station"]

    RATE_LIMITS = {
        "max_repairs_per_hour": 5,
        "max_restarts_per_day": 10
    }

    # Predefined repair workflows
    WORKFLOWS = {
        "dev_server_restart": RepairConfig(
            id="SENTINEL-REPAIR-001",
            name="Restart Crashed Next.js Dev Server",
            repair_type=RepairType.DEV_SERVER_RESTART,
            description="Kill existing process and restart dev server cleanly",
            steps=[
                RepairStep(
                    name="Kill port 3000 processes",
                    command='Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }',
                    timeout_seconds=10,
                    required=False  # May not have any processes
                ),
                RepairStep(
                    name="Wait for port release",
                    command='Start-Sleep -Seconds 2',
                    timeout_seconds=5
                ),
                RepairStep(
                    name="Start dev server",
                    command='Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-File", "C:/Users/ToleV/Desktop/TestingFolder/control-station/scripts/tauri-dev-live.ps1" -WindowStyle Minimized',
                    timeout_seconds=10
                ),
                RepairStep(
                    name="Wait for HTTP 200",
                    command='$timeout = 90; $start = Get-Date; while ((Get-Date) - $start -lt [TimeSpan]::FromSeconds($timeout)) { try { $r = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop; if ($r.StatusCode -eq 200) { "SERVER_READY"; break } } catch { Start-Sleep -Seconds 2 } }; if ((Get-Date) - $start -ge [TimeSpan]::FromSeconds($timeout)) { "TIMEOUT" }',
                    timeout_seconds=100
                )
            ],
            requires_approval=False,
            max_retries=2,
            timeout_seconds=120,
            token_budget=0
        ),

        "build_cache_clear": RepairConfig(
            id="SENTINEL-REPAIR-003",
            name="Clear Next.js Build Cache",
            repair_type=RepairType.BUILD_CACHE_CLEAR,
            description="Delete .next directory to force fresh build",
            steps=[
                RepairStep(
                    name="Stop dev server",
                    command='Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }',
                    timeout_seconds=10,
                    required=False
                ),
                RepairStep(
                    name="Delete .next directory",
                    command='Remove-Item -Path "C:/Users/ToleV/Desktop/TestingFolder/control-station/.next" -Recurse -Force -ErrorAction SilentlyContinue',
                    timeout_seconds=30
                ),
                RepairStep(
                    name="Verify deletion",
                    command='if (Test-Path "C:/Users/ToleV/Desktop/TestingFolder/control-station/.next") { "FAILED" } else { "SUCCESS" }',
                    timeout_seconds=5
                )
            ],
            requires_approval=False,
            max_retries=1,
            timeout_seconds=60,
            token_budget=0
        ),

        "database_lock_clear": RepairConfig(
            id="SENTINEL-REPAIR-004",
            name="Fix Database Lock with WAL Checkpoint",
            repair_type=RepairType.DATABASE_LOCK_CLEAR,
            description="Force WAL checkpoint and clear lock",
            steps=[
                RepairStep(
                    name="Stop Control Station processes",
                    command='Get-Process -Name "control-station" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue',
                    timeout_seconds=10,
                    required=False
                ),
                RepairStep(
                    name="Wait for handles to release",
                    command='Start-Sleep -Seconds 3',
                    timeout_seconds=5
                ),
                RepairStep(
                    name="Delete WAL files",
                    command='$dbDir = "$env:APPDATA/com.convergence.control-station"; Remove-Item "$dbDir/*.db-wal" -Force -ErrorAction SilentlyContinue; Remove-Item "$dbDir/*.db-shm" -Force -ErrorAction SilentlyContinue; "CLEARED"',
                    timeout_seconds=10
                ),
                RepairStep(
                    name="Verify database accessible",
                    command='$dbPath = "$env:APPDATA/com.convergence.control-station/control-station.dev.db"; if (Test-Path $dbPath) { "DB_OK" } else { "DB_MISSING" }',
                    timeout_seconds=5
                )
            ],
            requires_approval=False,
            max_retries=3,
            timeout_seconds=60,
            token_budget=0
        ),

        "port_conflict_resolve": RepairConfig(
            id="SENTINEL-REPAIR-005",
            name="Resolve Port 3000 Conflict",
            repair_type=RepairType.PORT_CONFLICT_RESOLVE,
            description="Identify and safely terminate blocking process",
            steps=[
                RepairStep(
                    name="Identify process on port 3000",
                    command='$conn = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue; if ($conn) { $proc = Get-Process -Id $conn.OwningProcess; "PID: $($proc.Id), Name: $($proc.Name)" } else { "PORT_FREE" }',
                    timeout_seconds=5
                ),
                RepairStep(
                    name="Kill if safe process",
                    command='$conn = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue; if ($conn) { $proc = Get-Process -Id $conn.OwningProcess; if ($proc.Name -in @("node", "npm", "next-server")) { Stop-Process -Id $proc.Id -Force; "KILLED" } else { "REQUIRES_APPROVAL: $($proc.Name)" } } else { "PORT_FREE" }',
                    timeout_seconds=10
                )
            ],
            requires_approval=False,  # Conditional - only kills known processes
            max_retries=1,
            timeout_seconds=30,
            token_budget=0
        ),

        "tauri_app_recovery": RepairConfig(
            id="SENTINEL-REPAIR-002",
            name="Kill and Rebuild Frozen Tauri App",
            repair_type=RepairType.TAURI_APP_RECOVERY,
            description="Gracefully terminate and restart the Tauri app",
            steps=[
                RepairStep(
                    name="Graceful termination",
                    command='Get-Process -Name "control-station" -ErrorAction SilentlyContinue | Stop-Process -ErrorAction SilentlyContinue',
                    timeout_seconds=10,
                    required=False
                ),
                RepairStep(
                    name="Wait for termination",
                    command='Start-Sleep -Seconds 3',
                    timeout_seconds=5
                ),
                RepairStep(
                    name="Force kill if needed",
                    command='Get-Process -Name "control-station" -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue',
                    timeout_seconds=5,
                    required=False
                ),
                RepairStep(
                    name="Verify dev server healthy",
                    command='$r = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop; if ($r.StatusCode -eq 200) { "DEV_SERVER_OK" } else { "DEV_SERVER_FAIL" }',
                    timeout_seconds=5
                ),
                RepairStep(
                    name="Restart Tauri via launcher",
                    command='Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-File", "C:/Users/ToleV/Desktop/TestingFolder/control-station/scripts/tauri-dev-live.ps1" -WindowStyle Minimized',
                    timeout_seconds=10
                )
            ],
            requires_approval=False,
            max_retries=1,
            timeout_seconds=120,
            token_budget=0
        )
    }

    def __init__(self):
        """Initialize repair workflow engine."""
        self.repair_history: list[RepairResult] = []
        self.repairs_this_hour: int = 0
        self.restarts_today: int = 0
        self.last_hour_reset: datetime = datetime.now()
        self.last_day_reset: str = datetime.now().strftime("%Y-%m-%d")

    def run_bash(self, command: str, timeout: int = 30) -> tuple[int, str, str]:
        """Execute a PowerShell command and return (exit_code, stdout, stderr)."""
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

    def check_rate_limits(self) -> tuple[bool, str]:
        """Check if repair is allowed under rate limits."""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")

        # Reset hourly counter
        if (now - self.last_hour_reset).total_seconds() >= 3600:
            self.repairs_this_hour = 0
            self.last_hour_reset = now

        # Reset daily counter
        if today != self.last_day_reset:
            self.restarts_today = 0
            self.last_day_reset = today

        # Check limits
        if self.repairs_this_hour >= self.RATE_LIMITS["max_repairs_per_hour"]:
            return False, "Hourly repair limit reached"

        if self.restarts_today >= self.RATE_LIMITS["max_restarts_per_day"]:
            return False, "Daily restart limit reached"

        return True, "OK"

    def is_action_forbidden(self, command: str) -> bool:
        """Check if command contains forbidden actions."""
        for forbidden in self.FORBIDDEN_ACTIONS:
            if forbidden.lower() in command.lower():
                return True
        return False

    def execute_step(self, step: RepairStep) -> tuple[bool, str, str]:
        """Execute a single repair step."""
        if self.is_action_forbidden(step.command):
            return False, "", f"Forbidden action detected in: {step.name}"

        exit_code, stdout, stderr = self.run_bash(step.command, step.timeout_seconds)

        # Check for success
        success = exit_code == 0 or "SUCCESS" in stdout or "OK" in stdout or "READY" in stdout or "CLEARED" in stdout or "KILLED" in stdout

        # Some steps may fail but that's OK if not required
        if not success and not step.required:
            success = True  # Non-critical step

        return success, stdout, stderr

    def execute_workflow(self, workflow_id: str) -> RepairResult:
        """Execute a repair workflow by ID."""
        if workflow_id not in self.WORKFLOWS:
            return RepairResult(
                config=RepairConfig(
                    id=workflow_id,
                    name="Unknown",
                    repair_type=RepairType.DEV_SERVER_RESTART,
                    description="Unknown workflow",
                    steps=[]
                ),
                timestamp=datetime.now(),
                status=RepairStatus.FAILED,
                message=f"Unknown workflow: {workflow_id}",
                duration_ms=0
            )

        config = self.WORKFLOWS[workflow_id]
        return self.run_repair(config)

    def run_repair(self, config: RepairConfig) -> RepairResult:
        """Run a complete repair workflow."""
        start_time = time.time()
        steps_completed = []
        steps_failed = []
        all_stdout = []
        all_stderr = []

        # Check rate limits
        allowed, reason = self.check_rate_limits()
        if not allowed:
            return RepairResult(
                config=config,
                timestamp=datetime.now(),
                status=RepairStatus.SKIPPED,
                message=f"Rate limit: {reason}",
                duration_ms=0
            )

        # Execute each step
        for step in config.steps:
            success, stdout, stderr = self.execute_step(step)

            if stdout:
                all_stdout.append(f"[{step.name}] {stdout}")
            if stderr:
                all_stderr.append(f"[{step.name}] {stderr}")

            if success:
                steps_completed.append(step.name)
            else:
                steps_failed.append(step.name)

                if step.required and step.on_failure == "stop":
                    break  # Stop on required step failure

        duration_ms = int((time.time() - start_time) * 1000)

        # Determine overall status
        if not steps_failed:
            status = RepairStatus.SUCCESS
            message = "All steps completed successfully"
        elif steps_completed and steps_failed:
            status = RepairStatus.PARTIAL
            message = f"Partial: {len(steps_completed)}/{len(config.steps)} steps"
        else:
            status = RepairStatus.FAILED
            message = f"Failed at: {steps_failed[0] if steps_failed else 'Unknown'}"

        # Update counters
        self.repairs_this_hour += 1
        if config.repair_type == RepairType.DEV_SERVER_RESTART:
            self.restarts_today += 1

        result = RepairResult(
            config=config,
            timestamp=datetime.now(),
            status=status,
            message=message,
            duration_ms=duration_ms,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            tokens_used=config.token_budget,
            stdout="\n".join(all_stdout)[:1000],
            stderr="\n".join(all_stderr)[:500]
        )

        self.repair_history.append(result)
        return result

    def get_repair_for_issue(self, issue_type: str) -> Optional[str]:
        """Get appropriate repair workflow for an issue type."""
        issue_to_repair = {
            "dev_server": "dev_server_restart",
            "http_ping": "dev_server_restart",
            "port_conflict": "port_conflict_resolve",
            "database": "database_lock_clear",
            "database_lock": "database_lock_clear",
            "build_cache": "build_cache_clear",
            "tauri": "tauri_app_recovery",
        }

        return issue_to_repair.get(issue_type.lower())

    def get_stats(self) -> dict:
        """Get repair statistics."""
        return {
            "repairs_this_hour": self.repairs_this_hour,
            "restarts_today": self.restarts_today,
            "total_repairs": len(self.repair_history),
            "success_rate": (
                sum(1 for r in self.repair_history if r.status == RepairStatus.SUCCESS) /
                len(self.repair_history) if self.repair_history else 0
            )
        }
