---
rule_version: "1"
id: ui-practices.schema
---

# UI practice profile

`.ddd/ui-practices.yaml` is the project's confirmed frontend practice profile. It records evidence and adopted rules separately so “best practice” never becomes an invisible implementation choice.

```yaml
schema_version: "1"
status: draft # draft -> confirmed after a separate user action
profile: react-antd-pro
profile_version: "1"
framework: react
framework_version: "<from lockfile>"
component_library: antd-pro
library_version: "<from lockfile>"
component_first:
  order: [library_primitive, profile_component, feature_component, logic_primitive, new_shared_component]
  wrapper_requires: [responsibility, owner, public_seam, reason, evidence, review_checks]
  second_consumer_required_for_shared: true
framework_rules: []
state_and_data:
  owner: pending
  derived_state: pending
  request_seam: pending
  async_states: [loading, empty, error, ready]
accessibility_and_testing:
  keyboard_and_focus: pending
  semantics: pending
  visual_regression: pending
  public_seam_tests: pending
deviations: []
sources: []
decisions: []
```

## Status rules

- A source-backed framework rule is an `agent_recommendation` until the user adopts or rejects it.
- A local precedent is evidence of convention, not proof that the convention is correct.
- A deviation must name its reason, owner, affected scope, and review check.
- The profile does not grant permission to implement. It is a prerequisite for `$ui-architecture`, `$scaffold-kit`, and UI review.
