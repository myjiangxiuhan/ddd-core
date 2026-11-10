---
name: delivery-loop
description: Implement and verify one approved domain slice without widening scope.
schema_version: "1"
---

# delivery-loop

## Trigger

Use after the gates in `ddd.interaction` for one approved slice.

## Responsibilities

- Implement the approved slice only: its input/command, pure domain rule, required port, adapter, and observable result.
- Build and test the pure domain model/rule before ports, adapters, or integration work.
- Compare the result with the source rules, acceptance scenarios, and selected profile.

## Output contract

Report changed files, focused checks, acceptance-scenario results, assumptions, risks, and any blocker.

## Hard stops

Apply `ddd.interaction` and `ddd.lifecycle` without local gate exceptions. Stop on a new boundary, unresolved rule conflict, or missing adapter convention.

## Canonical rules

- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [Four-stage lifecycle](../ddd-core/rules/lifecycle.md) (`ddd.lifecycle`)
- [Domain model](../ddd-core/rules/domain-model.md) (`ddd.domain-model`)
- [Evidence](../ddd-core/rules/evidence.md) (`ddd.evidence`)
