# Scenario: accepted payment change splits mapped responsibilities

## Lifecycle position

The workspace already contains a repository-mapped payment specification. It
records payment authorization, settlement, and webhook observations, plus an
unresolved settlement retry policy. Project code and repository documentation
outside `specspine/` deliberately contain conflicting and distracting details.

This scenario exercises one intentional lifecycle transition:

```text
existing mapped spine -> accepted architectural change -> responsibility split
```

## User decisions

The user explicitly accepts that:

- payment authorization and payment settlement evolve independently;
- `payment-processing.md` remains their concise overview;
- webhook handling remains a boundary described by that overview;
- settlement processing is idempotent;
- settlement retry policy is still unspecified and remains an open question.

## Expected behavior

`specspine-grow` should create `payment-authorization.md` and
`payment-settlement.md`. It should retain `payment-processing.md` as a concise,
reachable overview linking both canonical responsibility specifications.

The accepted decisions should be addressable in their canonical owners. The
existing addressable retry question should move with settlement without being
answered. Existing mapped observations should keep their statement kind and
meaning. Links and semantic-ID references should remain mechanically valid.

Grow should read only the existing SpecSpine as project evidence. It must not
inspect or modify the bait README, source, tests, or configuration, and it must
not create an implementation plan, feature specification, handoff, acceptance
criteria, tasks, or implementation-status artifact.

## Failure indicators

- authorization or settlement remains canonically defined in the overview;
- one of the independently evolving responsibilities has no specification;
- the overview is removed or no longer links the extracted responsibilities;
- webhook handling is extracted into an unrequested independent concept;
- settlement idempotency is left unapplied;
- Grow chooses a retry policy or drops the existing open question;
- observations are promoted to accepted intent;
- semantic IDs or relative Markdown links become invalid;
- repository material outside `specspine/` is read or changed;
- downstream implementation or feature-work artifacts are created.
