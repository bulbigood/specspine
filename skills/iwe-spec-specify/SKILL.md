---
name: iwe-spec-specify
description: Create or refine accepted durable software specifications in a Specspine v5 IWE library. Use for greenfield intent, requirements and architecture changes, impact analysis, and restructuring accepted specifications.
---

# IWE Spec Specify

Work only with accepted intent. Use the installed official `iwe-memory-system`
skill for every IWE operation and read it before continuing. If it is
unavailable, stop and direct the operator to the Specspine README setup.

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

1. Run the IWE compatibility gate. Locate candidates with bounded fuzzy and
   lexical `iwe find` recipes and read only the deliberately expanded closure.
   Once one owner is unambiguous, do not retrieve neighbors merely because they
   are linked.
2. Update the canonical owner. Do not copy claims between owners.
3. Apply the `refine` versus `expand` owner test from the semantics reference.
   Create a new owner only after `expand` passes and the plausible existing
   owners have been named and rejected with a boundary reason:

   ```bash
   iwe create --template specification --var title=<title> --var body=<body> --strict
   ```

   Use supported `--set` fields when creation-time frontmatter is known; use
   `iwe update` for later changes.
4. Use a link-only paragraph only to make the target a structural child. Keep
   dependencies and conceptual connections inline.
5. Use `iwe rename`, `iwe delete`, `iwe extract`, and `iwe inline` instead of
   maintaining links manually.
6. Run `iwe schema validate` after each write batch. Then apply the semantic
   audit gate to every changed owner. Stop on errors caused by the batch; do not
   report an owner ready while audit errors remain.

A new topic is not automatically a new owner. Place a claim in the existing
owner whose responsibility governs it unless accepted intent gives the topic
an independent durable boundary.

Statement IDs are owner-local, not globally unique. Refine a matching claim
instead of creating a near duplicate. A blocking `OQ-*` must exist in the same
document and be listed in its `blockers` frontmatter. Non-normative assets and
observations are evidence, not accepted intent and cannot support facet
advancement.

Do not invent relationship metadata, generated indexes, lifecycle state, or
other structures that duplicate IWE.
