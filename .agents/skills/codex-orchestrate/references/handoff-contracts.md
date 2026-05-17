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

When working inside MonskySkills, use `python3 scripts/create_orchestration_ledger.py` for the durable version. In other repos, use `docs/codex-orchestrate/run-ledger-template.md` manually. Keep private ledgers local or sanitized before committing.

## Context packet template

Initial subagent dispatch should use a compact context packet. Do not paste raw transcripts, full logs, or broad repo summaries into the first handoff.

```text
Context packet:
Packet id:
Scenario id:
Role:
Runtime agent type:
Tier:
Objective:
Scope:
- <file:path:line | folder | command surface>
Non-goals:
- <explicit exclusion>
Known evidence handles:
- <file:path:line | cmd:name | diff:path | ledger:entry | artifact:path | scenario:id>
Allowed tools/paths:
- <read/write boundary>
Model:
Reasoning effort:
Writable:
Entry condition:
Exit condition:
Output budget:
Context-request rule:
Use the Context request block before asking for broader context.
Expected return:
```

Entry condition must make the task startable: objective, scope, model/effort, writable or read-only status, and done condition are clear. If not, the subagent should request packet repair rather than widening scope.

Exit condition must define when the subagent returns: done, blocked, stuck, out of scope, or needing a specific additional context handle.

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

Entry failure returns to root as packet repair instead of broad exploration. Context requests must name packet id, reason, requested handle/path, and decision impact. Final root review checks that every active packet has terminal exit evidence.

## Default subagent assignment template

```text
Role:
You are the <agent role> for this Codex task.

Context packet:
<use the compact packet template above>

Objective:
<one specific outcome>

Why this agent exists:
<what root-model work, uncertainty, or risk this delegation avoids>

Delegation tier:
<Tier 1 | Tier 2 | Tier 3 | Tier 4>

Runtime agent type:
<custom role if callable | explorer | worker | default>

Model selected:
<actual model, for example gpt-5.3-codex-spark | gpt-5.4-mini | gpt-5.4 | gpt-5.5>

Why this model is sufficient:
<bounded reason tied to task risk and ambiguity>

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

Reasoning effort:
<minimal | low | medium | high | xhigh if supported>

Preferred concrete model:
<gpt-5.3-codex-spark | gpt-5.4-mini | gpt-5.4 | gpt-5.5>

Output budget:
<= <word count> words unless exact patch details or essential command output require more.

Escalation trigger:
<what conditions mean this attempt is stuck>

Escalation target if stuck:
<same-role higher model/effort target first, then pass-off target if role mismatch is found>

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
Escalation recommendation: <none | same role at higher model/effort | pass to role X | root decision needed>
Confidence:
```

## Stuck-state summary template

Use this when a subagent cannot complete the assigned objective.

```text
Original objective:
Agent/effort/model used:
Intended model:
Actual model:
Model fallback used:
What was tried:
Files inspected/touched:
Commands run:
Observed evidence:
What failed or remains unclear:
Smallest unresolved question:
Recommended next agent/model/effort:
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

Reasoning effort:
minimal or low

Preferred concrete model:
gpt-5.3-codex-spark

Model selected:
gpt-5.3-codex-spark

Escalation trigger:
Any ambiguity, behavior change, validation failure, or need to inspect unrelated files.

Escalation target if stuck:
implementer_simple at medium effort.

Return format:
Files changed:
Patch summary:
Validation:
Assumptions:
Stuck status:
Context request:
Escalation recommendation:
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

Reasoning effort:
low

Preferred concrete model:
gpt-5.3-codex-spark

Model selected:
gpt-5.3-codex-spark

Escalation trigger:
Relevant files/commands not found, multiple unrelated candidate surfaces, or low confidence.

Escalation target if stuck:
repo_scout_deep at medium effort; planner or architect only if the issue is sequencing or design.

Return format:
Relevant files:
Entry points:
Tests/checks:
Conventions:
Risks/open questions:
Stuck status:
Context request:
Escalation recommendation:
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

Reasoning effort:
medium

Preferred concrete model:
gpt-5.4

Escalation trigger:
Design/API uncertainty, migration ordering, or unresolved failure analysis.

Escalation target if stuck:
planner, architect, debugger, or migration_analyst depending on failure mode.

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

Reasoning effort:
<low | medium | high>

Preferred concrete model:
<gpt-5.3-codex-spark | gpt-5.4 | gpt-5.5>

Model selected:
<gpt-5.3-codex-spark for Implementer Simple | gpt-5.4 for Implementer | gpt-5.5 for Implementer Strong>

Escalation trigger:
Unable to implement within scope, unclear design, unexplained validation failure, or low confidence patch.

Escalation target if stuck:
Same implementation role at one higher model/effort if available; otherwise implementer_strong, debugger, architect, or reviewer according to failure mode.

Return format:
Patch summary:
Files changed:
Tests/checks run:
Failures:
Assumptions:
Residual risk:
Stuck status:
Context request:
Escalation recommendation:
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

Reasoning effort:
high

Preferred concrete model:
gpt-5.5

Model selected:
gpt-5.5

Escalation trigger:
Blocking issue requires design, security, migration, root-cause debugging, or higher model/effort disputed judgment.

Escalation target if stuck:
architect, security_auditor, migration_analyst, debugger, or reviewer at xhigh if supported and justified.

Return format:
Blocking issues:
Non-blocking issues:
Missing tests/checks:
Suggested fixes:
Stuck status:
Context request:
Escalation recommendation:
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

Reasoning effort:
low for known commands; medium for failure interpretation.

Preferred concrete model:
gpt-5.4-mini for known commands; gpt-5.4 for triage.

Model selected:
gpt-5.4-mini for known commands; gpt-5.4 for triage.

Escalation trigger:
Unknown command surface, flaky behavior, unexplained failure, environment blocker, or ambiguous introduced/pre-existing classification.

Escalation target if stuck:
test_triage or debugger.

Return format:
Commands run:
Results:
Failures:
Interpretation:
Recommended next check:
Stuck status:
Context request:
Escalation recommendation:
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
Original agent/effort/model:
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

Reasoning effort:
<medium | high | xhigh if supported>

Preferred concrete model:
<gpt-5.4 | gpt-5.5>

Model selected:
<gpt-5.4 | gpt-5.5>

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
