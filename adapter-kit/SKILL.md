---
name: adapter-kit
description: Map an approved domain contract to replaceable backend, database, transport, or UI conventions.
---

# adapter-kit

1. Read one selected, versioned profile and map only the ports required by the approved use case.
2. Keep domain meaning independent of framework, database, transport, and UI; display wording stays at the presentation edge.
3. Reuse existing repository patterns; record unknown conventions as pending instead of guessing.
4. Verify adapters with focused contract tests and one observable path.
5. Report unsupported capabilities; never drop or reinterpret a core rule.

Do not add a generic abstraction without a second concrete consumer or pre-generate unused adapters.

