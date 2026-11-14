# Skill repository glossary

This glossary defines the language of the skill system itself. A target project keeps its business language in `.ddd/GLOSSARY.md` or `.ddd/GLOSSARY-MAP.md`; those terms take precedence inside that project.

| Term | Meaning | Avoid using it as |
| --- | --- | --- |
| **user-invoked skill** | A workflow entrypoint the user explicitly names. It owns a bounded user-visible action and stops before another entrypoint. | an automatically selected route |
| **model-invoked skill** | A reusable method that an active workflow may call. It cannot make a material user decision or advance a gate. | a hidden implementation workflow |
| **entrypoint** | A user-invoked skill that starts or resumes one workflow. | a synonym for every skill |
| **gate** | A named condition in the workflow ledger that controls whether a later action is allowed. | a casual “ready” label |
| **transition** | One validated change from one ledger state to another. | a file edit or an inferred agreement |
| **decision** | A choice that changes scope, business meaning, authority, invariant, public seam, or technology commitment. | a suggestion or an implementation detail |
| **evidence** | A user statement, repository fact, cited source, or reproducible verification that supports a record. | a silent agent inference |
| **technology profile** | The exact application stack selected for the active slice. | a generic recommendation |
| **database profile** | The exact database engine, version, driver, migration boundary, and database-specific capabilities selected for a persistence slice. | a performance target |
| **performance contract** | The user-owned workload, budget, consistency, and measurement requirements for a slice. | a measured result |
| **baseline record** | Evidence bound to the exact baseline, contract, profile, dataset, commit, and slice. It is a shared project record, not a separate identity check. | a benchmark file that the agent may approve |
| **confirmed** | The user confirmed or corrected the content of a record. | permission to implement |
| **approved** | The user authorized one named slice or action to proceed. | confirmation of the whole project |
| **selected** | The user chose one exact profile. | permission to add alternatives |
| **hard stop** | A condition that prevents the skill from continuing until the named blocker is resolved. | a warning that can be ignored |
| **frontier** | The independent unanswered decisions whose prerequisites are already settled. | every possible question in the project |

The workflow status words remain defined by [`ddd-core/rules/keywords.md`](ddd-core/rules/keywords.md). Do not introduce a second synonym set in a skill.
