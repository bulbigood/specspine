# Scenario: branch-affine exhaustive Map with three worker slots

## Existing SpecSpine

The live Spine contains only its runtime composition. Six small, independent
runtime-adjacent responsibilities remain unmapped.

## User request

```text
Use `$specspine-map` in exhaustive mode to document every useful architectural
branch of this repository until saturation.
```

## Expected behavior

The orchestrator should start three producers, then refill every freed slot from
undispatched work without a batch barrier.
It may inspect the repository and existing Spine as needed to understand the
requested scope, while producers own deep evidence investigation. Each producer
performs one Map step per checkpoint; the consumer validates and publishes it
before any same-domain continuation without resending the Map bundle. A
candidate that already passes the local quality gate may publish and locally
saturate atomically. Producers
report every directly observed independent boundary in their coverage frontier,
and the orchestrator atomically records those boundaries in its temporary JSON
ledger before accepting saturation. A final ledger audit must reject queued,
active, blocked, or merely locally saturated branches.
Because the fixture contains no material deeper nodes, useful starting branches
should reach terminal `no useful node` in the publish checkpoint or one
same-session continuation. The orchestrator normalizes once
and removes the successful disposable run root, then recommends an independent
`$specspine-doctor` review in a new session without invoking it.

## Failure indicators

- the available slots are not refilled while ready work remains;
- useful branches lack either atomic terminal publication or a same-session
  terminal continuation;
- more than three producers are active;
- a producer session is reused for a different architectural area;
- a refusal for one sub-boundary closes its parent survey or siblings;
- a broad survey reaches saturation while directly observed independent
  boundaries are absent from its coverage frontier or ledger;
- final normalization starts before the ledger's final audit returns no
  findings;
- an interrupted run deletes its ledger instead of reporting the recovery path;
- a terminal continuation repeats the Map bundle or immutable shared context;
- producer prompts omit the inline mapping contract or tell workers to load it;
- any checker finding is bypassed or a candidate is moved after nonzero preflight;
- the final report omits the literal terminal phrase `no useful node`;
- Doctor is invoked in the current session or its new-session recommendation is
  omitted;
- source or tests change;
- the disposable run root remains after success.
