---
name: repair-loop
description: Reproduce, isolate, fix, and regression-test one confirmed bug without widening the approved domain slice.
---

# repair-loop

## Invocation

This is a user-invoked repair entrypoint. Use it for a concrete bug, failing acceptance scenario, regression, performance failure, or blocking `$code-review` finding in an existing slice. It is not a route for new features or for silently finishing an incomplete design.

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), and the active slice's acceptance scenarios before editing. Redact secrets from commands, logs, requests, and captured artifacts.
Before editing, run the bundled read-only gate check for `--require repair`. A non-zero result is a hard stop; report its reason instead of repairing the ledger silently.

## Process

1. **Capture.** Record the active slice, expected behavior, actual behavior, trigger, environment, and the smallest evidence supplied by the user. For a performance failure, also capture the contract id/version, dataset digest and cardinality, database engine/version, query-plan evidence, concurrency, warmup, duration, p50/p95/p99, throughput, error/resource metrics, and the exact failed budget. If the report came from code review, preserve the finding id, axis, rule, and file evidence. If the report is ambiguous, ask exactly one question and stop.
2. **Red.** Build a repeatable failing signal at the highest existing public seam: a test, HTTP/CLI harness, browser check, trace replay, or minimal harness. Do not start by reading random code or changing implementation.
   When the signal is a test or harness, prove that it can detect the defect: run it against a pristine copy and a forced, behavior-relevant mutation. If the mutation still passes, treat the red signal as untrusted and repair the evidence or stop before editing production code.
3. **Minimize.** Reduce the reproduction to the smallest input and preserve the failing artifact. Mark the result as `confirmed` only when it reliably fails.
4. **Hypothesize.** Generate 2-4 ranked, falsifiable causes and show the prediction for each. Ask the user to re-rank or rule out one before instrumenting. Keep product decisions `pending`; do not let the first plausible cause become the fix plan.
5. **Instrument.** Run one targeted experiment at a time, tied to a hypothesis. Record what the user decision or evidence changed.
6. **Fix.** Make the smallest change that restores the approved behavior. If the fix needs a new actor, command, invariant, boundary, schema contract, or capability, stop and return to `ddd-core` for a new design gate.
7. **Regression.** Run the red signal, the focused slice checks, and the affected acceptance scenarios. Add a regression test at the agreed public seam when the seam is stable.
8. **Stop.** Persist `delivery: verified` when the failure is fixed, or `delivery: blocked` with the exact evidence when it is not. Any repair resets the review gate to `not_started`; a later explicit `$code-review` is required before the slice can be reset. Report the reproduction, hypothesis ranking, change, checks, and remaining uncertainty. Do not start the next feature.

Use `workflow_gate.py --state .ddd/workflow-state.json --transition start-repair` before the repair and `verify` or `block` after the regression result. Do not edit the gate field directly.

## Output contract

Return the active slice ID, failure evidence, reproduction command or test, minimized case, mutation-proof result (or why it is not applicable), hypothesis history, changed files, regression checks, remaining uncertainty, and ledger state.

## Hard stops

- Do not invoke `ddd-core`, `adapter-kit`, `delivery-loop`, or another skill automatically.
- Do not turn a bug report into a feature, redesign, cleanup, or future-capability implementation.
- Do not claim a fix without a repeatable red signal that goes green after the change.
- For a performance repair, do not loosen the budget or replace the database-native strategy without a new user-confirmed performance decision; compare the same workload and plan evidence before and after the fix.
- Stop when the active slice or expected behavior is unknown, when evidence is insufficient, or when the failure exposes a new domain decision.

## Canonical rules

- [Scope and future-capability rules](../ddd-core/rules/scope.md) (`ddd.scope`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [Gated lifecycle](../ddd-core/rules/lifecycle.md) (`ddd.lifecycle`)
