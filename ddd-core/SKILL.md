---
name: ddd-core
description: Turn a plain-language requirement into the smallest evidence-backed DDD design before any implementation.
schema_version: "1"
---

# ddd-core

## Trigger

Use for an ordinary requirement or a request to design a domain slice. Start here before implementation.

## Responsibilities

- Produce the domain understanding and the smallest domain design.
- Keep the response evidence-backed and independent of technology choices.

## Output contract

Return the domain facts, roles, commands, rules, states, events, external actions, boundaries, evidence boundary, and (during design) 2-4 acceptance scenarios. Keep an unconfirmed design marked `draft`.

## Hard stops

Apply `ddd.interaction` and `ddd.lifecycle` without local gate exceptions.

## Canonical rules

- [Domain model](rules/domain-model.md) (`ddd.domain-model`)
- [Evidence](rules/evidence.md) (`ddd.evidence`)
- [Interaction and gates](rules/interaction.md) (`ddd.interaction`)
- [Four-stage lifecycle](rules/lifecycle.md) (`ddd.lifecycle`)
