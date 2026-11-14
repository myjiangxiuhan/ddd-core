# Workflow index

This repository defines a deliberately user-gated DDD workflow. The entrypoint skills are explicit-only; do not auto-chain them.

`domain-modeling` is the exception as a vocabulary layer: it may be applied beneath an active skill when a business term conflicts or needs sharpening, but it cannot advance gates or make a user decision.

- `ask-ddd`: route a request to one workflow and stop.
- `ddd-core`: interview the user, record scope and decisions, design one technology-neutral slice, and stop.
- `business-lab`: let the user investigate and draw the business mainline through one concrete question per turn; never complete the business model for them.
- `domain-modeling`: vocabulary layer that challenges ambiguous business terms and updates the canonical glossary only after user confirmation.
- `project-wayfinder`: map a large effort as named decisions with blockers before creating slices.
- `triage-loop`: classify raw incoming reports and produce an agent-ready brief.
- `research-loop`: collect primary-source evidence for one unresolved question.
- `oss-archaeology`: study one pinned open-source project and separate its facts from candidate rules for our domain.
- `prototype-loop`: answer one design question with a throwaway experiment.
- `performance-loop`: select a version-pinned database profile, generate bounded database-specific SQL, define and verify one slice performance contract, and obtain a separate user attestation for the reproducible metric baseline.
- `to-spec`: synthesize confirmed decisions into a reviewable handoff spec.
- `to-slices`: plan vertical slices and explicit blockers from a confirmed spec.
- `adapter-kit`: after slice approval, let the user select or confirm one exact technology profile; do not implement it.
- `ui-system`: define and confirm project tokens, themes, responsive layout, accessibility, and visual-state rules; do not implement them.
- `ui-practices`: collect version-pinned React, Vue, Angular, and UI-library guidance and confirm component-first practices; do not implement them.
- `ui-architecture`: collect primary-source UI-library evidence and confirm one component composition plan for a UI slice.
- `scaffold-kit`: inspect and explicitly apply one project-configured, `ng generate`-style UI or backend artifact generator; UI and backend use separate gate checks.
- `template-kit`: inspect pinned references and create or extract confirmed clean-room UI templates with provenance; do not copy source code.
- `delivery-loop`: after the required profile, contract, and (for database-backed slices) baseline-attestation gates, implement and verify one active slice, then stop.
- `repair-loop`: reproduce, fix, and regression-test one confirmed failure, then stop.
- `code-review`: review one verified fixed-point diff on separate Standards, Spec, DDD, UI, and Custom axes; never edit source.
- `retro-loop`: turn session failures into approved deterministic checks or rules.
- `rule-workbench`: maintain traceable records without changing gates implicitly.
- `approval-kit`: prepare and verify one detached user approval; never sign for the user or advance a gate by file editing.

For a target project, use `.ddd/workflow-state.json` as the gate ledger. A missing or contradictory ledger blocks downstream work. Each invocation may advance at most one gate transition; ordinary discovery asks the whole independent frontier, normally 1-4 questions, while `business-lab` uses one adaptive micro-question per turn. `user_decision`, `agent_recommendation`, `agent_inference`, and `pending` must stay distinct; the agent may propose options but never silently choose among material product or technology decisions. Every user transition must carry a detached approval credential signed with a user-owned private key outside the project and verified with an explicitly supplied trusted public key; never create `actor: user` or `user_decision` by editing JSON. Use the exact status words in `ddd-core/rules/keywords.md`.

Research is a separate evidence activity. An OSS or documentation study must stop after its cited note; it may not continue as a business interview or record research-session answers as product decisions. Start `$business-lab` or `$ddd-core` explicitly when the user wants to interpret evidence for the product.
