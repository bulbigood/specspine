# SpecSpine agent-bootstrap contract

## Purpose

The bootstrap gives every project agent a stable route to architectural
context. It prefers the installed extraction skill and preserves direct graph
navigation as a degraded fallback. It is project configuration, not
architecture and not a downstream workflow adapter.

| Artifact | Role | Load behavior |
|---|---|---|
| `specspine-extract` | Minimal task-oriented context retrieval | Architecture-relevant downstream tasks |
| `<spine-root>/README.md` and linked specs | Canonical claims and retrieval fallback | Relevant tasks |
| Persistent instruction block | Retrieval route, authority, conflict rule | Every agent turn |
| Feature specs, plans, tasks, code, tests | Downstream artifacts | Owned downstream |

## Authority

- `Decisions` and `Constraints` express accepted intent.
- `Observed` is repository evidence, not required intent.
- `Inferred` is unconfirmed.
- `Open questions` remain unresolved and may block downstream work.

Downstream artifacts must not silently replace accepted architecture. Preserve
disagreements and never infer that documented intent is implemented.

## Bootstrap

Keep the managed block small enough for every turn. It contains only:

1. the resolved index path;
2. the resolved SpecSpine documentation language;
3. when to use `specspine-extract`;
4. direct index-and-link fallback when extraction is unavailable;
5. compact authority and conflict semantics.

Use exactly one managed region:

```markdown
<!-- specspine:begin -->
...
<!-- specspine:end -->
```

Do not include framework commands, directory maps, copied architecture,
bindings, adapters, or downstream workflow instructions. Naming
`specspine-extract` as the framework-neutral retrieval route is part of this
contract, not workflow adaptation.

Preserve the language from an existing managed block. Otherwise resolve it from
the current request, applicable project instructions, or the SpecSpine index;
ask only if these sources are ambiguous.

## Ownership

The bootstrap owns only text inside its managed markers. Refresh idempotently.
Do not overwrite content outside the region, remove user-owned files, or create
additional artifacts.
