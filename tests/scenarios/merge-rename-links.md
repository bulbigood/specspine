# Scenario: merge and rename specifications

## Initial state

`billing.md` and `payment-processing.md` duplicate one responsibility. The user
account specification is named `users.md`; the index and authentication link to
it.

## User request

```text
Merge payment processing into billing and rename users.md to user-accounts.md.
Update every incoming link. Apply this restructuring now.
```

## Expected behavior

- keep `billing.md` as the canonical payment owner;
- remove `payment-processing.md` after preserving unique content;
- rename `users.md` to `user-accounts.md`;
- update all incoming links;
- preserve unrelated specifications;
- avoid redundant approval.

## Failure indicators

- an old path remains linked;
- unique payment behavior is lost;
- duplicate canonical ownership remains;
- the agent asks for confirmation already supplied by the request.
