# Development-Only Materials

This folder holds advanced or legacy-facing artifacts that are useful while developing
`codex-orchestrate`, but are not part of the basic runtime install.

End users only need:

```text
.agents/skills/codex-orchestrate/
.codex/agents/*.toml
```

## Contents

```text
advanced/AGENTS.orchestration.snippet.md
```

The AGENTS snippet is intentionally not part of the normal installation path. It is
kept for maintainers or power users who want to create a persistent local alias
after understanding the tradeoffs. Public install docs should continue to recommend
direct skill invocation through `[$codex-orchestrate](...)`.
