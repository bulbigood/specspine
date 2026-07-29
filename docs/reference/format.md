# SpecSpine v3 format

This document is the canonical storage contract for SpecSpine v3.

The stored `specspine` integer is the format major. SpecSpine tooling and
skill releases use semantic versions independently: minor and patch releases
MUST continue to accept the same v3 storage contract. Change the stored integer
only for a breaking storage or semantic-contract change; do not store tool
minor or patch versions in a Spine.

SpecSpine is a human-readable specification graph plus a small deterministic
manifest. Markdown specification nodes own meaning. `specspine.json` owns
completeness, reconstruction blockers, and exact non-Markdown assets.
Deterministic `_INDEX.md` files, embeddings, databases, and workspace graphs
are disposable.

## Spine root

Resolve `<spine-root>` once:

1. use the path explicitly supplied by the user or project instructions;
2. otherwise use a path explicitly named by project configuration;
3. otherwise use `specspine` below the working directory.

A valid root contains:

```text
<spine-root>/
├── _INDEX.md
├── specspine.json
├── authentication.md
├── session-management.md
├── contracts/
├── schemas/
├── scenarios/
├── fixtures/
└── verification/
```

Every directory in the Spine contains `_INDEX.md`. Only root `_INDEX.md` and
`specspine.json` have reserved root paths. Use lowercase
kebab-case paths for specifications. Organize by stable concepts, not source
directories, features, tickets, or delivery phases.

Write natural language in the configured SpecSpine documentation language.
Never translate paths, semantic IDs, API names, code identifiers, or other
exact identifiers.

## Manifest

`<spine-root>/specspine.json` is mandatory UTF-8 JSON. Its portable structural
schema is `shared/references/specspine.schema.json`. Installed skill packages
expose the same schema beside this reference as `specspine.schema.json`:

```json
{
  "specspine": 3,
  "project": "example",
  "implementation_freedom": "contract-equivalent",
  "areas": [
    {
      "owner": "session-management",
      "facets": {
        "architecture": "complete",
        "behavior": "complete",
        "interfaces": "complete",
        "data": "complete",
        "failure": "complete",
        "quality": "partial",
        "verification": "complete"
      },
      "blockers": [],
      "inspection": {
        "source": "commit-abc1234",
        "inspected": "2026-07-29",
        "mode": "refresh",
        "facets": {
          "architecture": "checked",
          "behavior": "checked",
          "interfaces": "checked",
          "data": "not-checked",
          "failure": "checked",
          "quality": "not-checked",
          "verification": "not-checked"
        }
      }
    }
  ],
  "assets": [
    {
      "path": "contracts/sessions.openapi.yaml",
      "owner": "session-management",
      "role": "interface-contract",
      "format": "openapi-3.1",
      "normative": true,
      "verifies": []
    }
  ]
}
```

The root object has these required fields:

- `specspine`: integer `3`;
- `project`: nonempty stable project name;
- `implementation_freedom`: `contract-equivalent`,
  `architecture-constrained`, or `exact`;
- `areas`: one completeness profile for every non-index document;
- `assets`: the complete registry of non-Markdown files in the Spine.

It may also contain `presentation`, the constrained rendering profile described
below. No other root fields are allowed.

Each area may contain an optional `inspection` record. It states which
repository-facing facets were actually inspected by Map at one evidence
baseline. It is distinct from specification completeness and never claims
implementation conformance. `source` identifies the inspected repository
state, `inspected` is an ISO date, `mode` is `survey`, `deepen`, `refresh`,
`drift`, or `exhaustive`, and every facet is `checked` or `not-checked`. Absence of `inspection`,
or a `not-checked` facet, means no current comparison claim.

### Presentation profile

Format v3 has one data and semantic model. An optional `presentation` object
may localize and order its Markdown rendering without creating a project-
specific dialect:

```json
{
  "profile": 1,
  "language": "ru",
  "headings": {
    "responsibility": "Ответственность",
    "boundaries": "Границы",
    "behavior": "Поведение"
  },
  "section_order": [
    "responsibility",
    "boundaries",
    "behavior",
    "interfaces",
    "information-model",
    "data-ownership",
    "lifecycle-and-invariants",
    "failure-behavior",
    "edge-cases",
    "configuration-contract",
    "compatibility",
    "relationships",
    "requirements",
    "guarantees",
    "invariants",
    "quality-constraints",
    "verification",
    "decisions",
    "constraints",
    "known-divergences",
    "observed",
    "inferred",
    "open-questions",
    "implementation",
    "risks",
    "rationale-and-trade-offs",
    "terminology"
  ]
}
```

`profile` is integer `1`. `language` is a nonempty BCP 47-style language tag.
`headings` is a partial mapping from the canonical keys listed in
`section_order` to unique rendered headings. Omitted headings retain their
English rendering. When `section_order` is present it contains every canonical
key exactly once; documents still omit empty sections.

The default order presents the owned architectural model and relationships
first, exact accepted claims next, then `Known divergences` before supporting
`Observed`, `Inferred`, and `Open questions`. Implementation navigation and
context follow last.

Canonical Markdown MUST NOT hide semantic sections or statements inside HTML
disclosure elements such as `<details>`. Collapsing is a renderer or IDE
presentation concern; derived views may collapse supplementary content without
changing canonical Markdown.

An optional `index` mapping configures only deterministic index text:
`root-title` (containing `{project}` exactly once), `purpose`, `scope`,
`guide-heading`, `guide`, `contents-heading`, `nested-heading`, and `empty`.

The profile MUST NOT change document identity, kinds, facets, statement
prefixes, relations, assets, blockers, authority, or reconstruction semantics.
Agents read it before writing Markdown. Mechanical tools resolve rendered
headings back to canonical keys before validation or retrieval.

The JSON schema owns portable manifest shape.
`shared/references/vocabulary.json` owns every reserved token, identifier
family, document kind, relation, and enumerated format value. The generated
glossary is its human-readable index. The shared `spec_contract.py` module
loads that vocabulary and owns presentation behavior consumed by Checker,
Extract, bootstrap, and index generation; consumers must not copy its values.

`implementation_freedom` defines what reconstruction means:

- `contract-equivalent` permits any internals satisfying all normative
  behavior, interfaces, data rules, qualities, and verification;
- `architecture-constrained` additionally requires the specified component
  boundaries and interactions;
- `exact` requires implementation choices explicitly declared exact by the
  specifications. It does not turn undocumented source details into intent.

### Areas and computed status

Every non-index document ID occurs exactly once as an area `owner`. `facets`
contains exactly:

```text
architecture behavior interfaces data failure quality verification
```

Each value is `complete`, `partial`, `missing`, or `not-applicable`.
`not-applicable` is a semantic claim and requires review; it is not a shortcut
for unknown content.

The document kind determines facets that cannot be `not-applicable`:

| Kind | Required facets |
|---|---|
| `system`, `subsystem`, `component`, `capability` | architecture, behavior, failure, verification |
| `behavior` | architecture, behavior, failure, verification |
| `interface` | architecture, interfaces, failure, verification |
| `data` | architecture, data, failure, verification |
| `policy` | architecture, behavior, verification |
| `deployment` | architecture, failure, quality, verification |
| `concept`, `x-*` | architecture |

Status is never stored:

- `blocked` when `blockers` is nonempty;
- `ready` when blockers are empty and every facet is `complete` or
  `not-applicable`;
- `incomplete` otherwise.

A `complete` verification facet requires at least one owned `VER-*` claim, an
owned verification asset, or a `verified-by` relation to a document that owns
`VER-*` claims.

For every other `complete` facet, the owner MUST contain semantic support in
its applicable prose, claims, relationships, or registered assets. The checker
reports conventional machine-resolvable support gaps as warnings because
translated headings and prose-only contracts require semantic review. A
warning does not downgrade the stored facet, and a mechanically supported
facet is not proof of semantic completeness.

Each blocker is the globally unique `OQ-*` ID of an unresolved choice that a
reconstruction agent MUST NOT invent. Non-blocking questions remain in
Markdown but are absent from `blockers`.

### Asset registry

Every non-Markdown file except `specspine.json` has exactly one asset record.
Each record has exactly:

- `path`: unique root-relative path;
- `owner`: non-index document ID;
- `role`: `interface-contract`, `data-schema`, `execution-contract`,
  `scenario`, `fixture`, or `verification`;
- `format`: nonempty precise format identifier;
- `normative`: whether conformance depends on the asset;
- `verifies`: zero or more globally unique `VER-*` IDs.

The file MUST exist and its owner MUST link to it using a relative Markdown
link. Registration establishes identity and machine retrieval; the owner
explains purpose, scope, versioning, and authority.

Use an `execution-contract` only when reconstruction depends on exact
toolchains or versions, deployable or build units, required generators, or
build and verification entry points. Its Markdown owner explains which fields
are normative and why. Do not register ordinary lockfiles, build output,
implementation scripts, or incidental local tooling. Connect the affected
owner through a precise relation such as `specified-by`, `constrained-by`, or
`depends-on` so task closure retrieves the contract when it applies.

## Deterministic indexes

Root `_INDEX.md` is the entry point. Every `_INDEX.md` contains:

1. exactly one H1;
2. a globally unique document ID and `Kind: index`;
3. a deterministic `Contents` list linking every immediate file except itself
   and the `_INDEX.md` of every immediate subdirectory.

The root uses ID `project-architecture`. Nested index IDs are derived
deterministically from their root-relative directory paths. Only the root
index contains the fixed SpecSpine purpose statement, project name, scope
statement, and compact reading guide. The guide makes the committed Spine
self-describing for agents and people without installed SpecSpine skills. It
explains authority, navigation, identifier families, divergence handling, and
canonical ownership; skills optimize retrieval and maintenance but are not
required to interpret the format.

Use this scope statement when creating an index, translated when needed:

> This directory contains the project's long-lived architectural intent and
> architecture-relevant repository observations.

Indexes are exhaustive physical navigation, not semantic parents and not
owners of project claims. Generate and update them only through the canonical
index script. Put all normative statements, observations, divergences, and
questions in non-index specification owners.

Completeness does not live in Markdown. Readers and tools obtain it from
`specspine.json`.

Do not add `Coverage`, `SpecSpine readiness`, `Reconstruction status`, or
`Facet status` sections to Markdown. These are computed views over
`specspine.json`, not durable specification content.

## Specification node

Every non-index Markdown document has:

```markdown
# Session management

**ID:** `session-management` · **Kind:** `subsystem`
**Aliases:** Application sessions

Creates and maintains provider-independent application sessions.

## Responsibility

Owns session lifecycle and session state.
```

There is exactly one H1. The summary immediately follows identity and optional
aliases. `Responsibility` is mandatory and nonempty.

Document IDs match:

```regex
^[a-z0-9]+(?:-[a-z0-9]+)*$
```

They are globally unique, stable across rename or move, independent of paths,
never reused, and preserved by tombstones when ownership moves.

Core kinds are:

```text
index system subsystem component capability behavior interface data policy
deployment concept
```

Kinds classify architectural ownership. Requirements, guarantees, invariants,
decisions, quality constraints, and verification are addressable statements,
not document kinds. Project-specific kinds use `x-*`.

## Canonical sections

Use only sections that carry durable information:

- `Responsibility` — canonical ownership;
- `Boundaries` — what is inside, outside, or owned elsewhere;
- `Behavior` — externally significant outcomes and coordination;
- `Interfaces` — APIs, commands, events, ports, and exact asset links;
- `Information model` — durable entities, values, and relationships;
- `Data ownership` — creation, mutation, reading, and consistency authority;
- `Lifecycle and invariants` — states, transitions, and durable truths;
- `Failure behavior` — errors, retry, degradation, compensation, and recovery;
- `Edge cases` — only architecture-significant boundaries;
- `Configuration contract` — settings, defaults, precedence, invalid
  combinations, and reload behavior;
- `Compatibility` — versioning, interoperability, deprecation, and supported
  data or protocol evolution;
- `Requirements` — accepted durable outcomes;
- `Guarantees` — accepted externally observable promises;
- `Invariants` — truths across all valid states and transitions;
- `Quality constraints` — measurable non-functional requirements;
- `Verification` — implementation-independent conformance criteria;
- `Decisions` and `Constraints` — accepted intent;
- `Observed` — selected architecture-significant exception evidence, never an
  implementation inventory;
- `Inferred` — explicitly unconfirmed interpretation;
- `Open questions` — unresolved choices;
- `Known divergences` — confirmed differences between intent and reality;
- `Implementation` — representative repository-relative evidence paths;
- `Terminology`, `Risks`, and `Rationale and trade-offs` when durable.

Do not store plans, tasks, delivery acceptance, progress, changelogs, generated
source walkthroughs, or temporary feature deltas. Promote accepted durable
meaning into its canonical owner.

## Normative statements

Use RFC 2119-style `MUST`, `SHOULD`, and `MAY` only for accepted intent.
Observations and inferences never create normative meaning.

Create a semantic ID only when another statement, asset, or workflow needs an
exact address. Definitions are bullets inside at most one marker region:

```markdown
<!-- specspine:semantic-ids:begin -->
## Guarantees

- **GUA-session-revocation** — A revoked session MUST fail all subsequent
  authorization checks.

## Verification

- **VER-session-revocation** — After revocation, every protected request made
  with the session returns the documented unauthenticated result.
<!-- specspine:semantic-ids:end -->
```

IDs match:

```regex
^(DEC|CON|REQ|GUA|INV|QLT|VER|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$
```

Definitions use bold IDs. References use the complete ID as a Markdown link
label and target the owning document:

```markdown
[GUA-session-revocation](session-management.md)
```

Do not add a URL fragment. Semantic IDs are globally unique in v3. A replaced
statement retains a tombstone linked to its successor.

Canonical headings determine prefixes: `Decisions`/`DEC`,
`Constraints`/`CON`, `Requirements`/`REQ`, `Guarantees`/`GUA`,
`Invariants`/`INV`, `Quality constraints`/`QLT`, `Verification`/`VER`,
`Observed`/`OBS`, `Inferred`/`INF`, and `Open questions`/`OQ`.
Translated headings preserve the same meaning; semantic review confirms them
when a dependency-free checker cannot.

## Evidence and divergences

A repository fact qualifies for `OBS` only under the retention rules in the
semantics reference: it exposes a material intent gap, supports a confirmed
divergence, affects an unresolved architectural question, or provides necessary
navigation to a surprising owner or boundary. Evidence already represented by
accepted intent belongs only in inspection coverage.

A document containing repository observations records one evidence baseline
near its first `Observed` section:

```markdown
<!-- specspine:evidence-baseline source=commit-abc1234; inspected=2026-07-21 -->
```

Use representative repository-relative inline-code paths:

```markdown
- **OBS-worker-retries** — Failed jobs are retried.
  Evidence: `src/worker.ts`, `tests/job-retry.test.ts`.
```

Every `Evidence:` code span is one complete repository-relative path. Do not
shorten subsequent paths by inheriting a directory prefix from an earlier
span. Map validates these paths against its recorded repository root.

Confirmed conflict is recorded once:

```markdown
## Known divergences

| Intended | Observed | Consequence |
|---|---|---|
| [CON-retry-limit](jobs.md) | [OBS-unbounded-retry](jobs.md) | A job can consume unbounded capacity |
```

`Intended` references a normative ID, `Observed` references an `OBS-*` ID, and
`Consequence` states architectural or user-visible impact.

## Typed relationships

Typed edges use:

```markdown
## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `constrained-by` | [CON-retry-limit](jobs.md) | Applies the system retry ceiling |
```

Each row has one canonical relation token, one relative link, and nonempty
meaning. Store a directed edge once; derive backlinks.

Core relations are:

```text
contains decomposes-into performs depends-on exposes consumes publishes
reads-from writes-to owns-data constrained-by implemented-by has-evidence
superseded-by related-to refines satisfies verified-by specified-by
compatible-with migrates-from
```

Extensions use `x-*`. Ordinary Markdown links remain navigation or references;
they do not become typed edges.

`contains` and `decomposes-into` MUST be acyclic. Use `related-to` only when no
more precise relation is justified.

## Decomposition and reachability

Split a node when a concern has independent ownership, lifecycle, contracts,
constraints, consumers, or evolution. Do not split merely because a document
is long. Do not mirror classes or directories.

Every Markdown specification MUST be reachable from root `_INDEX.md` through
relative links. Every registered asset is reached from its canonical owner.
Generated views and external links do not establish reachability.

A nested directory containing its own `_INDEX.md` and `specspine.json` is a
separate Spine and a traversal boundary. Its documents, IDs, manifest areas,
and assets do not belong to the parent Spine. Workspace tooling connects the
nearest ancestor Spine to the nested root and records otherwise independent
top-level roots in the disposable workspace graph.

## Reconstruction invariant

An area is `ready` only when a capable agent can implement it without source
access or policy invention, using the selected closure, registered assets, and
verification criteria. `ready` claims contract or architecture equivalence
according to `implementation_freedom`; it never claims source-code identity
unless exact choices are themselves specified.
