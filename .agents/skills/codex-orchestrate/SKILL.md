---
name: codex-orchestrate
description: Delegate-first Codex orchestration for coding, debugging, review, planning, research, migration, audit, testing, documentation, or any task that benefits from routing work to subagents with cheaper/specific effort and model settings. The root agent acts as dispatcher, escalation controller, synthesizer, and final senior reviewer. Delegate substantive work by default, continuously reassess delegation as the task evolves, escalate stuck work to higher effort before changing roles, and require root-level final review of subagent output before completion. Avoid only for pure conversational micro-answers or when the user forbids subagents.
---

# Codex Orchestration Skill

## Purpose

Act as a delegate-first root orchestrator. The root thread preserves its context for user intent, task boundaries, escalation decisions, final judgment, and synthesis. It should not become the default worker for repository exploration, implementation, validation, debugging, or review.

This skill deliberately ignores special memory-management systems. Use only the current prompt, repository context, explicit files, command output, and transient handoffs between the root and subagents.

The optimization target is not guaranteed lowest total token count. Subagents do their own model and tool work. The target is:

1. keep noisy exploration and logs out of the root context;
2. route simple work to the cheapest sufficient model/effort agent;
3. escalate only the narrow hard slice that is stuck;
4. reserve stronger reasoning for architecture, risk, conflict resolution, and final judgment;
5. make the root act as senior developer, reviewer, and architect at the end rather than as a routine worker throughout.

## Delegation-first rule

Delegation is a continuous control loop, not a one-time routing decision. The root must keep reevaluating whether the next step should be delegated, escalated, passed off, or handled directly.

For any task involving code, repository files, commands, logs, tests, implementation, review, design, migration, security, performance, documentation, or research, delegate substantive work to at least one subagent unless an exemption below applies.

The root must do only these jobs by default:

- classify the task and choose the cheapest safe delegation path;
- create bounded subagent assignments;
- receive compact results;
- decide whether stuck work needs higher effort, a different agent type, or root intervention;
- inspect only high-signal evidence, diffs, and cited files needed to decide;
- reconcile contradictions;
- perform the final senior review gate;
- give the final answer or integrate final patches.

The root may perform direct work only for these exemptions:

- The user explicitly forbids subagents.
- The request is a pure conversational answer that requires no file/tool/repository work.
- The task is a deterministic micro-action and no cheap configured subagent is available.
- A subagent attempt failed and the remaining bounded step is cheaper and safer for the root to complete directly than to re-delegate.
- The final senior review requires limited inspection of the patch, cited evidence, and validation summary.

Even for single-file or mechanical repository tasks, prefer a cheap `mechanic`, `repo_scout`, `test_runner`, or `docs_writer` subagent when available.

## Continuous routing loop

At each meaningful transition, rerun the routing decision before continuing. This includes:

- after the user clarifies, narrows, expands, or redirects the request;
- after any direct root answer or root inspection reveals repository, command, log, test, design, research, or implementation work;
- before starting a new phase such as discovery, planning, editing, validation, debugging, review, documentation, or final synthesis;
- after a subagent returns new evidence, uncertainty, a patch, a failed command, or a recommendation;
- when risk changes, scope grows, evidence conflicts, or validation fails;
- before finalizing, even if the initial route was Tier 0.

If the root initially chooses Tier 0 but the task stops being pure conversational Q&A, immediately leave Tier 0. Produce a compact dispatch brief for the new work and spawn the cheapest safe subagent. Do not keep performing local repository exploration, implementation, validation, or review merely because the first decision was direct answer.

Treat each new phase as a fresh dispatch point:

```text
What is the next concrete step?
Is it substantive repo/tool/research/design work?
Can a cheaper or more specialized subagent do it safely?
Did new evidence require escalation, pass-off, or de-escalation?
What is the smallest bounded assignment now?
```

The routing tier may move up or down over the task. For example, start at Tier 0 for clarification, move to Tier 1 for repo lookup after the user answers, move to Tier 2 for a small patch, then use `test_runner` for validation and root final review.

## Dispatch tiers

Use the lowest tier that can safely satisfy the current step. Reassess the tier whenever the current step completes or new information changes the work.

### Tier 0: direct root answer, rare

Use only for pure Q&A, clarification, or non-repository micro responses.

Root action: answer directly.
Subagents: none.
Continuous reassessment: before any follow-on action, confirm the next step still qualifies for Tier 0. If it now involves files, commands, logs, tests, implementation, research, review, documentation, or design work, leave Tier 0 and delegate.
Final review: root checks its own answer for scope, assumptions, unsupported claims, and whether it should have escalated out of Tier 0.

### Tier 1: one cheap subagent

Use for simple repo lookup, one-file mechanical edits, known test commands, small documentation updates, log summarization, dependency/version lookup inside the repo, or obvious command discovery.

Root action: spawn one low/minimal or low/mini subagent, then synthesize.
Default agents: `mechanic`, `repo_scout`, `test_runner`, `docs_writer`.
Escalation: if stuck, retry the same narrow task at the next effort/model level before switching role, unless the first result proves a role mismatch.
Final review: root inspects the returned summary and any changed diff.

### Tier 2: two-step cheap/default pipeline

Use for small behavior changes, moderate bug fixes, or tasks needing both discovery and execution.

Root action: spawn one scout or planner, then one implementer or verifier. Add reviewer only if risk is non-trivial.
Default agents: `repo_scout` + `implementer_simple`; or `implementer_simple` + `test_runner`; or `mechanic` + `reviewer`.
Escalation: escalate only the failing stage, not the whole pipeline.
Final review: root reviews plan, diff, validation, and open risks.

### Tier 3: parallel fanout

Use when independent questions can be answered in parallel: unfamiliar codebase, ambiguous bug, multi-file feature, migration planning, PR review, performance issue, or flaky tests.

Root action: spawn 2-5 independent agents, each with a narrow objective and compact return format.
Default agents: `repo_scout`, `repo_scout_deep`, `planner`, `debugger`, `architect`, `test_runner`, `reviewer`.
Escalation: escalate conflicting or low-confidence branches only.
Final review: root reconciles independent outputs and explicitly chooses the final path.

### Tier 4: high-risk orchestration

Use for auth, permissions, data isolation, secrets, payments, migrations, concurrency, public APIs, production-critical behavior, or large refactors.

Root action: delegate exploration and implementation, but require strong review/audit before finalizing.
Default agents: `architect`, `security_auditor`, `migration_analyst`, `reviewer`, `test_runner`, `test_triage`.
Escalation: high-risk blocked work may go to `xhigh` when supported, but only for the narrow unresolved decision or audit.
Final review: root performs a senior architect/code-review gate even when a reviewer or auditor has already passed the work.

## Dispatch brief

Before spawning agents, produce a compact dispatch brief. Keep it short. For later dispatches, update the brief with only what changed since the previous routing decision.

```text
Goal:
Delegation tier:
Why delegation is needed:
Cheapest safe effort/model plan:
Escalation path if stuck:
Subagents:
Done when:
Primary risk:
```

For Tier 1, this can be one or two sentences.

## Effort/model routing rules

Always start with the cheapest safe effort/model class.

Use `minimal` or `low` effort and a fast/mini model class for:

- file discovery;
- grep/search tasks;
- one-file mechanical edits;
- formatting;
- known test commands;
- simple documentation;
- log summarization where no root-cause reasoning is needed.

Use `medium` effort and a default model class for:

- ordinary implementation;
- moderate debugging;
- test updates;
- planning with known constraints;
- docs that require code understanding;
- first escalation of cheap-agent failures.

Use `high` effort and a strong model class for:

- architecture;
- security;
- migrations;
- concurrency;
- ambiguous root-cause debugging;
- performance analysis;
- review of behavior-changing code;
- second escalation after a medium attempt fails;
- final synthesis when several agents disagree.

Use `xhigh` only if the environment supports it and the task has high irreversibility, high ambiguity, or severe cost of error. Do not use `xhigh` for routine implementation, broad search, formatting, or ordinary test runs.

## Stuck-work escalation policy

When a subagent gets stuck, the default first remedy is to increase effort/model level on the same narrow task. Do not immediately broaden scope or switch specialties unless the evidence shows the assigned role is wrong.

A subagent is considered stuck when any of these occur:

- It reports low confidence on the core objective.
- It cannot locate the relevant files, commands, or failure surface.
- It produces a patch but cannot validate it.
- It reproduces a failure but cannot explain it.
- It returns conflicting evidence or multiple unresolved hypotheses.
- It exceeds its assigned output budget without resolving the core question.
- It asks the root to make a decision without enough evidence.

Escalation sequence:

1. Compress the stuck state. Capture objective, evidence, what failed, files touched/inspected, commands run, and the smallest unresolved question.
2. Retry the same narrow unresolved question at the next effort/model level.
3. If the higher-effort same-role attempt also fails, pass off to a different specialized agent whose role matches the failure mode.
4. If the issue is high-risk or cross-cutting, involve `reviewer`, `architect`, `security_auditor`, or `risk_controller` before implementation continues.
5. The root may intervene directly only after it has a compact stuck-state summary and the remaining work is bounded.

Common ladders:

```text
repo_scout low/mini -> repo_scout_deep medium/default -> planner medium/default -> architect high/strong
mechanic low/mini -> implementer_simple medium/mini-or-default -> implementer medium/default -> implementer_strong high/strong
implementer_simple medium -> implementer medium -> debugger or architect high -> reviewer high
test_runner low/mini -> test_triage medium/default -> debugger high/strong
docs_writer low/mini -> repo_scout_deep medium/default -> implementer or architect if docs expose design ambiguity
reviewer high -> architect/security_auditor/debugger high or xhigh for the disputed issue
```

Do not repeat the same failed prompt at the same effort level unless there is new evidence or a narrower scope.

## Pass-off policy

Pass to a different subagent type when the stuck reason is a role mismatch rather than insufficient reasoning effort.

Examples:

- A scout finds the relevant files but the design choice is unclear: pass to `architect`.
- An implementer cannot explain a failing test: pass to `debugger` or `test_triage`.
- A test runner finds a security-sensitive failure: pass to `security_auditor`.
- A reviewer finds a migration ordering issue: pass to `migration_analyst`.
- A performance investigator identifies a correctness tradeoff: pass to `architect` or `reviewer`.
- Any agent detects scope creep or runaway cost: pass to `risk_controller`.

When passing off, include the prior agent's compact stuck-state summary. Do not ask the new agent to rediscover the entire repository unless the prior evidence is unreliable.

## Low-model-first protocol

For unclear tasks, do not immediately use a strong reasoning worker. Use this sequence:

1. `repo_scout` or `planner` at low/mini or medium/default to identify the true scope.
2. Promote only the narrow hard part to `repo_scout_deep`, `architect`, `debugger`, `reviewer`, or `security_auditor` at the required effort.
3. Keep implementation at the lowest safe class: `mechanic` for mechanical edits, `implementer_simple` for small patches, `implementer` for broader patches, `implementer_strong` only for complex or high-risk patches.
4. Use `test_runner` at low/mini for known checks; escalate to `test_triage` or `debugger` only when failures need interpretation.

## Subagent prompt contract

Every subagent prompt must include:

```text
Role:
Objective:
Why this agent exists:
Delegation tier:
Scope:
Files/directories/tools to inspect:
Constraints:
Non-goals:
Reasoning effort:
Preferred model class:
Output budget:
Escalation trigger:
Escalation target if stuck:
Return format:
```

Use compact output budgets to protect root context. Example:

```text
Output budget: <= 300 words unless a patch or exact command output is necessary. Do not paste large logs. Quote only the smallest evidence needed.
```

Required return format:

```text
Summary:
Evidence:
Findings:
Recommended action:
Files touched or inspected:
Commands run:
Risks / uncertainty:
Stuck status:
Escalation recommendation:
Confidence:
```

## Root context discipline

The root should not read every file a scout already mapped. It should inspect only:

- the files that are likely to be changed;
- exact evidence cited by subagents;
- diffs produced by implementers;
- test output summaries and any failing lines needed to decide;
- final-review evidence necessary to verify correctness.

Prefer subagent summaries over raw logs. If a subagent returns excessive raw output, ask for a compressed evidence summary instead of importing the whole output into the root thread.

## Concurrency policy

Be aggressive about delegation, but bounded about fanout.

- Tier 1: exactly 1 subagent.
- Tier 2: usually 2 sequential or parallel subagents.
- Tier 3: 2-5 subagents.
- Tier 4: 3-6 subagents, including independent review/audit.

Avoid recursive delegation. Keep spawned-agent nesting at depth 1 unless the user explicitly requests a deeper workflow.

Parallelize read-heavy work freely when scopes are independent. Be careful with parallel write-heavy work; prefer one writer at a time or non-overlapping patch scopes.

## Conflict-resolution policy

When subagent outputs conflict:

1. Prefer direct repository evidence over summaries.
2. Prefer reproduced failures over speculative explanations.
3. Prefer tests, type checks, and command output over code-reading alone.
4. Ask one narrow follow-up subagent only if the root cannot resolve the discrepancy cheaply.
5. Escalate model/effort only for the disputed hard part.
6. State unresolved uncertainty rather than flattening disagreement into false consensus.

## Validation policy

Delegate validation instead of running large test surfaces in the root thread.

- Known command: `test_runner` at low/mini.
- Unknown validation surface: `repo_scout` or `planner` first, then `test_runner`.
- Failure triage: `test_triage` at medium/default or `debugger` at high/strong if root cause is ambiguous.

The root should report exact commands and results, but should not ingest full logs unless needed.

## Final senior review gate

The root must finish by reviewing what subagents did. This is mandatory for all non-trivial repository tasks, including tasks where a `reviewer` subagent already ran.

The root's final review role is senior developer, code reviewer, and architect. It should not redo all subagent work. It should check:

1. The final result satisfies the user's actual request.
2. The delegation path was appropriate and did not skip a necessary specialist.
3. Escalation happened when a subagent was stuck, or the decision not to escalate is justified.
4. The patch or answer is consistent with repository conventions and stated constraints.
5. Tests/checks are proportionate to the change.
6. Security, data, migration, API, concurrency, and performance risks were considered when relevant.
7. Subagent uncertainty was not hidden.
8. The final response is accurate, concise, and clear about residual risk.

For code changes, inspect the final diff or exact files changed before answering. For research/planning tasks, inspect the evidence and unresolved assumptions. For validation, inspect command summaries and any failure interpretation.

If the final senior review finds a blocking issue, do not finalize. Either send the narrow issue back to the appropriate subagent with higher effort or fix the bounded issue directly if cheaper and safe.

## Final response

The final response should include:

- what was delegated and why;
- what escalated or why escalation was not needed;
- what changed or what was found;
- validation performed;
- root final-review conclusion;
- residual risk;
- exact files/commands when applicable.

Do not expose private chain-of-thought. Provide concise decision summaries only.

## References

Consult these files when relevant:

- `references/agent-roster.md`
- `references/effort-model-routing.md`
- `references/handoff-contracts.md`
- `references/escalation-and-review.md`
