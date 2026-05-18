# Contributing

Thanks for considering a contribution to `codex-orchestrate`.

This repo is intentionally narrow: it exists to package and validate one Codex skill for continuous subagent orchestration. Please keep changes focused on that goal.

## Good Contributions

- Clearer install or usage docs.
- Safer orchestration policy wording.
- Better context-packet, lifecycle, or ledger validation.
- Small standard-library script improvements.
- Synthetic, commit-safe eval fixtures.
- Bug fixes for the dashboard, validators, sync script, or report generator.

## Please Avoid

- Adding unrelated skills.
- Adding third-party dependencies without a strong reason.
- Committing real run transcripts, private ledgers, credentials, or user data.
- Making broad stylistic rewrites that do not improve behavior.
- Weakening model-routing, final-review, lifecycle, or root-takeover safeguards without replacing them with a better mechanism.

## Local Checks

Repository tooling requires Python 3.11+ and uses only the standard library.

Start with:

```bash
python3 scripts/orchestration_check.py --quick
```

Before opening a larger pull request, run:

```bash
python3 scripts/orchestration_check.py --full --fail-fast
```

Focused scripts remain useful while debugging:

```bash
python3 scripts/check_orchestration_skill.py
python3 scripts/check_orchestration_context_packets.py evals/codex-orchestrate/sample-context-packets/*.json
python3 scripts/check_orchestration_ledger.py evals/codex-orchestrate/sample-ledgers/*.json
python3 scripts/check_orchestration_lifecycle.py evals/codex-orchestrate/sample-ledgers/*.json
python3 scripts/check_orchestration_behavior.py evals/codex-orchestrate/sample-ledgers/*.json
python3 scripts/check_orchestration_benchmarks.py
```

## Pull Request Notes

In a PR description, include:

- What behavior changed.
- Which files changed.
- Which checks passed.
- Any skipped checks and why.
- Any user-facing install or invocation changes.

## Privacy

Use synthetic examples only. Do not commit real private task details, real run ledgers, API keys, credentials, local exports, or machine-specific secrets.
