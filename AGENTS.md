# MonskySkills Agent Instructions

## Purpose

This repository stores reusable Codex skills, companion agent profiles, snippets, and installation notes created or curated for Douglas Monsky.

## Tech Stack

- Markdown for skill instructions and documentation.
- TOML for Codex custom agent profiles.
- Shell commands for install and verification workflows.

## Repo Layout

- `.agents/skills/<skill-name>/SKILL.md`: skill entrypoints.
- `.agents/skills/<skill-name>/references/`: optional supporting guidance for a skill.
- `.codex/agents/*.toml`: custom Codex agent profiles used by one or more skills.
- `.codex/config.orchestration.example.toml`: merge-only sample config for bounded orchestration fanout.
- `docs/`: install notes, snippets, examples, and rationale.
- `schemas/`: machine-readable contracts for skill output artifacts.

## Setup Commands

```bash
git clone <repo-url>
cd MonskySkills
```

## Verification Commands

There is no build system yet. For skill changes, run focused structural checks:

```bash
python3 scripts/check_orchestration_skill.py
python3 scripts/check_runtime_compatibility.py
python3 scripts/sync_orchestration_skill.py --check
find .agents/skills -name SKILL.md -print
find .codex/agents -name '*.toml' -print
git diff --check
```

When TOML agent profiles change, inspect them for valid names, explicit model routing, reasoning effort, and clear instructions.

## Source Of Truth And Sync

- Treat repo-local skill folders under `.agents/skills/` as authoritative.
- Treat `~/.codex/skills/` as an installed runtime copy, not the source of truth.
- After changing `codex-orchestrate`, sync `.agents/skills/codex-orchestrate/` to `~/.codex/skills/codex-orchestrate/` and copy `.codex/agents/*.toml` to `~/.codex/agents/`.
- Do not overwrite `~/.codex/config.toml`; merge settings manually from `.codex/config.orchestration.example.toml` when needed.
- When Codex shows both repo-local and global copies of a skill, prefer the repo-local copy while working in this repository.

## Data Privacy Rules

- Do not commit secrets, API keys, tokens, private exports, or machine credential files.
- Do not commit real student data or identifiable education records.
- Use synthetic examples in docs and fixtures.
- Keep local-only experiments under ignored folders such as `local/`, `tmp/`, or `data/private/`.

## Files And Folders To Treat Carefully

- Do not remove or rename a published skill folder without updating install docs.
- Do not overwrite `.codex/agents/*.toml` profiles without checking which skills refer to them.
- Do not add hard-coded user-specific absolute paths to reusable skill instructions unless the skill is explicitly local-only.

## Definition Of Done

- Skill instructions are clear enough to use after restarting Codex.
- Companion agent profiles or docs are committed with the skill when required.
- README or docs are updated when install behavior changes.
- `python3 scripts/check_orchestration_skill.py` passes when `codex-orchestrate` changes.
- `python3 scripts/sync_orchestration_skill.py --check` passes after syncing global installs.
- `python3 scripts/check_runtime_compatibility.py` runs and any runtime model warnings are understood.
- Model pins in `.codex/agents/*.toml` still match the documented `codex-orchestrate` model ladder.
- Ledger schema and template docs stay aligned when routing-ledger behavior changes.
- `git diff --check` passes.
- No secrets, tokens, or private data are staged.
