# Scenario: branch-affine deep-Map orchestration with three worker slots

## Existing SpecSpine

The live Spine contains only its runtime composition. Six small, independent
runtime-adjacent responsibilities remain unmapped.

## User request

```text
Use `$specspine-map-deep` to document the architecture of this repository.
```

## Expected behavior

The orchestrator should start three producers, then refill every freed slot from
undispatched work without a batch barrier.
It may inspect the repository and existing Spine as needed to understand the
requested scope, while producers own deep evidence investigation. Each producer
performs one Map step per checkpoint; the consumer validates and publishes it
before resuming the same session without resending the Map bundle. Because the
fixture contains no material deeper nodes, useful starting branches should then
reach terminal `no useful node`. The orchestrator normalizes once and removes
the successful disposable run root, then recommends an independent
`$specspine-doctor` review in a new session without invoking it.

## Failure indicators

- the available slots are not refilled while ready work remains;
- useful branches lack a same-session terminal continuation;
- more than three producers are active;
- a producer session is reused for a different architectural area;
- a terminal continuation repeats the Map bundle or immutable shared context;
- producer prompts omit the inline mapping contract or tell workers to load it;
- any checker finding is bypassed or a candidate is moved after nonzero preflight;
- the final report omits the literal terminal phrase `no useful node`;
- Doctor is invoked in the current session or its new-session recommendation is
  omitted;
- source or tests change;
- the disposable run root remains after success.
