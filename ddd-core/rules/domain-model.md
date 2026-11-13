---
rule_version: "2"
id: ddd.domain-model
---

# Domain model rules

The domain model is the smallest design supported by the available evidence for the current slice.

## Scope and output

- Extract domain facts, roles, commands, rules, states, events, external actions, boundaries, and the evidence boundary.
- Shape 2-4 acceptance scenarios during domain design.
- Keep canonical domain terms separate from customer-facing display terms.
- Use the confirmed term and context from `.ddd/GLOSSARY.md` or `.ddd/GLOSSARY-MAP.md`; challenge an overloaded or conflicting word before it enters a rule, scenario, interface, or test.
- Keep the current slice separate from `deferred_capabilities`; a deferred capability may be recorded with its evidence and open questions, but it is not part of the current design or implementation.

## Minimality and boundaries

- Do not add code, tables, APIs, UI, database/schema design, or technology choices to an ordinary-requirement response.
- Do not over-abstract, add defensive behavior without evidence, pre-generate future features, or widen the boundary of the current slice.
- Keep domain meaning independent of framework, database, transport, cache, storage provider, and UI conventions.
- When a future capability could constrain the current domain, record only the technology-neutral compatibility constraint and its evidence. For example, “same content may later be stored once” can be a pending content-identity constraint; choosing Redis or a hash-index schema belongs to a later adapter decision.
- A phrase such as “网盘” is a product boundary, not an implementation slice. Split it into one current command or minimal use case and record later capabilities such as content deduplication, indexing, sharing, or resumable upload as deferred until separately approved.

