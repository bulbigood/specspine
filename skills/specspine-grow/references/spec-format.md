# SpecSpine specification format

This document defines the recommended Markdown structure used by
`specspine-grow`.

It is a flexible template, not a schema. Include only sections that add useful
architectural information. Do not create empty sections merely to satisfy the
format.

## Contents

- [File organization](#file-organization)
- [Architecture index](#architecture-index)
- [Specification node](#specification-node)
- [Section guidance](#section-guidance)
- [Canonical ownership](#canonical-ownership)
- [Decomposition](#decomposition)
- [Terminal detail](#terminal-detail)
- [Reachability](#reachability)

## File organization

Store project specifications in a flat directory:

```text
specs/
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

Every SpecSpine has a `specs/README.md` entry point.

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

### Open questions

Use this section for uncertainty that remains relevant.

A useful question explains what decision is missing and why it matters:

```markdown
- Should existing accounts be linked automatically by verified email?
  This affects account takeover risk and the external identity flow.
```

Remove or convert questions when the user accepts a decision.

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

- `specs/README.md`; or
- another reachable specification.

The purpose is practical navigation, not formal graph validation.
