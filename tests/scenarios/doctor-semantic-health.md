# Scenario: advisory review of semantic architecture risks

## Existing SpecSpine

`billing.md` and `payments.md` both claim canonical ownership of payment state.
An inferred scaling interpretation appears under `Decisions`, and a broad
`application.md` mixes several independently evolving responsibilities. All
Markdown links are mechanically valid.

## User request

```text
Check mechanical integrity and perform an advisory semantic review of this SpecSpine.
```

## Expected behavior

The skill should:

- use current bundled semantics and stopping rules;
- distinguish reproducible mechanical findings from advisory risks requiring
  architectural judgment;
- identify competing ownership and the misclassified inference;
- describe the broad specification as a decomposition candidate rather than
  automatically splitting it;
- distinguish repairs Doctor can apply from choices requiring the user;
- report mechanical PASS/FAIL independently from advisory findings;
- avoid claiming semantic validity or completeness;
- remain read-only.

## Failure indicators

- the skill silently chooses a canonical owner;
- specifications are edited;
- every stylistic preference becomes an error;
- repository conformance is claimed even though Doctor does not inspect the repository.
- advisory findings change the mechanical PASS/FAIL result.
