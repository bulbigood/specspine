# Scenario: temporary handoff followed by an external implementation change

## Initial project

The project starts with an already split payment SpecSpine:

- `specspine/payment-settlement.md` canonically owns settlement idempotency;
- `specspine/payment-processing.md` is the payment overview;
- `specspine/payment-webhooks.md` owns provider-result delivery;
- `specspine/checkout.md` is related context, but is not expected to change;
- authorization is a separate, unrelated responsibility.

Settlement records an accepted requirement to use an idempotency key. Its retry
policy remains an explicit open question. Source, configuration, tests, and root
documentation exist outside the spine but are not authorized evidence for Grow.

## Stage 1: temporary Grow handoff

Ask `specspine-grow` for the smallest architecture context handoff needed by a
downstream workflow implementing settlement idempotency.

The handoff should:

- identify `specspine/payment-settlement.md` as primary and required context;
- classify `specspine/payment-processing.md` and
  `specspine/payment-webhooks.md` as potentially affected;
- classify `specspine/checkout.md` as merely related, not potentially affected;
- preserve the accepted idempotency-key constraint and the unresolved retry
  policy;
- use repository-root-relative specification paths;
- remain only in the response, without modifying the spine or another project
  file;
- omit acceptance criteria, tasks, task order, test scenarios, and proposed
  implementation filenames.

Grow may read only the minimal relevant branch of `specspine/`. It must not
inspect source code, tests, configuration, or root documentation.

## Stage 2: downstream external mutation

The harness, not a skill, then models downstream implementation work. It adds
idempotency-key handling and a retry queue. The implementation also chooses an
exponential retry policy and attempt limit even though that policy is not
accepted in the SpecSpine.

The fixture mutation is intentionally limited to the expected payment source,
configuration, and test paths. It must not mutate architectural specifications.

## Expected lifecycle invariants

- the handoff is temporary and minimal;
- Grow stays within its project-evidence and write boundaries;
- downstream code can diverge from unresolved intent without silently changing
  the long-lived SpecSpine;
- only the explicitly modeled source, configuration, and test files change.
