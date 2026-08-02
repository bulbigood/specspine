---
name: iwe-spec-map
description: Map boundary-significant repository evidence into Specspine v5 documents managed by IWE. Use for brownfield surveys, focused deepening, evidence refresh, and implementation drift inspection.
---

# IWE Spec Map

Map repository evidence without turning implementation details into accepted
intent.

Use the official `iwe-memory-system` skill for every IWE operation. If it is
unavailable, obtain it from the official `iwe-org/skills` distribution through
the environment's supported skill installer and read it before continuing.

Before interpreting or writing Specspine documents, read
[Specspine format](references/specspine-format.md) and
[Specspine semantics](references/specspine-semantics.md) completely. The
bundled schema is the executable contract for exact fields, values, sections,
ordering, and statement syntax; the references define the semantic rules that
the schema cannot express.

Resolve the applicable IWE project root as defined by the format reference
before inspecting configuration or running any IWE command. Use that root as
the working directory.

Inspect `.iwe/config.toml` and the bundled `assets/iwe` directly. Read
[IWE project setup](references/iwe-bootstrap.md) only when the Specspine
template, binding, or schema is missing or conflicting. Do not use or create a
Specspine bootstrap script.

1. Discover existing owners with `iwe find` and `iwe tree`.
2. Retrieve only the task-bounded neighborhood with `iwe retrieve`.
3. Select the inspection mode that matches the work:
   - `survey` for the first broad boundary pass;
   - `deepen` for focused evidence inside a known owner;
   - `refresh` for replacing stale evidence with a current inspection;
   - `drift` for comparing current implementation evidence with the last
     recorded inspection.
4. Record confirmed facts as owner-local `OBS-*` statements under
   `## Observed`; record interpretations as `INF-*` under `## Inferred`.
5. Store focused inspection metadata in the owner as
   `inspection: { source: <paths>, inspected: <YYYY-MM-DD>, mode: <mode> }`.
6. Create a document through the IWE `specification` template only for an
   independently useful responsibility, lifecycle, or external boundary.
7. Express structural decomposition with link-only paragraphs and other
   connections with inline references.
8. Run `iwe schema validate`, then audit owner-local ID uniqueness and blocker
   targets as semantic checks.

Never promote implementation evidence to accepted Behavior, Interfaces,
Failure behavior, Data ownership, Lifecycle, Requirements, or Verification.
Observations do not make a normative facet complete and do not make an owner
ready. Preserve existing accepted content.

Assign each fact to one canonical owner. For a cross-owner flow, record each
owner's part once and connect the owners instead of repeating claims. For a
combined Map → Specify task, validate the observed-only state before adding new
accepted intent.

Do not create a repository inventory, generated index, manifest, mapping
frontier, observed-edge registry, relationship type, or graph beside IWE.
