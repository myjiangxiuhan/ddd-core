---
rule_version: "2"
id: ddd.interaction
---

# Interaction and gate rules

The workflow is a state machine backed by `.ddd/workflow-state.json`. Read it before every skill invocation. Conversation text can explain an approval, but a skill must persist the corresponding transition before a later skill may act.

## Allowed transitions

| Current state | Explicit user action | Result | Skill allowed to act |
| --- | --- | --- | --- |
| missing or `new` | invoke `ddd-core` with a requirement | create a scope draft and enter `discovery` | `ddd-core` only |
| `phase: discovery` | answer the one question asked | record one `user_decision`; remain in discovery or create a draft design when no material questions remain | `ddd-core` only |
| `domain_design: draft` | separately confirm or correct the design | set `domain_design: confirmed` | `ddd-core` only |
| `domain_design: confirmed` | separately approve one named slice | set `slice_approval: approved` and `active_slice` | `ddd-core` only |
| `slice_approval: approved`, `technology_profile: pending` | explicitly select or confirm one profile | set `technology_profile: selected` | `adapter-kit` only |
| `slice_approval: approved`, `technology_profile: selected` | explicitly invoke delivery for the active slice | set `delivery: in_progress` | `delivery-loop` only |
| `delivery: in_progress` or `blocked` | report one concrete failure or invoke repair | enter the repair loop | `repair-loop` only |
| `delivery: verified` | explicitly approve a new slice | create a new draft; never reuse the old approval | `ddd-core` only |

## Rules

- Require two separate, explicit confirmations: first confirm the domain design, then approve implementation of one named slice. A single message that combines them satisfies neither transition.
- Ask at most one question per round. If a required field or approval is missing, stop after that one question.
- Perform at most one state transition per invocation. If a transition reveals another question, stop and wait for the next user round.
- User-invoked entrypoints must not auto-chain another entrypoint. In particular, `ddd-core` never invokes `adapter-kit`, `delivery-loop`, or `repair-loop`; a failing delivery never silently starts a repair.
- A draft, plan, issue, ticket, test result, or inferred agreement is not an approval. Do not promote state without the matching explicit user action.
- Do not read or invoke `adapter-kit` before the slice approval. Do not invoke `delivery-loop` before the technology profile is selected when the project has no existing profile.
- If the ledger is missing, invalid, stale, or contradictory, stop and report the exact field that blocks the transition.

