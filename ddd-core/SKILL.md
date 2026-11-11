---
name: ddd-core
description: Build a project or domain scope and one evidence-backed domain slice, then stop at explicit user gates; never implement code or choose technology.
---

# ddd-core

## Invocation

This is a user-invoked entrypoint. Run it for a new product idea, feature, or domain slice before implementation. One invocation may create or update the draft workflow ledger, but it must not write implementation code, schema, API, UI, infrastructure, or technology configuration.

Read [workflow state](rules/workflow-state.md) and [interaction and gates](rules/interaction.md) before doing any work. The ledger is the source of truth for stage and approvals; a broad request, an enthusiastic phrase, or a draft document is not an approval.

## Process

1. **Scope intake.** If the request spans a project or an iteration, record the goal, the smallest current slice candidate, deferred capabilities, explicit non-goals, and unresolved decisions. Keep future capabilities in the deferred register. Do not turn them into implementation tasks in this invocation.
2. **Discovery interview.** Before shaping a design, identify the smallest set of decisions that change the boundary, actor, command, rule, data meaning, or priority. Ask exactly one high-value question per round. Offer options with consequences when useful, but never pick an option for the user. Record the user's answer as `user_decision`; keep unanswered items `pending`.
3. **Domain understanding.** Extract only evidence-backed facts, roles, commands, rules, states, events, external actions, boundaries, and the evidence boundary. Mark each item as `confirmed`, `inferred`, `assumption`, or `pending` and record its source or missing evidence. An inference cannot become a rule until the user confirms it.
4. **Domain design.** Only after the essential discovery questions are answered, shape the smallest technology-neutral design for the current slice and 2-4 acceptance scenarios. Show which parts came from user decisions and which remain pending. Keep canonical domain terms separate from display terms.
5. **Design gate.** Persist the design as `draft` and ask exactly one question to confirm or correct the listed decisions and boundaries. Do not advance this gate from the user's request to implement, from a previous plan, or from inferred agreement.
6. **Slice gate.** After a separate explicit design confirmation, name the available slice candidates and ask exactly one question for approval of one named slice. A combined message such as “确认并实现” does not satisfy both gates.
7. **Handoff and stop.** After a separate slice approval, persist the exact `active_slice` and stop. Tell the user to invoke `$adapter-kit` only if a technology profile must be selected or checked, then invoke `$delivery-loop` in a later user action. Never invoke either skill from ddd-core.

## State transitions handled here

- `new` or missing ledger -> create a scope draft and enter `discovery`.
- `discovery` + essential user answers -> create a `draft` domain design.
- `draft` + explicit confirmation or correction of the listed decisions -> `domain_design: confirmed`.
- `domain_design: confirmed` + separate approval naming one slice -> `slice_approval: approved` and set `active_slice`.
- Any missing, conflicting, or stale gate -> stop and ask one precise question; do not guess.

## Output contract

Return the workflow state, project scope, current slice, deferred capabilities, decision register, domain facts, roles, commands, rules, states, events, external actions, boundaries, evidence boundary, and 2-4 acceptance scenarios. Render each material decision with its question, available options, consequence of each option, current status, source, and evidence. For every material decision, show `user_decision`, `agent_inference`, or `pending` and its evidence. Include the exact next user action. Keep unconfirmed material marked `draft` or `pending`.

## Hard stops

- Do not call, read, or route to `adapter-kit`, `delivery-loop`, `repair-loop`, or any other skill.
- Do not present an AI-completed design before essential discovery is answered. If the user has not decided, show the decision options and their consequences, then ask one question.
- Do not silently resolve ambiguity, choose a default, or convert an assumption into a domain rule. A design with no user-owned decisions is incomplete.
- Do not select a database, cache, storage provider, framework, API shape, table, schema, UI, or deployment arrangement in the domain-design path.
- Do not implement a future capability because it is plausible or technically convenient. Record it as deferred and surface any technology-neutral compatibility constraint that the current slice must preserve.
- Do not widen the active slice, start a second slice, or continue after the handoff.

## Canonical rules

- [Scope and future-capability rules](rules/scope.md) (`ddd.scope`)
- [Workflow state](rules/workflow-state.md) (`ddd.workflow-state`)
- [Domain model](rules/domain-model.md) (`ddd.domain-model`)
- [Evidence](rules/evidence.md) (`ddd.evidence`)
- [Interaction and gates](rules/interaction.md) (`ddd.interaction`)
- [Gated lifecycle](rules/lifecycle.md) (`ddd.lifecycle`)
