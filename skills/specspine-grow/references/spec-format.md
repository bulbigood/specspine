# SpecSpine specification format

This document defines the recommended Markdown structure used by
`specspine-grow`.

It is a flexible template, not a schema. Include only sections that add useful
architectural information. Do not create empty sections merely to satisfy the
format.

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

Recommended structure:

```markdown
# Project architecture

## Purpose

A concise description of the project and the problem it solves.

## Architecture map

- [Authentication](authentication.md) — identifies users and creates sessions.
- [User accounts](users.md) — owns user identity and profile data.
- [Notifications](notifications.md) — delivers user-facing messages.

## System-wide decisions

Only decisions that affect several specifications belong here.

## Open questions

Unresolved project-level architectural questions.
```

Keep the architecture map small enough to be useful. It may link directly to
top-level concepts and let those specifications link to more detailed concepts.

## Specification node

Recommended structure:

```markdown
# Specification name

A short summary of the concept.

## Responsibility

What this concept owns and why it exists.

## Boundaries

What belongs to this concept and what explicitly does not.

## Behavior

Significant externally observable or architecturally relevant behavior.

## Relationships

### Part of

Optional links to broader architectural contexts.

### Contains

Optional links to more detailed specifications.

### Depends on

Specifications required by this concept.

### Used by

Important consumers of this concept.

### Related

Relevant specifications that do not fit the relationships above.

## Decisions

Architectural or behavioral decisions already accepted by the user.

## Open questions

Unresolved questions that may affect architecture or behavior.
```

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
