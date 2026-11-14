---
name: repair-loop
description: Reproduce, isolate, fix, and regression-test one confirmed bug without widening the approved domain slice.
---

# repair-loop

## Invocation

This is a user-invoked repair entrypoint. Use it for a concrete bug, failing acceptance scenario, regression, performance failure, or blocking `$code-review` finding in an existing slice. It is not a route for new features or for silently finishing an incomplete design.

Read [the skill contract](../ddd-core/rules/skill-contract.md), [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), and the active slice's acceptance scenarios before editing. Redact secrets from commands, logs, requests, and captured artifacts.
Before editing, run the bundled read-only gate check for `--require repair`. A non-zero result is a hard stop; report its reason instead of repairing the ledger silently.

## Process

1. **Capture.** Record the active slice, expected behavior, actual behavior, trigger, environment, and the smallest evidence supplied by the user. For a performance failure, also capture the contract id/version, dataset digest and cardinality, database engine/version, query-plan evidence, concurrency, warmup, duration, p50/p95/p99, throughput, error/resource metrics, and the exact failed budget. If the report came from code review, preserve the finding id, axis, rule, and file evidence. If the report is ambiguous, ask exactly one question and stop.
2. **Feedback loop.** Call the model-invoked `feedback-loop` method to build and prove a red-capable signal, minimize the case, rank falsifiable hypotheses, instrument one variable at a time, and produce a regression result. When the signal is a test or harness, require a pristine-copy and behavior-relevant mutation check. For performance failures, keep the workload, query plan, and resource conditions fixed.
3. **Fix.** Apply the smallest change that restores the approved behavior after the loop returns usable evidence. If it needs a new actor, command, invariant, boundary, schema contract, or capability, stop and return to `ddd-core` for a new design gate.
4. **Gate and stop.** Run the red signal, focused slice checks, and affected acceptance scenarios. Persist `delivery: verified` when the failure is fixed, or `delivery: blocked` with the exact evidence when it is not. Any repair resets the review gate to `not_started`; a later explicit `$code-review` is required before the slice can be reset. Report the reproduction, hypothesis ranking, change, checks, and remaining uncertainty. Do not start the next feature.

The skill may record `start-repair` as internal bookkeeping before editing, then records `verify` or `block` after the regression result. Do not ask the user to run a separate start command or edit the gate field directly.

## Output contract

Return the active slice ID, failure evidence, reproduction command or test, minimized case, mutation-proof result (or why it is not applicable), hypothesis history, changed files, regression checks, remaining uncertainty, and ledger state.

## Hard stops

- Do not invoke `ddd-core`, `adapter-kit`, `delivery-loop`, or another skill automatically.
- Do not turn a bug report into a feature, redesign, cleanup, or future-capability implementation.
- Do not claim a fix without a repeatable red signal that goes green after the change.
- For a performance repair, do not loosen the budget or replace the database-native strategy without a new user-confirmed performance decision; compare the same workload and plan evidence before and after the fix.
- Stop when the active slice or expected behavior is unknown, when evidence is insufficient, or when the failure exposes a new domain decision.

## Canonical rules

- [Skill contract](../ddd-core/rules/skill-contract.md) (`ddd.skill-contract`)
- [Scope and future-capability rules](../ddd-core/rules/scope.md) (`ddd.scope`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [Gated lifecycle](../ddd-core/rules/lifecycle.md) (`ddd.lifecycle`)
