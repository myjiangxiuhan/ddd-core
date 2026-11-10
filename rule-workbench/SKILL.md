---
name: rule-workbench
description: Maintain the smallest traceable set of project rules, terms, decisions, and workflow records.
schema_version: "1"
---

# rule-workbench

## Trigger

Use when maintaining project rules, terms, decisions, or workflow records.

## Responsibilities

- Link each rule to one context, source, stable ID, scope, and status.
- Keep AGENTS.md as a short index and one canonical glossary; do not duplicate facts across documents.
- Separate canonical terms from customer display mappings and preserve old IDs when meaning changes.
- Use an ADR only for an irreversible, cross-boundary, or surprising decision.

## Output contract

Report pure rule checks, conflicts, missing evidence, assumptions, pending decisions, and any changed rule records.

## Hard stops

Do not promote one-off code or feedback into a universal rule without evidence. Keep each rule in one canonical source and preserve existing meaning unless an explicit decision changes it.

## Canonical rules

- [Evidence](../ddd-core/rules/evidence.md) (`ddd.evidence`)
- [Domain model](../ddd-core/rules/domain-model.md) (`ddd.domain-model`)
