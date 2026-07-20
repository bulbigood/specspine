---

name: specspine-grow
description: Grow and maintain a linked Markdown architecture for a software project. Use this skill to create a SpecSpine from an abstract idea, refine existing specifications, split broad concepts into separate specifications, update relationships, assess the architectural impact of requested changes, and prepare specifications for implementation. This skill works only with specifications and must not modify source code.
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# SpecSpine Grow

Maintain a lightweight network of linked Markdown specifications that forms the architectural spine of a software project.

The specifications describe the project's purpose, responsibilities, boundaries, significant behavior, architectural decisions, and relationships between concepts.

They do not reproduce source code or describe local implementation details.

## Scope

Use this skill when the user wants to:

* create a project architecture from an abstract idea;
* refine or expand an existing specification;
* add a new capability;
* change an architectural decision;
* discover which specifications a change affects;
* split an overly broad specification;
* merge overlapping specifications;
* improve links between specifications;
* review the current specification structure;
* prepare architectural context for implementation.

Do not use this skill to:

* modify source code;
* create an implementation plan unless explicitly requested;
* create task lists by default;
* reverse-engineer undocumented code;
* verify that code matches the specifications;
* invent product or architectural decisions without informing the user.

If the specifications do not contain enough information, preserve the uncertainty as an open question.

# Specification layout

Use this layout by default:

```text
specs/
├── README.md
└── <concept>.md
```

Keep specification files in a flat directory.

Do not represent architectural hierarchy through nested directories. Specifications form a graph and may participate in several architectural relationships at once.

Use lowercase kebab-case filenames based on stable concepts:

```text
authentication.md
account-linking.md
session-management.md
notification-delivery.md
```

Prefer concept names over change-request names.

Good:

```text
google-sign-in.md
account-linking.md
```

Avoid:

```text
add-google-login.md
fix-auth-flow.md
feature-017.md
```

Do not reorganize specifications into subdirectories unless the user explicitly requests it or the flat directory has become clearly difficult to navigate.

# README.md

`specs/README.md` is required.

It is the entry point into the SpecSpine, but it is not the semantic parent of every specification.

Its purpose is to help a new human or agent understand:

* what the project is;
* how the system is divided at the highest useful level;
* where to start reading;
* which decisions affect the whole system;
* which questions remain unresolved.

Use this structure:

```markdown
# Project architecture

## Purpose

A concise description of the project and the problem it solves.

## Architecture map

- [Authentication](authentication.md) — identifies users and creates authenticated sessions.
- [User accounts](users.md) — owns user identity and profile data.
- [Notifications](notifications.md) — delivers user-facing messages.

## System-wide decisions

Only decisions that affect several specifications belong here.

## Open questions

Unresolved project-level architectural questions.
```

Keep the architecture map curated. Do not list every specification when a smaller set of useful entry points is sufficient.

# Specification structure

A specification may use the following structure:

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

Sections are optional. Include only sections that contain useful information.

Do not create empty sections merely to satisfy the template.

# Core principles

## 1. One canonical home per concept

Each important rule, responsibility, behavior, or decision should have one primary specification.

Other specifications should link to it instead of repeating it.

Small contextual summaries are allowed, but they must not become competing definitions.

## 2. Treat specifications as a graph

Do not force every specification into a strict hierarchy.

Use hierarchical relationships when they are useful, but allow cross-cutting specifications such as:

* security;
* observability;
* transactions;
* audit;
* configuration;
* identity;
* error handling.

A specification may belong to one broader context while also being depended on by several unrelated specifications.

## 3. Split by responsibility

Propose a separate specification when a concept:

* has an independent responsibility;
* contains several significant decisions;
* has its own meaningful behavior or boundary;
* is referenced by several other specifications;
* can evolve independently from its current specification;
* makes its current specification difficult to understand.

Do not split merely because a document is long.

Do not create specifications for trivial implementation details.

## 4. Preserve uncertainty

Never silently convert an assumption into an accepted decision.

When information is missing:

* record it under `Open questions`;
* explain why it matters;
* ask the user only when the decision blocks useful progress.

Prefer a useful partial specification with explicit uncertainty over an invented complete specification.

## 5. Stop before reproducing code

Continue refinement until the specification gives an implementation agent enough information to understand:

* the responsibility;
* the boundaries;
* the significant behavior;
* the dependencies;
* the accepted decisions;
* the important constraints.

Stop when further detail would mainly describe:

* function calls;
* control flow obvious from code;
* local variable handling;
* framework boilerplate;
* internal algorithms that do not affect architecture or contracts.

Specifications should constrain implementation without becoming a second programming language.

## 6. Show structural impact before applying it

Before creating, renaming, deleting, splitting, merging, or modifying several specification files, present an impact proposal.

Use this format:

```text
Affected specifications

Create:
- specs/account-linking.md

Modify:
- specs/authentication.md
- specs/users.md
- specs/sessions.md

Rename:
- none

Remove:
- none

Reason:
Account linking has independent rules used by password authentication
and external identity providers.

Open decisions:
- Should accounts be linked automatically by verified email?

Proceed with these specification changes?
```

Wait for approval unless the user explicitly requested immediate application.

A small refinement confined to one existing specification may be applied directly when the user's request is unambiguous.

# Operating workflow

## Step 1: Read the existing spine

Start with:

```text
specs/README.md
```

Then follow only the links relevant to the user's request.

Do not read every specification by default.

If `specs/README.md` does not exist, treat the project as having no initialized SpecSpine.

## Step 2: Interpret the request

Determine whether the user wants to:

* initialize;
* grow;
* refine;
* split;
* merge;
* link;
* review;
* prepare implementation context.

The user does not need to use these operation names explicitly.

## Step 3: Locate the canonical concepts

Identify specifications that already own the relevant responsibilities.

Do not create a new specification when an existing specification is the correct canonical home.

When several specifications are affected, distinguish:

* the primary specification;
* directly affected specifications;
* related context that does not require modification.

## Step 4: Decide whether the structure should change

Consider whether the request reveals a new independent concept.

Do not automatically create one file per requested feature.

For example, adding Google Sign-In may require:

* updating `external-identity.md`;
* updating `authentication.md`;
* updating `sessions.md`;
* creating `account-linking.md` only if account linking contains independent behavior and decisions.

## Step 5: Present the impact proposal

Explain:

* which specifications will change;
* which specifications will be created;
* whether any concepts will move;
* why the proposed structure is appropriate;
* which decisions remain unresolved.

Keep the proposal concise.

## Step 6: Apply the approved change

After approval:

* create or update the specifications;
* maintain Markdown links;
* update both sides of important navigational relationships where useful;
* update `specs/README.md` when top-level navigation changes;
* remove duplicated descriptions;
* preserve unrelated content;
* keep parent or overview specifications concise.

## Step 7: Report the result

Summarize:

* files created;
* files modified;
* structural decisions made;
* unresolved questions;
* whether the affected area is ready for implementation.

# Initializing a new SpecSpine

When no SpecSpine exists, begin with the smallest useful architecture.

Do not attempt to anticipate the full project.

Create:

```text
specs/
├── README.md
└── one or more top-level specifications
```

For a vague request such as:

```text
Build a server for a small SaaS application.
```

A reasonable initial result might be:

```text
specs/
├── README.md
├── server.md
├── identity.md
├── persistence.md
└── operations.md
```

Each initial specification may be short and contain open questions.

The first version should be a useful skeleton, not a complete design.

# Growing an existing specification

When refining a specification:

1. Preserve its existing responsibility unless the user changes it.
2. Add newly accepted behavior or decisions.
3. Link to related specifications instead of duplicating their content.
4. Move independently evolving concepts into separate specifications when useful.
5. Keep broader specifications as concise summaries and navigation points.
6. Record unresolved details as open questions.

Example transformation:

```text
authentication.md
```

may initially describe all authentication behavior.

As the project grows, it may become:

```text
authentication.md
external-identity.md
password-authentication.md
session-management.md
account-linking.md
```

`authentication.md` should then become a concise overview linking the more specific concepts.

# Splitting a specification

When proposing a split:

* identify the responsibility being extracted;
* explain why it can evolve independently;
* list content that will move;
* list links that will change;
* preserve a summary and link in the original specification;
* avoid creating several tiny specifications at once.

After a split, each resulting specification must have a clear responsibility.

# Merging specifications

Propose a merge when:

* two specifications describe the same canonical concept;
* their responsibilities cannot be meaningfully distinguished;
* maintaining separate files causes repetition;
* one specification has become only a thin redirect without architectural value.

Preserve the clearest filename and update incoming links.

# Relationships

Use ordinary relative Markdown links:

```markdown
[Session management](session-management.md)
```

Prefer explicit relationship sections over large unstructured link lists.

Do not add a relationship merely because two concepts are loosely associated.

Links should help an agent decide where to navigate next.

Every new specification must be reachable from:

* `specs/README.md`; or
* another reachable specification.

# Architecture review

When asked to review the SpecSpine, look for:

* concepts described in several places;
* specifications with unclear responsibility;
* overly broad specifications;
* unnecessary fragmentation;
* missing links between directly dependent concepts;
* outdated overview text;
* unresolved questions presented as accepted decisions;
* implementation details that should remain in code;
* top-level specifications missing from `README.md`;
* files that are not reachable from the architecture map.

Present recommendations before restructuring the files.

# Preparing implementation context

When asked to prepare context for implementation, do not write code.

Return:

```text
Primary specification:
- the specification that owns the requested behavior

Required specifications:
- direct dependencies
- affected consumers
- relevant broader context

Accepted decisions:
- decisions the implementation must preserve

Open questions:
- unresolved decisions that block or influence implementation

Expected implementation outcome:
- a concise behavioral and architectural goal
```

Include only the smallest useful specification set.

Do not include unrelated branches of the SpecSpine.

# Readiness for implementation

An area is ready for implementation when:

* its responsibility is clear;
* its important boundaries are clear;
* significant behavior is described;
* directly affected specifications are identified;
* accepted architectural decisions are recorded;
* blocking questions are resolved;
* further refinement would mostly duplicate implementation details.

Do not require every open question to be resolved. Only blocking questions prevent readiness.

# Restrictions

Never:

* modify source code;
* create code files;
* invent repository structure;
* claim that specifications are synchronized with code;
* treat inferred assumptions as accepted decisions;
* create a rigid hierarchy when the architecture is naturally cross-linked;
* split specifications only to reduce line count;
* turn local implementation details into architectural requirements;
* rewrite the entire SpecSpine when a local update is sufficient;
* create plans and task files unless explicitly requested.

# Response style

Be concise and architectural.

Prefer concrete file operations and links over abstract discussion.

When proposing changes, make the affected specification set visible.

When applying changes, preserve user-authored wording unless it conflicts with the updated architecture.

The user owns product and architectural decisions. The skill owns organization, refinement, navigation, and consistency of the specification network.
