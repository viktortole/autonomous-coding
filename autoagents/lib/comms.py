"""
COMMS.md Utilities
==================

Inter-agent communication hub utilities.
All agents use these functions to read/write their sections in COMMS.md.

COMMS.md Structure:
- STATUS DASHBOARD (all 7 agents at a glance)
- Individual agent sections (one per agent)
- ANNOUNCEMENTS section
- FILE LOCKS section
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from .styles import Style


# Default COMMS.md location
DEFAULT_COMMS_PATH = Path(__file__).parent.parent.parent / "COMMS.md"

# Agent status indicators
STATUS_ACTIVE = "🟢 Active"
STATUS_IDLE = "⏸️ Idle"
STATUS_COMPLETE = "✅ Complete"
STATUS_ERROR = "🔴 Error"
STATUS_BLOCKED = "🟡 Blocked"


def get_comms_path(custom_path: Optional[Path] = None) -> Path:
    """
    Get the path to COMMS.md.

    Args:
        custom_path: Optional custom path, defaults to autonomous-coding/COMMS.md

    Returns:
        Path to COMMS.md
    """
    return custom_path or DEFAULT_COMMS_PATH


def read_comms(comms_path: Optional[Path] = None) -> str:
    """
    Read entire COMMS.md content.

    Args:
        comms_path: Optional custom path to COMMS.md

    Returns:
        Full content of COMMS.md, or empty string if not found
    """
    path = get_comms_path(comms_path)
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def write_comms(content: str, comms_path: Optional[Path] = None) -> None:
    """
    Write entire COMMS.md content.

    Args:
        content: Full content to write
        comms_path: Optional custom path to COMMS.md
    """
    path = get_comms_path(comms_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def get_agent_section(agent_id: str, comms_path: Optional[Path] = None) -> Optional[str]:
    """
    Extract a specific agent's section from COMMS.md.

    Args:
        agent_id: Agent ID (e.g., "COMMANDER", "SENTINEL")
        comms_path: Optional custom path to COMMS.md

    Returns:
        Agent's section content, or None if not found
    """
    content = read_comms(comms_path)
    if not content:
        return None

    # Pattern: ## [EMOJI] AGENT_ID until next ## or end of file
    pattern = rf"^## .+ {agent_id}\s*$(.*?)(?=^## |\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

    if match:
        return match.group(0).strip()
    return None


def update_agent_section(
    agent_id: str,
    emoji: str,
    status: str,
    mission: str,
    task_queue: list[dict],
    progress: list[dict],
    session_log: list[str],
    comms_path: Optional[Path] = None
) -> bool:
    """
    Update an agent's section in COMMS.md.

    Args:
        agent_id: Agent ID (e.g., "COMMANDER", "SENTINEL")
        emoji: Agent emoji (e.g., "👑", "🛡️")
        status: Current status (use STATUS_* constants)
        mission: One-line mission description
        task_queue: List of {"id": str, "desc": str, "status": str}
        progress: List of {"task": str, "done": bool}
        session_log: List of log entries with timestamps
        comms_path: Optional custom path to COMMS.md

    Returns:
        True if update successful
    """
    content = read_comms(comms_path)
    timestamp = datetime.now().strftime("%H:%M")

    # Build new section content
    section = f"""## {emoji} {agent_id}

**Status:** {status}
**Last Update:** {timestamp}

### Current Mission
> {mission}

### Task Queue
"""

    if task_queue:
        for task in task_queue:
            status_icon = "🔵" if task.get("status") == "in_progress" else "⚪"
            section += f"{status_icon} [{task['id']}]: {task['desc']} - {task.get('status', 'pending')}\n"
    else:
        section += "_No tasks queued_\n"

    section += "\n### Progress\n"
    for item in progress:
        checkbox = "[x]" if item.get("done") else "[ ]"
        section += f"- {checkbox} {item['task']}\n"

    section += "\n### Session Log\n```\n"
    for log_entry in session_log[-10:]:  # Keep last 10 entries
        section += f"{log_entry}\n"
    section += "```\n"

    # Find and replace agent section, or append if not found
    pattern = rf"^## .+ {agent_id}\s*$.*?(?=^## |\Z)"

    if re.search(pattern, content, re.MULTILINE | re.DOTALL):
        # Replace existing section
        new_content = re.sub(
            pattern,
            section.rstrip() + "\n\n",
            content,
            count=1,
            flags=re.MULTILINE | re.DOTALL
        )
    else:
        # Append new section before ANNOUNCEMENTS or at end
        if "## 📢 ANNOUNCEMENTS" in content:
            new_content = content.replace(
                "## 📢 ANNOUNCEMENTS",
                section + "\n---\n\n## 📢 ANNOUNCEMENTS"
            )
        else:
            new_content = content + "\n---\n\n" + section

    write_comms(new_content, comms_path)
    return True


def log_agent_action(
    agent_id: str,
    action: str,
    comms_path: Optional[Path] = None
) -> bool:
    """
    Add a timestamped log entry to an agent's session log.

    Args:
        agent_id: Agent ID
        action: Action description
        comms_path: Optional custom path

    Returns:
        True if successful
    """
    content = read_comms(comms_path)
    timestamp = datetime.now().strftime("%H:%M")
    log_entry = f"[{timestamp}] {action}"

    # Find agent's Session Log section and append entry
    pattern = rf"(## .+ {agent_id}.*?### Session Log\s*```\n)(.*?)(```)"

    def replacer(match):
        prefix = match.group(1)
        existing_logs = match.group(2)
        suffix = match.group(3)
        # Keep only last 9 entries + new one = 10 total
        log_lines = [l for l in existing_logs.strip().split("\n") if l][-9:]
        log_lines.append(log_entry)
        return prefix + "\n".join(log_lines) + "\n" + suffix

    new_content = re.sub(pattern, replacer, content, count=1, flags=re.DOTALL)

    if new_content != content:
        write_comms(new_content, comms_path)
        return True
    return False


def set_agent_status(
    agent_id: str,
    status: str,
    comms_path: Optional[Path] = None
) -> bool:
    """
    Quick update of just the agent's status.

    Args:
        agent_id: Agent ID
        status: New status (use STATUS_* constants)
        comms_path: Optional custom path

    Returns:
        True if successful
    """
    content = read_comms(comms_path)
    timestamp = datetime.now().strftime("%H:%M")

    # Update status and timestamp
    pattern = rf"(## .+ {agent_id}\s*\n+)\*\*Status:\*\* [^\n]+"
    replacement = rf"\1**Status:** {status}"
    new_content = re.sub(pattern, replacement, content, count=1)

    # Also update timestamp
    pattern2 = rf"(\*\*Status:\*\* {re.escape(status)}\n)\*\*Last Update:\*\* [^\n]+"
    replacement2 = rf"\1**Last Update:** {timestamp}"
    new_content = re.sub(pattern2, replacement2, new_content, count=1)

    if new_content != content:
        write_comms(new_content, comms_path)
        return True
    return False


def get_file_locks(comms_path: Optional[Path] = None) -> dict[str, str]:
    """
    Get current file locks.

    Args:
        comms_path: Optional custom path

    Returns:
        Dict of {file_path: agent_id}
    """
    content = read_comms(comms_path)
    locks = {}

    # Find FILE LOCKS section
    pattern = r"## 🔒 FILE LOCKS\s*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)

    if match:
        lock_section = match.group(1)
        # Parse lock entries: | path | agent | timestamp |
        for line in lock_section.split("\n"):
            if "|" in line and not line.startswith("|--"):
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4 and parts[1] and parts[2]:
                    # Skip header row
                    if parts[1] != "File" and parts[1] != "---":
                        locks[parts[1]] = parts[2]

    return locks


def acquire_file_lock(
    agent_id: str,
    file_path: str,
    comms_path: Optional[Path] = None
) -> bool:
    """
    Attempt to lock a file for editing.

    Args:
        agent_id: Agent requesting lock
        file_path: Path to lock
        comms_path: Optional custom path

    Returns:
        True if lock acquired, False if already locked by another agent
    """
    locks = get_file_locks(comms_path)

    # Check if already locked by another agent
    if file_path in locks and locks[file_path] != agent_id:
        return False

    content = read_comms(comms_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_lock = f"| {file_path} | {agent_id} | {timestamp} |"

    # Find or create FILE LOCKS section
    if "## 🔒 FILE LOCKS" not in content:
        content += "\n---\n\n## 🔒 FILE LOCKS\n\n| File | Agent | Acquired |\n|------|-------|----------|\n"

    # Add lock entry if not exists
    if file_path not in locks:
        pattern = r"(\| File \| Agent \| Acquired \|\n\|[^\n]+\|)"
        new_content = re.sub(pattern, rf"\1\n{new_lock}", content, count=1)
        write_comms(new_content, comms_path)

    return True


def release_file_lock(
    agent_id: str,
    file_path: str,
    comms_path: Optional[Path] = None
) -> bool:
    """
    Release a file lock.

    Args:
        agent_id: Agent releasing lock
        file_path: Path to unlock
        comms_path: Optional custom path

    Returns:
        True if released, False if not owned by this agent
    """
    locks = get_file_locks(comms_path)

    # Can only release own locks
    if file_path in locks and locks[file_path] != agent_id:
        return False

    content = read_comms(comms_path)

    # Remove lock entry
    pattern = rf"\| {re.escape(file_path)} \| {agent_id} \| [^\n]+ \|\n?"
    new_content = re.sub(pattern, "", content, count=1)

    if new_content != content:
        write_comms(new_content, comms_path)
        return True
    return False


def add_announcement(
    agent_id: str,
    emoji: str,
    message: str,
    priority: str = "INFO",
    comms_path: Optional[Path] = None
) -> bool:
    """
    Add an announcement visible to all agents.

    Args:
        agent_id: Announcing agent
        emoji: Agent emoji
        message: Announcement message
        priority: INFO, WARNING, or CRITICAL
        comms_path: Optional custom path

    Returns:
        True if added
    """
    content = read_comms(comms_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    priority_emoji = {"INFO": "ℹ️", "WARNING": "⚠️", "CRITICAL": "🚨"}.get(priority, "ℹ️")
    announcement = f"- {priority_emoji} **[{timestamp}] {emoji} {agent_id}:** {message}\n"

    # Find ANNOUNCEMENTS section
    if "## 📢 ANNOUNCEMENTS" not in content:
        content += "\n---\n\n## 📢 ANNOUNCEMENTS\n\n_Recent announcements from agents_\n\n"

    # Insert after header
    pattern = r"(## 📢 ANNOUNCEMENTS\s*\n+(?:_[^\n]+_\n+)?)"
    new_content = re.sub(pattern, rf"\1{announcement}", content, count=1)

    write_comms(new_content, comms_path)
    return True


def get_all_agent_statuses(comms_path: Optional[Path] = None) -> dict[str, dict]:
    """
    Get status summary of all agents.

    Args:
        comms_path: Optional custom path

    Returns:
        Dict of {agent_id: {"status": str, "mission": str, "last_update": str}}
    """
    content = read_comms(comms_path)
    statuses = {}

    # Find all agent sections
    pattern = r"## (.+) ([A-Z]+)\s*\n+\*\*Status:\*\* ([^\n]+)\s*\n\*\*Last Update:\*\* ([^\n]+).*?### Current Mission\s*\n> ([^\n]+)"

    for match in re.finditer(pattern, content, re.DOTALL):
        emoji, agent_id, status, last_update, mission = match.groups()
        statuses[agent_id] = {
            "emoji": emoji.strip(),
            "status": status.strip(),
            "last_update": last_update.strip(),
            "mission": mission.strip()
        }

    return statuses


def update_status_dashboard(comms_path: Optional[Path] = None) -> bool:
    """
    Regenerate the status dashboard from agent sections.

    Args:
        comms_path: Optional custom path

    Returns:
        True if updated
    """
    content = read_comms(comms_path)
    statuses = get_all_agent_statuses(comms_path)

    if not statuses:
        return False

    # Build dashboard
    dashboard = """## 📊 STATUS DASHBOARD

| Agent | Status | Last Update | Current Mission |
|-------|--------|-------------|-----------------|
"""

    for agent_id, info in sorted(statuses.items()):
        emoji = info.get("emoji", "❓")
        status = info.get("status", "Unknown")
        last_update = info.get("last_update", "Never")
        mission = info.get("mission", "No mission")[:40]
        dashboard += f"| {emoji} {agent_id} | {status} | {last_update} | {mission} |\n"

    dashboard += "\n---\n"

    # Replace or insert dashboard
    pattern = r"## 📊 STATUS DASHBOARD.*?(?=^## [^📊]|\Z)"

    if re.search(pattern, content, re.MULTILINE | re.DOTALL):
        new_content = re.sub(pattern, dashboard, content, count=1, flags=re.MULTILINE | re.DOTALL)
    else:
        # Insert at beginning after title
        pattern2 = r"(# [^\n]+\n+(?:[^\n]+\n)*?\n)"
        new_content = re.sub(pattern2, rf"\1{dashboard}\n", content, count=1)

    write_comms(new_content, comms_path)
    return True


def print_comms_status(agent_id: str, comms_path: Optional[Path] = None) -> None:
    """
    Print formatted COMMS status for an agent (for terminal output).

    Args:
        agent_id: Agent to show status for
        comms_path: Optional custom path
    """
    section = get_agent_section(agent_id, comms_path)

    if section:
        print(f"\n{Style.CYAN}┌─────────────────────────────────────┐{Style.RESET}")
        print(f"{Style.CYAN}│{Style.RESET} {Style.BOLD}📡 COMMS STATUS: {agent_id}{Style.RESET}")
        print(f"{Style.CYAN}└─────────────────────────────────────┘{Style.RESET}")

        # Extract status and mission from section
        status_match = re.search(r"\*\*Status:\*\* ([^\n]+)", section)
        mission_match = re.search(r"> ([^\n]+)", section)

        if status_match:
            print(f"  Status: {status_match.group(1)}")
        if mission_match:
            print(f"  Mission: {mission_match.group(1)}")
    else:
        print(f"{Style.YELLOW}⚠️ No COMMS section found for {agent_id}{Style.RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# COMMS MANAGER CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class CommsManager:
    """
    Convenience class for agent COMMS.md operations.

    Each agent creates one instance with their ID and emoji,
    then uses it for all COMMS.md operations.

    Usage:
        comms = CommsManager(comms_path, agent_id="SENTINEL", emoji="🛡️")
        comms.log_event("session_start", {"mode": "continuous"})
        comms.update_section(status="Active", mission="Monitoring")
    """

    def __init__(self, comms_path: Path, agent_id: str, emoji: str):
        """
        Initialize CommsManager for an agent.

        Args:
            comms_path: Path to COMMS.md file
            agent_id: Agent ID (e.g., "SENTINEL", "COMMANDER")
            emoji: Agent emoji (e.g., "🛡️", "👑")
        """
        self.comms_path = comms_path
        self.agent_id = agent_id
        self.emoji = emoji
        self.session_log: list[str] = []

    def log_event(self, event_type: str, details: dict) -> None:
        """
        Log an event to COMMS.md.

        Args:
            event_type: Type of event (e.g., "session_start", "task_complete")
            details: Event details as dict
        """
        import json

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {event_type}"

        # Add to local session log
        self.session_log.append(log_entry)

        # Try to update COMMS.md
        try:
            if not self.comms_path.parent.exists():
                self.comms_path.parent.mkdir(parents=True, exist_ok=True)

            # Simple append for events
            entry = f"""
### {self.emoji} {self.agent_id} - {timestamp}
**Event:** {event_type}
**Details:**
```json
{json.dumps(details, indent=2)}
```

"""
            # Read existing content
            content = ""
            if self.comms_path.exists():
                content = self.comms_path.read_text(encoding="utf-8")

            # Find agent section and append to session log
            log_agent_action(self.agent_id, f"{event_type}: {list(details.keys())}", self.comms_path)

        except Exception:
            pass  # Silently fail on COMMS.md errors

    def update_section(
        self,
        status: str = None,
        mission: str = None,
        progress: list[str] = None,
        log_entry: str = None,
    ) -> None:
        """
        Update this agent's section in COMMS.md.

        Args:
            status: Optional new status
            mission: Optional new mission
            progress: Optional list of progress items
            log_entry: Optional log entry to add
        """
        if log_entry:
            self.session_log.append(log_entry)

        # Build task queue and progress dicts
        task_queue = []
        progress_list = []

        if progress:
            for item in progress:
                progress_list.append({"task": item, "done": False})

        update_agent_section(
            agent_id=self.agent_id,
            emoji=self.emoji,
            status=status or STATUS_ACTIVE,
            mission=mission or "Working",
            task_queue=task_queue,
            progress=progress_list,
            session_log=self.session_log[-10:],
            comms_path=self.comms_path
        )

    def set_status(self, status: str) -> None:
        """Quick status update."""
        set_agent_status(self.agent_id, status, self.comms_path)

    def announce(self, message: str, priority: str = "INFO") -> None:
        """Add an announcement."""
        add_announcement(self.agent_id, self.emoji, message, priority, self.comms_path)
