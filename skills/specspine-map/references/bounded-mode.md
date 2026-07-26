# SpecSpine bounded mapping protocol

Map the requested repository scope by one shallowest useful step into the
smallest coherent set of linked architectural specifications. Map breadth
before depth and preserve the difference between accepted intent and repository
evidence.

## Authority and scope

Use this protocol for an initial high-level survey, one or more selected areas
or questions, one bounded deepening step, refresh, or drift recording.

Source code, tests, configuration, and other repository behavior may establish
observations and support inferences. They do not establish decisions or
constraints and never override accepted intent. Preserve disagreements until
the user or an authorized architecture workflow resolves them.

Do not:

- invent or evolve intended architecture; use `specspine-grow`;
- perform a general Spine integrity review; use `specspine-doctor`;
- extract downstream task context; use `specspine-extract`;
- modify production code or create requirements, plans, tasks, or
  implementation status;
- prove code/spec conformance or complete coverage.

## Workflow

1. Resolve `<spine-root>` using `spec-format.md`. If its `README.md` is absent
   and live writes are authorized, create a minimal v2 index from
   `assets/templates/architecture-index.md` before discovery, with the whole
   project `Unmapped`. If a separate output root was supplied, keep the live
   root read-only and stop for setup. Then read the index, relevant
   specifications, and only repository documentation or architecture records
   needed to understand existing intent.
2. Perform one shallowest useful mapping step for the requested scope. A step
   is the smallest coherent documentation change, not necessarily one file.
   For an initial survey, inspect whole-system shape but create only a few
   useful entry points. For a selected area or refresh, begin with the named
   specification and relevant changed paths. Report further depth and adjacent
   branches instead of pursuing them recursively in the same operation.
3. Inspect representative evidence: root documentation, manifests, runtime
   entry points, composition roots, public interfaces, schemas, integrations,
   deployment configuration, and representative tests as applicable. Inspect
   every cited source during the current operation; never cite unread evidence.
   Tests may reveal edge and failure behavior even though they are excluded
   from production-source compression estimates.
4. Model stable responsibilities, boundaries, runtime and data-flow shape, and
   relationships rather than directories or implementation details. Apply the
   coverage, quality, compression, and visual criteria from the mapping and
   format references. Classify claims with `spec-semantics.md`.
5. Treat the explicit mapping, refresh, or restructuring request as approval.
   Ask only before changing accepted intent or choosing among materially
   different canonical owners.
6. Write only under the explicitly supplied writable documentation root. By
   default this is `<spine-root>`. If the request supplies a separate output
   root, keep the live Spine read-only and create publish-ready new
   specifications or complete replacements of explicitly assigned existing
   specifications at paths relative to their final live destinations; do not
   update `README.md`.
7. For live writes, apply the smallest coherent change and preserve unrelated
   content, accepted intent, useful links, and reachability from the index.
   Verify changed relative links and semantic-ID definitions and references.
   A semantic-ID reference uses the plain ID as its complete link label and the
   owning Markdown file as its destination, without emphasis or a URL fragment.
8. Report evidence inspected, files created or changed, mapped
   responsibilities and relationships, material adjacent architectural
   questions, unconfirmed inferences, unresolved drift, source areas classified
   during this step, and qualitative remaining coverage. For an orchestrated
   checkpoint, explicitly assess ownership coverage, orientation, information
   gain, change utility, and non-duplication; do not report local saturation
   while any of those gates has a material gap. For every reported source area,
   name the concrete evidence inspected and whether it exposed a missing
   observation, an explicit existing owner claim, generated/vendored/test
   material, or only local implementation detail. Create or change no document
   when the live Spine already answers the question at the quality gate,
   evidence cannot support a useful architectural node, or further detail would
   reproduce implementation. Report that terminal reason explicitly instead of
   manufacturing output.

Stop when the requested architectural scope passes the qualitative depth gate
and additional reading would have low architectural value or mostly reproduce
implementation.
