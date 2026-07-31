# Scenario: brownfield survey followed by selected payment deepening

## Initial repository

The fixture is a small storefront with two runtime processes:

- an HTTP API accepts checkout requests and delegates payment authorization;
- a worker consumes payment-provider webhooks;
- checkout owns order creation while payment processing owns provider calls and
  provider-event handling;
- a shared SQL schema persists orders, payment attempts, and provider-event
  deduplication records.

There is no `specspine/` directory. Reporting code is present as an unrelated
branch that should not be inspected while deepening payment processing.

## Stage 1: initial survey

The user asks Map to create the smallest useful initial SpecSpine. The survey
should capture the broad runtime and responsibility shape without deeply
documenting payment internals. `payment-processing.md` is the stable selected
node for the next stage.

Expected behavior:

- create a reachable `specspine/_INDEX.md` and one bounded
  `payment-processing.md` observation owner;
- persist provider-webhook ingestion as the first mapping frontier lead and
  checkout as a later candidate instead of creating sibling documents;
- distinguish repository-backed observations from unconfirmed interpretation;
- attach an evidence baseline to repository-backed observations;
- leave mapping coverage qualitative and explicitly incomplete;
- modify only files under `specspine/`.

## Stage 2: expand the persisted frontier

The user generically asks Map to continue deepening payment documentation. The
known evidence boundary consists of the webhook handler and consumer, payment
configuration and schema, and one representative payment integration test.

Expected behavior:

- select the first persisted frontier lead instead of refining
  `payment-processing.md` again;
- create exactly one `payment-webhook-ingestion.md` observation owner;
- preserve `payment-processing.md` unchanged;
- connect the owners through an OBS-backed manifest observed edge;
- consume the selected frontier lead and retain any newly exposed candidates;
- avoid reopening the unrelated reporting branch or repeating a repository-wide
  survey;
- leave source, tests, configuration, schema, and root documentation unchanged.

## Failure indicators

- source-tree folders or individual handlers are mirrored as specifications;
- repository evidence is recorded as a decision or constraint;
- the expansion stage reads reporting internals or unrelated checkout internals;
- the second stage merely adds another OBS to `payment-processing.md`;
- the initial survey is repeated during deepening;
- source, tests, configuration, schema, or root documentation changes;
- the result claims complete mapping or code/spec conformance.
