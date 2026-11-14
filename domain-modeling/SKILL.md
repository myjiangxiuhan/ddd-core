---
name: domain-modeling
description: Sharpen the project's business language while designing by challenging ambiguous terms, testing relationships with concrete scenarios, and updating the canonical glossary after user confirmation.
---

# domain-modeling

This is a vocabulary layer, not a feature-planning or implementation entrypoint. It may run beneath `business-lab`, `ddd-core`, `triage-loop`, `to-spec`, `to-slices`, `ui-system`, `ui-practices`, `ui-architecture`, `performance-loop`, `delivery-loop`, and `code-review` when language is the problem. It does not advance workflow gates.

## Canonical records

Read [glossary format](references/GLOSSARY-FORMAT.md) and [record layout](../rule-workbench/references/record-layout.md).

- A single-context project keeps its canonical language in `.ddd/GLOSSARY.md`.
- A multi-context project keeps `.ddd/GLOSSARY-MAP.md`, which points to one `GLOSSARY.md` per context.
- `.ddd/business/term-candidates.md` may contain observations that have not been confirmed. It is not a canonical glossary.
- `.ddd/adr/` records a hard-to-reverse, surprising, trade-off-driven decision; it does not hold ordinary term definitions.

The canonical term is the one the people doing the business use and the user confirms. Code names, UI labels, storage names, and translations may be mapped to it, but they do not silently replace it.

## When to act

Apply this layer when:

- the same word appears to mean two different things;
- different words may mean the same business concept;
- a word is vague, overloaded, or imported from technology;
- a user changes a definition, relationship, actor, or state;
- a spec, test, UI, or code review uses a term that conflicts with the glossary.

Do not interrupt ordinary work for generic programming words. Only domain-relevant words belong here.

## Process

1. Read the nearest glossary or glossary map before repeating a term.
2. Quote the conflicting phrase and identify the context. Say what the glossary currently means and what the new phrase appears to mean.
3. Ask one precise question with concrete scenarios. For example: “When you say `account`, do you mean the person who signs in, the organization that owns storage, or the billing relationship?”
4. Keep the result as `pending` or `agent_recommendation` until the user confirms or corrects it. A recommendation can suggest a canonical term, but it never promotes itself.
5. Stress-test the relationship with one or two concrete scenarios: who can create it, who can change it, what happens after cancellation, and whether two records can coexist.
6. Once the user resolves the term, update `.ddd/GLOSSARY.md` immediately with the definition, aliases, context, examples, source, and status. Preserve the stable term ID when its meaning evolves.
7. If the change is hard to reverse, surprising without context, and the result of a real trade-off, offer an ADR. Otherwise keep it in the glossary and decision register.

## Language rules

- Define what a thing **is**, in one sentence. Do not define it by its database table, API, React component, or implementation.
- Use one canonical term for one meaning within a context. Record aliases to avoid, but keep historical or customer-facing names in the mapping.
- Do not force one global word across contexts when the people use the same word differently. Put the distinction in `GLOSSARY-MAP.md` and name the context every time.
- Keep business terms, display terms, and technical terms in separate columns.
- A state name describes a business condition; an event describes a business change that has already happened; a command describes an intention or request. Do not use them interchangeably.
- If the user says “system”, “data”, “normal”, “done”, or “failed”, ask what business actor, record, observable change, or consequence they mean.
- Do not create a domain term for a module, class, endpoint, table, cache key, or framework primitive unless the business actually uses that concept.

## Output contract

Return the term under discussion, current glossary meaning, competing meanings, context, one concrete scenario, the user's decision, aliases to avoid, evidence, and the exact record updated. If unresolved, leave it `pending` and state one next question. Never silently rename the user's language.

## Hard stops

- Do not invent a canonical term because it sounds cleaner.
- Do not edit implementation, specs, tests, UI labels, or APIs to match a glossary entry without a later explicit workflow step.
- Do not batch unresolved words into a glossary after the session; resolve and record them inline.
- Do not merge context-specific meanings just to make the glossary shorter.

## Canonical rules

- [Glossary format](references/GLOSSARY-FORMAT.md) (`domain-modeling.glossary`)
- [Human-led business investigation](../business-lab/SKILL.md) (`business-lab`)
- [Domain model rules](../ddd-core/rules/domain-model.md) (`ddd.domain-model`)
- [Evidence rules](../ddd-core/rules/evidence.md) (`ddd.evidence`)
