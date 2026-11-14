---
name: delivery-loop
description: Implement and verify one user-approved domain slice from the workflow ledger, then stop without choosing the next slice.
---

# delivery-loop

## Invocation

This is a user-invoked implementation entrypoint. Run it only after the user has explicitly approved the exact `active_slice` and the workflow ledger shows the required technology profile. It owns one delivery cycle and does not plan the product.

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), [codebase design vocabulary](../ddd-core/rules/codebase-design.md), `.ddd/GLOSSARY.md` or `.ddd/GLOSSARY-MAP.md`, and the source design before editing. Run `workflow_gate.py --state .ddd/workflow-state.json --require delivery --trusted-public-key <user-trust-key>` before editing. For a persistence, SQL, migration, index, queue, or external-call slice, this check also requires the signed `database_profile` and `performance_contract` gates; read the selected profile file, confirmed `.ddd/performance/<slice-id>.yaml`, its database adaptation mapping, and the current baseline or measurement plan. For a UI slice, also read the confirmed `.ddd/ui-system.yaml`, `.ddd/ui-practices.yaml`, `.ddd/ui-plan.yaml`, and scaffold contract. State the active slice and the user-owned decisions you are implementing before changing files.
Before editing, run the bundled read-only gate check for `--require delivery`. A non-zero result is a hard stop; report its reason instead of repairing the ledger silently.

## Process

1. Verify `domain_design: confirmed`, `slice_approval: approved`, a non-null `active_slice`, and `technology_profile: selected`. An existing repository profile must first be explicitly confirmed by `$adapter-kit`, which records it in the ledger. If any field is missing, stop and report it.
2. Restate the approved behavior, acceptance scenarios, non-goals, pending decisions, and public seam under test. If the slice has persistence, restate the workload shape, p50/p95/p99 and throughput/error/resource budgets, query shapes, index/order and pagination strategy, transaction/lock scope, timeout, and selected database-native capabilities. If the slice has a UI surface, also restate the confirmed UI system, UI practices, `.ddd/ui-plan.yaml`, and scaffold contract. Do not resolve a pending product decision or UI practice inside implementation. If the seam is new or ambiguous, stop and return to discovery rather than inventing it.
3. Set `delivery: in_progress`, then use a red-green-refactor loop for the pure domain rule and its focused behavior check first.
4. Add only the ports, adapters, transport, UI, and persistence required for this active slice. Reuse the selected profile; do not introduce a second database, cache, provider, or framework because it may help a future capability.
5. Run focused checks, the active slice's acceptance scenarios, and the performance contract's metric test. For a database path, use only the selected profile, capture the query plan on the pinned engine/version, and compare a reproducible baseline with `performance-loop/scripts/compare_budget.py --state .ddd/workflow-state.json --trusted-public-key <user-trust-key>`. Keep this verification local to the active slice; the separate `$code-review` entrypoint performs the independent Standards, Spec, DDD, UI, Performance, and Custom review axes afterward.
6. Set `delivery: verified` when the focused checks and acceptance scenarios pass, or `delivery: blocked` with the exact failing evidence when they do not. Report changed files, checks, decisions honored, assumptions, risks, and blockers, then stop.

Use the bundled `workflow_gate.py --state .ddd/workflow-state.json` transitions for `start-delivery`, `verify`, or `block`; do not edit the gate field directly.

## Output contract

Return the active slice ID, user-owned decisions honored, changed files, focused checks, acceptance-scenario results, UI-plan/scaffold contract when applicable, assumptions, risks, and ledger state. Tell the user that `$code-review` is a later explicit action; do not propose or start another slice in the same invocation.

## Hard stops

- Do not invoke `ddd-core`, `adapter-kit`, `repair-loop`, or another skill automatically.
- Stop before editing when the ledger is missing, the active slice is ambiguous, the profile is absent, or a pending domain decision affects the implementation.
- For a UI slice, stop before editing when `ui_system` or `ui_practices` is not confirmed; do not invent a theme, layout, component wrapper, or framework pattern in delivery.
- For a persistence, SQL, migration, index, queue, or external-call slice, stop before editing when the performance contract is absent or not confirmed. Do not invent latency budgets, indexes, pagination, transaction scope, or a database-specific fallback in delivery.
- Stop before editing when the selected database profile is absent, changed after its signed selection, or does not match the performance contract. Passing a database profile ID to a helper command is not evidence of a workflow approval.
- Stop and return to `ddd-core` when implementation reveals a new actor, command, invariant, boundary, or future capability; do not decide it in code. A new UI component responsibility returns to `$ui-architecture` rather than being invented inline.
- Stop and route to `$domain-modeling` when implementation or tests expose an overloaded business term; do not silently introduce a second name.
- Do not implement deferred capabilities such as content deduplication, Redis indexing, sharing, or resumable upload unless a new slice is separately modeled and approved.
- Do not widen the slice or treat a green test as approval for the next change.

## Canonical rules

- [Scope and future-capability rules](../ddd-core/rules/scope.md) (`ddd.scope`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [Gated lifecycle](../ddd-core/rules/lifecycle.md) (`ddd.lifecycle`)
- [Domain model](../ddd-core/rules/domain-model.md) (`ddd.domain-model`)
- [Evidence](../ddd-core/rules/evidence.md) (`ddd.evidence`)
- [Codebase design vocabulary](../ddd-core/rules/codebase-design.md) (`ddd.codebase-design`)
- [Performance contract](../performance-loop/references/contract-schema.md) (`performance.contract`)
- [Database adaptation rules](../performance-loop/references/database-adaptation.md) (`performance.database-adaptation`)
