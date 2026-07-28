# Markdown format

## Root index

`<spine-root>/README.md` is the entry point and curated architecture map. It is
not the semantic parent of every specification.

The index MUST contain:

- exactly one H1;
- `**ID:** \`...\` · **Kind:** \`index\``;
- a short scope statement explaining that the directory contains the project's
  long-lived architectural intent and architecture-relevant repository
  observations;
- a short project purpose and architectural context;
- a compact `Architecture map`.

It SHOULD also contain the main external boundaries, system-wide decisions and
constraints, and architecture-significant open questions. It MUST NOT become a
catalog of every document.

The root MUST also contain `specspine.json` with the exact schema defined by the
shared format contract. Completeness, blockers, and assets MUST NOT be
duplicated in Markdown.

## Specification node

Every non-index node MUST contain:

1. exactly one H1;
2. an identity line;
3. a one-to-three sentence summary immediately after identity and optional
   aliases;
4. a non-empty `Responsibility` section.

```markdown
# Order processing

**ID:** `order-processing` · **Kind:** `subsystem`
**Aliases:** Order orchestration

Owns the order lifecycle and coordinates reservation, payment, and delivery.

## Responsibility

- owns order state;
- validates state transitions;
- coordinates order fulfillment.
```

Other sections are added only when they contain useful architectural
information.

## Identity

Document IDs MUST match:

```regex
^[a-z0-9]+(?:-[a-z0-9]+)*$
```

An ID MUST be unique within the Spine, stable after publication, independent of
path and hierarchy, unchanged by rename or move, and never reused after
deletion.

Core kinds are:

```text
index system subsystem component capability behavior interface data policy
deployment concept
```

Requirements, guarantees, invariants, decisions, quality constraints, and
verification are statement kinds rather than document kinds.

Project extensions use `x-<project-kind>`. Unknown core-like kinds SHOULD
produce a warning; valid `x-*` kinds MUST be preserved.

Aliases MAY follow identity. They MUST be genuine, concise project terms and
MUST NOT be keyword stuffing.

## Sections

Use the following sections only for their stated responsibility:

- `Responsibility` — what the concept canonically owns.
- `Boundaries` — what is inside, outside, or owned by a neighbor.
- `Behavior` — externally significant coordination, transitions, and outcomes.
- `Interfaces` — stable architectural inputs, outputs, commands, events, APIs,
  and ports.
- `Information model` — durable concepts and relationships, not a copied
  physical schema.
- `Data ownership` — creation, mutation, reading, and consistency authority.
- `Lifecycle and invariants` — states, transitions, irreversible states, and
  durable truths.
- `Failure behavior` — retry, degradation, compensation, recovery,
  idempotency, and uncertain outcomes.
- `Edge cases` — only architecture-significant exceptions.
- `Quality attributes` — durable security, privacy, consistency, availability,
  latency, scalability, or maintainability properties.
- `Requirements`, `Guarantees`, `Invariants`, `Quality constraints`, and
  `Verification` — accepted durable normative claims.
- `Decisions`, `Constraints`, `Observed`, `Inferred`, and `Open questions` —
  statements with the remaining semantics defined in
  [Semantics and evidence](03-semantics-and-evidence.md).
- `Configuration contract` and `Compatibility` — durable settings,
  precedence, versioning, migration, and interoperability guarantees.
- `Implementation` — representative repository-relative source areas and entry
  points, written as inline code rather than required links.
- `Terminology` — local domain terms.
- `Risks` — durable architectural risks, not an issue backlog.
- `Known divergences` — confirmed intent/reality conflicts.

## Typed relationships

Typed edges MUST use this table:

```markdown
## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `depends-on` | [Inventory](inventory.md) | Obtains reservation outcomes |
| `constrained-by` | [CON-order-idempotency](order-invariants.md) | Prevents duplicate order creation |
```

Each row MUST contain one canonical relation token, exactly one relative
Markdown link, and a non-empty explanation. The direction is source document
to target. A reverse row MUST NOT be authored merely for navigation.

Core relations are:

| Relation | Meaning |
|---|---|
| `contains` | Technical composition |
| `decomposes-into` | Functional decomposition of responsibility |
| `performs` | Owner performs an independent behavior |
| `depends-on` | Significant dependency with no more precise type |
| `exposes` | Provides an interface or contract |
| `consumes` | Consumes an interface, event, or command |
| `publishes` | Publishes an event or message |
| `reads-from` | Reads data owned elsewhere |
| `writes-to` | Mutates a target through an allowed boundary |
| `owns-data` | Owns definition or mutation of data |
| `constrained-by` | Is restricted by intent or policy |
| `implemented-by` | Behavior or interface is implemented by a component |
| `has-evidence` | References a separate durable evidence document |
| `superseded-by` | Has a new canonical replacement |
| `related-to` | Weak relationship when no precise type is justified |
| `refines` | Adds more precise normative meaning |
| `satisfies` | Claims responsibility for satisfying a normative owner |
| `verified-by` | Points to a verification owner |
| `specified-by` | Points to an exact contract owner |
| `compatible-with` | Declares a compatibility dependency |
| `migrates-from` | Declares a supported migration predecessor |

Extensions use `x-<project-relation>`. An unknown relation without `x-` SHOULD
produce a warning but MUST NOT be destroyed or rewritten automatically.

Ordinary Markdown links outside the table are navigation, statement
references, or evidence references. They MUST NOT be treated as typed edges.

## Addressable statements

Use semantic IDs selectively when another document or workflow must reference
an exact statement:

```text
DEC — accepted decision
CON — accepted constraint
REQ — accepted durable requirement
GUA — accepted observable guarantee
INV — accepted invariant
QLT — accepted quality constraint
VER — durable conformance verification
OBS — repository-backed observation
INF — unconfirmed inference
OQ  — open question
```

IDs MUST match:

```regex
^(DEC|CON|REQ|GUA|INV|QLT|VER|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$
```

Definitions use bold IDs inside at most one balanced region:

```markdown
<!-- specspine:semantic-ids:begin -->
## Constraints

- **CON-payment-idempotency** — A provider result is applied at most once.
<!-- specspine:semantic-ids:end -->
```

References use the exact visible ID and target file without a URL fragment:

```markdown
[CON-payment-idempotency](payment-invariants.md)
```

Once externally referenced, a semantic ID MUST remain stable. A replaced
statement retains a tombstone that links to its successor.

## Decomposition and promotion

Split by independent responsibility, not length. Promote behavior, policy,
invariant, interface, or data ownership to its own node when it has independent
ownership, lifecycle, constraints, several consumers, or meaningful evolution.
A broad document may remain an overview and navigation point after a split.
