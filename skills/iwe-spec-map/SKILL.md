---
name: iwe-spec-map
description: Map boundary-significant repository evidence into Specspine v5 documents managed by IWE. Use for brownfield surveys, focused deepening, refresh, and drift inspection.
---

# IWE Spec Map

Map repository evidence without turning implementation details into accepted
intent.

Before reading IWE references or help, run the bundled
[`iwe-readiness.sh`](scripts/iwe-readiness.sh) beside this skill (add
`--descendants` only for a task spanning packages), then
compare any existing `templates.specification`, `schemas.specification`, and
schema file with the bundled assets or the protocol's allowed scoped binding.
Use the exact absolute asset paths printed by the script; do not rediscover
them with `find`. Complete this comparison before any IWE query or mutation.
Read the
[IWE bootstrap protocol](references/iwe-bootstrap.md) if anything is missing,
different, ambiguous, or conflicts with the requested path. Do not change
documents until that protocol resolves the condition. An existing
`library.path` different from the bundled fallback is authoritative, not a
collision. At the first real mismatch, read the bootstrap protocol immediately;
do not read other IWE references or query the library first.

When the workspace is ready, use the official `iwe-memory-system` skill for
all IWE operations. If it is unavailable, obtain it from the official
`iwe-org/skills` distribution through the environment's supported
skill-installation mechanism. Read only the skill and task-relevant references
before the first IWE operation. Use targeted command help only after syntax is
rejected or remains unknown; do not preload full help screens. The main
`iwe-memory-system` skill is sufficient for routine `find`, `retrieve`, and
`update` operations whose syntax is already established.

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
