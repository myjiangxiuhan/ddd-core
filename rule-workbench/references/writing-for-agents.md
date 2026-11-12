# Writing for agents

A context pointer is a short reference that names what a document contains and the branch that should trigger reading it. Make the pointer do the routing work.

- Put the trigger first and keep one trigger per branch.
- Do not repeat identity or body text in every pointer.
- Keep always-loaded instructions short; put branch-specific detail behind a pointer.
- Prefer exact verbs and state words over motivational prose.
- Spend context load on rules the agent must see every turn; spend cognitive load on questions and choices where the user must decide.
- When a rule is mechanical, implement a check. When it needs judgment, write a question or a decision record.
