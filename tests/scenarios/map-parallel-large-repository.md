# Scenario: parallel mapping of a large brownfield repository

## Existing SpecSpine

The repository already has a breadth-first index and broad runtime, frontend,
and persistence specifications. Several independent product and platform areas
remain only partially mapped.

## User request

```text
Continue mapping this large repository in parallel. Use isolated subagents for
independent architectural areas, then integrate their findings into one
coherent SpecSpine and run Doctor.
```

## Expected behavior

The orchestrator should:

- plan architectural questions rather than directory assignments;
- use the largest safe number of independent workers;
- prevent workers from modifying source or the live SpecSpine;
- accept workers that find no useful new specification;
- integrate candidate documents itself using repository evidence;
- reject duplicate or implementation-level candidates;
- preserve one canonical owner per durable concept;
- update useful links and curated overview navigation;
- avoid deep directory mirroring;
- run mechanical and semantic Doctor review after integration.

## Failure indicators

- workers concurrently edit existing specifications;
- workers recursively spawn an uncontrolled agent tree;
- a requested document count determines decomposition;
- filename collisions produce arbitrary numbered duplicates;
- all worker outputs are imported without source-aware review;
- Doctor is treated as a substitute for repository-backed integration;
- the result is unreachable, mechanically invalid, or organized like source
  directories.
