---
rule_version: "5"
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
| `slice_approval: approved`, `technology_profile: selected` | explicitly select or confirm one exact database profile for a persistence slice | set `database_profile: selected` with the profile file digest | `adapter-kit` only |
| `technology_profile: selected` | explicitly define project tokens, themes, responsive layout, or accessibility baseline | set `ui_system: draft` or `confirmed` through separate transitions | `ui-system` only |
| `technology_profile: selected` | explicitly collect or confirm framework and component-first practices | set `ui_practices: draft` or `confirmed` through separate transitions | `ui-practices` only |
| `technology_profile: selected`, both UI foundations confirmed | explicitly inspect, extract, or create a pinned UI template | write a draft or confirmed template record; no ledger transition | `template-kit` only |
| `slice_approval: approved`, `technology_profile: selected`, `ui_design: not_started` | explicitly plan a UI surface | set `ui_design: draft` | `ui-architecture` only |
| `ui_design: draft` | separately confirm or correct the UI composition | set `ui_design: confirmed` | `ui-architecture` only |
| `ui_design: confirmed` | explicitly inspect one configured UI generator | no gate change; produce a dry-run | `scaffold-kit` only |
| `phase: delivery`, selected backend profile, and no draft UI plan | explicitly inspect one configured backend generator | no gate change; produce a dry-run | `scaffold-kit` only |
| `slice_approval: approved`, `technology_profile: selected`, `ui_design: not_started` or `confirmed` | explicitly invoke delivery for the active slice | set `delivery: in_progress` | `delivery-loop` only |
| `slice_approval: approved`, `technology_profile: selected` and the slice touches persistence or external calls | explicitly define and confirm workload budgets, query access paths, and database capabilities | write or confirm `.ddd/performance/<slice-id>.yaml` and baseline evidence; no automatic delivery | `performance-loop` only |
| `database_profile: selected` | separately confirm the exact performance contract and database mapping | set `performance_contract: confirmed` over `.ddd/performance/<slice-id>.yaml` | `performance-loop` only |
| `performance_contract: confirmed` | separately review and approve the recorded baseline evidence | set `baseline_attestation: confirmed` over the exact baseline, contract, profile, dataset digest/row count, commit, and slice binding | `performance-loop` only |
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
- Lock the active entrypoint and objective at the start of a turn. A concrete example, research answer, or user reply cannot switch the session into a different workflow. A new workflow starts only from an explicit route or command; when signals conflict, preserve the active objective and ask one routing clarification.
- Research is evidence work, not business discovery. After a research note is written, stop; do not interview the user or record candidate rules as product decisions in the same session.
- A draft, plan, issue, ticket, test result, or inferred agreement is not an approval. Do not promote state without the matching explicit user action.
- UI confirmation transitions also require the file-backed record to be in the matching state and to carry an evidenced `user_decision`; changing only the ledger field is insufficient.
- Every user transition (`confirm-*`, `record-decision`, `approve-slice`, `select-profile`, `select-database-profile`, `confirm-performance`, `confirm-baseline`, and `reset-slice`) requires a detached approval credential. The agent first creates a request that contains the exact transition arguments, current ledger digest, and relevant record digests; the user reviews and signs it with a private key kept outside the project, then the transition checker verifies it with an explicitly supplied trusted public key. A missing key, changed request, changed evidence, expired credential, or replayed request is a hard stop.
- `actor: user` is produced only after that signature verification. A hand-edited `user_decision`, `actor: user`, or `status: confirmed` field is evidence of tampering, not an approval. Keep the trusted public key outside the repository in real projects; a project-controlled key cannot be a trust anchor against an agent that can edit the project.
- The checker can still not prove the user's real-world identity or that the user read a request carefully. The signature proves possession of the trusted private key and binds the exact reviewed payload; the skill must present the request and obtain the separate user response before the signing step.
- Do not read or invoke `adapter-kit` before the slice approval. Do not invoke `delivery-loop` before the technology profile is selected when the project has no existing profile.
- Do not invoke `ui-architecture` for a UI slice until both `ui_system` and `ui_practices` are confirmed. A UI system owns project-wide visual rules; a UI practice profile owns framework and component-first rules.
- `template-kit` is an explicit template workbench, not an automatic stage. Its `draft`/`confirmed` template record is separate from the workflow ledger; it may become a scaffold generator only after the user confirms its source, mapping, contract, and files.
- `performance-loop` is an explicit performance workbench, not an automatic benchmark or tuning stage. Its contract separates user budgets and workload facts from database-specific adapter choices; a persistence slice cannot use a draft contract as implementation permission.
- Project SQL generation requires the signed database profile gate. Performance baseline comparison requires the signed database profile, signed performance contract, and separate signed baseline-attestation gates; passing a profile ID or baseline path on the command line is not a substitute for the ledger.
- Do not invoke a UI generator in `scaffold-kit` before the UI plan is confirmed. A UI plan is optional for non-UI slices, but a draft UI plan blocks both delivery and a backend scaffold until it is confirmed or removed by an explicit user decision. Backend scaffolding uses the separate read-only `--require scaffold-backend` check and never treats missing UI records as a reason to invent them.
- A code review is a terminal check for the current active slice. It may pass or block the review gate in one transition, but it never fixes code, starts repair, or approves a new slice.
- If the ledger is missing, invalid, stale, or contradictory, stop and report the exact field that blocks the transition. Do not repair it by inference.
- A read-only `--require` must verify every user approval implied by the current gate values. It also needs the external trusted public key assertion and the fixed user trust path reported by `approval.py trust-path`; `DDD_APPROVAL_TRUST_MANIFEST` is rejected. A ledger whose final gates have no matching signed user history is a hard stop.

