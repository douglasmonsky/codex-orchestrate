"""Shared environment helpers for codex-orchestrate scripts."""

from __future__ import annotations

import ipaddress
import os
import sys
from pathlib import Path


PYTHON_REQUIREMENT = "Python 3.11+ is required for codex-orchestrate repository tooling."


def require_python_311() -> None:
    if sys.version_info < (3, 11):
        raise SystemExit(PYTHON_REQUIREMENT)


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def display_path(path: Path, *, repo_root: Path | None = None) -> str:
    resolved = path.expanduser()
    if repo_root is not None and is_relative_to(resolved, repo_root):
        return str(resolved.resolve().relative_to(repo_root.resolve()))

    code_home = codex_home()
    if is_relative_to(resolved, code_home):
        prefix = "$CODEX_HOME" if os.environ.get("CODEX_HOME") else "~/.codex"
        rel = resolved.resolve().relative_to(code_home.resolve()).as_posix()
        return f"{prefix}/{rel}" if rel else prefix

    home = Path.home()
    if is_relative_to(resolved, home):
        rel = resolved.resolve().relative_to(home.resolve()).as_posix()
        return f"~/{rel}" if rel else "~"

    return resolved.name


def is_loopback_host(host: str) -> bool:
    normalized = host.strip().strip("[]").lower()
    if normalized == "localhost":
        return True
    try:
        return ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        return False
