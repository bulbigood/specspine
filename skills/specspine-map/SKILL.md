---
name: specspine-map
description: Progressively map an existing brownfield software project into a long-lived network of linked Markdown architectural specifications. Use when documenting an unfamiliar repository, surveying runtime components, refining an architectural area, preserving intended-versus-observed disagreements, or preparing a minimal architecture context handoff for a downstream tool or coding agent. This skill reads repository evidence but modifies only specifications and does not prove code/spec conformance.
---

# SpecSpine Map

Map an existing repository into a lightweight, long-lived network of linked
architectural specifications. The network is the persistent artifact; a context
handoff is a temporary projection for downstream work.

Map breadth before depth. Build the smallest useful architectural model rather
than exhaustive code documentation.

## Resources

- Read [references/spec-semantics.md](references/spec-semantics.md) before
  creating, changing, or reviewing specifications.
- Read [references/mapping-method.md](references/mapping-method.md) before a
  substantial survey, refresh, or restructuring.
- Read [references/examples.md](references/examples.md) when choosing mapping
  depth, distinguishing evidence from interpretation, or deciding whether an
  area deserves a specification.
- Read [references/context-handoff.md](references/context-handoff.md) before
  preparing a context handoff.
- When creating files, use
  [assets/templates/architecture-index.md](assets/templates/architecture-index.md)
  and [assets/templates/specification.md](assets/templates/specification.md) as
  starting points. Omit empty sections.

## Scope

Use this skill to:

- create a SpecSpine for an existing repository;
- survey project purpose, runtime shape, and major responsibilities;
- map or deepen a selected architectural area;
- refresh specs after meaningful repository evolution;
- compare observed evidence with intended architecture;
- preserve uncertainty and intended-versus-observed disagreements;
- prepare a minimal architecture context handoff.

Do not use it to:

- modify production code or implement changes;
- produce exhaustive code or API documentation;
- mirror every directory, class, endpoint, table, or function;
- infer business intent solely from repository names;
- create feature specifications, acceptance criteria, plans, or tasks;
- claim complete coverage or prove code/spec conformance.

## Semantic contract

- `Decisions` and `Constraints` describe intended architecture.
- `Observed` records current repository evidence.
- `Inferred` records unconfirmed interpretation.
- `Open questions` preserves unresolved uncertainty.

Observed facts do not override decisions or constraints. Decisions and
constraints do not imply that code implements them. Preserve disagreements
until the user or a downstream workflow resolves them.

When repeated evidence suggests a useful architectural decision without an
authoritative source, propose it for confirmation. Never record it as accepted
intent automatically.

Keep stable responsibilities, ownership boundaries, architectural
relationships, long-lived decisions, and constraints in SpecSpine. Leave
feature deltas, temporary scope, acceptance criteria, implementation tasks, and
status to downstream workflows.

## Lifecycle role

Discover repository evidence, record observed architecture, and propose
interpretations or structural changes without silently altering normative
intent. Propose new decisions or constraints for user confirmation instead of
accepting them from evidence alone.

Remain fully usable without any companion skill. Update the linked network and
produce context handoffs without proving conformance or implementing changes.

## Workflow

### 1. Inspect existing architecture material

Read root documentation, `specs/README.md`, relevant specifications, and ADRs or
equivalent architecture records. Preserve accepted structure unless evidence or
the request justifies changing it.

### 2. Choose mapping depth

Use the shallowest depth that answers the request:

- `survey` — map the project broadly;
- `map` — describe a selected subsystem;
- `deepen` — add detail needed for a specific architectural question;
- `refresh` — update specs after repository evolution;
- `review` — identify weak or uncertain areas;
- `handoff` — prepare minimal downstream architectural context.

### 3. Gather representative evidence

Prioritize root docs and manifests, composition roots, runtime entry points,
public interfaces, schemas and migrations, integration edges, deployment
configuration, and representative tests. Read implementation internals only
where boundaries remain unclear.

### 4. Form the smallest useful model

Choose stable responsibilities rather than filesystem shapes. A directory is
not automatically a subsystem; several directories may implement one concept,
and one directory may contain several concepts.

Record direct evidence as `Observed`, plausible interpretation as `Inferred`,
accepted intent as `Decisions` or `Constraints`, and unresolved ambiguity as
`Open questions`.

### 5. Propose structural impact

Before creating, renaming, deleting, splitting, merging, or changing several
specifications, show:

```text
Mapping proposal

Create:
- paths, or none

Modify:
- paths, or none

Evidence inspected:
- representative sources

Inferred structure:
- unconfirmed interpretations, or none

Unresolved:
- conflicts or questions, or none
```

Wait for approval unless the user explicitly requested immediate application.
For a clear initial mapping request, a small non-destructive survey may be
applied directly.

### 6. Apply the map

- Modify only files under `specs/`.
- Preserve user-authored decisions and unrelated content.
- Keep useful relative links and reachability from `specs/README.md`.
- Keep observations separate from inference and normative intent.
- Do not rewrite intent to legitimize accidental implementation behavior.
- Update `specs/README.md` only when top-level navigation, system-wide intent,
  or mapping coverage changes.

### 7. Report

Summarize evidence inspected, files changed, mapped and deepened areas,
inferences awaiting confirmation, unresolved conflicts, and remaining coverage.

## Mapping rules

### Initial survey

Create `specs/README.md` and a small set of architectural entry points. Capture
project purpose, primary actors when apparent, deployable components, major
subsystems, persistence, integrations, broad relationships, and important
unknowns. Do not deeply map the first interesting module.

### Selected area

Identify responsibility, boundary, inputs and outputs, dependencies, consumers,
significant behavior, evidence status, and concepts that may deserve separate
specifications. Stop when another agent can find the area and understand what
must remain true; do not mirror the code.

### Refresh

Start from affected specifications and changed repository areas. Update the
smallest useful set, preserve normative intent, and record unresolved drift. Do
not remap the whole repository for a local change.

### Decomposition and cross-cutting concerns

Split only for an independent responsibility, runtime boundary, meaningful
interface, behavior set, or independently evolving navigation point. Treat
security, observability, configuration, transactions, audit, tenancy, and error
handling as cross-cutting; do not force them under one parent or create a file
without project-specific architectural value.

### Mapping status

Keep coverage qualitative: mapped, deepened, partial, or not mapped. Do not use
percentages or claim formal completeness.

### Intended versus observed architecture

When code and documentation disagree, preserve intended behavior under
`Decisions` or `Constraints`, implemented evidence under `Observed`, and the
conflict under `Open questions`. Do not resolve it silently.

### Context handoff

Follow `references/context-handoff.md`. Include the smallest useful context and
separate required, potentially affected, and merely related specifications.
Carry evidence status and blocking questions without adding downstream
artifacts.

## Readiness for context handoff

An area is ready when:

- a canonical owner is identified;
- responsibility, boundaries, and direct dependencies are understandable;
- relevant decisions and constraints are collected;
- potentially affected specifications are separated from related context;
- blocking architectural questions are explicit;
- observed and inferred claims are distinguishable.

This does not imply readiness for implementation. Product requirements, edge
cases, acceptance criteria, migrations, tests, and implementation readiness
belong downstream. A coding agent still reads relevant code.

## Restrictions

Never:

- modify production code or generate implementation changes;
- present inference or technical debt as accepted intent;
- claim synchronization, conformance, complete coverage, or implementation of
  documented intent;
- silently change normative decisions from repository evidence;
- silently resolve blocking questions or intended-versus-observed conflicts;
- turn the SpecSpine into a source-tree or function-level inventory;
- rewrite unrelated branches;
- create plans, tasks, acceptance criteria, or implementation status.

Be concise, evidence-aware, and architectural. Prefer responsibilities,
boundaries, runtime and data-flow shape, representative evidence, and explicit
uncertainty. The user owns architectural interpretation; this skill organizes
evidence into a durable, navigable SpecSpine.
