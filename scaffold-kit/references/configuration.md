---
rule_version: "1"
id: scaffold-kit.configuration
---

# Scaffold configuration

The interaction model follows Angular CLI's schematic idea: `ng generate` exposes named, inspectable generators with options and templates, while this project keeps a separate dry-run and explicit apply step so generation cannot silently become implementation. See the [Angular CLI schematic documentation](https://angular.dev/tools/cli/schematics) for the upstream model.

The project owns `.ddd/scaffold.yaml`. A profile is versioned so a generated artifact can be reviewed against the exact template contract that produced it. The generator supports inline `template` text or a repository-relative `template_file`; it performs only placeholder substitution.

```yaml
schema_version: "1"
default_profile: react-antd-pro
profiles:
  react-antd-pro:
    version: "1"
    aliases:
      c: component
    generators:
      component:
        file-entry-table:
          description: "File-entry list using the profile table primitive"
          required_components: ["ProTable"]
          public_seam: "FileEntryTable"
          review_checks: ["ui-procomponent-first", "ui-request-seam"]
          files:
            - path: "{{kebab_name}}/index.tsx"
              template: |
                import { ProTable } from '@ant-design/pro-components';

                export function {{pascal_name}}() {
                  return <ProTable rowKey="id" columns={[]} request={async () => ({ data: [], success: true })} />;
                }
```

The same `generators` map may contain a `backend` kind. Backend generators use the selected backend adapter profile and do not require UI records. Each backend generator declares `surface: backend`, `requires_ui: false`, an explicit `requires_database` boolean, a public seam, review checks, Cargo validation commands, and files. A `requires_database: true` generator is blocked until the signed database profile record is selected. It may create a seam, but it may not silently pick a query layer or generate SQL outside the selected profile.

```yaml
profiles:
  rust-axum-sqlx:
    version: "1"
    surface: backend
    generators:
      backend:
        service:
          surface: backend
          requires_ui: false
          requires_database: false
          public_seam: "FileEntryRouter"
          review_checks: [backend-route-seam, cargo-check]
          validation_commands:
            format: cargo fmt --all -- --check
            check: cargo check --workspace --all-targets
            lint: cargo clippy --workspace --all-targets --all-features -- -D warnings
            test: cargo test --workspace
            audit: cargo audit
          files:
            - path: "{{kebab_name}}/mod.rs"
              template: "pub fn router() {}"
```

The same `generators` map may contain a `template` kind. A template is a confirmed, project-owned clean-room pattern registered by `$template-kit`; it is still generated through the same dry-run and explicit apply boundary:

```yaml
      template:
        admin-shell:
          status: confirmed
          version: "1"
          description: "Application shell with named layout slots"
          record: ".ddd/templates/admin-shell.yaml"
          required_components: [ProLayout, ProCard]
          source:
            kind: oss
            locator: "https://github.com/example/project"
            ref: "v1.2.3"
            license: "MIT"
            attribution: "See .ddd/template-sources/admin-shell.md"
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
                - source: ElContainer
                  target: ProLayout
                  reason: "Preserve shell regions, not source implementation."
              target_invariants: [project_tokens, project_theme_roles, target_library, target_framework]
          slots: [navigation, header, content, footer]
          variables: [name, pascal_name, kebab_name, profile_id, target]
          public_seams: [AppShell]
          review_checks: [ui-theme-role, ui-layout-region, ui-component-first]
          confirmation:
            status: confirmed
            source: user_decision
            evidence: ".ddd/approvals/credentials/confirm-template.json"
          files:
            - path: "{{kebab_name}}/index.tsx"
              template_file: ".ddd/templates/admin-shell/index.tsx"
          file_digests:
            .ddd/templates/admin-shell/index.tsx: "<sha256-of-template-file>"
          source_evidence_digests:
            .ddd/template-sources/admin-shell.md: "<sha256-of-source-evidence>"
```

Required profile fields are `version` and `generators`. A backend profile also declares `surface: backend`; a UI profile remains the default surface when omitted. Each generator file needs `path` and exactly one of `template` or `template_file`. Supported placeholders are `name`, `pascal_name`, `camel_name`, `kebab_name`, `slice_id`, `profile_id`, and `target`. Unknown placeholders are errors.

Template generators additionally require `status: confirmed`, a version, a `record` path to the confirmed `.ddd/templates/<template-id>.yaml`, and a separate signed `template:confirm` user approval credential, plus one `source` or a `sources` array with provenance (`kind`, locator, ref, license, attribution, evidence, and `pattern_only` or explicitly licensed-copy extraction), UI-system and UI-practice mappings, theme roles, layout regions, target primitives, an adaptation map, slots or public seams, variables, review checks, a `file_digests` map for every `template_file`, and a `source_evidence_digests` map for every provenance note. The generator verifies the credential with an external trusted public key, compares the registration with the record, current template-file digests, and source-evidence digests, and never downloads or executes any source project.

Generator ids are stable names, not free-form code. A project may add `page`, `feature`, `hook`, `adapter`, or another kind, but each kind must still declare its output files and contract. The generated target is joined to the repository root and must remain inside it. A generator may not write anywhere under `.ddd`, including the workflow ledger, approvals, scaffold configuration, or template records. Templates cannot execute commands or refer to environment variables.

The optional `required_components`, `public_seam`, `review_checks`, and `description` fields are carried into the dry-run and code-review report. Backend fields `surface`, `requires_ui`, `requires_database`, and `validation_commands` are carried into the dry-run as implementation boundaries. Template fields such as `record`, `confirmation`, `source`/`sources`, `mapping`, `slots`, `variables`, `file_digests`, and `source_evidence_digests` are carried into the dry-run as provenance and contract evidence. A managed `--apply` additionally requires a signed `scaffold:apply` credential whose arguments include the exact profile, generator, name, target, force flag, and dry-run plan digest; its request must digest `.ddd/scaffold.yaml`. These approvals do not replace the user's UI plan, backend profile, or domain approval.
