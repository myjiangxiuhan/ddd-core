---
name: adapter-kit
description: Map an approved domain contract to replaceable backend, database, transport, or UI conventions.
schema_version: "1"
---

# adapter-kit

## Trigger

Use only after the gates in `ddd.interaction`; read one selected, versioned profile only after that gate.

## Responsibilities

- Read the project stack configuration and selected profile, reusing existing repository conventions.
- Infer existing settings before asking; allow an explicit per-task profile override without changing defaults.
- Keep domain meaning independent of framework, database, transport, and UI; keep display wording at the presentation edge.
- Map only the approved slice, preserve core rules, and report unsupported capabilities or pending conventions.

## Output contract

Return the selected profile, adapter decisions, focused contract checks, one observable path for the approved slice, and any unsupported capability or pending convention.

## Hard stops

Apply `ddd.interaction` and `ddd.lifecycle` without local gate exceptions. Stop when the exact profile is missing. Do not add a generic abstraction without a second concrete consumer, pre-generate unused adapters, or add a cloud-drive adapter without a separate explicit slice approval.

## Canonical rules

- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
- [Four-stage lifecycle](../ddd-core/rules/lifecycle.md) (`ddd.lifecycle`)
- [Domain model](../ddd-core/rules/domain-model.md) (`ddd.domain-model`)
- [Profile schema](profiles/schema.md) (`adapter.profile`)
