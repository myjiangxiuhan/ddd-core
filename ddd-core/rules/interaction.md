---
rule_version: "1"
id: ddd.interaction
---

# Interaction and gate rules

- Use ddd-core alone for an ordinary requirement. Never auto-chain another skill or infer a gate from a draft.
- Require two separate, explicit user confirmations: first confirm the domain design, then approve implementation of one named command or minimal use case.
- Ask at most one question per round. A design remains `draft` until the first confirmation; implementation cannot begin until both confirmations are present.
- Do not read or invoke adapter-kit before the second confirmation.

