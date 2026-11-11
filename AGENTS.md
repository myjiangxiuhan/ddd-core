# Workflow index

This repository defines a deliberately user-gated DDD workflow. The entrypoint skills are explicit-only; do not auto-chain them.

- `ddd-core`: interview the user, record scope and decisions, design one technology-neutral slice, and stop.
- `adapter-kit`: after slice approval, let the user select or confirm one exact technology profile; do not implement it.
- `delivery-loop`: after the profile gate, implement and verify one active slice, then stop.
- `repair-loop`: reproduce, fix, and regression-test one confirmed failure, then stop.
- `rule-workbench`: maintain traceable records without changing gates implicitly.

For a target project, use `.ddd/workflow-state.json` as the gate ledger. A missing or contradictory ledger blocks downstream work. Each invocation may advance at most one state transition and ask at most one question. `user_decision`, `agent_inference`, and `pending` must stay distinct; the agent may propose options but never silently choose among material product or technology decisions.
