---
name: iwe-spec-map
description: Map boundary-significant repository evidence into Specspine v5 documents managed by IWE. Use for brownfield surveys, focused deepening, evidence refresh, and implementation drift inspection.
---

# IWE Spec Map

Map repository evidence without turning implementation details into accepted
intent.

Use the installed official `iwe-memory-system` skill for every IWE operation
and read it before continuing. If it is unavailable, stop and direct the
operator to the Specspine README setup.

Treat its CLI examples as guidance that may lag the installed IWE binary. If a
command rejects an argument or prints a deprecation warning, run
`iwe <command> --help`, switch to the syntax reported by the installed CLI, and
do not retry the known-stale form.

Before interpreting or writing Specspine documents, read
[Specspine format](references/specspine-format.md) and
[Specspine semantics](references/specspine-semantics.md) completely. Read and
apply [IWE operations](references/specspine-operations.md) before discovery or
retrieval. Before
claiming semantic readiness, also read and apply
[semantic audit](references/specspine-audit.md) to every changed owner. The
workspace `.iwe/schemas/specification.yaml` is the executable contract for exact
fields, values, sections, ordering, and statement syntax; the references define
the semantic rules that the schema cannot express.

Resolve the applicable IWE project root as defined by the format reference
before running any IWE command. Use that root as the working directory and read
its `.iwe/config.toml` once to determine `library.path`. Treat unavailable IWE
or missing required Specspine configuration as an incomplete setup: stop and
ask the operator to run `iwe-spec-setup`. If that skill is unavailable, point
to the README manual fallback. Do not install or repair setup from this
workflow.

1. Run the IWE compatibility gate, then discover existing owners with bounded
   fuzzy and lexical `iwe find` recipes. Use `iwe tree` only when hierarchy
   disambiguates ownership.
2. Retrieve only the task-bounded neighborhood using explicit expansion
   directions and budgets from the operations reference.
3. Select the inspection mode that matches the work:
   - `survey` for the first broad boundary pass;
   - `deepen` for focused evidence inside a known owner;
   - `refresh` for replacing stale evidence with a current inspection;
   - `drift` for comparing current implementation evidence with the last
     recorded inspection.
4. Apply the evidence exception layer. Record a confirmed fact as owner-local
   `OBS-*` under `## Observed` only when it adds boundary-significant evidence,
   divergence, or requested provenance beyond accepted intent. Record a useful
   interpretation as `INF-*` under `## Inferred`.
5. Store focused inspection metadata in the owner as
   `inspection: { source: <paths>, inspected: <YYYY-MM-DD>, mode: <mode> }`.
6. Run the owner test before creating a document:
   - name the existing owner whose responsibility most plausibly governs it;
   - choose `refine` when that boundary already contains the fact;
   - choose `expand` only when the candidate is independently useful, has a
     durable responsibility, lifecycle, or external boundary, and is not a
     source-layout or feature subtopic.
   Create through the IWE `specification` template only after `expand` passes
   and record why each plausible existing owner failed the test.
7. Express structural decomposition with link-only paragraphs and other
   connections with inline references.
8. Run `iwe schema validate`, then apply the semantic audit gate to every changed
   owner. Stop on errors caused by the batch; do not report an owner ready while
   audit errors remain.

Never promote implementation evidence to accepted Behavior, Interfaces,
Failure behavior, Data ownership, Lifecycle, Requirements, or Verification.
Observations do not make a normative facet complete and do not make an owner
ready. Never change a facet on the strength of `OBS`, `INF`, inspection
metadata, or a non-normative asset. Preserve existing accepted content.

In `refresh` and `drift`, inspect prior `OBS-*` claims in scope. Keep confirmed
claims, update a claim whose current fact changed, and remove a claim that is no
longer true or exception-worthy. Do not append contradictory current-state
observations merely to preserve history.

Assign each fact to one canonical owner. For a cross-owner flow, record each
owner's part once and connect the owners instead of repeating claims. For a
combined Map → Specify task, validate the observed-only state before adding new
accepted intent.

Do not create a repository inventory, generated index, manifest, mapping
frontier, observed-edge registry, relationship type, or graph beside IWE.
