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

Required profile fields are `version` and `generators`. Each generator file needs `path` and exactly one of `template` or `template_file`. Supported placeholders are `name`, `pascal_name`, `camel_name`, `kebab_name`, `slice_id`, `profile_id`, and `target`. Unknown placeholders are errors.

Generator ids are stable names, not free-form code. A project may add `page`, `feature`, `hook`, `adapter`, or another kind, but each kind must still declare its output files and contract. The generated target is joined to the repository root and must remain inside it. Templates cannot execute commands or refer to environment variables.

The optional `required_components`, `public_seam`, `review_checks`, and `description` fields are carried into the dry-run and code-review report. They do not replace the user's UI plan or domain approval.
