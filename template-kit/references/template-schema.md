---
rule_version: "1"
id: template-kit.schema
---

# UI template record

`.ddd/templates/<template-id>.yaml` is the provenance and contract record for a reusable scaffold template. It is separate from the source note and from the generated files.

```yaml
schema_version: "1"
status: draft # draft -> confirmed after a separate user action
id: admin-shell
version: "1"
profile: react-antd-pro
profile_version: "1"
sources:
  - id: source-project
    kind: oss # oss | local | design-reference | user
    locator: "https://github.com/example/project"
    ref: "v1.2.3"
    license: "MIT"
    attribution: "Required notice or none"
    evidence: ".ddd/template-sources/admin-shell.md"
    extraction: pattern_only
mapping:
  ui_system: ".ddd/ui-system.yaml"
  ui_practices: ".ddd/ui-practices.yaml"
  theme_roles: [surface, text, action, focus]
  layout_regions: [app-shell, navigation, content]
  primitives: [ProLayout, ProCard]
  adaptation:
    source_framework: vue
    source_library: element-plus
    target_framework: react
    target_library: antd-pro
    primitive_map:
      - source: ElTable
        target: ProTable
        reason: "Keep the source table behavior while using the selected target library."
      - source: ElContainer
        target: ProLayout
        reason: "Preserve shell regions, not the source component implementation."
    target_invariants: [project_tokens, project_theme_roles, target_library, target_framework]
description: "Project application shell"
required_components: [ProLayout, ProCard]
public_seams: [AppShell]
slots: [navigation, header, content, footer]
variables: [name, pascal_name, kebab_name, profile_id, target]
review_checks: [ui-theme-role, ui-layout-region, ui-component-first]
confirmation:
  status: pending
  source: pending
  evidence: null
files:
  - path: "{{kebab_name}}/index.tsx"
    template_file: ".ddd/templates/admin-shell/index.tsx"
file_digests:
  .ddd/templates/admin-shell/index.tsx: "<sha256-of-template-file>"
source_evidence_digests:
  .ddd/template-sources/admin-shell.md: "<sha256-of-source-evidence>"
decisions: []
evidence: []
```

## Rules

- Use exactly one `source` object for a single reference or a `sources` array for a comparison or composite template. Every source needs a pinned `ref`, license, attribution, and evidence note.
- `source.ref`, `source.license`, and `source.evidence` are required for `oss` and `local` extraction. A source without provenance cannot be confirmed.
- `extraction: pattern_only` means the template is clean-room and contains placeholders or project-authored code. A copied file requires an explicit compatible-license decision and attribution record.
- `mapping` connects the template to the confirmed project UI system and practice profile; it does not replace either record.
- A confirmed template must include `confirmation.status: confirmed`, `confirmation.source: user_decision`, and evidence pointing to a signed `template:confirm` credential. The credential request must bind the exact template record digest, project ledger digest, template id, and record path. A mutable `status` or `source` field is never sufficient.
- When a file generator uses `template_file`, a confirmed record must include an exact `file_digests` map. The record digest is signed by `template:confirm`, and `$scaffold-kit` compares every current template file with that map before reading or generating it. Editing a template file after confirmation therefore invalidates the registration.
- A confirmed record must also include an exact `source_evidence_digests` map. The map is signed with the record, and `$scaffold-kit` compares every pinned source evidence note before accepting the registration. Editing provenance notes after confirmation therefore invalidates the registration.
- A registered template must include `record`, pointing to the same `.ddd/templates/<template-id>.yaml` record. `$scaffold-kit` compares the registered copy with that record and rejects drift.
- `mapping.adaptation` is required for every template. When the source and target match, record an identity map; when they differ, it must name the source and target primitives and the target invariants that remain authoritative.
- `slots`, `variables`, `public_seams`, and `review_checks` are part of the generator contract and must appear in the dry-run.
- A template may be confirmed only after the user reviews source, license, mapping, files, and generated output plan.
