---
name: delivery-loop
description: Implement and verify one user-approved domain slice from the workflow ledger, then stop without choosing the next slice.
---

# delivery-loop

## Invocation

This is a user-invoked implementation entrypoint. Run it only after the user has explicitly approved the exact `active_slice` and the workflow ledger shows the required technology profile. It owns one delivery cycle and does not plan the product.

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), [codebase design vocabulary](../ddd-core/rules/codebase-design.md), `.ddd/GLOSSARY.md` or `.ddd/GLOSSARY-MAP.md`, and the source design before editing. Run `workflow_gate.py --state .ddd/workflow-state.json --require delivery` before editing. Read supporting database, performance, UI, and scaffold records when the active slice uses them; they are evidence and implementation inputs, not automatic approval ceremonies. State the active slice and the user-owned decisions you are implementing before changing files.

## Process

1. Verify `domain_design: confirmed`, `slice_approval: approved`, a non-null `active_slice`, and `technology_profile: selected`. An existing repository profile must first be explicitly confirmed by `$adapter-kit`, which records it in the ledger. If any field is missing, stop and report it.
2. Restate the approved behavior, acceptance scenarios, non-goals, pending decisions, and public seam under test. If the slice has persistence, use the selected database profile and any available workload or performance evidence; do not invent a budget or baseline. For Rust + Axum, restate the exact adapter profile's Axum/Tokio/driver/migration versions and use its Cargo validation command set; do not replace it with a convenient unpinned command. If the slice has a UI surface, use the confirmed UI records when present and state any remaining visual assumptions. Do not resolve a pending product decision inside implementation. If the seam is new or ambiguous, stop and return to discovery rather than inventing it.
3. Set `delivery: in_progress`, then use a red-green-refactor loop for the pure domain rule and its focused behavior check first.
4. Add only the ports, adapters, transport, UI, and persistence required for this active slice. Reuse the selected profile; do not introduce a second database, cache, provider, or framework because it may help a future capability.
5. Run focused checks and the active slice's acceptance scenarios. If a performance contract exists, run its metric test; if a database path exists, use the selected profile and capture query-plan evidence on the pinned engine/version. Keep verification local to the active slice; the separate `$code-review` entrypoint performs the independent review axes afterward.
6. Set `delivery: verified` when the focused checks and acceptance scenarios pass, or `delivery: blocked` with the exact failing evidence when they do not. Report changed files, checks, decisions honored, assumptions, risks, and blockers, then stop.

The skill records `start-delivery` as internal bookkeeping, then records `verify` or `block` after the checks. Do not ask the user to run a separate start command or edit the gate field directly.

## Output contract

Return the active slice ID, user-owned decisions honored, changed files, focused checks, acceptance-scenario results, UI-plan/scaffold contract when applicable, assumptions, risks, and ledger state. Tell the user that `$code-review` is a later explicit action; do not propose or start another slice in the same invocation.

## Hard stops

- Do not invoke `ddd-core`, `adapter-kit`, `repair-loop`, or another skill automatically.
- Stop before editing when the ledger is missing, the active slice is ambiguous, the profile is absent, or a pending domain decision affects the implementation.
- For a UI slice, use the confirmed UI records when they exist. If they do not exist, state the visual assumptions and keep the composition small; do not silently introduce a project-wide design system.
- For a persistence, SQL, migration, index, queue, or external-call slice, use an existing performance contract when present. If a new budget or database behavior is needed, pause and ask the user; do not manufacture a budget or create an approval ceremony for its absence.
- Stop before editing when the selected database profile is missing for a SQL operation, or when the profile file no longer validates. A profile ID on a command line is not a substitute for reading the profile.
- For Rust + Axum, stop before editing when the selected adapter profile's framework, runtime, driver, migration, or Cargo command versions are not pinned or when the project Cargo.lock disagrees with the profile; create a new explicit profile decision rather than silently upgrading a crate.
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
