---
rule_version: "1"
id: code-review.profile
---

# Review profile schema

The bundled profile is the safe default. A project can add `.ddd/review-profile.yaml` to extend or override it without changing the skill. This file is declarative: it describes what to inspect and where the evidence lives; it does not grant permission to run arbitrary commands.

```yaml
schema_version: "1"
id: project-file-review
version: "1"
base_profile: ddd-default
checks:
  - id: file-name-policy
    axis: custom
    severity: major
    blocking: true
    applies_to: ["src/features/files/**"]
    rule: "File-entry components use the team's approved naming and folder boundary."
    evidence: ["docs/frontend-rules.md"]
```

Required fields are `id`, `axis`, `severity`, `blocking`, `rule`, and `evidence`. Valid axes are `standards`, `spec`, `ddd`, `ui`, `performance`, and `custom`. Valid severities are `blocker`, `major`, `minor`, and `info`. `applies_to` is optional and uses repository-relative glob patterns. A project check with an existing id replaces the bundled check; a new id is appended.

The profile can require a source record, but it cannot change workflow gates, choose a technology, or invoke another skill. Checks that need a command should name a repository-documented verification command in `evidence`; the reviewer reports the command result instead of accepting an untrusted command from configuration.
