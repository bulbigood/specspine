---
name: iwe-spec-specify
description: Create or refine accepted durable software specifications in a Specspine v5 IWE library. Use for greenfield intent, requirements and architecture changes, impact analysis, and restructuring accepted specifications.
---

# IWE Spec Specify

Work only with accepted intent. Use IWE for all document operations.

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

1. Locate candidates with `iwe find` and read the relevant closure with
   `iwe retrieve`. Once one owner is unambiguous, do not retrieve neighboring
   owners merely because they are linked.
2. Update the canonical owner. Do not copy claims between owners.
3. Create a new owner with `iwe create --template specification --var
   title=<title> --var body=<body> --strict` only when it has an independent
   durable boundary. Do not pass a positional key or unsupported `--set`
   options to `create`; refine generated frontmatter afterward with `iwe
   update` when necessary.

A new topic is not automatically a new durable owner. Create one only when
repository or accepted-intent evidence gives it an independent responsibility,
lifecycle, or external boundary. Otherwise place the claim in the existing
owner whose responsibility already governs it; absence of a matching phrase in
that owner does not justify a parallel specification.
4. Put a target link on its own line only to make it a structural child.
   Keep dependencies and conceptual connections inline.
5. Use `iwe rename`, `iwe delete`, `iwe extract`, and `iwe inline` instead of
   manually maintaining links.
6. Run `iwe schema validate` after every write batch.

Statement IDs are owner-local, not globally unique. First look for a matching
claim in the chosen canonical owner and refine it instead of creating a near
duplicate. The same ID may validly mean a different owner-local statement in
another document; do not rename either claim merely to obtain global
uniqueness. Use section-specific prefixes enforced by the IWE schema. Keep
facets honest. List a blocking `OQ-*` in the same document's frontmatter.
