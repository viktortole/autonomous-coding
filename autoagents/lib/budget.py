"""
Token Budget Tracking
=====================

Per-agent daily token budget management.
Tracks usage, warns on thresholds, prevents overspending.

Budget File: logs/{agent_id}/budget.json (per agent)
"""

import json
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from .styles import Style
from .output import print_warning, print_error, print_info


# Default budget limits per agent type
DEFAULT_BUDGETS = {
    "COMMANDER": {"daily_limit": 15000, "per_task": 5000, "warning_threshold": 0.8},
    "SENTINEL": {"daily_limit": 10000, "per_task": 3000, "warning_threshold": 0.8},
    "FRONTEND": {"daily_limit": 12000, "per_task": 4000, "warning_threshold": 0.8},
    "BACKEND": {"daily_limit": 12000, "per_task": 4000, "warning_threshold": 0.8},
    "ARCHITECT": {"daily_limit": 8000, "per_task": 3000, "warning_threshold": 0.8},
    "DEBUGGER": {"daily_limit": 10000, "per_task": 3000, "warning_threshold": 0.8},
    "TESTER": {"daily_limit": 10000, "per_task": 3000, "warning_threshold": 0.8},
}


class TokenBudget:
    """
    Token budget tracker for a single agent.

    Tracks daily usage, warns on thresholds, persists to disk.
    """

    def __init__(
        self,
        agent_id: str,
        logs_dir: Path,
        daily_limit: Optional[int] = None,
        per_task: Optional[int] = None,
        warning_threshold: float = 0.8
    ):
        """
        Initialize budget tracker.

        Args:
            agent_id: Agent ID (e.g., "SENTINEL")
            logs_dir: Directory for budget file
            daily_limit: Max tokens per day (default from DEFAULT_BUDGETS)
            per_task: Max tokens per task (default from DEFAULT_BUDGETS)
            warning_threshold: Warn when usage exceeds this % (0.0-1.0)
        """
        self.agent_id = agent_id.upper()
        self.logs_dir = logs_dir
        self.budget_file = logs_dir / "budget.json"

        # Get defaults for agent type
        defaults = DEFAULT_BUDGETS.get(self.agent_id, {
            "daily_limit": 10000,
            "per_task": 3000,
            "warning_threshold": 0.8
        })

        self.daily_limit = daily_limit or defaults["daily_limit"]
        self.per_task = per_task or defaults["per_task"]
        self.warning_threshold = warning_threshold or defaults["warning_threshold"]

        # Load or initialize state
        self._load_state()

    def _load_state(self) -> None:
        """Load budget state from file or initialize new."""
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        if self.budget_file.exists():
            try:
                with open(self.budget_file, "r") as f:
                    data = json.load(f)

                # Check if state is from today
                if data.get("date") == str(date.today()):
                    self.used_today = data.get("used_today", 0)
                    self.tasks_today = data.get("tasks_today", [])
                else:
                    # New day - reset counters
                    self._reset_daily()
            except (json.JSONDecodeError, KeyError):
                self._reset_daily()
        else:
            self._reset_daily()

    def _reset_daily(self) -> None:
        """Reset daily counters."""
        self.used_today = 0
        self.tasks_today = []
        self._save_state()

    def _save_state(self) -> None:
        """Persist budget state to file."""
        state = {
            "agent_id": self.agent_id,
            "date": str(date.today()),
            "daily_limit": self.daily_limit,
            "per_task": self.per_task,
            "used_today": self.used_today,
            "remaining": self.remaining,
            "tasks_today": self.tasks_today,
            "last_updated": datetime.now().isoformat()
        }

        with open(self.budget_file, "w") as f:
            json.dump(state, f, indent=2)

    @property
    def remaining(self) -> int:
        """Tokens remaining today."""
        return max(0, self.daily_limit - self.used_today)

    @property
    def usage_percent(self) -> float:
        """Usage as a percentage (0.0 - 1.0)."""
        return self.used_today / self.daily_limit if self.daily_limit > 0 else 1.0

    def can_run_task(self, estimated_tokens: Optional[int] = None) -> tuple[bool, str]:
        """
        Check if budget allows running a task.

        Args:
            estimated_tokens: Estimated tokens for task (defaults to per_task)

        Returns:
            (can_run, reason) tuple
        """
        estimate = estimated_tokens or self.per_task

        if self.remaining <= 0:
            return False, f"Daily budget exhausted ({self.used_today}/{self.daily_limit})"

        if estimate > self.remaining:
            return False, f"Insufficient budget: need ~{estimate}, have {self.remaining}"

        if self.usage_percent >= self.warning_threshold:
            return True, f"⚠️ Budget warning: {int(self.usage_percent * 100)}% used"

        return True, "OK"

    def record_usage(self, tokens: int, task_id: str = "unknown") -> None:
        """
        Record token usage for a task.

        Args:
            tokens: Tokens used
            task_id: Task identifier for tracking
        """
        self.used_today += tokens
        self.tasks_today.append({
            "task_id": task_id,
            "tokens": tokens,
            "timestamp": datetime.now().isoformat()
        })
        self._save_state()

        # Print warnings if needed
        if self.usage_percent >= 1.0:
            print_error(f"BUDGET EXHAUSTED: {self.agent_id} has used all {self.daily_limit} tokens")
        elif self.usage_percent >= self.warning_threshold:
            print_warning(
                f"Budget warning: {self.agent_id} at {int(self.usage_percent * 100)}% "
                f"({self.used_today}/{self.daily_limit})"
            )

    def get_summary(self) -> dict:
        """
        Get budget summary for reporting.

        Returns:
            Summary dict with usage stats
        """
        return {
            "agent_id": self.agent_id,
            "date": str(date.today()),
            "daily_limit": self.daily_limit,
            "used_today": self.used_today,
            "remaining": self.remaining,
            "usage_percent": round(self.usage_percent * 100, 1),
            "tasks_count": len(self.tasks_today),
            "status": (
                "EXHAUSTED" if self.remaining <= 0
                else "WARNING" if self.usage_percent >= self.warning_threshold
                else "OK"
            )
        }

    def print_status(self) -> None:
        """Print formatted budget status to terminal."""
        usage_pct = int(self.usage_percent * 100)

        # Choose color based on usage
        if usage_pct >= 100:
            bar_color = Style.RED
            status_icon = "🔴"
        elif usage_pct >= 80:
            bar_color = Style.YELLOW
            status_icon = "🟡"
        else:
            bar_color = Style.GREEN
            status_icon = "🟢"

        # Build progress bar
        bar_width = 20
        filled = int(bar_width * self.usage_percent)
        filled = min(filled, bar_width)  # Cap at max
        bar = "█" * filled + "░" * (bar_width - filled)

        print(f"\n{Style.CYAN}┌─────────────────────────────────────┐{Style.RESET}")
        print(f"{Style.CYAN}│{Style.RESET} {Style.BOLD}💰 TOKEN BUDGET: {self.agent_id}{Style.RESET}")
        print(f"{Style.CYAN}├─────────────────────────────────────┤{Style.RESET}")
        print(f"{Style.CYAN}│{Style.RESET} {status_icon} Status: {self.get_summary()['status']:<18}")
        print(f"{Style.CYAN}│{Style.RESET} 📊 Used: {self.used_today:,} / {self.daily_limit:,}")
        print(f"{Style.CYAN}│{Style.RESET} 📈 [{bar_color}{bar}{Style.RESET}] {usage_pct}%")
        print(f"{Style.CYAN}│{Style.RESET} 🎯 Remaining: {self.remaining:,} tokens")
        print(f"{Style.CYAN}│{Style.RESET} 📋 Tasks: {len(self.tasks_today)} today")
        print(f"{Style.CYAN}└─────────────────────────────────────┘{Style.RESET}")


class BudgetManager:
    """
    Manage budgets for all agents.

    Singleton-ish pattern for global budget tracking.
    """

    def __init__(self, base_logs_dir: Path):
        """
        Initialize budget manager.

        Args:
            base_logs_dir: Base logs directory (contains per-agent subdirs)
        """
        self.base_logs_dir = base_logs_dir
        self._budgets: dict[str, TokenBudget] = {}

    def get_budget(self, agent_id: str) -> TokenBudget:
        """
        Get or create budget tracker for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            TokenBudget instance
        """
        agent_id = agent_id.upper()

        if agent_id not in self._budgets:
            agent_logs_dir = self.base_logs_dir / agent_id.lower()
            self._budgets[agent_id] = TokenBudget(agent_id, agent_logs_dir)

        return self._budgets[agent_id]

    def get_all_summaries(self) -> dict[str, dict]:
        """
        Get budget summaries for all tracked agents.

        Returns:
            Dict of {agent_id: summary_dict}
        """
        return {
            agent_id: budget.get_summary()
            for agent_id, budget in self._budgets.items()
        }

    def print_all_statuses(self) -> None:
        """Print budget status for all tracked agents."""
        for budget in self._budgets.values():
            budget.print_status()

    def can_any_agent_run(self, min_tokens: int = 1000) -> list[str]:
        """
        Get list of agents that can still run tasks.

        Args:
            min_tokens: Minimum remaining tokens required

        Returns:
            List of agent IDs with sufficient budget
        """
        available = []
        for agent_id in DEFAULT_BUDGETS:
            budget = self.get_budget(agent_id)
            if budget.remaining >= min_tokens:
                available.append(agent_id)
        return available


def create_budget_tracker(
    agent_id: str,
    logs_dir: Optional[Path] = None
) -> TokenBudget:
    """
    Convenience function to create a budget tracker.

    Args:
        agent_id: Agent ID
        logs_dir: Logs directory (defaults to autonomous-coding/logs/{agent})

    Returns:
        TokenBudget instance
    """
    if logs_dir is None:
        base_dir = Path(__file__).parent.parent.parent / "logs"
        logs_dir = base_dir / agent_id.lower()

    return TokenBudget(agent_id, logs_dir)


def estimate_tokens(text: str) -> int:
    """
    Rough estimate of tokens in text.

    Uses ~4 characters per token approximation.

    Args:
        text: Text to estimate

    Returns:
        Estimated token count
    """
    return len(text) // 4
