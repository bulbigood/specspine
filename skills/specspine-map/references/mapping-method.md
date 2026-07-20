# SpecSpine brownfield mapping method

This reference describes how to progressively map an existing repository
without turning the SpecSpine into a source-code catalog.

## Goal

Create the smallest linked architecture that allows a new human or coding agent
to answer:

- What does this project do?
- What are its major runtime and responsibility boundaries?
- Where should I look for a particular behavior?
- Which other areas are affected by a change?
- Which claims are known, inferred, or still uncertain?

The goal is not complete documentation.

## Breadth-first discovery

Start with the whole-system shape.

A useful initial inspection sequence is:

1. Root README and existing architecture documents.
2. Package, workspace, or build manifests.
3. Top-level directories.
4. Runtime entry points.
5. Container, deployment, and process configuration.
6. Routes, public interfaces, or message consumers.
7. Database schemas and migrations.
8. Representative integration or end-to-end tests.
9. Internal implementation only where boundaries remain unclear.

This sequence is guidance, not a mandatory checklist.

## Signals and what they reveal

### Root documentation

Useful for:

- stated product purpose;
- intended setup;
- named components;
- explicit architecture.

Risk:

Documentation may be stale. Treat unsupported claims carefully.

### Manifests and workspace configuration

Useful for:

- package boundaries;
- executables;
- runtime dependencies;
- framework and infrastructure choices.

Risk:

A package boundary is not automatically an architectural boundary.

### Entry points and composition roots

Useful for:

- runtime components;
- dependency assembly;
- public adapters;
- process-level responsibilities.

These are usually among the highest-value files to inspect.

### Routes, consumers, schedulers, and commands

Useful for:

- external inputs;
- application capabilities;
- integration boundaries;
- asynchronous behavior.

Do not create one specification per route or handler.

### Schemas and migrations

Useful for:

- durable concepts;
- ownership clues;
- lifecycle constraints;
- integration state.

A table is not automatically a subsystem.

### Tests

Useful for:

- significant behavior;
- boundaries intended by the maintainers;
- failure cases;
- hidden contracts.

Prefer integration and end-to-end tests for architectural mapping.

### Deployment and operations files

Useful for:

- deployable units;
- external services;
- process relationships;
- runtime configuration;
- scaling boundaries.

## Choosing specification nodes

A useful specification node is a durable architectural concept.

Good candidates:

- deployable runtime components;
- domain or capability boundaries;
- shared platform responsibilities;
- persistence ownership;
- significant integrations;
- cross-cutting concerns with project-specific rules.

Weak candidates:

- utility directories;
- generic framework layers;
- individual classes;
- isolated endpoints;
- one-off scripts;
- generated code;
- trivial adapters.

Ask:

1. Does this concept own a responsibility?
2. Would a future agent navigate to it for a class of changes?
3. Does it have meaningful relationships or decisions?
4. Can it evolve independently?
5. Is it more stable than the current file layout?

If most answers are no, keep it inside a broader specification.

## Evidence discipline

Use three categories.

### Observed

Directly supported by repository evidence.

Examples:

- an executable starts an HTTP server;
- a migration creates a durable table;
- a consumer subscribes to an event;
- a test confirms idempotent behavior.

### Inferred

Architectural interpretation assembled from evidence.

Examples:

- several modules appear to form one billing subsystem;
- an event appears to be an ownership boundary;
- two packages appear intended as independently deployable services.

### Open question

A meaningful ambiguity or conflict.

Examples:

- documentation and code disagree;
- ownership is split across several modules;
- a dormant component may be obsolete;
- the repository does not reveal product intent.

Do not overuse path citations. Mention representative locations when they help
future navigation or support a non-obvious claim.

## Initial survey output

The first pass should usually produce:

```text
specs/
├── README.md
├── <major-component>.md
├── <major-capability>.md
└── <shared-foundation>.md
```

Each file can be short.

A useful initial node might contain:

```markdown
# Background processing

Runs asynchronous document-processing and notification jobs outside the API
request path.

## Responsibility

- consume queued jobs;
- coordinate long-running processing;
- report job outcomes.

## Relationships

### Depends on

- [Persistence](persistence.md)
- [External storage](external-storage.md)

### Used by

- [API server](api-server.md)

## Observed

- `apps/worker/src/main.ts` starts a separate process.
- Job handlers are registered from `packages/jobs`.

## Inferred

- Background work is intended to scale independently from the API.

## Open questions

- Are failed jobs retried by the queue or by application code?
```

## Deepening a branch

When a user asks to deepen a subsystem:

1. Read its existing specification.
2. Follow direct specification links.
3. Inspect its public entry points.
4. Inspect representative behavior tests.
5. Inspect schemas or contracts it owns.
6. Inspect integration edges.
7. Read local internals only where necessary.
8. Update the smallest affected specification set.

Deepening may reveal a split.

Example:

```text
document-processing.md
```

may become:

```text
document-processing.md
document-ingestion.md
content-extraction.md
search-indexing.md
```

Only split when these concepts have independent responsibilities or evolution.

## Refreshing an existing map

When code has changed:

- start from the affected specifications;
- inspect the relevant diff or changed areas;
- update observations;
- propose architectural changes when boundaries changed;
- preserve accepted decisions;
- record unresolved drift.

Do not perform a whole-repository remap for a local change.

## Stopping condition

Stop mapping when:

- the requested architectural question is answered;
- a new agent can find the relevant code area;
- major responsibility and boundary are clear;
- significant dependencies are linked;
- remaining detail is local implementation;
- additional reading would have low architectural value.

## Common failure modes

### Mirroring directories

Problem:

```text
specs/controllers.md
specs/services.md
specs/repositories.md
```

This often describes framework layering rather than project architecture.

Prefer domain, capability, runtime, and ownership concepts.

### Mapping too deeply too early

Problem:

The agent fully documents authentication internals before noticing that the
repository contains three runtime processes and two separate data stores.

Start with system shape.

### Treating names as intent

Problem:

A directory named `domain` is assumed to contain authoritative business rules.

Verify through usage, tests, interfaces, and documentation.

### Canonizing technical debt

Problem:

A direct database dependency is recorded as an accepted architectural decision
only because it exists.

Record it as observed. Ask whether it is intentional.

### Excessive path references

Problem:

The specification becomes a fragile list of filenames.

Use paths as representative evidence and navigation aids, not as the main
content.

### Claiming completeness

Problem:

A partial survey is presented as the full architecture.

Maintain a qualitative mapping-status section.
