# Acceptance and reconstruction

A specification is structurally valid when `iwe schema validate` succeeds.
It is ready when `blockers` is empty and every applicable facet is `complete`
or `not-applicable`.

Read a reconstruction closure through IWE rather than a generated index:

```bash
iwe retrieve -k <owner> --expand-includes 0 --expand-references 1 --children --backlinks
```

Verification must remain implementation-independent. Passing schema validation
proves format conformance, not implementation conformance.
