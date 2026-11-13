---
rule_version: "1"
id: business-lab.working-agreement
---

# Human-led working agreement

Copy this file to `.ddd/working-agreement.md` and edit it with the user. The defaults deliberately slow the agent down.

```yaml
control_mode: human_led
decision_owner: user
diagram_author: user
question_style: one_concrete_question_per_turn
blank_protocol: options_then_one_blank
agent_permissions:
  - quote_user_language
  - organize_observations
  - ask_frontier_questions
  - detect_contradictions
  - render_confirmed_cards_as_mermaid
agent_forbidden:
  - choose_business_terms
  - invent_actors_or_rules
  - choose_boundaries
  - choose_aggregates
  - choose_technology
  - write_implementation
required_confirmations:
  - story
  - mainline
  - rules_and_authority
  - slice_boundary
```

The agent can propose a question or a diagram edit, but it must label it `agent_recommendation` and leave it `pending` until the user accepts or changes it. `human_led` is the default when this file or the ledger does not specify a different mode.
