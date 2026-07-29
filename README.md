# SpecSpine

**A reconstructable system specification and architectural memory layer for
AI-assisted software development.**

SpecSpine helps people and coding agents maintain accepted architecture,
durable behavior, contracts, and evidence as a linked specification graph. A
sufficiently specified area can be independently reimplemented from SpecSpine
and checked against its conformance surface.

It describes responsibilities, requirements, guarantees, invariants,
interfaces, quality constraints, verification, evidence, uncertainty, and
relationships without duplicating implementation source.

## Why SpecSpine?

Coding agents can implement isolated tasks but often lack durable architectural
context. Architecture is scattered across source code, documentation, previous
conversations, and implicit decisions, so each task begins with rediscovery.

SpecSpine adds a persistent specification layer above feature and
implementation workflows:

```text
SpecSpine system specification
        ↓
Minimal task context
        ↓
Feature, SDD, review, or coding workflow
        ↓
Source code
```

The human owns product and architecture decisions. SpecSpine preserves accepted
durable intent and implementation-independent verification. An SDD owns a
proposed delta until its accepted durable meaning is promoted. Source code owns
implementation reality. Downstream systems own planning, implementation,
delivery state, and implementation-specific testing.

## Core properties

- Canonical meaning is ordinary Markdown; exact durable contracts may use
  owned machine-readable assets.
- Each architectural concept has one canonical owner.
- Typed relationships form a navigable graph.
- Normative claims, observations, inferences, and open questions remain
  distinct.
- Confirmed intent/reality conflicts remain explicit as Known divergences.
- Mandatory `specspine.json` records each owner's completeness facets,
  reconstruction blockers, implementation freedom, and exact assets once.
- Readiness is derived as `ready`, `incomplete`, or `blocked`.
- Derived indexes, graphs, diagrams, and handoffs are disposable.
- Skills keep disposable runtime files under the ignored workspace-local
  `.specspine/<skill>` directory.
- Retrieval degrades to direct Markdown navigation when acceleration is
  unavailable.
- No CLI, database, frontmatter, renderer, or vendor is required to understand
  the specification.

SpecSpine does not prove semantic completeness, correct decomposition, impact
completeness, or current-code conformance. `ready` is a specification claim
tested through blind reconstruction and conformance, not delivery state.

## Minimal node

```markdown
# Session management

**ID:** `session-management` · **Kind:** `subsystem`

Owns provider-independent authenticated application sessions.

## Responsibility

- creates and revokes application sessions;
- owns refresh-token lifecycle.

## Relationships

| Relation | Target | Meaning |
|---|---|---|
| `constrained-by` | [CON-session-isolation](session-policy.md) | Provider credentials cannot act as application sessions |
```

The root `<spine-root>/README.md` is a curated architecture map, not the
semantic parent of every specification. Ordinary Markdown links provide
navigation; only `Relationships` table rows create typed edges.

## Quick start

Install the recommended downstream pair:

```bash
npx skills add bulbigood/specspine --skill specspine-doctor
npx skills add bulbigood/specspine --skill specspine-extract
```

Connect a project:

```text
Expose this project's SpecSpine to agents through persistent project instructions.
```

Create intended architecture:

```bash
npx skills add bulbigood/specspine --skill specspine-evolve
```

Map a brownfield repository:

```bash
npx skills add bulbigood/specspine --skill specspine-map
```

Verify implementation conformance or run a blind reconstruction benchmark:

```bash
npx skills add bulbigood/specspine --skill specspine-verify
```

See [Installation and usage](docs/07-installation-and-usage.md) for complete
workflows.

## Documentation

The normative v3 contract starts at [docs/README.md](docs/README.md):

- [Core model](docs/01-core-model.md)
- [Markdown format](docs/02-markdown-format.md)
- [Semantics and evidence](docs/03-semantics-and-evidence.md)
- [Retrieval contract](docs/04-retrieval-contract.md)
- [Completeness, validation, and views](docs/05-completeness-validation-views.md)
- [Tooling and acceptance](docs/06-tooling-and-acceptance.md)
- [Installation and usage](docs/07-installation-and-usage.md)
- [Development and maintenance](docs/08-development.md)
- [Reconstruction specifications](docs/09-reconstruction-specifications.md)

## Status

SpecSpine is experimental. Its central hypothesis is that persistent normative
specification, architectural memory, and minimal task handoffs enable
contract-equivalent reconstruction while reducing architectural violations and
irrelevant repository exploration.
See [Development and maintenance](docs/08-development.md) for evaluation and
contribution guidance.

## License

MIT
