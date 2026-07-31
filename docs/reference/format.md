# SpecSpine v4 format

This document is the canonical storage and semantic contract for SpecSpine v4.

The stored `specspine` integer is the format major. SpecSpine tooling and
skill releases use semantic versions independently: minor and patch releases
MUST continue to accept the same v4 contract. Change the stored integer
only for a breaking storage or semantic-contract change; do not store tool
minor or patch versions in a Spine.

SpecSpine is a human-readable specification graph plus a small deterministic
manifest. Markdown specification nodes own meaning. `specspine.json` owns
completeness, reconstruction blockers, and normative non-Markdown assets.
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
├── README.md
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

Every directory in the Spine contains `_INDEX.md`. Root `README.md`,
`_INDEX.md`, and `specspine.json` have reserved root paths. Use lowercase
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
  "specspine": 4,
  "project": "example",
  "implementation_freedom": "contract-equivalent",
  "mapping": {
    "frontier": [
      {
        "id": "session-audit",
        "anchor_owner": "session-management",
        "title": "Session audit",
        "question": "Which session transitions and retention boundary does audit own?",
        "reason": "Session evidence exposes a distinct retained event lifecycle.",
        "seed_paths": ["src/audit/session-events.ts"]
      }
    ],
    "observed_edges": []
  },
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

- `specspine`: integer `4`;
- `project`: nonempty stable project name;
- `implementation_freedom`: `contract-equivalent` or
  `architecture-constrained`;
- `areas`: one completeness profile for every non-index document;
- `assets`: the complete registry of non-Markdown files in the Spine.

It may also contain `presentation`, the constrained rendering profile described
below, and `mapping`, the non-normative repository mapping state described
below. No other root fields are allowed.

Each area may contain an optional `inspection` record. It states which
repository-facing facets were actually inspected by Map at one evidence
baseline. It is distinct from specification completeness and never claims
implementation conformance. `source` identifies the inspected repository
state, `inspected` is an ISO date, `mode` is `survey`, `deepen`, `refresh`,
or `drift`, and every facet is `checked` or `not-checked`. Absence of `inspection`,
or a `not-checked` facet, means no current comparison claim.
Repository-derived `OBS`, `INF`, evidence, and inspection coverage MUST NOT
raise a completeness facet. A new observation-only owner starts with every
facet `missing`; Map preserves the accepted facets of an existing owner.

### Repository mapping state

The optional `mapping` object contains exactly `frontier` and
`observed_edges`. It records repository discovery, not accepted architecture,
completeness, conformance, or delivery work.

`frontier` is an ordered array of candidate owners available to a future
one-step Map expansion. Each entry contains:

- `id`: the proposed stable owner ID; it MUST NOT already belong to a document;
- `anchor_owner`: the existing non-index owner near which the candidate was
  discovered; it does not assert containment, parentage, or edge direction;
- `title`: a concise human-readable candidate title;
- `question`: the concrete boundary question for the next inspection;
- `reason`: why the candidate appears independently useful;
- `seed_paths`: one or more unique, safe repository-relative starting paths.

Candidate IDs are unique within the frontier. A successful expansion consumes
exactly one entry. Newly exposed adjacent candidates may be appended but MUST
NOT be created as documents in the current operation. A disproved candidate is
removed; an unresolved candidate is preserved.

`observed_edges` is the machine-traversable repository-observed owner graph.
Each entry contains exactly:

- `source_owner`: an existing non-index owner at the interaction source;
- `target_owner`: a distinct existing non-index owner at the interaction target;
- `observation`: an `OBS-*` statement defined by either endpoint.

The referenced observation is the SSOT for edge meaning and evidence. An
observed edge is non-normative and MUST NOT be rendered as a canonical
`Relationships` row. Evolve may promote its accepted meaning into a canonical
typed relationship and then remove the observed edge. Remove an edge when its
observation becomes stale or is removed.

### Presentation profile

Format v4 has one data and semantic model. An optional `presentation` object
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
`guide-heading`, `guide`, `glossary-heading`, `glossary`,
`contents-heading`, `nested-heading`, and `empty`. The default `glossary` is
generated from the canonical vocabulary and briefly defines every reserved
identifier family, document kind, section key, relation, facet, manifest
value, asset role, manifest or Markdown field, normative keyword, marker, and
path. A localized override MUST preserve that complete token coverage.

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
- `architecture-constrained` additionally requires explicitly accepted owner
  boundaries, interactions, topology, and mechanisms.

Neither value permits canonical documents to describe private implementation.
An architecture constraint is admissible only when the accepted system
contract intentionally restricts replacement implementations.

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
- `role`: `interface-contract`, `data-schema`, `scenario`, `fixture`, or
  `verification`;
- `format`: nonempty precise format identifier;
- `normative`: whether conformance depends on the asset;
- `verifies`: zero or more globally unique `VER-*` IDs.

The file MUST exist and its owner MUST link to it using a relative Markdown
link. Registration establishes identity and machine retrieval; the owner
explains purpose, scope, versioning, and authority.

Do not register lockfiles, build output, implementation scripts, toolchain
recipes, or incidental local tooling. An accepted topology or mechanism is
stated as an architecture constraint and related to its canonical owner; the
private recipe that implements it remains outside the Spine.

## Deterministic indexes

Root `README.md` is the human and agent introduction. It contains the fixed
SpecSpine purpose statement, project name, scope statement, compact reading
guide, and complete concise vocabulary.

Every `_INDEX.md`, including the root index, has the same deterministic
navigation structure and contains:

1. exactly one H1;
2. a globally unique document ID and `Kind: index`;
3. a deterministic `Contents` list linking every immediate file except itself
   and the `_INDEX.md` of every immediate subdirectory.

The root uses ID `project-architecture`. Nested index IDs are derived
deterministically from their root-relative directory paths. Root `README.md`
makes the committed Spine self-describing for agents and people without
installed SpecSpine skills. It explains authority, navigation, identifier
families, divergence handling, and canonical ownership; skills optimize
retrieval and maintenance but are not required to interpret the format.

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

**Summary:** Creates and maintains provider-independent application sessions.

## Responsibility

Owns session lifecycle and session state.
```

There is exactly one H1. The required, nonempty, single-line `Summary` field
immediately follows identity and optional aliases. Its short description is
rendered next to the document link in deterministic indexes. `Responsibility`
is mandatory and nonempty. Unlabelled summary paragraphs are invalid.

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

- `Responsibility` — canonical boundary ownership;
- `Boundaries` — accepted inputs, emitted outputs, controls, owned authority,
  and delegated responsibilities;
- `Behavior` — owner-relative observable outcomes and coordination;
- `Interfaces` — boundary APIs, commands, events, ports, and contract links;
- `Information model` — durable entities, values, and relationships;
- `Data ownership` — creation, mutation, reading, and consistency authority;
- `Lifecycle and invariants` — boundary-visible states, transitions, and truths;
- `Failure behavior` — boundary-visible errors, retry, degradation,
  compensation, and recovery;
- `Edge cases` — only boundary-significant conditions;
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
- `Observed` — selected boundary-significant exception evidence, never an
  implementation inventory;
- `Inferred` — explicitly unconfirmed interpretation;
- `Open questions` — unresolved choices;
- `Known divergences` — confirmed differences between intent and reality;
- `Implementation` — two to six non-normative representative
  repository-relative navigation anchors, never a walkthrough;
- `Terminology`, `Risks`, and `Rationale and trade-offs` when durable.

Do not store plans, tasks, delivery acceptance, progress, changelogs, private
algorithms, call sequences, helpers, framework state, generated source
walkthroughs, or temporary feature deltas. Promote accepted durable boundary
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

Do not add a URL fragment. Semantic IDs are globally unique in v4. A replaced
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

Repository comparison may publish OBS-backed interactions under
`mapping.observed_edges`, but it MUST NOT publish those observations as
canonical `Relationships`. Preserve existing accepted edges exactly; promote
an observed edge only through an intent-authorized workflow such as Evolve.

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

Plan directories as semantic navigation groups. Treat about 20 immediate index entries
as a soft density threshold, not a format limit: when a directory would
list more, explicitly reconsider whether stable conceptual subgroups or reading
routes justify child directories. Count each immediate specification file and
each immediate child-directory `_INDEX.md` as one entry. Never create arbitrary
numbered buckets, mirror source layout, or separate one coherent owner merely
to satisfy the threshold; a dense directory is valid when no durable semantic
grouping improves navigation.

Map applies this rule only while choosing paths for new owners. It MUST preserve
every existing owner's document path and may place new coherent groups in child
directories without moving existing documents. Evolve applies the same rule to
initialization and structural change and may move existing documents when the
approved operation permits reorganization, while preserving document IDs,
links, relationships, assets, and reachability.

Every Markdown specification MUST be reachable from root `_INDEX.md` through
relative links. Every registered asset is reached from its canonical owner.
Generated views and external links do not establish reachability.

A nested directory containing its own `README.md`, `_INDEX.md`, and
`specspine.json` is a
separate Spine and a traversal boundary. Its documents, IDs, manifest areas,
and assets do not belong to the parent Spine. Workspace tooling connects the
nearest ancestor Spine to the nested root and records otherwise independent
top-level roots in the disposable workspace graph.

## Reconstruction invariant

An area is `ready` only when a capable agent can implement it without source
access or policy invention, using the selected closure, registered assets, and
verification criteria. `ready` claims contract or architecture equivalence
according to `implementation_freedom`; it never claims source-code identity
or reproduction of private implementation choices.
