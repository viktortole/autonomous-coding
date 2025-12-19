"""
Workspace Resolution Helpers
============================

Resolve workspace-relative paths for task files, logs, and assets.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WorkspacePaths:
    root: Path
    tasks_dir: Path
    logs_dir: Path
    screenshots_dir: Path
    config_dir: Path


def resolve_workspace(workspace: str | Path | None = None) -> WorkspacePaths:
    """
    Resolve workspace paths.

    Priority:
    1) CLI arg
    2) AUTOAGENTS_WORKSPACE env var
    3) Repo root (two levels above this file)
    """
    if workspace is None:
        workspace = os.environ.get("AUTOAGENTS_WORKSPACE")

    if workspace:
        root = Path(workspace).expanduser().resolve()
    else:
        root = Path(__file__).resolve().parents[2]

    return WorkspacePaths(
        root=root,
        tasks_dir=root / "tasks",
        logs_dir=root / "logs",
        screenshots_dir=root / "screenshots",
        config_dir=root / "config",
    )
