# Specspine v5 format

## Workspace

The IWE project marker is `.iwe/`. The recommended library is `docs`, initialized with:

``` bash
iwe init --auto --library docs
```

Before any IWE command, resolve the applicable project root by checking the task working directory and its ancestors for `.iwe/config.toml`. For a task that explicitly spans packages, also inspect only the task-relevant descendants. Run IWE from the directory containing the selected `.iwe/`. If several roots plausibly own the task, ask the operator which one to use before changing anything. Do not assume that IWE invoked below a project root will discover its ancestor configuration.

Specspine documents live in a configured directory strictly below `library.path`. The default library-relative prefix is `specs`, so `library.path = "docs"` produces `docs/specs/`; a project may choose another contained prefix such as `architecture/specs`. The `specification` template key and schema match must use the same library-relative prefix. Other Markdown files in the IWE library remain ordinary IWE documents.

An existing configured `library.path` and compatible Specspine template/schema prefix are authoritative. Resolve physical paths from the library and derive IWE document keys relative to it; do not assume the default `docs/specs/` layout.

There is no `specspine.json`, `_INDEX.md`, required README, nested Spine root, or generated navigation artifact.

## Identity and metadata

The IWE document key is the canonical document identity. A document starts with YAML frontmatter:

``` yaml
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

The IWE document schema is normative for allowed fields, values, sections, ordering, and statement syntax. Cross-statement conditions that the schema cannot express remain semantic validation rules.

`coverage.external-boundary` is `open` unless the owner describes every allowed external interaction. Set it to `exhaustive` only when an unmentioned external interaction must be treated as outside the accepted boundary.

## Statements

Normative and evidence-bearing sections contain bullet lists. Each item begins with an owner-local semantic ID:

``` markdown
## Requirements

- REQ-valid-credentials — Valid credentials produce an authenticated subject.
```

Supported prefixes are `DEC`, `CON`, `REQ`, `GUA`, `INV`, `QLT`, `VER`, `OBS`, `INF`, and `OQ`. IDs must be unique within their owner document; the pair `<IWE key, semantic ID>` is the stable address.

Every ID in `blockers` must identify an `OQ-*` statement in the same owner.

## Assets

An asset registered with `normative: true` is part of accepted intent. An asset with `normative: false` is evidence or supporting material and cannot override a normative statement. The `role` field describes how the asset participates in the specification. The asset remains owned by its native repository format; Specspine records only its path, role, format, and authority.

## Links

Use a link that is the only content of its paragraph for structural inclusion:

``` markdown
[Session lifecycle](session-lifecycle.md)
```

Use an inline link for a non-structural reference:

``` markdown
Token issuance follows the [session lifecycle](session-lifecycle.md).
```

Do not encode either edge again in frontmatter or a relationship table.
