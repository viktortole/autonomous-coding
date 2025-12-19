"""
OpenCode CLI client adapter.

Runs prompts through the opencode CLI and adapts output to the same
message loop shape used by the Claude SDK client.
"""

from __future__ import annotations

import asyncio
import os
import shlex
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import AsyncIterator


class TextBlock:
    def __init__(self, text: str) -> None:
        self.text = text


class AssistantMessage:
    def __init__(self, content: list[TextBlock]) -> None:
        self.content = content


@dataclass
class OpenCodeConfig:
    bin_path: str
    model: str | None
    extra_args: list[str]


class OpenCodeClient:
    provider_label = "OpenCode CLI"

    def __init__(self, project_dir: Path, model: str | None = None) -> None:
        self.project_dir = project_dir
        self._prompt: str | None = None
        self._config = self._load_config(model)
        self._env = os.environ.copy()

    async def __aenter__(self) -> "OpenCodeClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def query(self, message: str) -> None:
        self._prompt = message

    async def receive_response(self) -> AsyncIterator[AssistantMessage]:
        if self._prompt is None:
            raise ValueError("OpenCodeClient.query() must be called before receive_response().")

        cmd = self._build_command(self._prompt)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(self.project_dir.resolve()),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=self._env,
        )
        stdout, stderr = await proc.communicate()
        stdout_text = stdout.decode(errors="replace")
        stderr_text = stderr.decode(errors="replace")

        if proc.returncode != 0:
            error_text = stderr_text.strip() or stdout_text.strip()
            raise RuntimeError(f"OpenCode failed (exit {proc.returncode}): {error_text}")

        output = stdout_text.strip()
        if not output and stderr_text.strip():
            output = stderr_text.strip()

        yield AssistantMessage([TextBlock(output)])

    def _load_config(self, model: str | None) -> OpenCodeConfig:
        bin_path = os.environ.get("OPENCODE_BIN", "opencode").strip()
        if not shutil.which(bin_path):
            raise ValueError(
                f"OpenCode CLI not found: '{bin_path}'. Install opencode or set OPENCODE_BIN."
            )

        env_model = os.environ.get("OPENCODE_MODEL")
        resolved_model = (env_model or model or "").strip() or None

        extra_args_raw = os.environ.get("OPENCODE_ARGS", "").strip()
        extra_args = shlex.split(extra_args_raw) if extra_args_raw else []

        return OpenCodeConfig(
            bin_path=bin_path,
            model=resolved_model,
            extra_args=extra_args,
        )

    def _build_command(self, prompt: str) -> list[str]:
        cmd = [self._config.bin_path, "run", prompt]
        if self._config.model:
            cmd.extend(["--model", self._config.model])
        if self._config.extra_args:
            cmd.extend(self._config.extra_args)
        return cmd
