# Scenario: external code evolution followed by intended/observed drift refresh

## Initial project

The project starts with an already split payment SpecSpine:

- `specspine/payment-settlement.md` canonically owns settlement behavior;
- `specspine/payment-processing.md` is a stable payment overview;
- `specspine/checkout.md` is a related but unaffected responsibility;
- `specspine/reporting.md` is unrelated to the requested refresh.

Settlement contains accepted normative intent: every provider capture uses a
stable idempotency key. Its retry strategy, delay, and attempt limit remain an
explicit open question. The initial implementation captures a payment without
either an idempotency key or retry queue, so the starting Spine does not imply
code/spec conformance.

## Stage 1: downstream external mutation

The harness, not a skill, models downstream implementation work. It replaces
the settlement adapter and adds a retry queue, configuration, and a
representative test.

The evolved implementation:

- passes a stable idempotency key to provider capture;
- preserves that key in retry jobs;
- uses exponential delay with five maximum attempts.

The concrete retry policy is intentionally not accepted architectural intent.
The fixture mutation must not alter any specification.

## Stage 2: targeted Map refresh

Ask `specspine-map` to refresh only settlement architecture from the affected
specification and named payment evidence boundary.

The refresh should:

- preserve the accepted idempotency constraint as normative intent;
- record implemented idempotency-key propagation as `Observed`, with
  representative evidence;
- record the implemented retry queue and its concrete policy as `Observed`,
  not as a `Decision` or `Constraint`;
- retain the retry-policy open question and make the intended/observed drift
  explicit rather than resolving it;
- refresh the evidence baseline only for observations actually rechecked;
- modify only `specspine/payment-settlement.md`;
- leave checkout, reporting, the payment overview, and all repository evidence
  unchanged;
- inspect only the named settlement specification, directly related payment
  overview, and targeted changed source, configuration, and test evidence;
- keep links and semantic identifiers valid.

Map must not claim that the code conforms to the accepted constraint. The
scenario checks classifications and scope without requiring exact explanatory
prose.

## Failure indicators

- repository evidence is rewritten by Map;
- the implemented retry policy becomes accepted normative intent;
- the retry-policy open question disappears or is silently answered;
- the existing idempotency constraint is weakened or replaced;
- checkout, reporting, top-level navigation, or the payment overview changes;
- Map performs a broad repository survey or reads unrelated branches;
- the refresh claims conformance between the Spine and implementation.
