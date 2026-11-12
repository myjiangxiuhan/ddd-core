# Project record layout

Keep durable project language and decisions in one place:

- `.ddd/GLOSSARY.md`: canonical terms, definitions, aliases, examples, source, and status.
- `.ddd/adr/NNNN-<decision>.md`: irreversible, cross-boundary, or surprising decisions.
- `.ddd/workflow-state.json`: current workflow state and gates.
- `.ddd/triage/`: raw issue reports and their triage briefs when no external tracker is configured.
- `.ddd/slices/`: one approved vertical-slice record per file when no issue tracker is configured.

Create files lazily. Define a term once. A glossary entry that changes meaning keeps its ID and records the change. An ADR records the decision and alternatives, not a copy of the entire design.

Only user-confirmed terms become canonical. Inferences stay marked as inferred; pending terms stay out of code and acceptance criteria.
