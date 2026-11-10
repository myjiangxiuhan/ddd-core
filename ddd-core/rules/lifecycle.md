---
rule_version: "1"
id: ddd.lifecycle
---

# Four-stage lifecycle

1. **Domain understanding**: read the nearest rules and records; extract evidence-backed domain facts and mark their evidence status.
2. **Domain design**: shape the smallest domain design and 2-4 acceptance scenarios.
3. **Single-slice implementation**: after the gates in `ddd.interaction`, implement only the approved command or minimal use case. ddd-core itself does not write implementation code.
4. **Verification and stop**: verify only the current slice and its acceptance scenarios, report the result, and stop.

The implementation boundary is one approved slice. Do not widen it, select or start a next slice, or invoke another skill automatically after verification.

