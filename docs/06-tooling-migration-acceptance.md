# Tooling, migration, and acceptance

## Derived model

A disposable implementation MAY materialize:

- document identity, title, kind, aliases, summary, and sections;
- semantic statements and their kinds;
- typed relationships and navigation links;
- incoming edges;
- evidence paths;
- coverage and Known divergences;
- full-text search fields.

The same canonical Markdown MUST always produce the same derived records and
edges. Derived storage MUST be rebuildable and MUST NOT accept independent
architectural edits.

Exact IDs, paths, titles, and aliases outrank broad full-text matches. Inline
code SHOULD be indexed because it often carries important domain and code
identifiers. Recommended ranking weights are implementation tuning, not
canonical architectural data.

## Component responsibilities

- Shared format and semantics references own the reusable contract consumed by
  runtime skills.
- Templates provide the minimum valid index and node shapes.
- The checker owns deterministic mechanical findings.
- Extract owns deterministic structured retrieval and Markdown handoff
  projection.
- Map records observed brownfield architecture and evidence without converting
  observations into intent.
- Grow creates or evolves accepted intended architecture without inspecting
  project code by default.
- Doctor manages the bounded project-agent connection and diagnoses or repairs
  Spine health within its authorization boundary.
- Repository-only tools may validate shared resources, run diagnostics, or
  generate framework adapters, but are not runtime architecture authorities.

Runtime skills remain framework-neutral. Feature workflow conventions belong to
external adapters and downstream systems.

## Migration from an earlier Spine

Migration SHOULD proceed incrementally:

1. inventory Markdown specifications and preserve existing content;
2. establish the root index and qualitative coverage;
3. add stable identity and kind to each node;
4. identify canonical owners before removing duplication;
5. convert architecturally meaningful links into typed relationship rows while
   retaining useful prose navigation;
6. classify accepted intent, observations, inferences, and questions;
7. add semantic IDs only where exact references are needed;
8. record confirmed intent/reality conflicts once as Known divergences;
9. run the parser and checker;
10. build the disposable index and retrieval path;
11. validate representative structured queries and degraded navigation.

Migration MUST NOT silently choose ownership, manufacture acceptance, resolve
open questions, or rewrite intent from code. Stable externally referenced IDs
must be preserved.

## Acceptance criteria

### Human readability

Without special tooling, a reader can open the root index, find an area,
understand responsibility and boundaries, navigate links, interpret typed
relationships, distinguish intent from evidence, see uncertainty and coverage,
and find known divergences and consequences.

### Determinism and traceability

The same Spine produces the same document records, statement records, graph,
navigation, and generated views. Scripts can resolve canonical owners,
dependencies, interfaces, constraints, data ownership, representative
implementation locations, incoming impact, coverage, and divergences.

### Authority and drift

Reference scenarios demonstrate that agents preserve the authority split,
never promote `OBS` to `DEC` or `CON`, do not treat code as automatic rejection
of intent, return applicable divergences and incomplete coverage, avoid
out-of-scope drift repair, and apply accepted supersession without losing stable
identity or history.

### Retrieval quality

Evaluation targets:

- canonical-owner recall: 100%;
- critical decision and constraint recall: 100%;
- required-neighbor recall: as close to 100% as practical;
- potentially affected precision measured separately;
- no hidden no-match, truncation, invalidity, or partial coverage.

Compared with code-first exploration, retrieval should require one primary tool
call, substantially fewer context tokens and irrelevant source reads, no worse
functional correctness, and no increase in architectural violations. A
tenfold context reduction in well-mapped tasks is an evaluation goal, not a
format guarantee.

### Resilience

Deleting derived storage does not damage canonical documents, lose
architectural information, prevent direct Markdown navigation, or prevent a
complete rebuild.

### Script-only extraction

For the same structured request and Spine, extraction produces the same closure
without an AI model or source-code reads. It returns one normative status,
never reports `complete` for incomplete coverage, includes required owners,
intent, coverage, divergences, and blocking questions, and reports omitted
information explicitly.

## Delivery boundary

The v2 contract does not require a canonical graph database, YAML frontmatter,
embeddings, generated narrative, runtime telemetry ingestion, automated
conformance proof, framework-specific SDD runtime, feature planning,
implementation task management, or release tracking.

The final invariant is:

> SpecSpine stores accepted architectural intent once in readable Markdown.
> Code remains the source of implementation reality, and known disagreements
> remain explicit. Stable identity, canonical responsibility, coverage,
> addressable statements, and explained typed relationships let an agent find
> the owner and assemble the smallest useful task closure without turning the
> documentation into a formal modeling framework.
