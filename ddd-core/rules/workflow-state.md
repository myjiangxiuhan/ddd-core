---
rule_version: "2"
id: ddd.workflow-state
---

# Workflow state ledger

Use `.ddd/workflow-state.json` as the durable control record for a project. It is a small planning artifact, not implementation output. Every downstream skill reads it before acting and writes the next state only after its own gate.

The bundled read-only checker can be run before a gated operation:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require delivery
```

Use `technology`, `delivery`, or `repair` for the corresponding entrypoint. A non-zero exit is a hard stop.

## Minimum shape

```json
{
  "schema_version": "1",
  "project": { "goal": "..." },
  "scope": {
    "current_slice_candidate": { "id": "...", "name": "..." },
    "deferred_capabilities": [
      { "id": "...", "description": "...", "status": "deferred", "evidence": "..." }
    ],
    "out_of_scope": ["..."]
  },
  "decisions": [
    { "id": "...", "question": "...", "status": "pending", "source": "pending", "answer": null, "evidence": null }
  ],
  "gates": {
    "phase": "discovery",
    "domain_design": "draft",
    "slice_approval": "pending",
    "technology_profile": "pending",
    "delivery": "not_started"
  },
  "active_slice": null
}
```

## State meanings

- `phase` is one of `discovery`, `domain_design`, `slice_approved`, `technology`, `delivery`, `verification`, or `repair`.
- `domain_design` is `draft` or `confirmed`.
- `slice_approval` is `pending` or `approved`.
- `technology_profile` is `pending` or `selected`.
- `delivery` is `not_started`, `in_progress`, `verified`, or `blocked`.
- `active_slice` is null until the user approves one named slice. Once set, its `id` and acceptance scenarios are immutable for that delivery cycle.

## Write rules

- `ddd-core` may create or update scope, decisions, domain design, and approval gates; it must not set `delivery: in_progress` or `technology_profile: selected` by inference.
- `adapter-kit` may set `technology_profile: selected` only after the user explicitly chooses or confirms the exact profile. It must not write implementation files.
- `delivery-loop` may set `delivery: in_progress` and later `verified` or `blocked` only for the existing `active_slice`.
- `repair-loop` may update the failure evidence and return the active slice to `verified` or `blocked`; it may not create a new feature or change the active slice.
- A missing, malformed, or contradictory ledger blocks work. Report the exact field and ask one question rather than repairing the state silently.
