---
name: iwe-spec-specify
description: Create or refine accepted durable software specifications in a Specspine v5 IWE library. Use for greenfield intent, requirements and architecture changes, impact analysis, and restructuring accepted specifications.
---

# IWE Spec Specify

Work only with accepted intent. Use IWE for all document operations.

1. Locate candidates with `iwe find` and read the relevant closure with
   `iwe retrieve`.
2. Update the canonical owner. Do not copy claims between owners.
3. Create a new owner with `iwe create --template specification` only when it
   has an independent durable boundary.
4. Put a target link on its own line only to make it a structural child.
   Keep dependencies and conceptual connections inline.
5. Use `iwe rename`, `iwe delete`, `iwe extract`, and `iwe inline` instead of
   manually maintaining links.
6. Run `iwe schema validate` after every write batch.

Use owner-local statement IDs and the section-specific prefixes enforced by
the IWE schema. Keep facets honest. List a blocking `OQ-*` in the same
document's frontmatter.
