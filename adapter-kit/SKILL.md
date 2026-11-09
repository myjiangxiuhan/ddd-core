---
name: adapter-kit
description: Map an approved domain contract to replaceable backend, database, transport, or UI conventions.
---

# adapter-kit

1. Read the project's stack configuration (for example `.ddd/project.yaml`) and one selected, versioned profile; infer existing settings before asking.
2. Map only the ports required by the approved use case; a one-time project setting should not be repeated in every request.
3. Keep domain meaning independent of framework, database, transport, and UI; display wording stays at the presentation edge.
4. Reuse existing repository patterns, record unknown conventions as pending, and allow an explicit per-task profile override without changing defaults.
5. Verify adapters with focused contract tests and one observable path; report unsupported capabilities rather than changing a core rule.

Do not add a generic abstraction without a second concrete consumer or pre-generate unused adapters.
