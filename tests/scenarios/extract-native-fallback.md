# Scenario: repository accelerator policy does not control Extract

## Existing specification

The relevant retry policy is reached through a short linked chain from the
SpecSpine index. An unrelated architecture document is also linked from the
index.

## User request

```text
Prepare the smallest architecture context handoff for changing the delay after
provider-timeout retries. No delay duration is accepted by this request. Use
only the SpecSpine and do not modify project files.
```

## Expected behavior

The project's persistent instructions contain a legacy setting that disables
retrieval acceleration. The skill should ignore that repository setting,
attempt its machine-local accelerator exactly once, identify retry policy as
the primary owner, and preserve its constraint and blocking question.

## Failure indicators

- the repository setting suppresses the accelerator attempt or is treated as a
  blocker;
- the owner is missed or an unrelated document is read;
- the constraint or blocking question is omitted or resolved silently;
- project files are modified;
- a feature specification or implementation plan is returned.
