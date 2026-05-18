# Basic Install

This is the small install path for using `codex-orchestrate` without the development, eval, dashboard, ledger, and validation tooling in this repository.

## What You Need

Install only these runtime pieces:

```text
.agents/skills/codex-orchestrate/
.codex/agents/*.toml
```

You do not need `evals/`, `schemas/`, `scripts/`, `ui/`, or the development docs to use the skill. The `references/` and `agents/openai.yaml` files inside `.agents/skills/codex-orchestrate/` are part of the skill and should be copied with it.

## Global Install

From a checkout of `MonskySkills`:

```bash
mkdir -p ~/.codex/skills ~/.codex/agents
rm -rf ~/.codex/skills/codex-orchestrate
cp -R .agents/skills/codex-orchestrate ~/.codex/skills/
cp .codex/agents/*.toml ~/.codex/agents/
```

The `rm -rf` line removes only the previous installed `codex-orchestrate` copy. It does not change this repository.

Restart Codex after installing or updating the global copy.

## Repository-Scoped Install

To install the skill into one project instead of globally:

```bash
mkdir -p /path/to/repo/.agents/skills /path/to/repo/.codex/agents
rm -rf /path/to/repo/.agents/skills/codex-orchestrate
cp -R .agents/skills/codex-orchestrate /path/to/repo/.agents/skills/
cp .codex/agents/*.toml /path/to/repo/.codex/agents/
```

Then restart Codex in that project.

## Enable `/orchestrate`

Add this rule to your global `~/.codex/AGENTS.md` or to the target project's `AGENTS.md`:

```text
When a user starts a request with /orchestrate, use $codex-orchestrate for continuous delegate-first orchestration. Reevaluate delegation after each phase, keep subagent packets compact, recover stalled subagents by repairing/redelegating the same objective, and finish with root senior review before responding.
```

For a fuller prompt surface, copy the relevant parts of:

```text
docs/codex-orchestrate/AGENTS.orchestration.snippet.md
```

## Optional Fanout Limits

If you want bounded subagent fanout, manually merge these keys into `~/.codex/config.toml` or the project's `.codex/config.toml`:

```toml
[agents]
max_threads = 6
max_depth = 1
job_max_runtime_seconds = 1800
```

Keep `max_depth = 1` unless recursive delegation is intentionally needed. Do not overwrite an existing Codex config file.

## Smoke Check

After restarting Codex, start a new session in any repository and ask:

```text
/orchestrate Explain how you would route a non-trivial repo task before making changes.
```

You should see the assistant initialize a routing loop, discuss delegation, compact context packets, stuck-work recovery, and final root review.

## Updating

To update later, pull the latest `MonskySkills` checkout and repeat the global or repository-scoped copy commands above.

If you are developing this repo, use the validation workflow in `README.md`. If you only want to use the skill, this file is enough.
