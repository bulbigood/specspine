# Documentation-first ToDo seeding

Use this protocol when exhaustive Map starts with existing specification nodes.

Before source inventory:

1. Read `README.md` and every live Markdown node.
2. Treat the graph as architecture memory, not presumed truth.
3. Extract bounded ToDo from partial/unmapped coverage, open questions, broad
   owners, weak relationships, missing failure/lifecycle/interface/data/
   operational depth, stale evidence, navigation gaps, and inconsistencies.
4. Anchor every task in a precise document location and state what is already
   known. A document title or “map this area deeper” is not a bounded task.
5. Give each task evidence likely to answer it and explicit sibling exclusions.

Save:

```json
{
  "evidence_inspected": ["README.md", "identity.md", "sessions.md"],
  "todo": [
    {
      "id": "identity-session-failures",
      "question": "Who owns recovery when expiry races with refresh?",
      "reason": "Normal expiry is covered but recovery ownership is absent",
      "evidence": ["src/identity", "tests/session-refresh.test.ts"],
      "documents": ["identity.md", "sessions.md"],
      "excludes": ["token issuance", "login", "storage deployment"],
      "anchor": {
        "document": "sessions.md",
        "location": "Lifecycle / active-to-expired transition",
        "known": "Creation and normal expiry ownership are established"
      }
    }
  ],
  "terminal_reason": null
}
```

`evidence_inspected` must equal the complete live Markdown inventory. If no
bounded direction exists, use an empty `todo` and:

```text
no documentation-derived ToDo: <evidence-based reason>
```

Record the seed before source classification:

```text
python3 <map-skill-root>/scripts/campaign.py seed-from-spine \
  <campaign> <spine-root> <documentation-plan.json>
```

The seed is only the initial ToDo. Later recursive depth comes from the root
integration pass rereading accepted documents and appending new anchored ToDo.
Producers never recurse or mutate this list themselves.
