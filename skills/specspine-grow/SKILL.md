---
name: specspine-grow
description: Grow and maintain a long-lived network of linked Markdown architectural specifications. Use this skill to create a SpecSpine from an abstract idea, evolve intended architecture, split or merge architectural concepts, assess architectural impact, preserve intended-versus-observed disagreements, and prepare minimal architecture context handoffs for downstream tools or coding agents. This skill modifies only specifications and does not implement changes or prove code/spec conformance.
---

# SpecSpine Grow

Maintain a lightweight, long-lived network of linked architectural
specifications. The network is the persistent artifact; a context handoff is a
temporary projection for downstream work.

## Resources

- Read [references/spec-semantics.md](references/spec-semantics.md) before
  creating, changing, or reviewing specifications.
- Read [references/spec-format.md](references/spec-format.md) when initializing
  a SpecSpine, choosing sections, or changing specification structure.
- Read [references/examples.md](references/examples.md) when deciding whether to
  split, merge, create, or reuse a specification.
- Read [references/context-handoff.md](references/context-handoff.md) before
  preparing a context handoff.
- When creating files, use
  [assets/templates/architecture-index.md](assets/templates/architecture-index.md)
  and [assets/templates/specification.md](assets/templates/specification.md) as
  starting points. Omit empty sections.

## Scope

Use this skill to:

- initialize a SpecSpine from an abstract project idea;
- evolve intended architecture and accepted decisions or constraints;
- identify architectural concepts affected by a requested change;
- split, merge, rename, or link specifications;
- review canonical ownership, boundaries, navigation, and uncertainty;
- prepare a minimal architecture context handoff.

Do not use it to:

- modify source code or verify code/spec conformance;
- reverse-engineer undocumented code deeply;
- create feature specifications, acceptance criteria, plans, or tasks;
- track implementation, release, or review status;
- silently invent or resolve product and architectural decisions.

Preserve missing information as an open question. Mark it blocking when a
downstream workflow must not answer it silently.

## Semantic contract

- `Decisions` and `Constraints` describe intended architecture.
- `Observed` records current repository evidence.
- `Inferred` records unconfirmed interpretation.
- `Open questions` preserves unresolved uncertainty.

Observed facts do not override decisions or constraints. Decisions and
constraints do not imply that code implements them. Preserve disagreements
until the user or a downstream workflow resolves them.

Keep stable responsibilities, ownership boundaries, architectural
relationships, long-lived decisions, and constraints in SpecSpine. Leave
feature deltas, temporary scope, acceptance criteria, implementation tasks, and
status to downstream workflows.

## Lifecycle role

Own intentional evolution of normative architecture. Preserve relevant
observations already known to the user, but do not deeply discover them from
code. When a request primarily requires repository discovery, leave that work
to a separate mapping workflow.

Remain fully usable without any companion skill. Update the linked network and
produce context handoffs without proving conformance or implementing changes.

## Workflow

### 1. Read the spine

Start with `specs/README.md`, then follow only links relevant to the request. If
the index does not exist, treat the project as uninitialized.

### 2. Classify the request

Determine whether the user wants to initialize, refine, split, merge, link,
review, or prepare a context handoff.

### 3. Locate canonical owners

Identify the primary specification, directly affected specifications, required
context, and merely related context. Reuse an existing canonical home when it
already owns the responsibility.

### 4. Decide whether structure changes

Create or extract a specification only for an independent responsibility,
boundary, behavior, decision set, or independently evolving concept. Do not
create one file per feature or split by length alone.

### 5. Propose structural impact

Before creating, renaming, deleting, splitting, merging, or changing several
specifications, show:

```text
Affected specifications

Create:
- paths, or none

Modify:
- paths, or none

Rename:
- paths, or none

Remove:
- paths, or none

Reason:
- why this structure is appropriate

Open decisions:
- unresolved choices, or none
```

Wait for approval unless the user explicitly requested immediate application.
A clear, local refinement of one existing specification may be applied
directly.

### 6. Apply the change

- Modify only specifications.
- Preserve unrelated and user-authored content.
- Maintain useful relative Markdown links and reachability from
  `specs/README.md`.
- Keep one canonical home per concept; replace duplicates with summaries and
  links.
- Keep overview specifications concise after decomposition.
- Update `specs/README.md` only when top-level navigation or system-wide intent
  changes.

### 7. Report

Summarize changed files, structural decisions, unresolved questions, and
whether the area is ready for context handoff.

## Operation rules

### Initialize

Create `specs/README.md` and the smallest useful set of top-level concept
specifications. Do not anticipate the full project. Short specifications with
explicit open questions are acceptable.

### Refine

Preserve the existing responsibility unless the user changes it. Add accepted
behavior or intent, link canonical neighbors, and extract a concept only when it
now evolves independently.

### Split or merge

For a split, identify the extracted responsibility, moved content, and changed
links; retain a concise overview when it remains a useful navigation point. For
a merge, preserve the clearest canonical filename and update incoming links.

### Review

Look for duplicated ownership, unclear or overly broad responsibilities,
unnecessary fragmentation, missing direct links, stale overview text,
unreachable files, hidden uncertainty, and implementation detail. Recommend
changes before restructuring.

### Prepare a context handoff

Follow `references/context-handoff.md`. Include the smallest useful set and
separate required, potentially affected, and merely related specifications.
Preserve decisions, constraints, observations, inferences, and blocking
questions without adding downstream artifacts.

## Readiness for context handoff

An area is ready when:

- a canonical owner is identified;
- responsibility, boundaries, and direct dependencies are understandable;
- relevant decisions and constraints are collected;
- potentially affected specifications are separated from related context;
- blocking architectural questions are explicit;
- observed and inferred claims are distinguishable when evidence is involved.

This does not imply readiness for implementation. Product requirements, edge
cases, acceptance criteria, migrations, tests, and implementation readiness
belong downstream.

## Restrictions

Never:

- modify or create source-code files;
- invent repository structure;
- claim synchronization or conformance between specifications and code;
- claim that normative intent is implemented merely because it is documented;
- treat inference as fact or accepted intent;
- silently resolve blocking questions or intended-versus-observed conflicts;
- reproduce local implementation details in specifications;
- rewrite unrelated branches of the SpecSpine;
- create plans, tasks, acceptance criteria, or implementation status.

Be concise and architectural. Prefer concrete file operations and links. The
user owns product and architectural decisions; this skill owns organization,
refinement, navigation, and consistency of the specification network.
