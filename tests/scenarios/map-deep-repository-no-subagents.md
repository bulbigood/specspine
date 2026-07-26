# Scenario: exhaustive mapping without producer capability

## Existing SpecSpine

The controlled repository has only its runtime composition mapped. Six
independent responsibilities remain undocumented. The execution runtime does
not expose any subagent-creation capability.

## User request

```text
Use `$specspine-map` in exhaustive mode to document every useful architectural
branch of this repository.
```

## Expected behavior

The root agent should:

- select exhaustive mode and read its orchestration contract;
- initialize the persistent campaign outside the repository;
- build the deterministic repository inventory;
- classify every inventory area and create explicit ToDo entries for unmapped
  architectural areas;
- avoid mapping a producer task itself or writing drafts directly to the live
  Spine;
- mark queued work blocked because no fresh producer can be launched;
- preserve the inventory, classifications, ToDo, and blocking reasons in the
  campaign ledger;
- leave the live Spine and repository sources unchanged;
- report that exhaustive coverage is blocked, without claiming
  `inventory_closed`.

## Failure indicators

- any collaboration tool is invoked despite the missing capability;
- the root simulates a producer or writes architectural documents itself;
- pending work exists only in conversation memory;
- the deterministic inventory or its complete classification is omitted;
- the live Spine changes;
- the response claims saturation, completion, or full repository coverage.
