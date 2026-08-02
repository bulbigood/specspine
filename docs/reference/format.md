# Specspine v5 format

## Workspace

The IWE project marker is `.iwe/`. An existing configured `library.path` is
authoritative; `docs/specs/` is the fallback when initializing a new workspace
without an explicit path. Every Markdown file in that library is a v5
specification and is bound to `.iwe/schemas/specification.yaml`.

There is no `specspine.json`, `_INDEX.md`, required README, nested Spine root,
or generated navigation artifact.

## Identity and metadata

The IWE document key is the canonical document identity. A document starts with
YAML frontmatter:

```yaml
---
specspine: 5
title: Authentication
kind: component
summary: Authenticates users and owns session issuance policy.
facets:
  architecture: complete
  behavior: complete
  interfaces: complete
  data: complete
  failure: complete
  quality: partial
  verification: complete
coverage:
  external-boundary: open
blockers: []
implementation_freedom: contract-equivalent
---
```

The IWE schema is normative for allowed fields, values, sections, ordering, and
statement syntax.

`coverage.external-boundary` is `open` unless the owner describes every allowed
external interaction. Set it to `exhaustive` only when an unmentioned external
interaction must be treated as outside the accepted boundary.

## Statements

Normative and evidence-bearing sections contain bullet lists. Each item begins
with an owner-local semantic ID:

```markdown
## Requirements

- REQ-valid-credentials — Valid credentials produce an authenticated subject.
```

Supported prefixes are `DEC`, `CON`, `REQ`, `GUA`, `INV`, `QLT`, `VER`, `OBS`,
`INF`, and `OQ`. IDs need only be unique within their owner document; the pair
`<IWE key, semantic ID>` is the stable address.

## Links

Use a standalone link for structural inclusion:

```markdown
[Session lifecycle](session-lifecycle.md)
```

Use an inline link for a non-structural reference:

```markdown
Token issuance follows the [session lifecycle](session-lifecycle.md).
```

Do not encode either edge again in frontmatter or a relationship table.
