# SpecSpine specification format

This document defines the self-contained Markdown artifacts produced by a
SpecSpine workflow. It is the canonical instruction for what belongs in those
artifacts; workflow skills should only route here.

It is a flexible template, not a schema. Include only sections that add useful
architectural information. Do not create empty sections merely to satisfy the
format.

Keep each durable architectural concept in its own document. Do not embed
feature specifications, acceptance criteria, plans, tasks, implementation
status, or framework-specific workflow state. A downstream SDD framework may
consume, link, copy, or adapt these ordinary Markdown documents without owning
their format.

## Contents

- [File organization](#file-organization)
- [Architecture index](#architecture-index)
- [Specification node](#specification-node)
- [Section guidance](#section-guidance)
- [Extension sections](#extension-sections)
- [Addressable statements](#addressable-statements)
- [Visual representations](#visual-representations)
- [Canonical ownership](#canonical-ownership)
- [Decomposition](#decomposition)
- [Terminal detail](#terminal-detail)
- [Reachability](#reachability)

## File organization

Resolve `<spine-root>` once before reading or writing specifications:

1. Use the root explicitly supplied by the user, project instructions, or an
   installer integration.
2. Otherwise use an existing configured SpecSpine root.
3. Otherwise default to `specspine`.

Keep this value stable for the operation. Store project specifications in a
flat directory beneath it:

```text
<spine-root>/
├── README.md
├── authentication.md
├── account-linking.md
├── session-management.md
└── users.md
```

Use lowercase kebab-case filenames based on stable concepts.

Prefer:

```text
authentication.md
external-identity.md
notification-delivery.md
```

Avoid:

```text
add-google-login.md
feature-017.md
fix-auth-flow.md
```

Specifications form a graph through relative Markdown links. Directory nesting
should not encode architectural hierarchy.

## Architecture index

Every SpecSpine has a `<spine-root>/README.md` entry point.

It is a curated architecture map, not the semantic parent of every
specification.

Use the architecture-index template routed from `SKILL.md` when creating it.
The index should contain project purpose, a curated architecture map, accepted
system-wide decisions and constraints, and project-level open questions.

Keep the architecture map small enough to be useful. It may link directly to
top-level concepts and let those specifications link to more detailed concepts.

## Specification node

Use the specification template routed from `SKILL.md` when creating a node.
Select only useful sections; the template is a menu, not a required schema.

The document must remain understandable outside the producing skill. Use
ordinary Markdown and relative links. Do not require custom frontmatter,
directives, generated indexes, or tool-specific parsers for its meaning.

## Section guidance

### Summary

The first paragraph should explain the concept in one or two sentences.

A new agent should understand why the specification exists without reading the
rest of the file.

### Responsibility

Describe what the concept owns.

Prefer stable responsibilities over implementation descriptions.

Good:

```text
Creates and maintains provider-independent application sessions.
```

Avoid:

```text
Contains SessionService, TokenRepository, and the refreshToken handler.
```

### Boundaries

State what belongs elsewhere when confusion is likely.

Use links to canonical specifications:

```markdown
Password validation belongs to
[Password authentication](password-authentication.md).
```

### Behavior

Describe significant behavior visible to users, other subsystems, or the
architecture.

Do not document every branch of local control flow.

### Relationships

Add only useful navigation links.

Do not turn this section into a list of everything remotely associated with the
concept.

Use ordinary relative Markdown links:

```markdown
[Session management](session-management.md)
```

### Decisions

Record accepted choices that constrain future implementation.

Examples:

- application sessions are independent of identity providers;
- external provider access tokens are not persisted;
- background jobs use at-least-once delivery semantics.

Do not store unresolved assumptions here.

### Constraints

Record accepted restrictions on acceptable architecture or implementation.
Constraints describe intended architecture but do not imply that the current
code satisfies them.

### Observed and inferred

Use these sections only when repository evidence matters. Record direct
evidence under `Observed` and unconfirmed interpretation under `Inferred`.
Neither overrides accepted decisions or constraints.

When an observation needs traceability, add representative repository-relative
evidence without claiming exhaustive coverage:

```markdown
- **OBS-worker-retries** — Failed jobs are retried by the worker.
  Evidence: `src/worker.ts`, `tests/job-retry.test.ts`.
```

### Open questions

Use this section for uncertainty that remains relevant.

A useful question explains what decision is missing and why it matters:

```markdown
- Should existing accounts be linked automatically by verified email?
  This affects account takeover risk and the external identity flow.
```

Remove or convert questions when the user accepts a decision.

## Extension sections

The standard sections are a common vocabulary, not a closed schema. Add a
project-specific section only when it describes a durable architectural aspect,
is understandable without a special parser, and does not duplicate a canonical
specification or downstream feature artifact.

Useful optional sections include:

- `Interfaces` — architectural inputs, outputs, commands, events, and external
  contracts;
- `Data ownership` — owned data and mutation authority;
- `Lifecycle` — significant states and transitions;
- `Failure behavior` — retries, degradation, recovery, and failure boundaries;
- `Quality attributes` — security, privacy, consistency, availability, latency,
  and similar architectural properties;
- `Terminology` — local domain language when a project-wide glossary is
  unnecessary;
- `Rationale and trade-offs` — reasoning that remains useful after a decision;
- `Evidence` — shared sources supporting several observations.

Do not add an `Assumptions` section. Put unconfirmed interpretation under
`Inferred` and unresolved choices under `Open questions`.

## Addressable statements

Use a short semantic identifier only when another specification, context
handoff, or downstream artifact needs to reference a particular statement.
Do not identify every paragraph or bullet.

An addressable definition is an unordered-list item whose first element is a
bold identifier, followed by an em dash and the statement:

```markdown
## Decisions

- **DEC-provider-independent-sessions** — Application sessions are independent
  of authentication providers.
```

Use this identifier grammar:

```text
^(DEC|CON|OBS|INF|OQ)-[a-z0-9]+(?:-[a-z0-9]+)*$
```

Match the prefix to the owning section: `DEC` for `Decisions`, `CON` for
`Constraints`, `OBS` for `Observed`, `INF` for `Inferred`, and `OQ` for
`Open questions`. Define an ID only once within a specification. IDs are local
to their canonical specification, so an address is the resolved specification
path plus the ID. An identifier adds addressability, not authority or proof.

A reference is an ordinary Markdown link whose complete visible label is the
target ID and whose destination is the target specification:

```markdown
- Job processing must preserve
  [CON-retry-limit](job-processing.md).
```

This binds the path and ID in one Markdown AST node. A checker can recognize a
reference by the ID-shaped link label and resolve it without interpreting
adjacent prose. Keep human context outside the link when useful.

Definitions use bold IDs; references use linked IDs. Do not define addressable
statements in tables or diagrams. Do not invent a URL fragment such as
`job-processing.md#CON-retry-limit`; the ID does not create a Markdown anchor.

Once referenced externally, keep the identifier stable across wording changes.
If its meaning is replaced, retain a short tombstone that points to the
replacement instead of silently reusing or deleting the identifier:

```markdown
- **DEC-legacy-session-model** — Superseded by
  [DEC-provider-independent-sessions](session-management.md).
```

When ownership moves to another specification, leave the same kind of
tombstone in the old canonical location and link its replacement by ID.

## Visual representations

Choose the smallest representation that makes the relationship easier to read:

- unordered lists for responsibilities, boundaries, rules, and dependencies;
- ordered lists for protocols and ordered lifecycles;
- Markdown tables for comparisons, ownership matrices, interface mappings, and
  repeated fields;
- Mermaid `flowchart` for components, dependencies, and data flow;
- Mermaid `sequenceDiagram` for multi-party interactions;
- Mermaid `stateDiagram-v2` for states and transitions;
- Mermaid `erDiagram` for conceptual data relationships;
- Mermaid `classDiagram` for architectural types and contracts;
- Mermaid `mindmap` for a compact area overview when the target renderer
  supports it reliably.

Never use ASCII diagrams. They render inconsistently and break under wrapping
or automated editing.

A diagram must not be the only source of meaning. State its important
conclusion in nearby prose, a list, or a table. Keep one diagram focused on one
question, avoid file- or function-level detail, and do not maintain duplicate
copies of the same topology in several specifications.

## Canonical ownership

Each important concept should have one canonical specification.

Small summaries may appear elsewhere for context, but detailed definitions and
decisions should link back to the canonical home.

When two specifications contain competing definitions:

1. Choose the clearer canonical home.
2. Move the full definition there.
3. Replace the duplicate with a short summary and link.

## Decomposition

Create a separate specification when a concept:

- has an independent responsibility;
- contains several meaningful decisions;
- has its own behavior or boundary;
- is referenced by multiple other specifications;
- can evolve independently.

Do not split based only on line count.

After a split, keep the broader specification as a concise overview and
navigation point.

## Terminal detail

Refine a specification until an implementation agent can understand:

- responsibility;
- boundaries;
- significant behavior;
- dependencies;
- accepted decisions;
- important constraints.

Stop when additional prose would mostly reproduce source code, framework
boilerplate, function calls, or local algorithms.

## Reachability

Every specification should be reachable from:

- `<spine-root>/README.md`; or
- another reachable specification.

The purpose is practical navigation, not formal graph validation.
