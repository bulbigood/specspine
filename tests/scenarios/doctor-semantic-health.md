# Scenario: diagnose semantic architecture problems

## Existing SpecSpine

`billing.md` and `payments.md` both claim canonical ownership of payment state.
An inferred scaling interpretation appears under `Decisions`, and a broad
`application.md` mixes several independently evolving responsibilities. All
Markdown links are mechanically valid.

## User request

```text
Review the semantic health of this SpecSpine.
```

## Expected behavior

The skill should:

- use current bundled semantics and stopping rules;
- distinguish confirmed defects from risks requiring architectural judgment;
- identify competing ownership and the misclassified inference;
- describe the broad specification as a decomposition candidate rather than
  automatically splitting it;
- assign remediation to the user or `specspine-grow`;
- remain read-only.

## Failure indicators

- the skill silently chooses a canonical owner;
- specifications are edited;
- every stylistic preference becomes an error;
- repository conformance is claimed without repository-aware authorization.
