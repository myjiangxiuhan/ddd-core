---
rule_version: "1"
id: approval-kit.security-boundary
---

# Approval security boundary

The verifier treats the project as agent-writable. A project JSON file, a checked-in public key, a request filename, and an `actor: user` field are not trusted evidence.

| Attack | Control | Regression evidence |
| --- | --- | --- |
| Generate a new Ed25519 key and pass it as the trusted key | The user-managed manifest pins the public-key path and fingerprint; a CLI key is only a matching assertion | `test_generated_key_cannot_replace_pinned_trust` |
| Point `DDD_APPROVAL_TRUST_MANIFEST`, `HOME`, or `USERPROFILE` at an agent-created trust directory | The manifest path is derived from the system user-directory API and canonical project root; all caller-selected environment paths are ignored or rejected | `test_environment_cannot_replace_fixed_manifest`, `test_system_user_directory_ignores_home_variables` |
| Replace an existing key with `keygen` | Key generation uses exclusive creation and refuses overwrite | `test_keygen_refuses_to_overwrite_an_existing_key` |
| Change a request after the user reviewed it | The user carries the displayed payload digest into `sign`; signing rejects a mismatch | `test_sign_refuses_a_request_changed_after_review` |
| Edit a signed request, credential, or evidence record | The credential binds the canonical payload, request id, ledger digest, and record digests | `test_missing_or_tampered_approval_cannot_advance_user_gate` |
| Reuse a credential after rolling the ledger back | A successful transition appends the request id to a sequential receipt hash chain and a separate anchor checkpoint; truncation, deletion, reordering, or editing fails closed | `test_valid_approval_is_consumed_and_replay_is_rejected`, `test_receipt_chain_rejects_rollback_and_tampering` |
| Mark a final gate or decision by editing JSON | Read-only checks require the signed transitions implied by gate values, an answered decision, and one signed `record-decision` per answered decision | `test_workflow_require_rejects_final_gates_without_user_history` and formal scaffold checks |
| Change the confirmed domain scope or design inputs | `confirm-design` signs a canonical digest of `project`, `scope`, `decisions`, `business_artifact`, and `domain_design` | formal scaffold scope-tamper check |
| Change a confirmed template file after signing | The signed template record carries a digest for every `template_file` | formal scaffold file-digest check |
| Change a pinned source evidence note after signing | The signed template record carries `source_evidence_digests` for every provenance note | formal scaffold source-evidence check |
| Apply an altered scaffold plan | Managed apply requires a separate `scaffold:apply` credential over the config digest and dry-run plan digest | formal scaffold apply guard |

The trust manifest must also pin the absolute project root. Its path, the public key path, the receipt-log path, and the anchor path are fixed by the canonical project root and the system-resolved user directory; the verifier rejects `DDD_APPROVAL_TRUST_MANIFEST` instead of accepting a caller-selected replacement and never falls back to `HOME` or `USERPROFILE`. All four files must be provisioned before the first approval and kept in a user-controlled directory outside the project. The verifier refuses missing stores and rejects a manifest reused for another checkout. If an agent can rewrite that fixed directory or operate the user's private key, the agent controls the trust boundary and no in-process signature check can establish that the signer was the human.

The receipt log is protected against ordinary project rollback and concurrent double-spend with an external lock, sequential entry digests, and a separate anchor chain. It is not a tamper-proof ledger against an attacker who can edit the fixed user trust directory; use OS ACLs, a protected secret store, or an append-only service for that stronger threat model.
