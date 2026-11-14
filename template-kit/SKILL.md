---
name: template-kit
description: Inspect, extract, create, and validate reusable UI templates from pinned references without copying unapproved source code.
---

# template-kit

This is a user-invoked template workbench. It turns a confirmed UI system, layout, and framework practice profile into a project-owned, inspectable scaffold template. A source may be an open-source repository, a local page, a design reference, or a user-provided artifact; multiple pinned sources may be compared for one template. The skill records provenance and extracts patterns, slots, contracts, and placeholders; it does not silently copy source code, assets, or licenses. A source's layout can be adapted to the target profile: its structure is evidence, while the project's component library, tokens, themes, and framework contracts remain authoritative.

## Preconditions

Read [workflow state](../ddd-core/rules/workflow-state.md), [interaction and gates](../ddd-core/rules/interaction.md), the confirmed `.ddd/ui-system.yaml`, the confirmed `.ddd/ui-practices.yaml`, and [the template schema](references/template-schema.md). Run both foundation checks:

```text
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require ui-system
python ddd-core/scripts/workflow_gate.py --state .ddd/workflow-state.json --require ui-practices
```

A non-zero result is a hard stop. A template must target the selected technology profile. If the source is an open-source project, use a pinned tag, release, commit, or archive and record the license and attribution requirements before extracting anything.

## Modes

- `inspect`: collect source facts, version, license, theme mechanisms, layout regions, component tree, public seams, and reusable patterns.
- `extract`: turn the inspected facts into a `draft` pattern template with slots and placeholders. Extract structure and contracts, not copied implementation.
- `create`: create a project-owned template from a user-confirmed pattern, local precedent, or user-provided skeleton.
- `validate`: check provenance, profile compatibility, safe paths, placeholders, contract fields, and the scaffold registration without changing source code.

If the user asks for all modes at once, begin with `inspect`, stop with an evidence note, and wait before extracting or registering a template.

Typical sources can include Vben Admin, Ant Design Pro examples, `xxx-admin` projects, or a local design reference. Treat each as a pinned reference with its own framework, component library, theme, layout, structure, and license; the name alone is never evidence.

## Extraction rules

1. Pin every source and state the extraction question. A URL without a ref is not a stable source.
2. Separate `source_fact`, `agent_recommendation`, `agent_inference`, and `user_decision`.
3. Extract only the reusable shape: theme roles, token references, layout regions, slots, component responsibilities, state boundaries, generator variables, and review checks.
4. Do not copy source code, images, fonts, trademarks, or configuration unless the user explicitly provides a compatible license and asks for that exact asset. Prefer a clean-room template with placeholders and a source citation.
5. Preserve license, attribution, notices, and incompatible-license findings for every source in the template record. A permissive license does not prove that a pattern fits this project.
6. Build an adaptation map from source primitives to target primitives. For example, a source `Element Plus` table or shell may map to the selected `Ant Design`/`ProComponents` primitive; the source component is never emitted into the target template.
7. Compare the pattern with the confirmed UI system and practice profile. Record `same_role`, `adapted_role`, `conflict`, or `missing_evidence`; never overwrite the project's decisions with the source's defaults.

## Process

1. Read the foundations, selected profile, source, and local precedent.
2. For `inspect`, write one cited note under `.ddd/template-sources/` and stop.
3. For `extract` or `create`, draft `.ddd/templates/<template-id>.yaml` and any clean-room template files under `.ddd/templates/<template-id>/`. Keep the record `status: draft` and show every file and placeholder.
4. Ask the independent frontier, normally 1-4 questions: target scope, source adaptation, slots/regions, variables, license handling, and generator kind. Do not select a template boundary because the reference looks polished.
5. After the user confirms or corrects the pattern, compute `file_digests` for every `template_file` and `source_evidence_digests` for every provenance note, then create a separate signed `template:confirm` approval request over the exact template record. The user must inspect the displayed payload digest and sign it with a private key kept outside the project. Store the credential path in `confirmation.evidence`, change the record to `status: confirmed`, and then register it under the selected profile's `generators.template` section in `.ddd/scaffold.yaml` with matching `record`, `file_digests`, and `source_evidence_digests` back to the same file. `$scaffold-kit` verifies the credential against the fixed user trust manifest and append-only receipt chain, then compares the registration, current template files, and provenance notes with the signed record before it can generate. This is the only point at which the template becomes available to `$scaffold-kit`.
6. Run `scaffold.py check`, `describe`, and a dry-run `generate template ...`. Stop. The user must invoke `$scaffold-kit` explicitly to apply it.

## Output contract

Return the mode, pinned source and license evidence, extracted facts, adapted pattern, UI-system and practice mappings, template ID/version, files and placeholders, generator contract, unresolved decisions, validation result, and the exact next user action. State whether the template is `draft` or `confirmed` and whether it is registered for scaffolding.

## Hard stops

- Do not fetch an unpinned `main` branch and call it a stable template source.
- Do not merge multiple source findings into one pattern without identifying which source supplied each layout, theme, or component observation.
- Do not copy code, assets, fonts, trademarks, or project configuration by default.
- Do not register or generate a `draft` template.
- Do not treat a copied `status: confirmed`, `source: user_decision`, or `actor: user` field as human approval; the registration must carry a signed `template:confirm` credential whose request covers the current template record, and point back to the confirmed template record.
- Do not accept a project-controlled public key or manifest as the real trust anchor. Use `approval.py trust-path` to resolve the fixed user-managed manifest outside the project; `DDD_APPROVAL_TRUST_MANIFEST` is forbidden, and `--trusted-public-key` must match the fixed path and fingerprint. The checked-in key in the formal example is synthetic fixture data only.
- Do not change `.ddd/ui-system.yaml` or `.ddd/ui-practices.yaml` from an extracted source; conflicts return to those explicit skills.
- Do not generate implementation files, install packages, run arbitrary source commands, or start delivery in this skill.
- Do not call `$scaffold-kit`, `$ui-system`, `$ui-practices`, `$ui-architecture`, `$delivery-loop`, or `$code-review` automatically.

## Canonical rules

- [Template schema](references/template-schema.md) (`template-kit.schema`)
- [Scaffold configuration](../scaffold-kit/references/configuration.md) (`scaffold-kit.configuration`)
- [Workflow state](../ddd-core/rules/workflow-state.md) (`ddd.workflow-state`)
- [Interaction and gates](../ddd-core/rules/interaction.md) (`ddd.interaction`)
