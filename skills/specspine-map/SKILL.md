---
name: specspine-map
description: Map boundary-significant repository evidence into Specspine v5 documents managed by IWE. Use for brownfield surveys, focused deepening, refresh, and drift inspection.
---

# Specspine Map

Map repository evidence without turning implementation details into accepted
intent.

1. Discover existing owners with `iwe find` and `iwe tree`.
2. Retrieve the bounded neighborhood with `iwe retrieve`.
3. Record confirmed boundary evidence as owner-local `OBS-*` statements and
   interpretations as `INF-*`.
4. Store inspection metadata in that owner's frontmatter.
5. Create a document through the IWE `specification` template only for an
   independently useful owner.
6. Express structural decomposition with standalone inclusion links and other
   connections with inline references.
7. Run `iwe schema validate`.

Do not create a repository inventory, generated index, manifest mapping
frontier, or separate observed-edge registry.
