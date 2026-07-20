---
name: specspine-map
description: Progressively map an existing brownfield software project into a long-lived network of linked Markdown architectural specifications. Use when documenting an unfamiliar repository, surveying runtime components, refining an architectural area, preserving intended-versus-observed disagreements, or preparing a minimal architecture context handoff for a downstream tool or coding agent. This skill reads repository evidence but modifies only specifications and does not prove code/spec conformance.
---

# SpecSpine Map

Build and progressively refine a linked Markdown architecture for an existing
software project.

The result is a SpecSpine: a lightweight network of specifications describing
the project's purpose, major responsibilities, boundaries, significant
behavior, decisions, and relationships.

The persistent result is the linked specification network. A context handoff is
only a temporary, task-oriented projection of that network for a downstream
tool or coding agent.

Map the project from broad understanding toward selected detail.

Do not attempt to document every file, class, function, endpoint, table, or
implementation detail.

Read [references/spec-semantics.md](references/spec-semantics.md) before
creating, changing, or reviewing specifications. Read
[references/context-handoff.md](references/context-handoff.md) before preparing
a context handoff.

## Scope

Use this skill when the user wants to:

- create a SpecSpine for an existing repository;
- understand an unfamiliar brownfield project;
- document the high-level system architecture;
- identify major runtime components and subsystems;
- refine the map of a selected architectural area;
- preserve knowledge discovered while investigating code;
- prepare architectural context for future agents;
- prepare an architecture context handoff for a downstream workflow or coding
  agent;
- compare existing code with an existing SpecSpine;
- identify uncertain or conflicting architectural interpretations.

Do not use this skill to:

- modify source code;
- implement features or bug fixes;
- produce exhaustive code documentation;
- generate API reference documentation;
- create feature acceptance criteria or track implementation status;
- treat every directory as an architectural subsystem;
- claim intent that cannot be supported by the repository;
- silently convert technical debt into an accepted architectural decision.

This skill may read source code, configuration, tests, migrations, deployment
files, and existing documentation. It may create or update files under
`specs/`, but it must not modify production code.

# Core mapping principle

Map breadth before depth.

Use this progression:

```text
Repository
    ↓
Project purpose and runtime shape
    ↓
Major components and responsibilities
    ↓
Relationships and boundaries
    ↓
Selected subsystem
    ↓
Significant behavior and decisions
```

Do not deeply document the first interesting module before understanding the
overall project.

The goal is the smallest useful architectural map, not complete documentation.

# Specification layout

Use this layout by default:

```text
specs/
├── README.md
└── <concept>.md
```

Keep specification files in a flat directory.

Software architecture is a graph. Do not mirror the source tree or encode
architectural hierarchy through nested specification directories.

Use lowercase kebab-case filenames based on stable concepts:

```text
api-server.md
authentication.md
background-processing.md
document-indexing.md
persistence.md
```

Avoid filenames based on repository paths, temporary changes, tickets, or
implementation classes:

```text
src-services.md
auth-service-class.md
feature-142.md
legacy-fix.md
```

Read [references/mapping-method.md](references/mapping-method.md) before
performing a substantial repository survey or restructuring an existing
SpecSpine.

Read [references/examples.md](references/examples.md) when choosing mapping
depth, distinguishing observations from inference, or deciding whether a code
area deserves its own specification.

# README.md

`specs/README.md` is required.

It is the entry point into the mapped architecture, not the semantic parent of
every specification.

It should explain:

- what the project appears to do;
- the major runtime components or architectural areas;
- where a new agent should start reading;
- important system-wide observations or accepted decisions;
- unresolved architectural questions;
- the current mapping coverage.

Recommended structure:

```markdown
# Project architecture

## Purpose

A concise description of the project and the problem it solves.

## Architecture map

- [API server](api-server.md) — serves the public application API.
- [Background processing](background-processing.md) — runs asynchronous jobs.
- [Persistence](persistence.md) — owns durable application data.

## System-wide decisions

Accepted decisions that affect several specifications.

## System-wide constraints

Accepted restrictions that affect several specifications.

## Mapping status

- Mapped: high-level runtime architecture
- Deepened: authentication
- Not yet mapped: reporting subsystem

## Open questions

Architectural questions that cannot be resolved confidently from the repository.
```

Do not list every specification when a smaller set of useful entry points is
enough.

# Specification structure

Use the following flexible structure:

```markdown
# Specification name

A short summary of the concept.

## Responsibility

What this concept owns in the current system.

## Boundaries

What belongs to this concept and what belongs elsewhere.

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

## Observed

Facts directly supported by repository evidence.

## Inferred

Architectural interpretations that are plausible but not explicitly established.

## Decisions

Accepted architectural decisions supported by documentation or confirmed by
the user.

## Constraints

Accepted restrictions on downstream architecture or implementation.

## Open questions

Unresolved questions, ambiguities, or conflicts.
```

Sections are optional. Include only sections containing useful information.

Do not add empty sections merely to satisfy the template.

# Statement semantics and evidence levels

Use these meanings consistently:

- `Decisions` and `Constraints` describe intended architecture.
- `Observed` describes current repository evidence.
- `Inferred` describes unconfirmed interpretation.
- `Open questions` preserves unresolved uncertainty.

Observed facts do not override decisions or constraints. Decisions and
constraints do not imply that code implements them. Preserve disagreements
explicitly until the user or a downstream workflow resolves them.

Brownfield mapping must distinguish facts from interpretation.

## Observed

Use `Observed` for claims directly supported by repository evidence such as:

- runtime entry points;
- dependency declarations;
- configuration;
- route registration;
- schemas and migrations;
- test behavior;
- deployment files;
- explicit documentation;
- data flow visible across modules.

Where helpful, mention representative code locations using repository-relative
paths.

Example:

```markdown
## Observed

- `apps/api/src/main.ts` starts the HTTP server.
- `apps/worker/src/main.ts` starts a separate background worker.
- Both processes use the PostgreSQL connection configured in
  `packages/database`.
```

Do not turn `Observed` into a file inventory.

## Inferred

Use `Inferred` for architectural interpretations such as:

- a group of modules appears to form one subsystem;
- a directory boundary seems to represent ownership;
- an event stream appears to be the integration boundary;
- a service is likely intended to be independently deployable.

State inference cautiously.

Example:

```markdown
## Inferred

- The API and worker appear to be separate runtime components sharing one
  application data model.
```

## Decisions

Use `Decisions` only when:

- the repository explicitly documents the decision;
- an ADR or equivalent record establishes it;
- the user confirms the interpretation;
- the decision is unambiguous and intentionally encoded by the system.

Do not classify an accidental implementation detail as an architectural
decision.

When repeated repository evidence suggests a useful architectural decision but
no authoritative intent exists, propose the decision and ask the user to
confirm it. Do not write it as an accepted decision automatically.

## Constraints

Use `Constraints` for accepted restrictions that downstream architecture or
implementation must preserve. A constraint is normative intent, not evidence
that the repository currently satisfies it.

# Role in the project lifecycle

`specspine-map` discovers repository evidence, records observed architecture,
and proposes interpretations or structural changes. It must not silently alter
normative decisions or constraints.

`specspine-grow` owns intentional evolution of the SpecSpine. It creates and
updates normative architecture and may preserve relevant observations without
deeply discovering them from code.

Both skills may update the linked specification network and produce the same
architecture context handoff. Both preserve intended-versus-observed
disagreements. Neither proves code/spec conformance, implements changes, or
silently resolves blocking architectural questions.

# Mapping passes

## Pass 1: Survey

Build a high-level map of the whole repository.

Inspect the smallest useful set of project signals:

- root documentation;
- package or workspace manifests;
- top-level directories;
- runtime entry points;
- deployment and container files;
- configuration;
- major dependency boundaries;
- database schemas or migrations;
- representative tests.

Determine:

- project purpose;
- primary users or external actors when apparent;
- deployable or executable components;
- major subsystems;
- persistence and external integrations;
- broad relationships;
- important unknowns.

Create only a small number of specifications.

A survey result should usually contain between three and eight architectural
entry points, but use judgment rather than a numeric rule.

Do not deeply map internal modules during the survey unless required to
understand the system shape.

## Pass 2: Map a selected area

For a selected subsystem:

- identify its responsibility;
- determine its boundary;
- find its main inputs and outputs;
- identify important dependencies and consumers;
- describe significant behavior;
- distinguish observed facts from inferred architecture;
- identify concepts that deserve separate specifications;
- preserve unresolved ambiguity.

Read representative code rather than every file.

Prefer entry points, public interfaces, tests, schemas, and integration edges
over local implementation internals.

## Pass 3: Deepen only when useful

Deepen a branch when:

- the user asks about it;
- an upcoming change requires it;
- its current specification is too abstract for safe implementation;
- several distinct responsibilities have emerged;
- a cross-cutting dependency is unclear.

Stop when a new coding agent can understand where to look, what the area owns,
what it depends on, and which decisions must be preserved.

Do not continue until the prose mirrors the code.

# Operating workflow

## Step 1: Inspect existing architecture material

Read:

- the repository root documentation;
- any existing `specs/README.md`;
- relevant existing specifications;
- ADRs or architecture documentation when present.

If a SpecSpine already exists, preserve its accepted structure unless evidence
or the user request justifies a change.

## Step 2: Choose mapping depth

Infer the requested depth:

- `survey` — map the project broadly;
- `map` — describe a selected subsystem;
- `deepen` — add detail required for a specific change;
- `refresh` — update specs after meaningful repository evolution;
- `review` — identify weak or uncertain areas in the current map.
- `handoff` — prepare minimal architectural context for downstream work.

The user does not need to use these words explicitly.

Default to the shallowest depth that answers the request.

## Step 3: Gather representative evidence

Inspect enough repository evidence to support an architectural description.

Do not read the entire repository by default.

Prioritize:

1. entry points and composition roots;
2. public interfaces and routing;
3. module or package boundaries;
4. schemas, migrations, and contracts;
5. integration adapters;
6. representative tests;
7. implementation internals only when necessary.

## Step 4: Form the smallest useful model

Identify stable concepts rather than copying the filesystem.

A directory deserves a specification only when it represents an architectural
responsibility or useful navigation boundary.

Several directories may belong to one specification.

One directory may contain several architectural concepts.

## Step 5: Present structural impact

Before creating, renaming, deleting, splitting, merging, or modifying several
specification files, present an impact proposal.

Use this format:

```text
Mapping proposal

Create:
- specs/api-server.md
- specs/background-processing.md
- specs/persistence.md

Modify:
- specs/README.md

Evidence inspected:
- package manifests
- runtime entry points
- deployment configuration
- database migrations

Inferred structure:
- API and worker are separate runtime components sharing persistence.

Unresolved:
- Ownership of scheduled reporting jobs is unclear.

Proceed with these specification changes?
```

Wait for approval unless the user explicitly requested immediate application.

For an initial mapping request that clearly asks the skill to create the
SpecSpine, the skill may apply a small, non-destructive initial survey directly
and report what was created.

## Step 6: Apply the approved map

After approval:

- create or update specifications;
- use ordinary relative Markdown links;
- update `specs/README.md` when top-level navigation changes;
- keep observations separate from inference;
- avoid duplicated canonical descriptions;
- preserve existing user-authored decisions;
- do not rewrite unrelated specifications;
- keep broad overview files concise.

## Step 7: Report mapping coverage

Summarize:

- evidence inspected;
- specifications created or modified;
- areas mapped at high level;
- areas deepened;
- inferred architecture awaiting confirmation;
- unresolved questions;
- recommended next branch to map, only when useful.

# Creating the initial map

When no SpecSpine exists, create:

```text
specs/
├── README.md
└── a small set of top-level specifications
```

A repository containing a web application, API process, worker, and shared
database might initially produce:

```text
specs/
├── README.md
├── web-application.md
├── api-server.md
├── background-processing.md
└── persistence.md
```

Do not immediately create specifications for every domain module.

The initial map should be useful even when incomplete.

# Mapping existing architecture versus desired architecture

The repository shows the implemented system, not necessarily the intended
system.

When code and documentation disagree:

- describe the implemented behavior under `Observed`;
- preserve explicit intended behavior under `Decisions` when authoritative;
- record the mismatch under `Open questions`;
- do not silently resolve the conflict;
- do not rewrite the specification to legitimize accidental code behavior.

Example:

```markdown
## Observed

- The API directly writes audit records during request handling.

## Decisions

- The existing ADR states that audit delivery should be asynchronous.

## Open questions

- Is the synchronous path temporary technical debt or has the ADR been
  superseded?
```

# Working with an existing SpecSpine

When specifications already exist:

1. Treat accepted decisions as architectural intent.
2. Use code to add observations and implementation context.
3. Do not replace concise architecture with a source-tree description.
4. Propose changes when the repository reveals missing responsibilities or
   incorrect boundaries.
5. Preserve disagreements explicitly.

Do not claim that the SpecSpine and code are synchronized merely because both
were inspected.

SpecSpine does not guarantee code/spec conformance. Preserve meaningful
disagreements between observed evidence and intended decisions or constraints
as part of the architectural record.

# Decomposition

Propose a separate specification when an observed concept:

- has an independent responsibility;
- owns a distinct runtime boundary;
- exposes a meaningful interface;
- contains several significant behaviors or decisions;
- is used by multiple architectural areas;
- evolves independently;
- is necessary as a navigation point for future agents.

Do not split based on directory count or file length alone.

After a split, retain a concise overview and links in the broader
specification.

# Cross-cutting concerns

Security, observability, configuration, transactions, audit, tenancy, and error
handling may cut across several subsystems.

Do not force them under a single parent merely to create a hierarchy.

Create a separate specification only when the concern has project-specific
behavior, decisions, or boundaries worth preserving.

Otherwise record the relevant relationship or decision in the specifications
that own the behavior.

# Mapping status

Use `Mapping status` in `specs/README.md` to communicate coverage without
formal metadata.

Example:

```markdown
## Mapping status

- High-level map complete
- Deepened: authentication, document processing
- Partially mapped: billing
- Not mapped: internal administration tools
```

Keep this qualitative. Do not create a complex coverage system.

# Preparing an architecture context handoff

When asked to prepare context for downstream work, follow
[references/context-handoff.md](references/context-handoff.md). Return:

```text
Change intent:
- what the downstream workflow is expected to accomplish

Primary specification:
- the canonical owner of the changed responsibility

Required specifications:
- specifications that must be read to understand the change safely

Potentially affected specifications:
- specifications that may require architectural updates

Architectural decisions and constraints:
- accepted architectural intent that downstream work must preserve

Relevant observations:
- current repository facts that affect downstream execution

Unconfirmed inferences:
- interpretations that downstream tools must not treat as accepted decisions

Blocking questions:
- questions that downstream work must not answer silently

Expected architectural outcome:
- the architectural state expected after the downstream change
```

Include only the smallest useful context. Do not classify every related
specification as potentially affected.

# Readiness for context handoff

An architectural area is ready for context handoff when:

- a canonical owner is identified;
- responsibility and boundaries are understandable;
- direct dependencies are identified;
- relevant decisions and constraints are collected;
- potentially affected specifications are separated from merely related ones;
- blocking architectural questions are explicit;
- observed and inferred claims are distinguishable.

Readiness for context handoff does not imply readiness for implementation.
Downstream workflows remain responsible for product requirements, acceptance
criteria, edge cases, migration plans, test requirements, and implementation
readiness. A coding agent still reads relevant code; SpecSpine tells it where
to look and which architectural intent to preserve.

# Restrictions

Never:

- modify source code;
- generate implementation changes;
- document every source file;
- mirror the repository tree mechanically;
- infer business intent solely from names;
- present inference as observed fact;
- present technical debt as accepted architecture;
- describe local algorithms unless they affect architecture or behavior;
- rewrite the entire SpecSpine when a local update is sufficient;
- create a rigid hierarchy for naturally cross-linked concepts;
- claim complete coverage without evidence;
- claim synchronization between specs and code;
- claim that a decision or constraint is implemented merely because it is in a
  specification;
- silently change normative decisions based on repository evidence;
- silently resolve intended-versus-observed disagreements or blocking
  architectural questions;
- create plans, task files, acceptance criteria, or implementation status.

# Response style

Be concise, evidence-aware, and architectural.

Prefer:

- major responsibilities;
- runtime boundaries;
- data and control relationships;
- representative evidence;
- uncertainty made explicit.

Avoid:

- exhaustive file listings;
- speculative product requirements;
- implementation narration;
- generic architecture advice unrelated to the repository.

The user owns architectural interpretation. The skill organizes repository
evidence into a durable, navigable SpecSpine.
