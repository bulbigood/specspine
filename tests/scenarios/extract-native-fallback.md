# Scenario: extract through the native Markdown graph

## Existing specification

The relevant retry policy is reached through a short linked chain from the
SpecSpine index. An unrelated architecture document is also linked from the
index.

## User request

```text
Prepare the smallest architecture context handoff for changing the delay after
provider-timeout retries. The bundled retrieval accelerator cannot be executed
in this environment; do not invoke it. Navigate the existing Markdown links
instead. No delay duration is accepted by this request. Use only the SpecSpine
and do not modify project files.
```

## Expected behavior

The skill should follow the Markdown chain, identify retry policy as the
primary owner, preserve its constraint and blocking question, and return the
same kind of concise handoff it would produce with acceleration.

## Failure indicators

- the unavailable accelerator is invoked or treated as a blocker;
- the linked owner is missed or an unrelated document is read;
- the constraint or blocking question is omitted or resolved silently;
- project files are modified;
- a feature specification or implementation plan is returned.
