---
name: iwe-spec-verify
description: Verify implementation conformance against Specspine v5 contracts retrieved through IWE. Use for implementation-independent checks and code/spec comparison.
---

# IWE Spec Verify

1. Run `iwe schema validate`; stop on schema errors.
2. Retrieve the owner and relevant IWE graph closure with `iwe retrieve`.
3. Treat `REQ`, `GUA`, `INV`, `QLT`, `DEC`, `CON`, and `VER` as normative.
4. Treat `OBS` and `INF` as evidence, never authority.
5. Evaluate implementation-independent verification criteria and registered
   assets listed in document frontmatter.
6. Emit findings as `missing`, `conflicting`, `uncovered-boundary`, or
   `unverified`. Include owner key, claim ID when applicable, expected behavior,
   implementation evidence, and confidence for every finding.
7. Classify an external interaction not governed by the retrieved specification
   closure as `uncovered-boundary`. Its absence from a specification is not a
   conflict. Record whether every governing owner declares
   `coverage.external-boundary: exhaustive`.
8. Do not modify or delete anything.

Schema validity does not prove implementation conformance.
