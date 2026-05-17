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

## Privacy

Do not store secrets, tokens, private student data, local exports, or machine-specific credential files in this repository. Use synthetic examples only.
