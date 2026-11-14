---
rule_version: "5"
id: ddd.workflow-state
---

# Workflow state ledger

Use `.ddd/workflow-state.json` as the durable control record for a project. It is a small planning artifact, not implementation output. Every downstream skill reads it before acting and writes the next state only after its own gate.

The bundled read-only checker can be run before a gated operation:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require delivery
```

Use `business`, `technology`, `database-profile`, `performance`, `ui-system`, `ui-practices`, `ui-design`, `scaffold`, `delivery`, `repair`, or `review` for the corresponding entrypoint. A non-zero exit is a hard stop.

Use the exact state vocabulary in [canonical workflow keywords](keywords.md). The ledger is intentionally boring: every change should be easy to audit from the actor, transition, and evidence.

The checker can also apply one transition atomically. Agent transitions need evidence from the repository or a verification command. User transitions additionally need a detached Ed25519 approval credential. The credential request is created before the transition and must be signed with a private key kept outside the project; pass the external trusted public key when applying it:

```text
python ddd-core/scripts/approval.py request --state .ddd/workflow-state.json --action workflow:confirm-design --arguments-json '{"transition":"confirm-design","evidence":"user confirmed the domain design"}' --output .ddd/approvals/requests
python ddd-core/scripts/approval.py sign --request .ddd/approvals/requests/<request-id>.json --expected-payload-digest <payload-digest-shown-by-request> --private-key <private-key-outside-project> --output .ddd/approvals/credentials/confirm-design.json
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --transition confirm-design --evidence "user confirmed the domain design" --approval .ddd/approvals/credentials/confirm-design.json --trusted-public-key <trusted-public-key-outside-project>
```

The request command prints the canonical request path. The user should inspect its action, arguments, ledger digest, and evidence digests before signing. Run `approval.py trust-path --state .ddd/workflow-state.json` to resolve the fixed user-managed manifest, public key, receipt log, and receipt anchor outside the project; `DDD_APPROVAL_TRUST_MANIFEST` is forbidden and cannot replace that path. `--trusted-public-key` is only a matching assertion. `workflow_gate.py` rejects a missing signature, a changed ledger or record, an expired credential, a different trusted key, a request id already recorded in history, or a request id already consumed in the append-only receipt chain. A user transition appends pre/post ledger digests to that chain before the ledger is written. Read-only `--require` checks still verify every approval required by the current gate values; a hand-edited final gate with no matching user history is rejected.

Available transitions are `start-business-lab`, `record-mainline`, `confirm-mainline`, `record-decision`, `confirm-design`, `approve-slice`, `select-profile`, `select-database-profile`, `confirm-performance`, `draft-ui-system`, `confirm-ui-system`, `draft-ui-practices`, `confirm-ui-practices`, `draft-ui`, `confirm-ui`, `start-delivery`, `verify`, `block`, `start-repair`, `pass-review`, `block-review`, and `reset-slice`. It applies only one gate transition per invocation and rejects invalid predecessors; recording several answers from one discovery frontier is still one discovery round.

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
    "database_profile": "pending",
    "performance_contract": "pending",
    "ui_system": "not_started",
    "ui_practices": "not_started",
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

- `control_mode` is `human_led` by default. The bundled checker currently accepts only `human_led`; another mode needs an explicit workflow rule before it can be introduced.
- `phase` is one of `discovery`, `business_discovery`, `domain_design`, `slice_approval`, `slice_approved`, `technology`, `ui_design`, `delivery`, `verification`, or `repair`.
- `business_discovery` is `not_started`, `in_progress`, `draft`, or `confirmed`. In `human_led` mode, the user must confirm the business mainline before the domain design can be confirmed.
- `domain_design` is `draft` or `confirmed`.
- `slice_approval` is `pending` or `approved`.
- `technology_profile` is `pending` or `selected`.
- `database_profile` is optional for slices without persistence; when present it is `pending` or `selected` and can advance only through the signed `select-database-profile` transition.
- `performance_contract` is optional for slices without persistence; when present it is `pending` or `confirmed` and can advance only through the signed `confirm-performance` transition over the exact `.ddd/performance/<slice-id>.yaml` record.
- `ui_system` is `not_started`, `draft`, or `confirmed`. It records the project-level tokens, themes, layout, responsive, and accessibility contract.
- `ui_practices` is `not_started`, `draft`, or `confirmed`. It records the version-pinned framework and component-first practice profile.
- `ui_design` is `not_started`, `draft`, or `confirmed`. It is optional for slices without a UI surface; when a UI plan exists, delivery must wait for `confirmed`.
- `delivery` is `not_started`, `in_progress`, `verified`, or `blocked`.
- `review` is `not_started`, `passed`, or `blocked`. A blocked review keeps the delivery verified until a later repair explicitly starts.
- `active_slice` is null until the user approves one named slice. Once set, its `id` and acceptance scenarios are immutable for that delivery cycle.
- A slice that uses persistence may carry `active_slice.requires_database: true`; selecting a database profile also marks the ledger as database-backed. The database profile record stores its ID, engine version, project-relative path, and file digest.
- `business_artifact` points to the user-editable business mainline record; it is evidence, not an implementation plan.
- `history` is append-only evidence. An entry for a user transition must have `actor: user` plus `approval.request_id`, `credential`, `request`, `payload_digest`, `public_key_fingerprint`, and the signed action/arguments. The checker verifies the detached credential and matches its receipt; it does not trust those fields because they are present in JSON.
- `reset-slice` resets the UI system and practice gates as well as the page plan because the next slice may select a different technology profile. A project may reuse the records only after the new profile confirms they still match.

## Write rules

- `ddd-core` may create or update scope, decisions, domain design, and approval gates; it must not set `delivery: in_progress` or `technology_profile: selected` by inference.
- `business-lab` may record business observations and the path to a user-authored mainline; only a separate user confirmation may set `business_discovery: confirmed`.
- `domain-modeling` may update canonical vocabulary after the user confirms a term; it never advances a gate or substitutes for a business-mainline confirmation.
- `adapter-kit` may set `technology_profile: selected` only after the user explicitly chooses or confirms the exact profile. It must not write implementation files.
- `adapter-kit` may set `database_profile: selected` only through the separate signed `select-database-profile` transition, after the application technology profile is selected. The transition must bind the exact profile file, ID, engine version, and digest; selecting a database because of a deferred capability is not allowed.
- `ui-system` may create a draft project UI system and set `ui_system: draft`; only a separate user confirmation may set `ui_system: confirmed`.
- `ui-practices` may create a draft framework practice profile and set `ui_practices: draft`; only a separate user confirmation may set `ui_practices: confirmed`.
- The bundled transition checker verifies that the corresponding UI record exists with the expected draft/confirmed status, matches the selected technology profile, and (for a confirmed UI record) includes at least one evidenced `user_decision`.
- A confirmed UI record is not a user approval by itself. Its `confirm-ui-system`, `confirm-ui-practices`, or `confirm-ui` ledger transition must carry a verified approval credential whose record digest covers that exact file.
- `ui-architecture` may create the UI catalog and draft plan, then set `ui_design: draft`; only a separate user confirmation may set `ui_design: confirmed`.
- `performance-loop` may create or update a slice performance contract and baseline evidence; it must keep user budgets, workload facts, database adaptation, and measured results distinct. A persistence, SQL, migration, index, queue, or external-call slice may not enter delivery without a confirmed `.ddd/performance/<slice-id>.yaml` or an explicit user decision that the path is outside the contract.
- `performance-loop` may set `performance_contract: confirmed` only through the separate signed `confirm-performance` transition. The transition binds the exact contract file and the already-selected database profile; editing `status: confirmed` in YAML does not advance the gate.
- `scaffold-kit` may write only the files shown in a dry-run from a configured generator after `ui_design: confirmed`; it must not change gate fields or run arbitrary commands.
- `delivery-loop` may set `delivery: in_progress` and later `verified` or `blocked` only for the existing `active_slice`. When the ledger is database-backed, `database_profile: selected` and `performance_contract: confirmed` are mandatory and their files must still match their signed digests.
- `repair-loop` may update the failure evidence and return the active slice to `verified` or `blocked`; it may not create a new feature or change the active slice.
- `code-review` may set `review: passed` or `review: blocked` after reviewing the verified active-slice diff; it must not edit source files or start repair.
- A missing, malformed, or contradictory ledger blocks work. Report the exact field and ask one question rather than repairing the state silently.
- Keep `.ddd/approvals/requests/` and `.ddd/approvals/credentials/` under version control only when the project deliberately wants an audit trail; keep the fixed trust manifest, trusted public key, private key, receipt log, and receipt anchor outside the project. The private key must never be generated or stored by an agent in the project directory. The fixed user trust directory is part of the security boundary: the verifier rejects environment-based manifest replacement and detects receipt-log truncation, reordering, and tampering. If an agent can rewrite the fixed trust directory itself, signatures no longer prove a user decision; protect that directory with operating-system permissions or a protected store.
