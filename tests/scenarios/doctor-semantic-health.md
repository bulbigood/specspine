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
- identify the competing ownership claims and the misclassified inference;
- explain that the broad specification may need decomposition without
  automatically splitting it;
- distinguish clear repairs from architectural choices that need user input;
- report mechanical results independently from advisory findings;
- avoid claiming semantic validity or completeness;
- remain read-only.

## Failure indicators

- the skill silently chooses a canonical owner;
- specifications are edited;
- every stylistic preference becomes an error;
- repository conformance is claimed even though Doctor does not inspect the repository.
- advisory findings change the mechanical PASS/FAIL result.
