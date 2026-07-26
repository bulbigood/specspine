# Scenario: exhaustive Map with three one-shot producer slots

## Repository

The repository exposes six independent production responsibilities plus their
shared configuration work unit. Existing specifications cover runtime
composition but leave those seven units unverified.
Only three producers may be active simultaneously.

## User request

```text
Use `$specspine-map` to cover the whole repository.
```

## Expected behavior

The orchestrator should:

- mechanically generate the deterministic source frontier;
- create verification ToDo for every production work unit;
- start at most three fresh producers at a time;
- give each producer exactly one task packet and private staging root;
- accept one checkpoint from each producer and never continue or reuse it;
- refill a free slot with a new producer while ready ToDo remains;
- publish accepted drafts transactionally;
- integrate settled publications centrally;
- disposition every producer suggestion;
- append accepted and newly observed refinements to persistent ToDo;
- dispatch every new ToDo to another fresh producer;
- stop only at `inventory_verified` or an evidence-backed `blocked`.

## Failure indicators

- one producer handles two tasks;
- a producer receives a follow-up after its checkpoint;
- a producer edits the live Spine or shared navigation;
- producer self-reported quality or saturation closes the campaign;
- an empty ready list hides unintegrated publications;
- producer suggestions disappear without an integration disposition;
- a production work unit lacks an integrated producer checkpoint;
- more than three producers are active;
- the root claims exhaustive coverage without fresh producer support.
