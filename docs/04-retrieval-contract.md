# Retrieval contract

## Goal

Retrieval returns the smallest task-closed architectural context, not the
largest set of lexical matches:

```text
Task
→ direct candidates
→ canonical owner
→ typed graph closure
→ relevant sections and statements
→ machine result
→ optional Markdown handoff
```

For a structured request, script-only extraction MUST be deterministic, MUST
NOT require an AI model, and MUST NOT read source code.

## Structured input

The input MUST support:

- document IDs;
- semantic IDs;
- repository-relative Markdown paths;
- literal terms;
- synonym groups;
- task facets;
- a token budget.

```json
{
  "id": "payment-retry-change",
  "targets": ["payment-processing"],
  "terms": [
    ["retry", "repeated attempt"],
    ["provider event", "provider notification"]
  ],
  "facets": ["behavior", "failure", "data-mutation"],
  "token_budget": 8000
}
```

A user, calling agent, or query planner may translate natural language into this
input. The deterministic extractor is not required to understand unrestricted
natural language.

## Candidate and owner selection

Strong direct signals are evaluated in this order:

1. exact semantic ID;
2. exact document ID;
3. exact path;
4. exact title;
5. exact alias;
6. summary;
7. responsibility;
8. relationship meaning;
9. divergence consequence;
10. heading;
11. body.

A high lexical score does not prove ownership. The owner is confirmed through
Responsibility, Kind, typed and incoming relationships, the architecture map,
semantic ownership, coverage, and applicable divergences. A body-only mention
is a weak owner signal.

Independently owned query concerns SHOULD be separate slices. Unrelated owners
MUST NOT be forced into one required lexical match.

## Typed closure

Traversal follows relation semantics:

- `superseded-by` is always followed.
- `constrained-by` normally makes its target required.
- `owns-data` is required for state, mutation, lifecycle, persistence, and
  consistency changes.
- `exposes` is required for external contract changes.
- `consumes` and `publishes` are required for event and integration changes.
- `reads-from` and `writes-to` are required for data flow, consistency, and
  mutation-authority changes.
- `contains` and `decomposes-into` provide selective structural or functional
  zoom; not every child is loaded.
- `performs` is followed when the task touches its outcome, interface,
  lifecycle, or constraint.
- `depends-on` is followed when vocabulary, meaning, failure behavior, or a
  boundary risk makes the target relevant.
- `implemented-by` returns the component or location without loading source.
- `has-evidence` returns a citation without loading evidence content.
- `related-to` is only potentially affected unless stronger signals exist.

Incoming edges support impact analysis but are not automatically required.
Consumers become potentially affected when a task changes an interface, event,
data ownership, accepted constraint, or externally visible behavior.

Traversal SHOULD have a safety depth, such as two, but completeness MUST NOT be
defined only by depth. Stop after required relation semantics, owner,
boundaries, applicable intent, coverage, divergences, and blocking questions are
closed, or when the budget requires explicit truncation.

## Projection

The primary projection includes identity, summary, responsibility, boundaries,
relevant behavior/interfaces/data/lifecycle/failure behavior, relevant
relationships, applicable intent, evidence semantics, questions, divergences,
and coverage.

A required neighbor includes identity, summary, responsibility, the relevant
relationship row, referenced statements, and directly relevant sections.

A potentially affected neighbor includes path, ID, title, summary,
relationship, and impact reason.

## Budget

Budgets SHOULD use tokens; bytes MAY be a fallback. Inclusion priority is:

1. primary identity and responsibility;
2. coverage;
3. blocking questions;
4. known divergences;
5. constraints;
6. decisions;
7. boundaries;
8. referenced statements;
9. required relationships;
10. failure, lifecycle, data, and interface sections;
11. observations;
12. potentially affected neighbors.

Truncation MUST NOT be silent. The result identifies what was omitted, why,
how to retrieve it, and whether closure is complete.

## Machine result

The result MUST have exactly one `closure_status`:

- `complete` — required closure was collected within `Mapped` scope;
- `partial` — useful information exists, but coverage, relationships, or
  required information is incomplete;
- `no-match` — no primary owner was found;
- `truncated` — required information exceeded the budget;
- `invalid` — the request or Spine is mechanically invalid.

`Partially mapped` and `Unmapped` MUST NOT return `complete`. `complete` means
closure from documented architecture, never code/spec conformance.

The result MUST contain primary owner, required and potentially affected
specifications, applicable decisions and constraints, divergences, blocking
questions, coverage, omitted information, source paths, status, and reason.

```json
{
  "closure_status": "complete",
  "reason": "mapped_task_closure_satisfied",
  "coverage": "mapped",
  "primary": "payment-processing",
  "required": [],
  "potentially_affected": [],
  "decisions": [],
  "constraints": [],
  "known_divergences": [],
  "blocking_questions": [],
  "omitted": [],
  "sources": []
}
```

On incomplete results, the extractor MUST state the specific cause, missing
targets, sections, or relationships, and whether direct Markdown navigation or
code investigation may help. It MUST NOT fill gaps with assumptions.

## Human-readable handoff

A Markdown handoff MAY be generated from the machine result and selected
canonical fragments:

```markdown
# Architecture context handoff

## Change intent
## Primary specification
## Required specifications
## Potentially affected specifications
## Architectural decisions and constraints
## Known divergences
## Coverage and confidence
## Relevant behavior and failure boundaries
## Relevant observations
## Unconfirmed inferences
## Blocking questions
## Expected architectural outcome
## Sources
```

The handoff is a temporary projection and MUST NOT become a canonical
specification.
