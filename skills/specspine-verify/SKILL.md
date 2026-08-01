---
name: specspine-verify
description: Verify implementation conformance against Specspine v5 contracts retrieved through IWE. Use for implementation-independent checks and code/spec comparison.
---

# Specspine Verify

1. Run `iwe schema validate`; stop on schema errors.
2. Retrieve the owner and relevant IWE graph closure with `iwe retrieve`.
3. Treat `REQ`, `GUA`, `INV`, `QLT`, `DEC`, `CON`, and `VER` as normative.
4. Treat `OBS` and `INF` as evidence, never authority.
5. Evaluate implementation-independent verification criteria and registered
   assets listed in document frontmatter.
6. Report conforming, diverging, and unverified claims separately.

Schema validity does not prove implementation conformance.
