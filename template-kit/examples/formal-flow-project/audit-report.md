# Formal flow audit

## Guards now enforced

- The registered generator must point to the same confirmed template record through `record`.
- The registration and record must match on version, profile, sources, mapping, slots, variables, review checks, confirmation, files, and signed `file_digests`.
- Source evidence, confirmation evidence, and local template files must exist inside the project root.
- A managed project must have a valid `human_led` ledger, an approved active slice, selected profile, confirmed UI system/practices/plan, `delivery: not_started`, and user transition history.
- The active `--slice-id` must equal the ledger's approved slice.
- UI confirmation transitions require the corresponding file record to be in the expected state, match the selected profile, and contain an evidenced `user_decision`.
- Every `actor: user` history entry carries a signed Ed25519 approval. The signature binds the transition arguments, pre-transition ledger digest, and relevant record digests; request ids cannot be replayed because successful transitions are consumed in the fixed user trust path's append-only receipt chain.
- The `confirm-design` approval binds the project goal, complete scope, decisions, business-artifact reference, and any `domain_design` record through a canonical domain-design digest. A later scope or decision substitution therefore invalidates the scaffold gate.
- Template registration carries a separate `template:confirm` credential bound to the template record digest and the current template-file digests. The scaffold checker requires an explicitly supplied trusted public key that matches the fixed user trust manifest; an environment-supplied manifest is rejected.
- The signed template record also carries `source_evidence_digests`, so provenance notes cannot be edited after confirmation without invalidating registration.

## Negative checks

The audit used temporary copies of this fixture and verified that the following all fail:

- changing the template record without changing `scaffold.yaml`;
- changing `delivery` to `in_progress`;
- removing the workflow ledger;
- leaving the UI plan in `draft`;
- omitting template confirmation;
- using a wrong active slice;
- confirming a UI record without a user decision or with a different profile;
- changing `control_mode` away from `human_led`.
- deleting the approval metadata from an `actor: user` history entry;
- changing the trusted key or corrupting a credential signature;
- changing a signed record after the confirmation request was issued.
- changing a confirmed template file without updating its signed `file_digests`.
- replacing the CLI key with an agent-generated key while the trust manifest remains pinned.
- rolling the ledger back to its pre-transition bytes and replaying a consumed credential.
- deleting or truncating the receipt log, or editing its anchor checkpoint.

## Remaining boundary

The repository can now detect file-only `user_decision`/`actor: user` forgery, changed evidence, key substitution, changed template files, credential replay, environment-based manifest replacement, and receipt-log rollback when the fixed trust manifest, public key, receipt log, and receipt anchor are kept outside the project. The signature proves possession of that private key and the exact reviewed payload; it does not prove a real-world identity or that the user read the request. The skill must show the request digest and wait for the user's independent signing step. If an agent can modify the fixed user trust directory itself, it can rewrite the trust boundary; real deployments must enforce that boundary with operating-system permissions or a protected append-only store.
