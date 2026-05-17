# MonskySkills

Personal Codex skill repository for storing, reviewing, and reusing skills and companion agent configuration.

## How to use this

1. Add each reusable skill under `.agents/skills/<skill-name>/`.
2. Keep optional Codex agent profiles under `.codex/agents/`.
3. Keep install notes, snippets, and usage examples in `docs/`.
4. Commit each skill or meaningful update separately so it is easy to review or roll back.

## Layout

```text
.agents/skills/       Codex skill folders, each with a SKILL.md entrypoint
.codex/agents/        Optional custom agent TOML profiles used by skills
docs/                 Install notes, snippets, and design rationale
README.md             Repo overview and usage
AGENTS.md             Project-specific Codex instructions
```

## Current skills

- `codex-orchestrate`: delegate-first Codex orchestration skill for routing repository work through subagents, selecting explicit models/effort, escalating stuck work, and requiring final root review.

## Source of truth

This repository is the source of truth for skills we create. For `codex-orchestrate`, the authoritative copy is:

```text
.agents/skills/codex-orchestrate/
```

The global copy in `~/.codex/skills/codex-orchestrate/` is an installed runtime copy. After changing the repo copy, sync it globally and restart Codex before expecting other sessions to use the update.

## Installing a stored skill locally

Copy a skill into the global Codex skills folder:

```bash
mkdir -p ~/.codex/skills
cp -R .agents/skills/<skill-name> ~/.codex/skills/
```

If a skill has companion agent profiles, copy those too:

```bash
mkdir -p ~/.codex/agents
cp .codex/agents/*.toml ~/.codex/agents/
```

Restart Codex after installing or updating global skills.

For `codex-orchestrate`, sync the current repo copy with:

```bash
rm -rf ~/.codex/skills/codex-orchestrate
cp -R .agents/skills/codex-orchestrate ~/.codex/skills/
mkdir -p ~/.codex/agents
cp .codex/agents/*.toml ~/.codex/agents/
```

## Enabling `/orchestrate`

After installing `codex-orchestrate`, add this rule to your global or project `AGENTS.md`:

```text
When a user starts a request with `/orchestrate`, treat it as an explicit instruction to use `$codex-orchestrate` for continuous delegate-first orchestration. Reevaluate delegation after each phase, spawn the cheapest safe subagents for substantive repository work, use built-in fallback roles when custom agents are unavailable, escalate stuck work narrowly, and finish with root senior review before responding.
```

## Model routing

`codex-orchestrate` treats model choice as a first-class routing decision:

```text
gpt-5.3-codex-spark  ultra-fast text-only coding loops, scouts, mechanics, simple targeted fixes
gpt-5.4-mini         efficient lightweight support, known validation, docs edits, log/test summaries
gpt-5.4              ordinary implementation, planning, deep discovery, test triage, risk checks
gpt-5.5              high-risk or high-ambiguity architecture, review, security, debugging, migration, performance
```

Smaller models can preserve local-message usage limits, but subagent fanout still consumes usage. Stronger models are intentionally pinned for quality-sensitive roles.

## Validation

Run the skill-pack checker before committing orchestration changes:

```bash
python3 scripts/check_orchestration_skill.py
```

The checker validates required skill sections, fallback role mapping, model routing scenarios, agent TOML model pins, duplicate stuck-protocol cleanup, and source-of-truth docs.

## Privacy

Do not store secrets, tokens, private student data, local exports, or machine-specific credential files in this repository. Use synthetic examples only.
