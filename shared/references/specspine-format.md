# Specspine v5 format

## Workspace

The IWE project marker is `.iwe/`, and the recommended library for a new project
is `docs`. Ask an applicable IWE skill to resolve the project root and Markdown
library. If several roots plausibly own the task, ask the operator which one to
use before changing anything. Do not prescribe how the IWE skill discovers or
operates on the project.

Specspine documents live in a configured directory strictly below `library.path`. The default library-relative prefix is `specs`, so `library.path = "docs"` produces `docs/specs/`; a project may choose another contained prefix such as `architecture/specs`. The `specification` template key and schema match must use the same library-relative prefix. Other Markdown files in the IWE library remain ordinary IWE documents.

An existing configured `library.path` and compatible Specspine template/schema prefix are authoritative. Resolve physical paths from the library and derive IWE document keys relative to it; do not assume the default `docs/specs/` layout.

There is no `specspine.json`, `_INDEX.md`, required README, nested Spine root, or generated navigation artifact.

## Identity and metadata

The IWE document key is the canonical address of an owner. It is stable until
an explicit IWE-managed rename migrates the owner to a new key and rewrites
managed links. A rename does not change the owner's accepted meaning, but
external consumers that store a key must treat it as an address migration.
Specspine does not add a second document identifier beside IWE.

A document starts with YAML frontmatter:

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

An exhaustive boundary also requires `coverage.basis`, naming an owner-local `CON-*` statement that explicitly declares the enumerated external boundary complete. `basis` is forbidden for an open boundary. Schema validation checks the shape; semantic audit checks that the statement exists in the same owner and actually supplies the claimed authority.

Facet applicability depends on owner kind:

| Kind                                                         | Facets that cannot be `not-applicable`          |
| ------------------------------------------------------------ | ----------------------------------------------- |
| `system`, `subsystem`, `component`, `capability`, `behavior` | architecture, behavior, failure, verification   |
| `interface`                                                  | architecture, interfaces, failure, verification |
| `data`                                                       | architecture, data, failure, verification       |
| `policy`                                                     | architecture, behavior, verification            |
| `deployment`                                                 | architecture, failure, quality, verification    |
| `concept`                                                    | architecture                                    |

Kinds identify the owner's primary durable boundary:

| Kind | Use for |
| ---- | ------- |
| `system` | The highest-level product or service boundary in scope. |
| `subsystem` | A major durable boundary within a system. |
| `component` | An independently owned structural unit. |
| `capability` | A cohesive user- or business-visible ability that may span structure. |
| `behavior` | A cohesive behavioral contract without a separate structural boundary. |
| `interface` | A protocol or interaction boundary between parties. |
| `data` | An owned information model, schema, or durable dataset boundary. |
| `policy` | A durable rule set that constrains decisions or behavior. |
| `deployment` | A runtime topology, packaging, or operational boundary. |
| `concept` | A shared domain or architectural concept without independent behavior. |

Facets cover architecture, behavior, interfaces, data, failure behavior,
quality properties, and verification criteria. `complete` means the applicable
accepted contract is substantively specified, `partial` means some accepted
contract is present but known coverage is incomplete, `missing` means required
coverage is absent, and `not-applicable` means the concern does not apply to the
owner kind or boundary.

Optional `aliases` are alternate human-facing owner names; they are not keys or
parallel identifiers. Optional `inspection` records the repository-relative
source scope, inspection date, and evidence-inspection mode: `survey` is a broad
first pass, `deepen` is focused inspection of a known boundary, `refresh`
replaces stale recorded evidence after reinspection, and `drift` compares
current implementation evidence with the recorded specification state.

`verification: complete` requires at least one owner-local `VER-*` statement. A
normative asset with role `verification` may implement or support those
criteria, but it does not replace them; every listed `verifies` ID must resolve
to an owner-local `VER-*` statement. Other complete facets require substantive
accepted support in the applicable prose, statements, relationships, or
normative assets.

## Statements

Normative and evidence-bearing sections contain bullet lists. Each item begins with an owner-local semantic ID:

``` markdown
## Requirements

- REQ-valid-credentials — Valid credentials produce an authenticated subject.
```

Prefix meanings, section placement, and authority are defined in
[Specspine semantics](specspine-semantics.md#semantic-statements). IDs must be
unique within their owner document. The pair `<IWE key, semantic ID>` is the
canonical statement address and migrates when its owner is renamed.

Every ID in `blockers` must identify an `OQ-*` statement in the same owner.

## Assets

An asset registered with `normative: true` is part of accepted intent. An asset with `normative: false` is evidence or supporting material and cannot override a normative statement. The `role` field describes how the asset participates in the specification. The asset remains owned by its native repository format; Specspine records only its repository-relative path, role, format, authority, and optional owner-local `VER-*` targets. Asset paths must not be absolute, escape through `..`, or contain backslashes. Semantic audit confirms that each path exists as a regular file inside the workspace.

Asset roles are `interface-contract` for protocol or API definitions,
`data-schema` for machine-readable data structure, `scenario` for behavioral
examples, `fixture` for reusable verification inputs, and `verification` for an
artifact that implements or supplies verification evidence.

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
