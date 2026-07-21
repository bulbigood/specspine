---
name: specspine-map
description: Map observed brownfield repository architecture into a linked Markdown SpecSpine. Use for repository surveys, evidence-backed subsystem mapping, selective deepening, refresh after code changes, drift recording, and evidence-aware context handoffs. Do not use to invent or evolve intended architecture (use specspine-grow), perform general integrity audits (use specspine-doctor), implement changes, or claim code/spec conformance.
---

# SpecSpine Map

Runtime contract: SpecSpine v1.

Map an existing repository into a lightweight, long-lived network of linked
architectural specifications. The network is the persistent artifact; a context
handoff is a temporary projection for downstream work.

Map breadth before depth. Build the smallest useful architectural model rather
than exhaustive code documentation.

## Resources

- Read [references/spec-semantics.md](references/spec-semantics.md) before
  classifying or changing architectural claims.
- Read [references/spec-format.md](references/spec-format.md) before creating or
  editing specification documents. It owns their organization, content, and
  stopping rules; do not reconstruct those rules from this workflow.
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

## Lifecycle role

Discover repository evidence, record observed architecture, and propose
interpretations or structural changes without silently altering normative
intent. Propose new decisions or constraints for user confirmation instead of
accepting them from evidence alone.

Remain fully usable without any companion skill. Update the linked network and
produce context handoffs without proving conformance or implementing changes.

## Workflow

### 1. Inspect existing architecture material

Resolve `<spine-root>` using `references/spec-format.md`. Read root
documentation, `<spine-root>/README.md`, relevant specifications, and ADRs or
equivalent architecture records. Preserve accepted structure unless evidence
or the request justifies changing it.

### 2. Choose mapping depth

Use the shallowest depth that answers the request:

- `survey` — map the project broadly;
- `map` — describe a selected subsystem;
- `deepen` — add detail needed for a specific architectural question;
- `refresh` — update specs after repository evolution;
- `handoff` — prepare minimal downstream architectural context.

### 3. Gather representative evidence

Prioritize root docs and manifests, composition roots, runtime entry points,
public interfaces, schemas and migrations, integration edges, deployment
configuration, and representative tests. Read implementation internals only
where boundaries remain unclear.

For a selected-area or refresh request, begin from the named specification and
known relevant paths. Use targeted path and symbol searches; do not start with a
repository-wide content search or read unrelated branches merely to inventory
them. A filename listing is discovery metadata, not authorization to read every
listed file. Before reading file contents, establish a boundary of relevant
specifications, paths, and symbols from the request and filename metadata, then
scope content searches to that boundary. Expand it only when inspected evidence
reveals a cross-boundary dependency relevant to the requested map, and report
the expansion.

### 4. Form the smallest useful model

Choose stable responsibilities rather than filesystem shapes. A directory is
not automatically a subsystem; several directories may implement one concept,
and one directory may contain several concepts.

Classify every architectural claim according to
`references/spec-semantics.md`.

### 5. Apply authority-aware approval

Treat an explicit mapping, refresh, or restructuring request as approval; do
not ask twice. Apply observations, inferences, evidence baselines, navigation,
and clearly meaning-preserving structure directly. Never treat repository
evidence as approval of normative intent.

Stop and request a decision only when the change would alter accepted intent,
resolve a conflict or blocking question, choose among plausible canonical
owners, or introduce an agent-initiated structure whose meaning is unclear.
When approval is still required, show:

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

For an explicitly requested or otherwise safe change, apply it and include the
same mapping information in the final report instead of pausing.

### 6. Apply the map

- Modify only files under `<spine-root>/`.
- Preserve user-authored decisions and unrelated content.
- Keep useful relative links and reachability from `<spine-root>/README.md`.
- Keep observations separate from inference and normative intent.
- Add or refresh the evidence baseline for repository-backed observations.
- Write repository evidence paths as inline code, not as Markdown links that
  escape `<spine-root>`; reserve relative Markdown links for the specification
  graph.
- When adding or changing a semantic ID, follow `Addressable statements` in
  `references/spec-format.md`. Preserve the document's language and local
  heading style when the statement kind remains unambiguous.
- Do not rewrite intent to legitimize accidental implementation behavior.
- Update `<spine-root>/README.md` only when top-level navigation, system-wide
  intent, or mapping coverage changes.

### 7. Report

Summarize evidence inspected, files changed, mapped and deepened areas,
inferences awaiting confirmation, unresolved conflicts, and remaining coverage.

## Mapping rules

### Initial survey

Create `<spine-root>/README.md` and a small set of architectural entry points
using `references/spec-format.md`. Survey broadly; do not deeply map the first
interesting module.

### Selected area

Populate the smallest affected document set from representative evidence using
`references/spec-format.md`. Do not mirror the code.

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

### Directories

Start flat. Introduce a few broad directories only when navigation has become
materially difficult and stable cohesive clusters are clear. Do not mirror the
source tree or treat directories as architectural ownership.

### Intended versus observed architecture

Apply the disagreement rules in `references/spec-semantics.md`. Do not resolve
conflicts silently.

### Context handoff

Follow `references/context-handoff.md`. Include the smallest useful context and
separate required, potentially affected, and merely related specifications.
Carry evidence status and blocking questions without adding downstream
artifacts.

## Readiness for context handoff

An area is ready when:

- a canonical owner is identified;
- its documents satisfy the applicable stopping rules in
  `references/spec-format.md`;
- potentially affected specifications are separated from related context;
- blocking architectural questions are explicit;
- claims follow `references/spec-semantics.md`.

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
