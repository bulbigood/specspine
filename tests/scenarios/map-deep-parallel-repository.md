# Scenario: parallel exhaustive mapping of a large repository

## Existing SpecSpine

The repository already has broad runtime, frontend, and persistence owners.
Several product and platform areas remain partial.

## User request

```text
Use `$specspine-map` to cover every production area in this repository. After
mapping, recommend a separate SpecSpine Doctor review.
```

## Expected behavior

The orchestrator should:

- read the complete existing Spine and seed anchored documentation ToDo;
- build a deterministic source inventory and classify every area;
- plan architectural questions rather than directory-shaped specifications;
- dispatch each task to one fresh producer;
- keep producers read-only outside private staging;
- accept exactly one checkpoint from each producer;
- let producers suggest, but never directly enqueue, narrower directions;
- integrate every publication centrally;
- append integration-derived directions to persistent ToDo;
- repeat with fresh producers until ToDo is empty, all publications are
  integrated, and the source inventory is current;
- report `inventory_closed`, not generic model-asserted saturation;
- recommend Doctor in a new session.

## Failure indicators

- a producer is reused or continued;
- a producer maps a discovered child in the same task;
- a producer edits existing live specifications or `README.md`;
- source discovery is only a prose assertion rather than a classified inventory;
- producer quality self-assessment controls completion;
- accepted suggestions are not represented in ToDo;
- root integration skips candidate prose or graph neighbors;
- an empty queue alone becomes a coverage claim;
- Doctor runs during Map.
