---
rule_version: "7"
id: ddd.workflow-state
---

# Workflow state ledger

Use `.ddd/workflow-state.json` as the durable coordination record for a project. It records the current slice, decisions, supporting records, and delivery status. It does not replace the user's conversation.

The read-only checker remains available:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require delivery
```

A user decision transition uses the evidence visible in the current conversation:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --transition confirm-design --evidence "user confirmed the slice design"
```

There is no external approval path. The ledger records the user's evidence and the resulting transition so every collaborator can inspect the same project state.

## Minimum shape

```json
{
  "schema_version": "1",
  "control_mode": "human_led",
  "project": { "goal": "..." },
  "scope": {
    "current_slice_candidate": { "id": "...", "name": "..." },
    "deferred_capabilities": [],
    "out_of_scope": []
  },
  "decisions": [],
  "gates": {
    "phase": "discovery",
    "business_discovery": "not_started",
    "domain_design": "draft",
    "slice_approval": "pending",
    "technology_profile": "pending",
    "delivery": "not_started",
    "review": "not_started"
  },
  "technology_profile": null,
  "active_slice": null,
  "business_artifact": null
}
```

## State meanings

- `business_discovery` records whether the user has supplied a business mainline: `not_started`, `in_progress`, `draft`, or `confirmed`.
- `domain_design` is `draft` or `confirmed`.
- `slice_approval` is `pending` or `approved`; it identifies the current `active_slice`.
- `technology_profile` is `pending` or `selected`; its record names the exact application stack.
- `database_profile`, `performance_contract`, and `baseline` result are supporting records. UI foundation, practice, and plan files are the source of truth for visual boundaries; older `gates.ui_system`, `gates.ui_practices`, and `gates.ui_design` fields may remain as summaries but are not required when the records are present. Supporting records are validated when a tool uses them; they do not become separate workflow gates.
- `delivery` is `not_started`, `in_progress`, `verified`, or `blocked`.
- `review` is `not_started`, `passed`, or `blocked`.
- `history` records the transition, actor, and evidence. A user transition records `actor: user` from the explicit command; it does not claim identity beyond the project history.

## Write rules

- `$ddd-core` owns scope, decisions, domain design, and the active slice.
- `$business-lab` owns business observations and the user-authored mainline.
- `$adapter-kit` records one exact application technology profile.
- `$performance-loop` owns the database profile, performance contract, and baseline records when persistence evidence is needed. `$ui-system`, `$ui-practices`, `$ui-architecture`, and `$template-kit` own their supporting records. A supporting snapshot may be written mechanically after the record is confirmed; none of them silently starts delivery.
- `$delivery-loop` owns one active slice and its verification result.
- `$repair-loop` owns one confirmed failure and its regression evidence.
- `$code-review` is read-only and owns the review result.
- A missing or contradictory ledger blocks the owning skill. Do not create a new gate to hide the contradiction.
