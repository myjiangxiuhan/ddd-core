# Workflow index

This repository defines a deliberately user-led DDD workflow. User-invoked entrypoint skills are explicit-only; do not auto-chain them. Reusable model-invoked skills may run beneath an active entrypoint, but they cannot make a user decision or advance a core gate.

`domain-modeling`, `grilling`, and `feedback-loop` are model-invoked layers. They may be applied beneath an active skill for vocabulary, decision-frontier, or failure-feedback work, but they cannot advance core gates or make a user decision.

## Skill design contract

Every skill must follow [the skill contract](ddd-core/rules/skill-contract.md). Keep one skill responsible for one bounded outcome and make its trigger, ownership boundary, inputs, process, stop condition, output, and exact next action visible. Put long examples, schemas, rationale, and command catalogs in `rules/`, `references/`, scripts, or tests instead of repeating them in every `SKILL.md`.

- User-invoked skills orchestrate one workflow and may call model-invoked skills; they must not call another user-invoked skill automatically.
- Model-invoked skills provide reusable methods; they must not change `user_decision`, `actor: user`, or workflow gates.
- Use one canonical term for one meaning. Use `必须`, `可以`, `不得`, and `停止` for rule strength, and keep `user_decision`, `agent_recommendation`, `agent_inference`, and `pending` distinct.
- Prefer skill descriptions of 160 characters or fewer and compact entrypoint instructions. A longer skill needs a stated reason and should move reusable text into a model layer or referenced rule; these are maintenance targets, not workflow gates.
- Do not create a project workflow gate, user approval, or ledger field merely to enforce this writing contract. Add a new gate only when a real product, domain, technology, or safety decision needs user ownership.
- Keep gates for user-owned decisions and independent review. Draft writes, start markers, evidence snapshots, and other mechanical bookkeeping may happen inside the owning invocation; do not turn them into extra user tasks.
- Supporting UI, performance, baseline, and template records carry their own `status`, user evidence, and provenance. Do not add a second `confirm-*` ledger transition for a record that is already confirmed.
- Prefer a small composable method over a state-machine ceremony: call `grilling` for the current decision frontier and `feedback-loop` for one failure signal, then return the result to the owning skill.
- Keep `SKILL.md` and `agents/openai.yaml` in the same invocation mode. Every skill change must run:

  ```text
  python ddd-core/scripts/skill_lint.py --root .
  ```

- A behavior or gate change also requires a regression test. Do not weaken a gate merely to make the skill shorter.

- `ask-ddd`: route a request to one workflow and stop.
- `ddd-core`: interview the user, record scope and decisions, design one technology-neutral slice, and stop.
- `business-lab`: let the user investigate and draw the business mainline through one concrete question per turn; never complete the business model for them.
- `domain-modeling`: vocabulary layer that challenges ambiguous business terms and updates the canonical glossary only after user confirmation.
- `project-wayfinder`: map a large effort as named decisions with blockers before creating slices.
- `triage-loop`: classify raw incoming reports and produce an agent-ready brief.
- `research-loop`: collect primary-source evidence for one unresolved question.
- `oss-archaeology`: study one pinned open-source project and separate its facts from candidate rules for our domain.
- `prototype-loop`: answer one design question with a throwaway experiment.
- `performance-loop`: select a version-pinned database profile, generate bounded database-specific SQL, and record one slice performance contract and reproducible metric baseline when the slice needs them.
- `to-spec`: synthesize confirmed decisions into a reviewable handoff spec.
- `to-slices`: plan vertical slices and explicit blockers from a confirmed spec.
- `adapter-kit`: after slice approval, let the user select or confirm one exact technology profile; do not implement it.
- `ui-system`: define and confirm project tokens, themes, responsive layout, accessibility, and visual-state rules; do not implement them.
- `ui-practices`: collect version-pinned React, Vue, Angular, and UI-library guidance and confirm component-first practices; do not implement them.
- `ui-architecture`: collect primary-source UI-library evidence and confirm one component composition plan for a UI slice.
- `scaffold-kit`: inspect and explicitly apply one project-configured, `ng generate`-style UI or backend artifact generator; UI and backend use separate checks.
- `template-kit`: inspect pinned references and create or extract confirmed clean-room UI templates with provenance; do not copy source code.
- `delivery-loop`: after a selected profile and active slice, implement and verify one active slice, using database, performance, UI, and scaffold records as supporting evidence when present, then stop.
- `repair-loop`: reproduce, fix, and regression-test one confirmed failure, then stop.
- `code-review`: review one verified fixed-point diff on separate Standards, Spec, DDD, UI, and Custom axes; never edit source.
- `retro-loop`: turn session failures into approved deterministic checks or rules.
- `rule-workbench`: maintain traceable records without changing gates implicitly.
- `grilling`: model-invoked method for asking the current independent decision frontier; never changes the ledger.
- `feedback-loop`: model-invoked method for reproducing one failure and locking its regression signal; never changes the ledger.

For a target project's workflow, use `.ddd/workflow-state.json` as the coordination ledger. A missing or contradictory ledger blocks a project-changing skill; research-only and inspect modes may run without one and must not write it. A transition records explicit conversational evidence in the project; do not create external trust directories, private-key workflows, receipt chains, or detached approval fields. `user_decision`, `agent_recommendation`, `agent_inference`, and `pending` must stay distinct; the agent may propose options but never silently choose among material product or technology decisions. Use the exact status words in `ddd-core/rules/keywords.md`.

Research is a separate evidence activity. An OSS or documentation study must stop after its cited note; it may not continue as a business interview or record research-session answers as product decisions. Start `$business-lab` or `$ddd-core` explicitly when the user wants to interpret evidence for the product.
