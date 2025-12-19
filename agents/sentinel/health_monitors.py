"""
🛡️ SENTINEL-DEV Health Monitors
================================

Tiered health check implementations for dev server monitoring.

Tiers:
- Tier 1: Pure bash commands, zero token cost
- Tier 2: Smart analysis with minimal Claude usage
- Tier 3: Deep diagnostics with full Claude analysis
"""

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    ERROR = "error"
    UNKNOWN = "unknown"


class CheckTier(Enum):
    """Health check tier levels."""
    TIER_1_BASH = 1      # Pure bash, 0 tokens
    TIER_2_SMART = 2     # Minimal Claude, ~500 tokens
    TIER_3_DEEP = 3      # Full analysis, ~2000 tokens


@dataclass
class HealthCheckConfig:
    """Configuration for a health check."""
    id: str
    name: str
    tier: CheckTier
    component: str
    command: str
    timeout_seconds: int = 10
    success_patterns: list[str] = field(default_factory=list)
    failure_patterns: list[str] = field(default_factory=list)
    on_failure_escalate_to: Optional[str] = None
    frequency_seconds: int = 300
    token_budget: int = 0


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    config: HealthCheckConfig
    timestamp: datetime
    status: HealthStatus
    message: str
    duration_ms: int
    stdout: str = ""
    stderr: str = ""
    tokens_used: int = 0
    details: dict = field(default_factory=dict)


class HealthMonitor:
    """Health monitoring engine for SENTINEL-DEV."""

    # Control Station paths
    CONTROL_STATION = Path("C:/Users/ToleV/Desktop/TestingFolder/control-station")
    DEV_SERVER_URL = "http://127.0.0.1:3000"
    DEV_SERVER_PORT = 3000

    # Predefined health checks
    CHECKS = {
        # Tier 1: Pure bash, zero tokens
        "http_ping": HealthCheckConfig(
            id="SENTINEL-HEALTH-001",
            name="Dev Server HTTP Ping",
            tier=CheckTier.TIER_1_BASH,
            component="Dev Server HTTP",
            command='curl -f http://127.0.0.1:3000 --max-time 3 --silent --output $null; if ($LASTEXITCODE -eq 0) { "HEALTHY" } else { "UNHEALTHY" }',
            timeout_seconds=5,
            success_patterns=["HEALTHY"],
            failure_patterns=["UNHEALTHY", "Connection refused"],
            on_failure_escalate_to="SENTINEL-DIAG-001",
            frequency_seconds=300,
            token_budget=0
        ),
        "port_status": HealthCheckConfig(
            id="SENTINEL-HEALTH-006",
            name="Port 3000 Status",
            tier=CheckTier.TIER_1_BASH,
            component="Port 3000",
            command='$conn = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue; if ($conn) { "PORT_IN_USE" } else { "PORT_FREE" }',
            timeout_seconds=5,
            success_patterns=["PORT_IN_USE"],
            failure_patterns=["PORT_FREE"],
            on_failure_escalate_to="SENTINEL-REPAIR-001",
            frequency_seconds=300,
            token_budget=0
        ),
        "database_file": HealthCheckConfig(
            id="SENTINEL-HEALTH-005",
            name="Database File Check",
            tier=CheckTier.TIER_1_BASH,
            component="Database File",
            command='$dbPath = "$env:APPDATA/com.convergence.control-station/control-station.dev.db"; if (Test-Path $dbPath) { "EXISTS" } else { "MISSING" }',
            timeout_seconds=5,
            success_patterns=["EXISTS"],
            failure_patterns=["MISSING"],
            on_failure_escalate_to="SENTINEL-DIAG-004",
            frequency_seconds=300,
            token_budget=0
        ),
        "build_cache": HealthCheckConfig(
            id="SENTINEL-HEALTH-003",
            name="Build Cache Validity",
            tier=CheckTier.TIER_1_BASH,
            component="Build Cache",
            command='$cacheDir = "C:/Users/ToleV/Desktop/TestingFolder/control-station/.next"; if (Test-Path $cacheDir) { $age = (Get-Date) - (Get-Item $cacheDir).LastWriteTime; if ($age.TotalHours -lt 24) { "VALID" } else { "STALE" } } else { "MISSING" }',
            timeout_seconds=5,
            success_patterns=["VALID"],
            failure_patterns=["STALE", "MISSING"],
            on_failure_escalate_to="SENTINEL-REPAIR-003",
            frequency_seconds=1800,
            token_budget=0
        ),

        # Tier 2: Smart checks with minimal Claude
        "typescript_check": HealthCheckConfig(
            id="SENTINEL-HEALTH-004",
            name="TypeScript Compilation",
            tier=CheckTier.TIER_2_SMART,
            component="TypeScript",
            command='cd C:/Users/ToleV/Desktop/TestingFolder/control-station; npx tsc --noEmit 2>&1 | Select-Object -First 10',
            timeout_seconds=60,
            success_patterns=["error TS"],  # Inverted - success if no matches
            failure_patterns=["error TS"],
            on_failure_escalate_to="SENTINEL-DIAG-003",
            frequency_seconds=1800,
            token_budget=500
        ),

        # Tier 3: Deep diagnostics
        "full_health_api": HealthCheckConfig(
            id="SENTINEL-DIAG-001",
            name="Full Health API Check",
            tier=CheckTier.TIER_3_DEEP,
            component="Health API",
            command='curl -f http://127.0.0.1:3000/api/health --max-time 5 --silent',
            timeout_seconds=10,
            success_patterns=["healthy", "ok"],
            failure_patterns=["error", "unavailable"],
            frequency_seconds=3600,
            token_budget=2000
        ),
    }

    def __init__(self):
        """Initialize health monitor."""
        self.results_cache: dict[str, HealthCheckResult] = {}
        self.last_check_times: dict[str, datetime] = {}

    def run_bash(self, command: str, timeout: int = 10) -> tuple[int, str, str]:
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

    def run_check(self, check_id: str) -> HealthCheckResult:
        """Run a specific health check by ID."""
        if check_id not in self.CHECKS:
            return HealthCheckResult(
                config=HealthCheckConfig(
                    id=check_id,
                    name="Unknown",
                    tier=CheckTier.TIER_1_BASH,
                    component="Unknown",
                    command=""
                ),
                timestamp=datetime.now(),
                status=HealthStatus.UNKNOWN,
                message=f"Unknown check: {check_id}",
                duration_ms=0
            )

        config = self.CHECKS[check_id]
        return self.execute_check(config)

    def execute_check(self, config: HealthCheckConfig) -> HealthCheckResult:
        """Execute a health check and return result."""
        start_time = time.time()

        # Run the command
        exit_code, stdout, stderr = self.run_bash(config.command, config.timeout_seconds)

        duration_ms = int((time.time() - start_time) * 1000)

        # Determine status based on patterns
        output = stdout + stderr

        # Check for failure patterns first
        has_failure = any(pattern.lower() in output.lower() for pattern in config.failure_patterns)
        has_success = any(pattern.lower() in output.lower() for pattern in config.success_patterns)

        # Special case: TypeScript check - success means NO errors
        if "typescript" in config.id.lower():
            if "error TS" in output or exit_code != 0:
                status = HealthStatus.ERROR
                message = "TypeScript errors detected"
            else:
                status = HealthStatus.HEALTHY
                message = "TypeScript OK (0 errors)"
        elif has_failure and not has_success:
            status = HealthStatus.ERROR
            message = f"Check failed: {config.failure_patterns[0] if config.failure_patterns else 'Unknown'}"
        elif has_success:
            status = HealthStatus.HEALTHY
            message = "Check passed"
        elif exit_code == 0:
            status = HealthStatus.HEALTHY
            message = "Check passed (exit code 0)"
        else:
            status = HealthStatus.ERROR
            message = f"Check failed (exit code {exit_code})"

        result = HealthCheckResult(
            config=config,
            timestamp=datetime.now(),
            status=status,
            message=message,
            duration_ms=duration_ms,
            stdout=stdout[:500] if stdout else "",
            stderr=stderr[:500] if stderr else "",
            tokens_used=0 if config.tier == CheckTier.TIER_1_BASH else config.token_budget
        )

        # Cache result
        self.results_cache[config.id] = result
        self.last_check_times[config.id] = datetime.now()

        return result

    def run_tier1_checks(self) -> list[HealthCheckResult]:
        """Run all Tier 1 (bash-only) health checks."""
        tier1_checks = [c for c in self.CHECKS.values() if c.tier == CheckTier.TIER_1_BASH]
        return [self.execute_check(c) for c in tier1_checks]

    def run_tier2_checks(self) -> list[HealthCheckResult]:
        """Run all Tier 2 (smart) health checks."""
        tier2_checks = [c for c in self.CHECKS.values() if c.tier == CheckTier.TIER_2_SMART]
        return [self.execute_check(c) for c in tier2_checks]

    def run_tier3_checks(self) -> list[HealthCheckResult]:
        """Run all Tier 3 (deep) health checks."""
        tier3_checks = [c for c in self.CHECKS.values() if c.tier == CheckTier.TIER_3_DEEP]
        return [self.execute_check(c) for c in tier3_checks]

    def should_run_check(self, check_id: str) -> bool:
        """Determine if a check should run based on last run time and frequency."""
        if check_id not in self.CHECKS:
            return False

        config = self.CHECKS[check_id]
        last_run = self.last_check_times.get(check_id)

        if last_run is None:
            return True

        elapsed = (datetime.now() - last_run).total_seconds()
        return elapsed >= config.frequency_seconds

    def get_cached_result(self, check_id: str) -> Optional[HealthCheckResult]:
        """Get cached result if still valid."""
        if check_id not in self.results_cache:
            return None

        result = self.results_cache[check_id]
        config = self.CHECKS.get(check_id)

        if config is None:
            return None

        # Check if cache is still valid
        age = (datetime.now() - result.timestamp).total_seconds()
        if age < config.frequency_seconds:
            return result

        return None

    def get_overall_status(self, results: list[HealthCheckResult]) -> HealthStatus:
        """Determine overall health status from multiple results."""
        if not results:
            return HealthStatus.UNKNOWN

        if any(r.status == HealthStatus.ERROR for r in results):
            return HealthStatus.ERROR

        if any(r.status == HealthStatus.DEGRADED for r in results):
            return HealthStatus.DEGRADED

        if all(r.status == HealthStatus.HEALTHY for r in results):
            return HealthStatus.HEALTHY

        return HealthStatus.UNKNOWN
