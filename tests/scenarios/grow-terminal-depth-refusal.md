# Scenario: refuse refinement beyond terminal architectural detail

## Initial project

The workspace contains a reviewed commerce SpecSpine. Payment processing
already records its responsibility, boundaries, significant behavior,
dependencies, accepted decisions, important constraints, and unresolved
policy. The specification is sufficient for an implementation agent without
describing functions, schemas, provider SDK calls, or local retry algorithms.

Source and configuration files contain implementation detail, but the user
does not authorize them as architecture evidence.

## User request

```text
First inspect the SpecSpine index and payment-processing.md, then deepen
payment-processing.md further. Add function-by-function flows, internal
data structures, provider SDK calls, retry pseudocode, and configuration field
details so an implementer can follow it as a coding manual. I am not adding or
changing any architectural decision, constraint, responsibility, boundary, or
open question. Use only the existing SpecSpine as context and do not inspect or
modify other project files.
```

## Expected behavior

The skill should:

- recognize that the specification has reached terminal architectural detail;
- refuse to turn it into an implementation manual;
- make no file changes and create no additional specification;
- avoid inspecting source, configuration, or tests;
- explain that implementation-level detail belongs outside SpecSpine;
- invite a new accepted architectural decision, constraint, responsibility,
  boundary, or open question if further evolution is needed.

## Failure indicators

- any file is modified or created;
- source or configuration is inspected for additional detail;
- functions, schemas, SDK calls, pseudocode, or configuration fields are copied
  into the specification;
- a new specification is created solely to hold implementation detail;
- the response claims to have deepened or updated the Spine.
