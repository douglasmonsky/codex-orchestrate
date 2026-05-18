# Public Release Checklist

Use this before making the repository public or cutting a release.

## Required

- [ ] Confirm the intended license is correct.
- [ ] Confirm the GitHub repository visibility change is intentional.
- [ ] Run `python3 scripts/orchestration_check.py --full --fail-fast`.
- [ ] Run `python3 scripts/sync_orchestration_skill.py --check`.
- [ ] Search for private absolute paths:

```bash
rg -n "/U""sers/[^/< >]+/" . --glob '!local/**' --glob '!__pycache__/**' --glob '!.git/**'
```

The full validation wrapper also runs a strict secret scan.

- [ ] Confirm `local/`, generated caches, private ledgers, and smoke artifacts are ignored.
- [ ] Confirm install docs use direct skill invocation and do not require `AGENTS.md` edits.
- [ ] Confirm `README.md`, `INSTALL.md`, `CONTRIBUTING.md`, and `SECURITY.md` are current.
- [ ] Confirm no real run transcripts, private ledgers, student data, credentials, or local exports are staged.

## Recommended

- [ ] Add GitHub topics for discoverability.
- [ ] Add a concise GitHub repository description.
- [ ] Create a first release tag after public visibility is set.
- [ ] Use the README explanation prompt from `README.md` in a fresh Codex or ChatGPT session and check whether the response matches the intended positioning.

## Release Notes Seed

```text
Initial public release of codex-orchestrate: a Codex skill and companion custom-agent profile set for continuous subagent orchestration, compact context packets, model routing, stuck-work recovery, ledger-backed lifecycle evidence, and root final review.
```
