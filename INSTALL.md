# Basic Install

This is the small install path for using `codex-orchestrate` without the development, eval, dashboard, ledger, and validation tooling in this repository.

## One Step Auto Installation

The easiest path is to ask Codex to install it for you. Open a new Codex session and paste one of these prompts.

If Codex can access GitHub:

```text
Install codex-orchestrate from https://github.com/douglasmonsky/codex-orchestrate into my global Codex environment. Use the repo's INSTALL.md. Copy only the runtime skill folder and companion agent TOMLs. Leave AGENTS.md unchanged and do not overwrite my Codex config. After installing, print the exact direct skill mention I should paste into Codex, using the installed SKILL.md path. Restart instructions are enough if you cannot restart Codex for me. Verify the installed files and tell me exactly what changed.
```

If you already have this repository open locally:

```text
Install codex-orchestrate from this checkout into my global Codex environment. Use INSTALL.md. Copy only .agents/skills/codex-orchestrate/ and .codex/agents/*.toml. Leave AGENTS.md unchanged and do not overwrite my Codex config. After installing, print the exact direct skill mention I should paste into Codex, using the installed SKILL.md path. Verify the installed files and tell me exactly what changed.
```

If you only want it in the current project:

```text
Install codex-orchestrate into this project only. Use this repo's INSTALL.md. Copy the skill to this repo's .agents/skills/ folder and the companion TOMLs to this repo's .codex/agents/ folder. Leave AGENTS.md unchanged and do not touch my global Codex config. After installing, print the exact direct skill mention I should paste into Codex, using the project-local SKILL.md path. Verify the installed files and tell me exactly what changed.
```

After Codex finishes, restart Codex so the new skill and agent profiles are loaded.

## Manual Install - What You Need

Everything below is only for users who want to get in the weeds and install manually instead of relying on Codex to perform the One Step Auto Installation prompts above.

Install only these runtime pieces:

```text
.agents/skills/codex-orchestrate/
.codex/agents/*.toml
```

You do not need `evals/`, `schemas/`, `scripts/`, `ui/`, or the development docs to use the skill. The `references/` and `agents/openai.yaml` files inside `.agents/skills/codex-orchestrate/` are part of the skill and should be copied with it.

## Global Install

From a checkout of `codex-orchestrate`:

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

## Direct Skill Invocation

No `AGENTS.md` change is required for normal use. After global install, invoke the skill by directly mentioning the installed `SKILL.md`:

```text
[$codex-orchestrate](/Users/<your-user>/.codex/skills/codex-orchestrate/SKILL.md) Use this skill for the following repository task: <task>
```

If your home directory is different, use your actual installed path:

```text
[$codex-orchestrate](/Users/<your-user>/.codex/skills/codex-orchestrate/SKILL.md)
```

For a repository-scoped install, use that repo's local skill path:

```text
[$codex-orchestrate](/path/to/repo/.agents/skills/codex-orchestrate/SKILL.md)
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
[$codex-orchestrate](/Users/<your-user>/.codex/skills/codex-orchestrate/SKILL.md) Explain how you would route a non-trivial repo task before making changes.
```

You should see the assistant initialize a routing loop, discuss delegation, compact context packets, stuck-work recovery, and final root review.

## Updating

To update later, pull the latest `codex-orchestrate` checkout and repeat the global or repository-scoped copy commands above.

If you are developing this repo, use the validation workflow in `README.md`. If you only want to use the skill, this file is enough.
