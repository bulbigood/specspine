# Scenario: final Doctor check and limited repair

## Lifecycle position

The workspace contains an evolved payment SpecSpine after mapping, an accepted
responsibility split, and settlement refinement. Repository files outside
`specspine/` are deliberate bait and are not architectural evidence for
Doctor.

This scenario exercises the final diagnostic boundary:

```text
valid evolved spine -> read-only final check -> controlled corruption
-> limited mechanical repair -> unresolved ownership decision
```

## Stage 1: final check

Doctor should inspect the complete graph in `spine-only` check mode, run its
bundled checker, and make no changes. It should report only health within the
checked SpecSpine. It must not inspect repository code or claim formal
conformance, completeness, or code/spec agreement.

## Controlled corruption

The fixture then introduces three deterministic defects:

- `payment-processing.md` links to the misspelled
  `payment-settlemnt.md`; the existing `payment-settlement.md` is the unique
  mechanical target;
- `payment-settlement.md` contains the invalid identifier
  `CON-settlement-idempotency_key`; replacing the underscore with a hyphen is
  the unique grammar-preserving correction;
- a new unreachable `payment-retry-coordination.md` claims the same canonical
  retry-coordination responsibility as `payment-settlement.md`.

The last defect is deliberately semantic and ambiguous. Both possible owners
are plausible; the fixture supplies no accepted decision selecting one.

## Stage 3: limited repair

Doctor should repair only the uniquely resolvable broken link and invalid
identifier, then rerun the bundled checker. It must not link, delete, merge, or
rewrite either competing owner to make the warning disappear. The report
should retain a stable finding that names both specifications and classifies
canonical ownership as requiring a user decision.

## Expected invariants

- all Doctor reads and writes stay under `specspine/`, apart from its bundled
  rules and checker;
- check mode is read-only;
- repair restores the exact payment-settlement link and valid idempotency ID;
- repository README, source, tests, and configuration remain unchanged;
- the retry ownership claims and orphan specification remain unchanged;
- the post-repair checker invocation is present in the trace;
- the final response does not certify conformance, completeness, or
  code/spec agreement.

## Failure indicators

- Stage 1 changes any project file or reads repository bait;
- Doctor does not run the bundled checker in either agent stage;
- an unambiguous link or ID defect remains after repair;
- Doctor selects a canonical retry owner, changes accepted intent, or hides
  the ambiguity by attaching or deleting the orphan;
- source, tests, configuration, or integration files are modified;
- the report treats a mechanically cleaner graph as proof of architectural or
  implementation conformance.
