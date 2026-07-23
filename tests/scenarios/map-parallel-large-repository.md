# Scenario: parallel mapping of a large brownfield repository

## Existing SpecSpine

The repository already has a breadth-first index and broad runtime, frontend,
and persistence specifications. Several independent product and platform areas
remain only partially mapped.

## User request

```text
Use `$specspine-map-large` to continue mapping this large repository. Use
isolated subagents for independent architectural areas, then publish every
worker-produced specification without re-reading source. After saturation,
normalize the SpecSpine once and run one final Doctor semantic review.
```

## Expected behavior

The orchestrator should:

- plan architectural questions rather than directory assignments;
- perform only a shallow initial topology scan and keep a bounded backlog;
- use the largest safe number of independent workers;
- prevent workers from modifying source or the live SpecSpine;
- accept workers that find no useful new specification;
- require workers to create only publish-ready specifications;
- make each worker responsible for source evidence, ownership, format, and
  final relative links;
- consume and publish every worker result as soon as that worker finishes;
- continuously maintain ready, active, and dependency-blocked questions;
- immediately refill the freed slot from the ready queue;
- add material follow-up questions from completion reports without stopping
  active workers;
- extend the backlog primarily from worker reports without rereading source;
- read each candidate once for bounded acceptance without validating its source;
- publish every acceptable worker file unchanged using a filesystem move tool,
  without reconstructing or rereading it;
- maintain a disposable recovery ledger and retry a failed question once;
- skip source-aware integration and navigation updates during continuous
  mapping;
- after saturation, perform one SpecSpine-only normalization of broad
  directories, relative links, and curated navigation;
- run the deterministic checker after normalization;
- invoke Doctor once after the complete map, then request operator approval
  before applying its proposed semantic repairs.

## Failure indicators

- workers concurrently edit existing specifications;
- workers recursively spawn an uncontrolled agent tree;
- the orchestrator introduces planning waves or waits for all active workers
  while a ready question and a safe slot are available;
- a freed slot remains idle while the orchestrator reviews a completed result;
- a requested document count determines decomposition;
- filename collisions produce arbitrary numbered duplicates;
- the orchestrator deeply explores or rereads source after dispatch begins;
- the orchestrator reconstructs candidate files instead of moving them;
- the orchestrator rereads a candidate after moving it;
- an acceptable worker output is merged, rewritten, or selectively copied;
- the orchestrator reorganizes documents while mapping work remains;
- normalization inspects repository source or changes architectural meaning;
- Doctor runs between worker completions or writes semantic repairs without
  approval.
