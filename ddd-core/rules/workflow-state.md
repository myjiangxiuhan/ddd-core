---
rule_version: "3"
id: ddd.workflow-state
---

# Workflow state ledger

Use `.ddd/workflow-state.json` as the durable control record for a project. It is a small planning artifact, not implementation output. Every downstream skill reads it before acting and writes the next state only after its own gate.

The bundled read-only checker can be run before a gated operation:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require delivery
```

Use `business`, `technology`, `ui-design`, `scaffold`, `delivery`, `repair`, or `review` for the corresponding entrypoint. A non-zero exit is a hard stop.

Use the exact state vocabulary in [canonical workflow keywords](keywords.md). The ledger is intentionally boring: every change should be easy to audit from the actor, transition, and evidence.

The checker can also apply one transition atomically. Each transition needs evidence from the user's answer, a repository record, or a verification command:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --transition confirm-design --evidence "user confirmed the domain design"
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --transition approve-slice --slice-id file-entry-crud --evidence "user approved file-entry-crud"
```

Available transitions are `start-business-lab`, `record-mainline`, `confirm-mainline`, `record-decision`, `confirm-design`, `approve-slice`, `select-profile`, `draft-ui`, `confirm-ui`, `start-delivery`, `verify`, `block`, `start-repair`, `pass-review`, `block-review`, and `reset-slice`. It applies only one gate transition per invocation and rejects invalid predecessors; recording several answers from one discovery frontier is still one discovery round.

## Minimum shape

```json
{
  "schema_version": "1",
  "control_mode": "human_led",
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
    "business_discovery": "not_started",
    "domain_design": "draft",
    "slice_approval": "pending",
    "technology_profile": "pending",
    "ui_design": "not_started",
    "delivery": "not_started",
    "review": "not_started"
  },
  "technology_profile": null,
  "active_slice": null,
  "business_artifact": null
}
```

## State meanings

- `control_mode` is `human_led` by default. Use another mode only when the user explicitly changes the working agreement.
- `phase` is one of `discovery`, `business_discovery`, `domain_design`, `slice_approval`, `slice_approved`, `technology`, `ui_design`, `delivery`, `verification`, or `repair`.
- `business_discovery` is `not_started`, `in_progress`, `draft`, or `confirmed`. In `human_led` mode, the user must confirm the business mainline before the domain design can be confirmed.
- `domain_design` is `draft` or `confirmed`.
- `slice_approval` is `pending` or `approved`.
- `technology_profile` is `pending` or `selected`.
- `ui_design` is `not_started`, `draft`, or `confirmed`. It is optional for slices without a UI surface; when a UI plan exists, delivery must wait for `confirmed`.
- `delivery` is `not_started`, `in_progress`, `verified`, or `blocked`.
- `review` is `not_started`, `passed`, or `blocked`. A blocked review keeps the delivery verified until a later repair explicitly starts.
- `active_slice` is null until the user approves one named slice. Once set, its `id` and acceptance scenarios are immutable for that delivery cycle.
- `business_artifact` points to the user-editable business mainline record; it is evidence, not an implementation plan.

## Write rules

- `ddd-core` may create or update scope, decisions, domain design, and approval gates; it must not set `delivery: in_progress` or `technology_profile: selected` by inference.
- `business-lab` may record business observations and the path to a user-authored mainline; only a separate user confirmation may set `business_discovery: confirmed`.
- `domain-modeling` may update canonical vocabulary after the user confirms a term; it never advances a gate or substitutes for a business-mainline confirmation.
- `adapter-kit` may set `technology_profile: selected` only after the user explicitly chooses or confirms the exact profile. It must not write implementation files.
- `ui-architecture` may create the UI catalog and draft plan, then set `ui_design: draft`; only a separate user confirmation may set `ui_design: confirmed`.
- `scaffold-kit` may write only the files shown in a dry-run from a configured generator after `ui_design: confirmed`; it must not change gate fields or run arbitrary commands.
- `delivery-loop` may set `delivery: in_progress` and later `verified` or `blocked` only for the existing `active_slice`.
- `repair-loop` may update the failure evidence and return the active slice to `verified` or `blocked`; it may not create a new feature or change the active slice.
- `code-review` may set `review: passed` or `review: blocked` after reviewing the verified active-slice diff; it must not edit source files or start repair.
- A missing, malformed, or contradictory ledger blocks work. Report the exact field and ask one question rather than repairing the state silently.
