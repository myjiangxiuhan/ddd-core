---
rule_version: "1"
id: business-lab.review-checklist
---

# Business artifact review checklist

This checklist finds missing evidence and contradictions. It cannot prove that a business model is complete. The agent reviews the user's artifact; it does not fill missing cells with plausible rules.

## Coverage dimensions

| id | dimension | inspect |
| --- | --- | --- |
| R1 | scenario | one concrete case, scope, and evidence source |
| R2 | trigger | the real event that starts the case |
| R3 | promise | observable completion and who confirms it |
| R4 | actors | initiator, executor, beneficiary, authority, and affected business object |
| R5 | mainline | 5-9 non-skippable business changes in order |
| R6 | vocabulary | canonical terms, aliases, overloaded words, and context |
| R7 | state/event | conditions versus changes that already happened |
| R8 | rules | permissions, invariants, decisions, and timing constraints |
| R9 | branches | refusal, expiry, duplicate, cancellation, retry, compensation, and human judgement |
| R10 | lifecycle | create, change, archive/delete, restore, ownership, visibility, and retention |
| R11 | evidence | the person, record, observation, or user decision supporting each material claim |

## Review output

For every dimension, return one of `confirmed`, `pending`, `contradictory`, or `not_applicable`:

| id | observed user evidence | status | missing or conflicting evidence | one question only if requested |
| --- | --- | --- | --- | --- |
| R1 |  | pending |  |  |

The review must preserve the user's wording and card IDs. A missing dimension is a question for the user, not an agent recommendation. If several dimensions are missing, show the list and let the user choose the next one.

## Completeness boundary

The artifact is ready for `record-mainline` only when the user has reviewed the checklist, every material dimension is `confirmed` or explicitly `deferred`, and contradictions have a named owner or next evidence source. This is a handoff condition, not a claim that every future business rule is known.
