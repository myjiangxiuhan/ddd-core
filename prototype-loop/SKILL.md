---
name: prototype-loop
description: Build a throwaway experiment to answer one design question before committing to production implementation.
---

# prototype-loop

This is a user-invoked design detour. Use it when paper reasoning cannot settle a state model, behavior, performance question, or UI interaction. A prototype is evidence, not production code.

## Process

1. State exactly one question and the observable result that would distinguish the options.
2. Declare the prototype boundary, inputs, success signal, time budget, and what will not be carried into production.
3. Build the smallest throwaway experiment in an isolated directory or branch. Keep it easy to delete or preserve as a primary source.
4. Run the experiment, capture the result, and compare it with the proposed options. Record facts, surprises, and unresolved decisions.
5. Return the evidence to the user and stop. A production slice still requires `$ddd-core` approval.

## Hard stops

- Do not silently promote prototype code into the product.
- Do not answer multiple unrelated design questions in one prototype.
- Do not invoke `$ddd-core`, `$adapter-kit`, or `$delivery-loop` automatically.
