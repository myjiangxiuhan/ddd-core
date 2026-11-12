---
rule_version: "1"
id: ddd.codebase-design
---

# Codebase design vocabulary

Use these words consistently when a domain slice crosses into code design:

- **Module**: anything with an interface and an implementation.
- **Interface**: everything a caller must know, including invariants, ordering, errors, configuration, and performance characteristics.
- **Depth**: how much behavior a caller gets per unit of interface it must learn.
- **Seam**: the place where behavior can be changed without editing the caller; tests observe the seam.
- **Adapter**: a concrete thing that satisfies an interface at a seam.
- **Locality**: how much behavior can be understood and changed in one place.
- **Leverage**: how much caller complexity a module removes.

Do not substitute overloaded words such as “service”, “component”, “API”, or “boundary” when the distinction matters. DDD `boundary` remains a domain-context term; `seam` is the code-design term.

Before adding a new seam, state what it makes testable, what it hides, and what it leaves outside scope. Prefer one deep seam over several shallow wrappers.
