# Scenario: extract a minimal handoff through accelerated retrieval

## Existing specification

The SpecSpine contains several dozen short architectural areas, including
plausible timeout and retry neighbors. Settlement retry intent is owned by a
nested payment specification and depends on a scheduling boundary owned by job
processing. The owner preserves an observation, an inference, and an unresolved
policy question.

## User request

```text
Prepare the smallest architecture context handoff for downstream work that will
add delayed retries after settlement-provider timeouts. Use only the SpecSpine
as architecture authority and do not modify project files.
```

## Expected behavior

The skill should use its retrieval accelerator, read the current canonical
owner and required linked boundary, and return a concise handoff. It should
preserve semantic IDs, evidence provenance, unconfirmed inference, and the open
retry-policy question without importing unrelated architecture or inventing
implementation work.

## Failure indicators

- the retrieval accelerator is not attempted despite being available;
- unrelated catalog or reporting documents are read or included;
- payment settlement is not identified as the primary owner;
- the scheduling boundary, observation, inference, or open question is lost;
- cached routing text is used without reading the current Markdown source;
- project files are modified or an implementation plan is produced.
