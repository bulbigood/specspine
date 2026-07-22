# Scenario: repeated Grow deepening remains lightweight

## Lifecycle position

The workspace starts with a small, reviewed commerce SpecSpine. Checkout,
payment processing, and inventory reservations already have separate canonical
owners. Source and configuration outside `specspine/` contain verbose
implementation details and are not authorized architecture evidence.

This scenario applies three accepted changes to the same Spine:

```text
payment safety -> inventory compensation -> provider-event safety
```

Each change adds important architectural meaning, but none introduces a new
independently evolving responsibility. The existing overview and canonical
owners should remain easy to scan after every step.

## Expected behavior

`specspine-grow` should preserve a compact four-document graph while adding the
addressable decisions, constraints, and open questions requested at each
stage. It should consolidate related statements instead of appending a fresh
explanation of the complete workflow on every run.

The architecture index should remain a short navigation document. Each domain
specification should state responsibilities, boundaries, and the important
behavioral rules without becoming a function-by-function walkthrough,
pseudocode listing, feature plan, or copy of runtime configuration.

The evaluation combines semantic-preservation assertions with per-document and
whole-Spine word budgets. The budgets are regression limits for this frozen
fixture, not universal limits for all SpecSpine documents.

## Failure indicators

- an accepted decision, constraint, or unresolved question disappears;
- the same responsibility is restated canonically in multiple documents;
- a new specification is created for a local algorithm or event-handling detail;
- repeated growth duplicates the full checkout or payment workflow;
- the index or a domain specification grows beyond the fixture's word budget;
- implementation identifiers, pseudocode, acceptance criteria, or tasks dominate;
- project files outside `specspine/` are read or changed;
- links or semantic IDs become invalid.
