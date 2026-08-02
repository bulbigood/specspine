---
name: iwe-spec-map
description: Map boundary-significant repository evidence into Specspine v5 documents managed by IWE. Use for brownfield surveys, focused deepening, refresh, and drift inspection.
---

# IWE Spec Map

Map repository evidence without turning implementation details into accepted
intent.

Use the official `iwe-memory-system` skill for all IWE operations. If it is not
available, obtain it from the official `iwe-org/skills` distribution through
the environment's supported skill-installation mechanism. Read it before
continuing. Do not substitute generic CLI help or guess syntax that the skill
or targeted command help can establish.

Inspect `.iwe/config.toml` before starting. Read the
[IWE bootstrap protocol](references/iwe-bootstrap.md) only when IWE is not
initialized, its Specspine template or schema is missing, or the requested
library path conflicts with the configured path.

1. Discover existing owners with `iwe find` and `iwe tree`.
2. Retrieve the bounded neighborhood with `iwe retrieve`.
3. Record confirmed boundary evidence as owner-local `OBS-*` statements and
   interpretations as `INF-*`, under the schema sections `## Observed` and
   `## Inferred` respectively.
4. Store inspection metadata in that owner's frontmatter as
   `inspection: { source: <focused evidence paths>, inspected: <YYYY-MM-DD>, mode: deepen }`.
   Use the supported `deepen` mode; do not guess alternate modes.
5. Create a document through the IWE `specification` template only for an
   independently useful owner.
6. Express structural decomposition with standalone inclusion links and other
   connections with inline references.
7. Run `iwe schema validate`.

Add new implementation knowledge only as `OBS-*` or `INF-*`; do not restate it
as accepted Behavior, Interfaces, Failure behavior, Data ownership, Lifecycle,
Requirements, or Verification content. Preserve existing normative prose.
Assign each fact to one canonical owner. For a cross-owner flow, record each
owner's part once and connect owners with an inline reference instead of
repeating the fact or failure behavior. Before finishing, audit touched owners
for semantically duplicated claims and observation promoted to intent.

For a combined Map → Specify task, write and validate the observed-only Map
state before adding any new normative claim.

Do not create a repository inventory, generated index, manifest mapping
frontier, or separate observed-edge registry.
