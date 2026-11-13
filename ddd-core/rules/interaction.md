---
rule_version: "3"
id: ddd.interaction
---

# Interaction and gate rules

The workflow is a state machine backed by `.ddd/workflow-state.json`. Read it before every skill invocation. Conversation text can explain an approval, but a skill must persist the corresponding transition before a later skill may act.

## Allowed transitions

| Current state | Explicit user action | Result | Skill allowed to act |
| --- | --- | --- | --- |
| missing or `new` | invoke `ddd-core` with a requirement | create a scope draft and enter `discovery` | `ddd-core` only |
| `phase: discovery` | answer the current frontier | record the answers; remain in discovery or create a draft design when no material questions remain | `ddd-core` only |
| `business_discovery: not_started` | explicitly investigate the business and draw the mainline | set `business_discovery: in_progress` | `business-lab` only |
| `business_discovery: in_progress` | record a user-authored mainline artifact | set `business_discovery: draft` | `business-lab` only |
| `business_discovery: draft` | separately confirm or correct the mainline | set `business_discovery: confirmed` | `business-lab` only |
| `domain_design: draft` | separately confirm or correct the design | set `domain_design: confirmed` | `ddd-core` only |
| `domain_design: confirmed` | separately approve one named slice | set `slice_approval: approved` and `active_slice` | `ddd-core` only |
| `slice_approval: approved`, `technology_profile: pending` | explicitly select or confirm one profile | set `technology_profile: selected` | `adapter-kit` only |
| `slice_approval: approved`, `technology_profile: selected`, `ui_design: not_started` | explicitly plan a UI surface | set `ui_design: draft` | `ui-architecture` only |
| `ui_design: draft` | separately confirm or correct the UI composition | set `ui_design: confirmed` | `ui-architecture` only |
| `ui_design: confirmed` | explicitly inspect one configured generator | no gate change; produce a dry-run | `scaffold-kit` only |
| `slice_approval: approved`, `technology_profile: selected`, `ui_design: not_started` or `confirmed` | explicitly invoke delivery for the active slice | set `delivery: in_progress` | `delivery-loop` only |
| `delivery: in_progress` or `blocked` | report one concrete failure or invoke repair | enter the repair loop | `repair-loop` only |
| `delivery: verified`, `review: not_started` or `blocked` | explicitly review the fixed-point diff | set `review: passed` or `blocked` | `code-review` only |
| `delivery: verified`, `review: blocked` | explicitly repair a review finding | set `delivery: in_progress` and reset review | `repair-loop` only |
| `delivery: verified`, `review: passed` | explicitly approve a new slice | create a new draft; never reuse the old approval | `ddd-core` only |
| any state with an ambiguous or conflicting business term | clarify the term with a concrete scenario | update glossary only after user confirmation; no gate change | `domain-modeling` vocabulary layer |

## Rules

- Require two separate, explicit confirmations: first confirm the domain design, then approve implementation of one named slice. A single message that combines them satisfies neither transition.
- In `human_led` mode, require a user-authored and separately confirmed business mainline before confirming the domain design. The agent may organize or challenge the mainline, but it may not author the business model for the user.
- Ask the whole current frontier of independent questions in one round, normally 1-4 questions. If a question depends on another open question, defer it to the next round.
- `business-lab` is adaptive: ask one micro-question per turn, start open-ended, offer 2-4 options plus `不知道/其他` only when the user is blank or asks for help, and wait for the user's wording before creating a business card.
- Perform at most one gate transition per invocation. Recording the answers from the current frontier is part of that round; do not also confirm a design, approve a slice, or start delivery in the same invocation.
- User-invoked entrypoints must not auto-chain another entrypoint. In particular, `ddd-core` never invokes `adapter-kit`, `delivery-loop`, or `repair-loop`; a failing delivery never silently starts a repair.
- A draft, plan, issue, ticket, test result, or inferred agreement is not an approval. Do not promote state without the matching explicit user action.
- Do not read or invoke `adapter-kit` before the slice approval. Do not invoke `delivery-loop` before the technology profile is selected when the project has no existing profile.
- Do not invoke `scaffold-kit` before the UI plan is confirmed. A UI plan is optional for non-UI slices, but a draft UI plan blocks delivery until it is confirmed or removed by an explicit user decision.
- A code review is a terminal check for the current active slice. It may pass or block the review gate in one transition, but it never fixes code, starts repair, or approves a new slice.
- If the ledger is missing, invalid, stale, or contradictory, stop and report the exact field that blocks the transition. Do not repair it by inference.

