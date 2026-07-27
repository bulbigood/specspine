# SpecSpine

**An architectural context and memory layer for AI-assisted software
development.**

SpecSpine helps people and coding agents maintain long-lived architectural
memory as a graph of linked Markdown specifications and retrieve the smallest
useful architectural context for downstream work.

It describes responsibilities, boundaries, important behavior, accepted
decisions, constraints, evidence, uncertainty, and relationships without
duplicating source code.

## Why SpecSpine?

Coding agents can implement isolated tasks but often lack durable architectural
context. Architecture is scattered across source code, documentation, previous
conversations, and implicit decisions, so each task begins with rediscovery.

SpecSpine adds a small persistent layer above feature and implementation
workflows:

```text
SpecSpine architecture
        ↓
Minimal task context
        ↓
Feature, SDD, review, or coding workflow
        ↓
Source code
```

The human owns product and architecture decisions. SpecSpine preserves accepted
long-lived intent. Source code owns implementation reality. Downstream systems
own feature requirements, acceptance criteria, planning, implementation,
testing, and delivery.

## Core properties

- Canonical architecture is ordinary Markdown.
- Each architectural concept has one canonical owner.
- Typed relationships form a navigable graph.
- Decisions, constraints, observations, inferences, and open questions remain
  distinct.
- Confirmed intent/reality conflicts remain explicit as Known divergences.
- Coverage is reported as `Mapped`, `Partially mapped`, or `Unmapped`.
- Derived indexes, graphs, diagrams, and handoffs are disposable.
- Retrieval degrades to direct Markdown navigation when acceleration is
  unavailable.
- No CLI, database, frontmatter, schema language, DSL, renderer, or vendor is
  required to understand the architecture.

SpecSpine does not prove semantic completeness, correct decomposition, impact
completeness, implementation readiness, or code/spec conformance.

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
npx skills add bulbigood/specspine --skill specspine-grow
```

Map a brownfield repository:

```bash
npx skills add bulbigood/specspine --skill specspine-map
```

See [Installation and usage](docs/07-installation-and-usage.md) for complete
workflows.

## Documentation

The normative v2 contract starts at [docs/README.md](docs/README.md):

- [Core model](docs/01-core-model.md)
- [Markdown format](docs/02-markdown-format.md)
- [Semantics and evidence](docs/03-semantics-and-evidence.md)
- [Retrieval contract](docs/04-retrieval-contract.md)
- [Coverage, validation, and views](docs/05-coverage-validation-views.md)
- [Tooling, migration, and acceptance](docs/06-tooling-migration-acceptance.md)
- [Installation and usage](docs/07-installation-and-usage.md)
- [Development and maintenance](docs/08-development.md)

## Status

SpecSpine is experimental. Its central hypothesis is that persistent
architectural memory and minimal task handoffs reduce architectural violations
and irrelevant repository exploration without reducing functional correctness.
See [Development and maintenance](docs/08-development.md) for evaluation and
contribution guidance.

## License

MIT
