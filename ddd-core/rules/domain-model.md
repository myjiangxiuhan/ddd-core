---
rule_version: "1"
id: ddd.domain-model
---

# Domain model rules

The domain model is the smallest design supported by the available evidence.

## Scope and output

- Extract domain facts, roles, commands, rules, states, events, external actions, boundaries, and the evidence boundary.
- Shape 2-4 acceptance scenarios during domain design.
- Keep canonical domain terms separate from customer-facing display terms.

## Minimality and boundaries

- Do not add code, tables, APIs, UI, database/schema design, or technology choices to an ordinary-requirement response.
- Do not over-abstract, add defensive behavior without evidence, pre-generate future features, or widen the boundary of the current slice.
- Keep domain meaning independent of framework, database, transport, and UI conventions.

