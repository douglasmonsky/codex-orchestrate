#!/usr/bin/env python3
"""Check or sync the installed codex-orchestrate skill pack.

The repo-local MonskySkills copy is authoritative. The global ~/.codex copy is
the installed runtime copy.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SKILL = ROOT / ".agents" / "skills" / "codex-orchestrate"
SOURCE_AGENTS = ROOT / ".codex" / "agents"
TARGET_CODEX = Path.home() / ".codex"
TARGET_SKILL = TARGET_CODEX / "skills" / "codex-orchestrate"
TARGET_AGENTS = TARGET_CODEX / "agents"


def iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file())


def relative_files(root: Path) -> set[Path]:
    return {path.relative_to(root) for path in iter_files(root)}


def compare_tree(source: Path, target: Path, label: str) -> list[str]:
    changes: list[str] = []
    if not source.exists():
        raise FileNotFoundError(f"missing source {label}: {source}")

    source_files = relative_files(source)
    target_files = relative_files(target)

    for rel in sorted(source_files - target_files):
        changes.append(f"missing in installed {label}: {rel}")
    for rel in sorted(target_files - source_files):
        changes.append(f"extra in installed {label}: {rel}")
    for rel in sorted(source_files & target_files):
        if not filecmp.cmp(source / rel, target / rel, shallow=False):
            changes.append(f"different installed {label}: {rel}")
    return changes


def compare_agents() -> list[str]:
    changes: list[str] = []
    if not SOURCE_AGENTS.exists():
        raise FileNotFoundError(f"missing source agents: {SOURCE_AGENTS}")

    source_files = sorted(SOURCE_AGENTS.glob("*.toml"))
    target_files = sorted(TARGET_AGENTS.glob("*.toml")) if TARGET_AGENTS.exists() else []
    source_names = {path.name for path in source_files}
    target_names = {path.name for path in target_files}

    for name in sorted(source_names - target_names):
        changes.append(f"missing in installed agents: {name}")
    for name in sorted(target_names - source_names):
        changes.append(f"extra in installed agents: {name}")
    for name in sorted(source_names & target_names):
        if not filecmp.cmp(SOURCE_AGENTS / name, TARGET_AGENTS / name, shallow=False):
            changes.append(f"different installed agents: {name}")
    return changes


def check() -> int:
    changes = compare_tree(SOURCE_SKILL, TARGET_SKILL, "skill")
    changes.extend(compare_agents())
    if changes:
        print("DRIFT: installed codex-orchestrate copy differs from repo source")
        for change in changes:
            print(f"- {change}")
        return 1

    print("OK: installed codex-orchestrate skill and agents match repo source")
    return 0


def mirror_directory(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)


def apply() -> int:
    before = compare_tree(SOURCE_SKILL, TARGET_SKILL, "skill")
    before.extend(compare_agents())

    mirror_directory(SOURCE_SKILL, TARGET_SKILL)
    TARGET_AGENTS.mkdir(parents=True, exist_ok=True)
    source_agent_names = {source.name for source in SOURCE_AGENTS.glob("*.toml")}
    for target in sorted(TARGET_AGENTS.glob("*.toml")):
        if target.name not in source_agent_names:
            target.unlink()
    for source in sorted(SOURCE_AGENTS.glob("*.toml")):
        shutil.copy2(source, TARGET_AGENTS / source.name)

    after = compare_tree(SOURCE_SKILL, TARGET_SKILL, "skill")
    after.extend(compare_agents())
    if after:
        print("FAIL: sync completed but installed copy still differs")
        for change in after:
            print(f"- {change}")
        return 1

    if before:
        print("SYNCED: installed codex-orchestrate copy updated")
        for change in before:
            print(f"- {change}")
    else:
        print("OK: installed codex-orchestrate copy was already current")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="compare repo source against installed ~/.codex copy")
    mode.add_argument("--apply", action="store_true", help="sync repo source into installed ~/.codex copy")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    try:
        if args.check:
            return check()
        return apply()
    except FileNotFoundError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
