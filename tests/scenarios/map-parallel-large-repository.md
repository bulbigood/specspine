# Scenario: parallel mapping of a large brownfield repository

## Existing SpecSpine

The repository already has a breadth-first index and broad runtime, frontend,
and persistence specifications. Several independent product and platform areas
remain only partially mapped.

## User request

```text
Continue mapping this large repository in parallel. Use isolated subagents for
independent architectural areas, then publish every worker-produced
specification without re-reading source. After saturation, normalize the
SpecSpine once and run one final Doctor semantic review.
```

## Expected behavior

The orchestrator should:

- plan architectural questions rather than directory assignments;
- use the largest safe number of independent workers;
- prevent workers from modifying source or the live SpecSpine;
- accept workers that find no useful new specification;
- require workers to create only publish-ready specifications;
- make each worker responsible for source evidence, ownership, format, and
  final relative links;
- consume and publish every worker result as soon as that worker finishes;
- immediately refill the freed slot from the bounded independent-question
  queue instead of waiting for the active batch;
- check destination path collisions without reading document contents;
- mechanically move every worker file into the live SpecSpine unchanged;
- skip source-aware integration and per-wave index updates;
- after saturation, perform one SpecSpine-only normalization of broad
  directories, relative links, and curated navigation;
- run the deterministic checker after normalization;
- invoke Doctor once after the complete map, then request operator approval
  before applying its proposed semantic repairs.

## Failure indicators

- workers concurrently edit existing specifications;
- workers recursively spawn an uncontrolled agent tree;
- the orchestrator waits for all active workers while an independent question
  remains queued and a safe slot is free;
- a freed slot remains idle while the orchestrator reviews a completed result;
- a requested document count determines decomposition;
- filename collisions produce arbitrary numbered duplicates;
- the orchestrator reads source or candidate contents after workers finish;
- worker outputs are rejected, merged, rewritten, or selectively imported;
- the orchestrator reorganizes documents after every wave;
- normalization inspects repository source or changes architectural meaning;
- Doctor runs between waves or writes semantic repairs without approval.
