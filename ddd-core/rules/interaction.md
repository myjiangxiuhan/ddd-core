---
rule_version: "6"
id: ddd.interaction
---

# Lightweight interaction rules

The workflow ledger records where the work is. It is a coordination aid, not a second conversation. User-invoked skills are the only entrypoints that can start a workflow; model-invoked skills provide reusable methods inside the active entrypoint.

## Core pauses

Keep only the pauses that protect a material change:

1. **Business understanding** — the user supplies or confirms the business mainline when the domain is unclear.
2. **Slice design** — the user confirms the current technology-neutral slice and its boundaries.
3. **Technology choice** — the user explicitly chooses the application profile before implementation.
4. **Implementation and review** — the user explicitly invokes delivery, repair, or review.

Database profiles, performance contracts, templates, and baselines are supporting records. Their confirmed status and user evidence live in the record itself; a tool may bind a digest snapshot for collaboration, but it must not add a second approval transition. UI system/practice/plan records are the design artifacts for the slice; a UI tool reads the record itself rather than requiring a mirrored gate field or another top-level approval ceremony.

## Allowed movement

| Current situation | Explicit user action | Result |
| --- | --- | --- |
| missing or `new` ledger | invoke `$ddd-core` or `$business-lab` | create a scope or business draft |
| business draft | confirm or correct the mainline | mark the business record `confirmed` |
| domain draft | confirm or correct the slice design | mark `domain_design: confirmed` |
| confirmed design | name one slice and choose the application components | set `active_slice` and `technology_profile: selected` |
| selected profile | invoke `$delivery-loop` | set `delivery: in_progress` and implement one slice |
| delivery failure | invoke `$repair-loop` | reproduce and repair one confirmed failure |
| verified delivery | invoke `$code-review` | report standards/spec findings and set review status |

User decision transitions require explicit `--evidence`; mechanical transitions may use a concise generated history note. The evidence and resulting history entry stay in the project so collaborators can review them together. A workflow does not need a separate “start” transition before it records its first artifact.

## Rules

- User-invoked skills do not auto-chain another user-invoked skill. They state the next explicit command and stop.
- A model-invoked skill cannot make a material product or technology decision, write `user_decision`, or advance a workflow gate.
- Keep `user_decision`, `agent_recommendation`, `agent_inference`, and `pending` distinct.
- A draft, research note, test result, or green build is evidence; it is not a user decision unless the user says so.
- If the ledger is missing, malformed, or contradictory, report the exact blocker and stop. Do not repair it from inference.
- Do not introduce cryptographic approval, external trust directories, receipt chains, or private-key handoffs for ordinary workflow pauses. Use a project record, a concise evidence line, and the normal Git review history.
- Do not create a new ledger gate merely to enforce a skill-writing rule. Add one only for a real user-owned product, domain, technology, or safety decision.
