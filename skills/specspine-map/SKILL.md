---
name: specspine-map
description: Map observed brownfield repository architecture into a linked Markdown SpecSpine. Use for repository surveys, evidence-backed subsystem mapping, selective deepening, large-repository parallel mapping, refresh after code changes, and drift recording. Do not use to invent or evolve intended architecture (use specspine-grow), perform general integrity audits (use specspine-doctor), extract downstream context, implement changes, or claim code/spec conformance.
---

# SpecSpine Map

Map an existing repository into the smallest useful network of linked
architectural specifications. Map breadth before depth and preserve the
difference between accepted intent and repository evidence.

## Resources

- Read [references/spec-semantics.md](references/spec-semantics.md) before
  classifying claims or recording code/spec disagreement.
- Read [references/spec-format.md](references/spec-format.md) before creating,
  editing, or restructuring specifications. It owns document organization,
  semantic IDs, decomposition, and stopping rules.
- Read [references/mapping-method.md](references/mapping-method.md) before a
  substantial survey, refresh, or restructuring.
- Read [references/parallel-mapping.md](references/parallel-mapping.md) before
  orchestrating subagents for a large repository.
- Read [references/examples.md](references/examples.md) when mapping depth or a
  specification boundary is unclear.
- Start new files from the templates under `assets/templates/` and omit empty
  sections.

## Authority and scope

Use this skill to survey an existing repository, map or deepen a selected area,
refresh repository-backed observations, and record drift between observed and
intended architecture.

Repository evidence may establish observations and support inferences. It does
not establish decisions or constraints and never overrides accepted intent.
Preserve disagreements until the user or an authorized architecture workflow
resolves them.

Map owns repository discovery and the resulting persistent architectural map.
It does not:

- invent or evolve intended architecture; use `specspine-grow`;
- perform a general Spine integrity review; use `specspine-doctor`;
- extract downstream task context; use `specspine-extract`;
- modify production code or create feature requirements, acceptance criteria,
  plans, tasks, or implementation status;
- prove code/spec conformance or complete coverage.

## Workflow

1. Resolve `<spine-root>` using `references/spec-format.md`. Read its index and
   relevant specifications, plus repository documentation or architecture
   records needed to understand existing intent.
2. Choose the shallowest operation that answers the request: whole-repository
   survey, selected-area map, deepening, refresh, or parallel mapping waves.
   For a large repository with subagents available, explicitly enumerate
   independent architectural questions and available worker slots before
   choosing execution shape. When two or more questions can be investigated
   independently, use `references/parallel-mapping.md` and launch the largest
   safe set of workers allowed by its concurrency formula. Do not serialize
   independent investigation merely to avoid write conflicts: workers use
   private staging roots. Investigation within a wave is parallel; source-aware
   integration and planning between bounded waves are sequential. Launching
   only one worker is justified only when exactly one independent question
   remains or repository I/O or available slots impose that limit; report that
   reason. Use ordinary sequential mapping for small or tightly coupled scopes.
3. Gather representative evidence. For a survey, prioritize root docs,
   manifests, runtime entry points, composition roots, public interfaces,
   schemas, integrations, deployment configuration, and representative tests.
   For a selected area or refresh, start from the named specification and
   relevant changed paths; expand only for dependencies that affect the map.
   Before recording an observation or refreshing its evidence baseline, inspect
   every repository source cited for that claim during the current operation;
   never cite unread evidence.
4. Model stable responsibilities, boundaries, runtime and data-flow shape, and
   relationships rather than directories or implementation details. Classify
   claims with `references/spec-semantics.md`.
5. Treat an explicit mapping, refresh, or restructuring request as approval.
   Ask only before changing accepted intent, resolving a conflict or blocking
   question, or choosing among materially different canonical owners.
6. Modify only files under `<spine-root>`, except for disposable isolated
   staging roots used by the parallel protocol. Apply the smallest coherent
   persistent change; preserve unrelated content, accepted intent, useful
   links, and reachability from the index. Follow `references/spec-format.md`
   instead of duplicating its document and semantic-ID rules here. Before
   reporting, verify changed relative links and semantic-ID definitions and
   references against that format. A semantic-ID reference uses the plain ID
   as the complete link label and the owning Markdown file as its destination;
   do not add emphasis or a URL fragment.
7. Report evidence inspected, files changed, mapped or deepened areas,
   unconfirmed inferences, unresolved drift, and qualitative remaining
   coverage.

For an initial survey, create the index and only a few useful architectural
entry points. For a local refresh, do not remap the whole repository. Stop when
the requested architectural question is answered and further detail would
mostly reproduce the code.
