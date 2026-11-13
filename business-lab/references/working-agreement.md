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
interaction_mode: adaptive
ai_question_policy: one_micro_question
ai_suggestion_policy: options_when_blank
blank_protocol: concrete_case_then_options
review_policy: checklist_only
question_budget_per_turn: 1
write_back_after_cards: 3
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

Modes:

- `adaptive`: default. The agent asks one small memory prompt, waits for the user's words, and escalates to options only after `不知道`, vagueness, or an explicit request for help. When the user supplies an artifact, it switches to checklist review.
- `self_authored`: the user writes or draws first; the agent records and runs the checklist only after the user asks for review.
- `coached`: the user explicitly asks for guidance; the agent asks one concrete question per turn with 2-4 options and `不知道/其他`.

`one_micro_question` allows one prompt per turn, never a completed business answer. `options_when_blank` makes options a recovery aid, not a recommendation. The user can switch to `只记录`, `检查完整性`, `引导我`, or `自我设计` at any time. `human_led` is the default when this file or the ledger does not specify a different mode.
