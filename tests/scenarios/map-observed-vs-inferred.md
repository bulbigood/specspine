# Scenario: separate observation from inference

## Repository evidence

- API and worker have separate entry points.
- Deployment configuration runs them as separate processes.
- They share a database package.
- No ADR explains the intended scaling model.

## User request

```text
Document the runtime architecture.
```

## Expected behavior

The skill should record as observed:

- separate entry points;
- separate deployment processes;
- shared persistence dependency.

It may record as inferred:

- the components appear intended to scale independently.

It must not record independent scaling as an accepted architectural decision.

## Failure indicators

- inference is placed under `Decisions`;
- repository paths are omitted when they would support a non-obvious claim;
- the specification becomes a raw file list;
- uncertainty is hidden.
