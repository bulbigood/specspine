---
name: specspine-map
description: Map observed brownfield repository architecture into a linked Markdown SpecSpine. Use for initial repository surveys, one bounded architectural question, evidence-backed subsystem mapping, selective deepening, local refresh after code changes, and drift recording. Do not orchestrate complete or sustained large-repository runs; the operator must explicitly invoke specspine-map-large for that operation. Do not invent intended architecture, perform general integrity audits, extract downstream context, implement changes, or claim code/spec conformance.
---

# SpecSpine Map

Map one requested repository scope into the smallest useful set of linked
architectural specifications. Map breadth before depth and preserve the
difference between accepted intent and repository evidence.

## Resources

- Read [references/spec-semantics.md](references/spec-semantics.md) before
  classifying claims or recording code/spec disagreement.
- Read [references/spec-format.md](references/spec-format.md) before creating,
  editing, or restructuring specifications.
- Read [references/mapping-method.md](references/mapping-method.md) before a
  substantial survey, refresh, or restructuring.
- Read [references/examples.md](references/examples.md) only when mapping depth
  or a specification boundary is unclear.
- Start new files from `assets/templates/` and omit empty sections.

## Authority and scope

Use this skill for an initial high-level survey, one selected area, deepening,
refresh, or drift recording. Do not select or orchestrate a continuous
large-repository run; only an explicit operator invocation of
`$specspine-map-large` starts that operation.

Repository evidence may establish observations and support inferences. It does
not establish decisions or constraints and never overrides accepted intent.
Preserve disagreements until the user or an authorized architecture workflow
resolves them.

Do not:

- invent or evolve intended architecture; use `specspine-grow`;
- perform a general Spine integrity review; use `specspine-doctor`;
- extract downstream task context; use `specspine-extract`;
- modify production code or create requirements, plans, tasks, or
  implementation status;
- prove code/spec conformance or complete coverage.

## Workflow

1. Resolve `<spine-root>` using `references/spec-format.md`. Read its index,
   relevant specifications, and only the repository documentation or
   architecture records needed to understand existing intent.
2. Choose the shallowest operation that answers the bounded request. For an
   initial survey, inspect whole-system shape but create only a few useful entry
   points. For a selected area or refresh, begin with the named specification
   and relevant changed paths.
3. Inspect representative evidence: root documentation, manifests, runtime
   entry points, composition roots, public interfaces, schemas, integrations,
   deployment configuration, and representative tests as applicable. Inspect
   every cited source during the current operation; never cite unread evidence.
4. Model stable responsibilities, boundaries, runtime and data-flow shape, and
   relationships rather than directories or implementation details. Classify
   claims with `references/spec-semantics.md`.
5. Treat the explicit bounded mapping, refresh, or restructuring request as
   approval. Ask only before changing accepted intent or choosing among
   materially different canonical owners.
6. Write only under the explicitly supplied writable documentation root. By
   default this is `<spine-root>`. If the request supplies a separate output
   root, keep the live Spine read-only and create only publish-ready new
   specifications at paths relative to their final live destinations; do not
   update `README.md`.
7. For live writes, apply the smallest coherent change and preserve unrelated
   content, accepted intent, useful links, and reachability from the index.
   Verify changed relative links and semantic-ID definitions and references.
   A semantic-ID reference uses the plain ID as its complete link label and the
   owning Markdown file as its destination, without emphasis or a URL fragment.
8. Report evidence inspected, files created or changed, mapped
   responsibilities and relationships, material adjacent architectural
   questions, unconfirmed inferences, unresolved drift, and qualitative
   remaining coverage. It is valid to create no document when the live Spine
   already answers the question or further detail would reproduce code.

Stop when the requested architectural question is answered and additional
reading would have low architectural value or mostly reproduce implementation.
