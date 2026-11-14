---
rule_version: "1"
id: ui-system.schema
---

# UI system record

`.ddd/ui-system.yaml` is a project-level design contract. It separates source-backed observations from user-owned visual decisions and keeps implementation mappings out of the domain workflow.

```yaml
schema_version: "1"
status: draft # draft -> confirmed after a separate user action
profile: react-antd-pro
profile_version: "1"
scope: project
tokens:
  format: dtcg-2025.10-or-local-compatible
  primitive_groups: [color, typography, spacing, sizing, radius, border, elevation, motion, breakpoint, z_index]
  semantic_roles: [surface, text, border, action, focus, success, warning, danger]
  source: pending
themes:
  - id: light
    selection: pending
    semantic_overrides: pending
  - id: dark
    selection: pending
    semantic_overrides: pending
layout:
  shell: pending
  regions: []
  container: pending
  density: pending
  breakpoints: pending
  responsive_rules: []
accessibility:
  contrast: pending
  keyboard_and_focus: pending
  reduced_motion: pending
  text_scaling: pending
  touch_targets: pending
visual_states: [loading, empty, error, disabled, ready]
non_goals: []
decisions: []
evidence: []
```

## Record rules

- Primitive tokens describe scales; semantic tokens describe meaning. Components should consume semantic roles.
- A theme records behavior as well as colors: selection, persistence, system preference, fallback, contrast, and runtime switching.
- A layout record names regions and transformations, not component filenames or CSS selectors.
- The system may contain recommendations, but `status: confirmed` requires the user's confirmation of the material choices.
- A page-specific exception belongs in `.ddd/ui-plan.yaml`, with a reason and owner; it does not silently change the project system.

## Sources

Start with the selected profile's exact official documentation. For a technology-neutral token exchange format, consult the [Design Tokens Community Group](https://www.w3.org/community/design-tokens/) and its [2025.10 format report](https://w3c.github.io/cg-reports/design-tokens/CG-FINAL-format-20251028/). Treat the format as an interoperability aid, not as a reason to select a tool.
