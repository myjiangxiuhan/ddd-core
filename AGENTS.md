# Workflow index

This repository defines a deliberately user-gated DDD workflow. The entrypoint skills are explicit-only; do not auto-chain them.

- `ask-ddd`: route a request to one workflow and stop.
- `ddd-core`: interview the user, record scope and decisions, design one technology-neutral slice, and stop.
- `project-wayfinder`: map a large effort as named decisions with blockers before creating slices.
- `triage-loop`: classify raw incoming reports and produce an agent-ready brief.
- `research-loop`: collect primary-source evidence for one unresolved question.
- `prototype-loop`: answer one design question with a throwaway experiment.
- `to-spec`: synthesize confirmed decisions into a reviewable handoff spec.
- `to-slices`: plan vertical slices and explicit blockers from a confirmed spec.
- `adapter-kit`: after slice approval, let the user select or confirm one exact technology profile; do not implement it.
- `ui-architecture`: collect primary-source UI-library evidence and confirm one component composition plan for a UI slice.
- `scaffold-kit`: inspect and explicitly apply one project-configured, `ng generate`-style artifact generator.
- `delivery-loop`: after the profile gate, implement and verify one active slice, then stop.
- `repair-loop`: reproduce, fix, and regression-test one confirmed failure, then stop.
- `code-review`: review one verified fixed-point diff on separate Standards, Spec, DDD, UI, and Custom axes; never edit source.
- `retro-loop`: turn session failures into approved deterministic checks or rules.
- `rule-workbench`: maintain traceable records without changing gates implicitly.

For a target project, use `.ddd/workflow-state.json` as the gate ledger. A missing or contradictory ledger blocks downstream work. Each invocation may advance at most one gate transition; each discovery round asks the whole independent frontier, normally 1-4 questions. `user_decision`, `agent_recommendation`, `agent_inference`, and `pending` must stay distinct; the agent may propose options but never silently choose among material product or technology decisions. Use the exact status words in `ddd-core/rules/keywords.md`.
