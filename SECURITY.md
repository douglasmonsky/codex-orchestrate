# Security Policy

`codex-orchestrate` is an instruction and tooling package for Codex. It does not run a hosted service and should not require secrets to install.

## Supported Versions

Use the latest `main` branch unless a release tag says otherwise.

## Reporting A Vulnerability

If you find a vulnerability or a dangerous orchestration behavior, please report it privately first.

Preferred report contents:

- A short description of the issue.
- The affected file or policy area.
- Reproduction steps using synthetic data.
- The likely impact.
- A suggested fix, if you have one.

Do not include real credentials, private run transcripts, private task ledgers, student data, or customer data in reports.

## Security-Sensitive Areas

Pay special attention to:

- Prompts that could encourage root takeover after failed delegation.
- Context packets that leak private transcripts, broad logs, secrets, or user data.
- Scripts that read from or write to paths outside the repository or `~/.codex`.
- Sync behavior that could overwrite user configuration.
- Dashboard endpoints, which should remain local and read-only.

## Current Boundaries

- The local dashboard binds to `127.0.0.1` by default.
- `scripts/serve_orchestration_ui.py` rejects write methods.
- `scripts/sync_orchestration_skill.py` syncs skill and agent files only; it does not overwrite `~/.codex/config.toml`.
- Real run ledgers should stay under ignored `local/` unless they are sanitized.
