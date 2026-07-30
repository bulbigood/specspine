# Core model

## Purpose

SpecSpine is a human-readable, long-lived graph of canonical owners and their
durable boundary contracts for people and AI agents. It stores what each owner
must provide across its boundary and the minimum architecture needed to assign
that responsibility, without duplicating implementation source.

Its primary success criterion is:

> A new agent with no conversation history can find the canonical owner of a
> task, obtain the required neighboring constraints, and understand the
> architectural risks faster and at lower context cost than by exploring the
> codebase from scratch.

For an area whose computed status is `ready`, an agent using only the SpecSpine bundle
and standard toolchains can create an independent contract-equivalent
implementation that passes the owned conformance surface without inventing
unresolved policy.

SpecSpine MUST:

- remain understandable as plain Markdown without a CLI, database, renderer,
  or external service;
- form a connected typed graph;
- preserve accepted intent, evidence provenance, and unresolved uncertainty;
- support deterministic script-only extraction of task-specific context;
- exclude private implementation detail owned by code;
- permit owned machine-readable contracts and implementation-independent
  verification where exact reconstruction semantics require them.

## Authority boundaries

SpecSpine is the source of truth for accepted, durable system intent.

Accepted intent includes durable owner-relative contracts: responsibility,
inputs and outputs, controls, data authority, observable lifecycle and failure
behavior, compatibility, relationships, and explicit architecture constraints.
Evidence, uncertainty, divergence, implementation navigation, risks,
terminology, and rationale retain their narrower non-intent semantics.

| Knowledge | Canonical source |
|---|---|
| Long-lived architecture, requirements, contracts, and verification | SpecSpine |
| Proposed delta of a change | SDD or change specification until acceptance |
| Current implementation | Source code |
| Current observed behavior | Code, tests, and runtime evidence |
| Backlog, delivery, and release status | External workflow system |

A draft, an agent inference, or existing code MUST NOT create or rewrite an
accepted normative claim. Approval belongs to a human or an explicitly
designated external workflow. Durable accepted SDD meaning MUST be promoted
into canonical SpecSpine owners.

Code does not automatically invalidate architectural intent. Architectural
intent does not prove that code conforms to it. A material disagreement MUST be
preserved explicitly until an authorized decision resolves it.

## Canonical and derived information

The data direction is:

```text
Canonical Markdown and owned contract assets
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

Every Spine MUST have `README.md`, `_INDEX.md`, and `specspine.json`. A flat structure is the
default:

```text
<spine-root>/
├── README.md
├── _INDEX.md
├── specspine.json
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

- defines a stable owner responsibility or boundary;
- describes an owner-to-owner relationship;
- records accepted long-lived boundary intent;
- defines durable requirements, guarantees, interfaces, invariants, quality
  constraints, or implementation-independent verification;
- preserves boundary-significant uncertainty or divergence;
- remains useful across multiple changes.

Keep proposed feature deltas, temporary delivery acceptance, implementation
tasks, delivery state, release scope, pull-request details, temporary runtime
metrics, and source-level walkthroughs in downstream systems. Promote accepted
durable behavior and reusable black-box verification into SpecSpine.

Use the replacement test: a statement belongs here when it must remain true if
the owner is reimplemented behind the same boundary. Private algorithms, call
sequences, helpers, framework state, class/function decomposition, and
incidental source layout belong to code unless an accepted architecture
constraint deliberately fixes them.

## Non-goals

SpecSpine is not:

- a canonical graph database or formal architecture-description language;
- a universal source of implementation truth;
- an automatic proof of code/spec conformance;
- a node-per-file, class, function, test, or telemetry knowledge graph;
- an implementation planner, task manager, or release tracker;
- a guarantee of source-text identity or a replacement for human product
  judgment;
- a YAML, embedding, C4, arc42, ICOM, SQLite, or SaaS runtime.
