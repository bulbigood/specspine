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

- create a reachable `specspine/README.md` and a small, flat set of
  responsibility-oriented specifications;
- include checkout and payment processing without creating one document per
  source directory, file, handler, table, or runtime process;
- distinguish repository-backed observations from unconfirmed interpretation;
- attach an evidence baseline to repository-backed observations;
- leave mapping coverage qualitative and explicitly incomplete;
- modify only files under `specspine/`.

## Stage 2: selected payment deepen

The user asks Map to deepen only `specspine/payment-processing.md`. The known
evidence boundary consists of the payment adapter, the checkout-to-payment
port, the webhook consumer, payment configuration and schema, and one
representative payment integration test.

Expected behavior:

- begin from the selected specification and inspect representative files only
  inside the stated boundary;
- describe payment authorization, webhook ingestion, persistence ownership,
  and the checkout boundary at architectural rather than function-by-function
  depth;
- preserve `Observed` versus `Inferred` classification and refresh the
  evidence baseline for observations actually checked;
- update the smallest useful SpecSpine document set;
- avoid reopening the unrelated reporting branch or repeating a repository-wide
  survey;
- leave source, tests, configuration, schema, and root documentation unchanged.

## Failure indicators

- source-tree folders or individual handlers are mirrored as specifications;
- repository evidence is recorded as a decision or constraint;
- the deepen stage reads reporting internals or unrelated checkout internals;
- the initial survey is repeated during deepening;
- source, tests, configuration, schema, or root documentation changes;
- the result claims complete mapping or code/spec conformance.
