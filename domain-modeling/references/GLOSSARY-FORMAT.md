---
rule_version: "1"
id: domain-modeling.glossary
---

# Canonical glossary format

Create this file lazily. Keep it short enough for a domain expert to review.

```markdown
# GLOSSARY

## File lifecycle

| id | Canonical term | What it is | Context | Display terms | Technical mapping | Aliases to avoid | Status | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| file-entry | File entry | A user's named reference to a stored file in a folder. | file-management | 文件、文件项 | `FileEntry` | object, blob, document | confirmed | business-lab/mainline.md |

### Relationships

- A **File entry** belongs to one **Folder**.
- A **File entry** may refer to one **Content identity**; the storage strategy is deferred.

### Example dialogue

> Domain expert: ...
> Designer: ...
```

Rules:

- `id` is stable and survives wording corrections.
- `Canonical term` is one phrase for one meaning inside the named context.
- `What it is` is one sentence about the business concept, not its implementation.
- `Display terms` and `Technical mapping` are references, not alternate domain names.
- `Aliases to avoid` is guidance for new records; preserve historical language in evidence.
- `Status` is `pending`, `confirmed`, `deprecated`, or `conflicted`.
- Every confirmed term has a source and at least one concrete example or relationship.

## Multiple contexts

When the same word has different meanings, create `.ddd/GLOSSARY-MAP.md`:

```markdown
# GLOSSARY MAP

| Context | Glossary | Meaning of `account` |
| --- | --- | --- |
| identity | `src/identity/GLOSSARY.md` | A sign-in identity. |
| billing | `src/billing/GLOSSARY.md` | The party responsible for payment. |
```

The map is a routing index. Each context glossary owns its terms and examples.
