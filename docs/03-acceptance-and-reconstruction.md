# Acceptance and reconstruction

`iwe schema validate` proves format conformance. Semantic readiness additionally
requires:

- an empty `blockers` list;
- every applicable facet to be `complete` or `not-applicable`;
- every blocker ID to name an `OQ-*` statement in the same owner;
- every semantic ID to be unique within its owner;
- completeness claims to agree with the document's actual accepted content.

These semantic conditions remain workflow checks when the IWE document schema
cannot express them directly. Do not add a second Markdown parser or lifecycle
engine to enforce them.

Retrieve the graph neighborhood needed to reconstruct a boundary through IWE:

```bash
iwe retrieve -k <owner> --expand-includes 0 --expand-references 1 --children
```

Verification criteria describe observable outcomes without prescribing private
implementation details. Verifying conformance still requires comparing those
criteria and other normative claims with implementation evidence. Schema
validity alone does not prove implementation conformance.
