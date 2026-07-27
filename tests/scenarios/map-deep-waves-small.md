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
- precompute prompts and emit each wave's fresh producer spawns back-to-back;
- give each producer exactly one task packet and private staging root;
- accept one checkpoint from each producer and never continue or reuse it;
- read-only harvest completed handoffs while the rest of the wave runs;
- use wave-level harvest and acceptance commands without shell-delimited records;
- stop only at a predeclared timeout or an explicitly reported stall;
- wait for every producer in the wave and never refill an early finish;
- accept the settled wave and integrate it once before the next wave;
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
- a three-producer launch burst takes more than 30 seconds;
- a replacement producer starts before the whole prior wave is terminal;
- early harvest mutates the ledger or live Spine;
- a producer is stopped merely because root woke or elapsed time increased;
- the root claims exhaustive coverage without fresh producer support.
