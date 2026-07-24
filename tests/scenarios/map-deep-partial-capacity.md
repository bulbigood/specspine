# Scenario: Map Deep with unknown partial producer capacity

## Existing SpecSpine

The repository has several independent unmapped architectural branches. The
environment supports subagents but does not expose producer capacity in
advance. It accepts one producer start and rejects additional starts while that
producer remains active.

## User request

```text
Use `$specspine-map-deep` to map the whole repository as deeply as useful
architectural evidence supports.
```

## Expected behavior

The orchestrator should count only a confirmed addressable producer as active.
Branches whose starts fail should remain queued and unowned. It should continue
with the confirmed producer, retry queued work after capacity is released, and
eventually cover every useful branch without treating failed starts as
completed work. If no producer can be started later, it should preserve the
same protocol locally.

## Failure indicators

- a branch becomes active before a producer handle is confirmed;
- an attempted or failed start consumes a logical slot;
- a rejected branch disappears from the ToDo;
- partial capacity is mistaken for complete lack of subagent support;
- the orchestrator waits for producers that were never created;
- mapping stops while a failed-start branch remains queued and actionable.
