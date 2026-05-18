# Handoff Contracts

## Table Of Contents

- Routing ledger template
- When to produce a durable ledger
- Context packet template
- Context request template
- Subagent lifecycle ledger template
- Default subagent assignment template
- Stuck-state summary template
- Mechanic handoff
- Scout handoff
- Deep scout handoff
- Implementation handoff
- Review handoff
- Validation handoff
- Pass-off template
- Root synthesis and final review template

Use these templates to keep subagent work bounded, cheap, comparable, and escalation-ready.

## Routing ledger template

Use this compact ledger before delegating, after each subagent result, after validation, and before final review. Keep it short; it is a control surface, not a transcript.

```text
Goal:
Current step:
Tier:
Active/finished agents:
Runtime role mapping:
Model selected:
Reasoning effort:
Why this model is sufficient:
Evidence gathered:
Open risks/uncertainty:
Next routing decision:
Escalation status:
Final-review gate:
```

## When to produce a durable ledger

Produce a durable post-run ledger for any Tier 3 or Tier 4 run, any model fallback, any security/privacy/migration/auth task, any run with more than two subagents, any failed validation, or any final-review blocker. Tier 1 and Tier 2 ledgers are optional unless one of those triggers appears.

Durable ledgers are not automatic runtime logs. When a trigger applies, final review is blocked until the root creates the ledger or explicitly states why it could not. In the `codex-orchestrate` repository, use `python3 scripts/create_orchestration_ledger.py` for repo-local ledgers or add `--global-output` to write under `~/.codex/orchestration-ledgers/`. In other repos, write the same JSON shape to `~/.codex/orchestration-ledgers/` or use `docs/codex-orchestrate/run-ledger-template.md` manually. Keep private ledgers local/global or sanitized before committing.

## Context packet template

Initial subagent dispatch should use a minimal context packet. Do not paste raw transcripts, full logs, broad repo summaries, or root routing rationale into the first handoff.

```text
Context packet:
Packet id:
Role/mission:
Objective:
Scope:
- <file:path:line | folder | command surface>
Non-goals:
- <explicit exclusion>
Known evidence handles:
- <file:path:line | cmd:name | diff:path | ledger:entry | artifact:path | scenario:id>
Allowed actions/paths:
- <read/write/command boundary>
Constraints:
- <behavior, scope, privacy, or style constraint>
Done condition:
Output budget:
Context-request rule:
Use the Context request block before asking for broader context.
Expected return:
```

The packet must make the task startable: objective, scope, allowed actions/paths, constraints, and done condition are clear. If not, the subagent should request packet repair rather than widening scope.

Subagents should return when done, blocked, stuck, out of scope, or needing a specific additional context handle.

Root-only routing metadata stays out of the subagent-visible packet: model, reasoning effort, tier, runtime mapping, model sufficiency, preferred concrete model, and escalation target belong in the routing ledger.

## Context request template

Use only when the packet lacks context needed for the assigned decision.

```text
Context request:
Reason:
Requested handle/path:
Decision impact:
```

The root should reassess routing before granting context: provide only the narrow handle needed, escalate, pass off, repair the packet, or stop fanout.

## Subagent lifecycle ledger template

Use durable ledger lifecycle entries when a post-run ledger is required. Every delegated subagent should have a packet id, a start event, and a terminal exit.

```text
Subagent lifecycle:
Packet id:
Role:
Event: <started | completed | stuck | blocked | context-requested | escalated | skipped | packet-repaired>
Exit status: <done | blocked | stuck | out-of-scope | context-requested>
Evidence:
Context request:
Root decision:
```

An unclear packet returns to root as packet repair instead of broad exploration. Context requests must name packet id, reason, requested handle/path, and decision impact. Final root review checks that every active packet has terminal exit evidence.

If a subagent times out, is closed, or produces no useful changes, record a `stuck` lifecycle event with `exit_status: stuck`, evidence that no usable result was produced, and a root decision to repair, split, redelegate, or escalate the same narrow objective. Do not turn that timeout into root implementation except for a deterministic micro-action.

## Default subagent assignment template

```text
Role:
You are the <agent role> for this Codex task.

Context packet:
<use the minimal packet template above>

Objective:
<one specific outcome>

Scope:
<files, folders, commands, docs, or error logs>

Constraints:
- Stay within the assigned scope.
- Do not inspect unrelated areas.
- Do not modify files unless explicitly asked.
- Preserve existing project conventions.
- Return evidence, not just conclusions.
- Keep output compact.
- If stuck, return a stuck-state summary instead of broadening scope.
- If more context is required, return a structured Context request.

Non-goals:
- <what not to solve>
- <what not to change>

Output budget:
<= <word count> words unless exact patch details or essential command output require more.

Done condition:
<what counts as done, blocked, stuck, out of scope, or needing a Context request>

Return format:
Summary:
Evidence:
Findings:
Recommended action:
Files touched or inspected:
Commands run:
Risks / uncertainty:
Stuck status: <not stuck | stuck | blocked by scope | blocked by environment | role mismatch>
Context request: <none | structured request>
Recommended next route: <none | same objective needs stronger route | pass to role X | root decision needed>
Confidence:
```

## Stuck-state summary template

Use this when a subagent cannot complete the assigned objective.

```text
Original objective:
Agent role used:
What was tried:
Timeout/closed/no-change status:
Files inspected/touched:
Changes produced:
Commands run:
Observed evidence:
What failed or remains unclear:
Smallest unresolved question:
Recommended next role/action:
Confidence:
```

The root should feed this summary into the next agent rather than forcing full rediscovery.

## Mechanic handoff

Use for deterministic, narrow edits.

```text
Role:
Mechanic

Objective:
Apply this exact bounded change: <change>

Scope:
Only modify:
- <file/dir>

Constraints:
- Do not broaden the change.
- Do not redesign.
- Do not add dependencies.
- Preserve formatting and style.
- If the edit requires judgment, stop and recommend escalation.

Escalation trigger:
Any ambiguity, behavior change, validation failure, or need to inspect unrelated files.

Return format:
Files changed:
Patch summary:
Validation:
Assumptions:
Stuck status:
Context request:
Recommended next route:
```

## Scout handoff

Use before the root reads many files.

```text
Role:
Repo Scout

Objective:
Map the smallest relevant code/documentation surface for <task>.

Scope:
<repo area or suspected files>

Constraints:
- Read-only.
- Prefer search and targeted reads.
- Do not propose broad redesign.
- Keep output <= 300 words.
- If relevant surface is unclear, return the best evidence and recommend escalation.

Escalation trigger:
Relevant files/commands not found, multiple unrelated candidate surfaces, or low confidence.

Return format:
Relevant files:
Entry points:
Tests/checks:
Conventions:
Risks/open questions:
Stuck status:
Context request:
Recommended next route:
```

## Deep scout handoff

```text
Role:
Repo Scout Deep

Objective:
Resolve this specific discovery gap: <gap>

Prior stuck-state summary:
<paste compact summary>

Scope:
<repo area, suspected files, or modules>

Constraints:
- Read-only.
- Do not implement.
- Return only the smallest decision-ready map.

Escalation trigger:
Design/API uncertainty, migration ordering, or unresolved failure analysis.

Return format:
Resolved surface:
Evidence:
Remaining unknowns:
Recommended next agent:
Context request:
Confidence:
```

## Implementation handoff

Use only after planning/scope is clear.

```text
Role:
<Implementer Simple | Implementer | Implementer Strong>

Objective:
Apply the following bounded change: <change>

Prior stuck-state summary if this is escalation:
<paste compact summary or N/A>

Scope:
Only modify:
- <file/dir>
- <file/dir>

Acceptance criteria:
- <criterion>
- <criterion>

Tests/checks:
Run:
- <command>

Constraints:
- Do not broaden the change.
- Do not introduce new dependencies unless explicitly required.
- Add or update tests if behavior changes.
- Report exact files changed.
- If validation fails and the cause is unclear, stop and recommend test_triage or debugger.

Escalation trigger:
Unable to implement within scope, unclear design, unexplained validation failure, or low confidence patch.

Return format:
Patch summary:
Files changed:
Tests/checks run:
Failures:
Assumptions:
Residual risk:
Stuck status:
Context request:
Recommended next route:
Confidence:
```

## Review handoff

```text
Role:
Reviewer

Objective:
Review the current plan or patch for correctness, regression risk, missing tests, and unnecessary complexity.

Scope:
<diff, files, plan, or feature area>

Review priorities:
1. Definite correctness bugs
2. Missing validation
3. Edge cases
4. Maintainability risk
5. Scope creep

Escalation trigger:
Blocking issue requires design, security, migration, root-cause debugging, or higher model/effort disputed judgment.

Return format:
Blocking issues:
Non-blocking issues:
Missing tests/checks:
Suggested fixes:
Stuck status:
Context request:
Recommended next route:
Confidence:
```

## Validation handoff

```text
Role:
<Test Runner | Test Triage>

Objective:
Run or interpret the smallest meaningful validation for <change/task>.

Scope:
<commands, files, package, or test names>

Constraints:
- Prefer focused checks before broad suites.
- Summarize output; do not paste full logs unless necessary.
- Identify whether failures appear introduced or pre-existing.
- If the failure cannot be interpreted, recommend debugger rather than guessing.

Escalation trigger:
Unknown command surface, flaky behavior, unexplained failure, environment blocker, or ambiguous introduced/pre-existing classification.

Return format:
Commands run:
Results:
Failures:
Interpretation:
Recommended next check:
Stuck status:
Context request:
Recommended next route:
Confidence:
```

## Pass-off template

Use when a prior subagent was stuck or a role mismatch was found.

```text
Role:
<new specialist role>

Objective:
Resolve this narrow unresolved issue: <issue>

Prior attempt summary:
Original role:
What was tried:
Files inspected/touched:
Commands run:
Evidence:
What remains unclear:

Why this is a pass-off rather than same-role escalation:
<role mismatch evidence>

Scope:
<narrow scope>

Constraints:
- Do not repeat broad discovery unless prior evidence is unreliable.
- Focus on the unresolved issue.
- Return a decision-ready recommendation.

Return format:
Resolved issue:
Evidence:
Recommended action:
Remaining uncertainty:
Context request:
Confidence:
```

## Root synthesis and final review template

After subagents return, the root should synthesize and review in this format internally, then present only the useful parts to the user:

```text
Delegation used:
- <agent>: <model/effort/model class> — <why>

Subagent results:
- <agent>: <one-line result>

Escalations / pass-offs:
- <from> -> <to>: <reason>

Agreements:
- <shared findings>

Conflicts / gaps:
- <disagreement or missing evidence>

Root final-review checks:
- User intent satisfied: <yes/no>
- Scope appropriate: <yes/no>
- Evidence sufficient: <yes/no>
- Validation proportionate: <yes/no>
- Risk categories considered: <yes/no/N/A>
- Subagent uncertainty preserved: <yes/no>

Root decision:
- <chosen path and why>

Validation:
- <tests/checks/evidence>

Residual risk:
- <what remains uncertain>
```
