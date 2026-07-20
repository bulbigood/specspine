# Architecture context handoff

A context handoff is a temporary, task-oriented projection of the long-lived
SpecSpine. It transfers the smallest useful architectural context to OpenSpec,
spec-kit, another feature workflow, or a coding agent. It is not a feature
specification, implementation plan, or claim of code conformance.

Use this format:

```markdown
# Architecture context handoff

## Change intent

What the downstream workflow is expected to accomplish.

## Primary specification

The canonical owner of the changed responsibility.

## Required specifications

Specifications that must be read to understand the change safely.

## Potentially affected specifications

Specifications that may require architectural updates but are not known to
change yet.

## Architectural decisions and constraints

Accepted architectural intent that downstream work must preserve.

## Relevant observations

Current repository facts that affect downstream execution.

## Unconfirmed inferences

Interpretations that downstream tools must not treat as accepted decisions.

## Blocking questions

Questions that the downstream workflow must not answer silently.

## Expected architectural outcome

The architectural state expected after the downstream change.
```

Include only sections containing useful information. Preserve the distinction
between required and potentially affected specifications. Do not mark every
related specification as potentially affected.

Do not include:

- acceptance criteria;
- implementation tasks or task order;
- proposed implementation filenames;
- test scenarios;
- implementation or release status;
- effort estimates;
- release scope.

Readiness for context handoff does not imply readiness for implementation.
