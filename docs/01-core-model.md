# Core model

## Purpose

SpecSpine is a human-readable, long-lived architectural memory layer for people
and AI agents. It stores responsibilities, boundaries, important behavior,
accepted decisions, constraints, uncertainty, and relationships without
duplicating source code.

Its primary success criterion is:

> A new agent with no conversation history can find the canonical owner of a
> task, obtain the required neighboring constraints, and understand the
> architectural risks faster and at lower context cost than by exploring the
> codebase from scratch.

SpecSpine MUST:

- remain useful as plain Markdown without a CLI, database, generator, schema
  registry, renderer, or external service;
- form a connected typed graph;
- preserve accepted intent, evidence provenance, and unresolved uncertainty;
- support deterministic script-only extraction of task-specific context;
- avoid reproducing implementation detail already represented more clearly by
  code.

## Authority boundaries

SpecSpine is the source of truth only for accepted, long-lived architectural
intent.

| Knowledge | Canonical source |
|---|---|
| Long-lived responsibilities, boundaries, decisions, and constraints | SpecSpine |
| Delta of a particular accepted change | Accepted SDD or change specification |
| Current implementation | Source code |
| Current observed behavior | Code, tests, and runtime evidence |
| Backlog, delivery, and release status | External workflow system |

A draft, an agent inference, or existing code MUST NOT create or rewrite an
accepted Decision or Constraint. Approval belongs to a human or an explicitly
designated external workflow.

Code does not automatically invalidate architectural intent. Architectural
intent does not prove that code conforms to it. A material disagreement MUST be
preserved explicitly until an authorized decision resolves it.

## Canonical and derived information

The data direction is:

```text
Canonical Markdown
    → parser
    → disposable index and typed graph
    → reports, views, and context handoffs
```

Canonical Markdown wins whenever a derived artifact disagrees with it. A graph,
SQLite database, JSONL file, backlink list, diagram, report, or context handoff
MUST NOT become an independent architecture source.

Each architectural concept MUST have one canonical owner document. Other
documents may provide local context and link to that owner, but MUST NOT
maintain competing copies of rules, lifecycle, ownership, interface contracts,
retry policies, or invariants.

One authored architectural relationship is stored once. Reverse edges,
backlinks, impact reports, and diagram edges are derived.

## File organization

Every Spine MUST have a root `README.md`. A flat structure is the default:

```text
<spine-root>/
├── README.md
├── authentication.md
├── session-management.md
└── payment-processing.md
```

Directories MAY group several documents that form a stable cohesive area.
Paths organize navigation but MUST NOT define architectural hierarchy. Moving a
file MUST NOT change its document ID.

Specification filenames SHOULD use `lowercase-kebab-case.md` and stable concept
names. Temporary feature, issue, or implementation-task names SHOULD NOT be
used.

## What belongs in SpecSpine

Include information that:

- defines stable responsibility or ownership;
- describes an architectural relationship;
- records accepted long-lived intent;
- preserves architecture-significant uncertainty or divergence;
- remains useful across multiple changes.

Keep feature deltas, acceptance criteria, implementation tasks, delivery state,
release scope, pull-request details, temporary runtime metrics, and source-level
walkthroughs in their owning downstream systems.

## Non-goals

SpecSpine is not:

- a canonical graph database or formal architecture-description language;
- a universal source of implementation truth;
- an automatic proof of code/spec conformance;
- a node-per-file, class, function, test, or telemetry knowledge graph;
- an implementation planner, task manager, or release tracker;
- a replacement for source exploration or human architectural judgment;
- a mandatory YAML, embedding, C4, arc42, ICOM, SQLite, or SaaS runtime.
