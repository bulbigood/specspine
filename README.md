# SpecSpine

**A lightweight specification backbone for AI-built software.**

SpecSpine helps humans and coding agents grow abstract software ideas into a
long-lived network of linked Markdown architectural specifications.

The specifications form an architectural spine for the project: they describe responsibilities, boundaries, important behavior, decisions, and relationships between system concepts without duplicating the source code.

SpecSpine is intentionally lightweight:

* Markdown only
* no schema or DSL
* no formal validation
* no required CLI
* no implementation workflow
* no vendor lock-in

The human owns product and architecture decisions. AI agents organize, refine,
and navigate the resulting specification network. Downstream tools or coding
agents own feature specification and implementation workflows.

## Product contract

SpecSpine has two distinct outputs:

```text
Persistent artifact:
Linked architectural specifications

Task-oriented output:
Minimal architecture context handoff
```

The specification network is the durable project spine. A context handoff is a
temporary projection containing the smallest useful architectural context for a
particular downstream task. Its Markdown format is SpecSpine's stable
interoperability contract, not a programmatic API or tool-specific adapter.

SpecSpine does not guarantee that specifications conform exactly to the code.
It may explicitly preserve disagreements between intended architecture and
observed repository evidence until the user or a downstream workflow resolves
them.

## Why SpecSpine?

Coding agents are good at implementing isolated tasks, but they often lack durable architectural context.

A typical repository contains:

* source code that explains local implementation;
* scattered documentation;
* decisions hidden in previous conversations;
* architecture that must be rediscovered for every task.

SpecSpine adds a small, persistent layer above feature and implementation
workflows:

```text
                 ┌───────────────────────────┐
                 │  SpecSpine architecture   │
                 │  long-lived project spine│
                 └─────────────┬─────────────┘
                               │
                     minimal context handoff
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
      OpenSpec             spec-kit           coding agent
          │                    │                    │
          └────────────────────┴────────────────────┘
                               │
                    implementation workflow
```

Instead of asking an agent to explore the entire repository blindly, SpecSpine gives it a navigable map of the system and tells it which areas matter for the current change.

## Core idea

`<spine-root>` denotes the configurable SpecSpine document root. Its default is
`specspine`; an installer or project instruction may set another location.

Specifications are stored as ordinary Markdown files:

```text
<spine-root>/
├── README.md
├── authentication.md
├── account-linking.md
├── session-management.md
├── users.md
└── notifications.md
```

The directory is intentionally flat.

Software architecture is rarely a strict tree. A concept such as authentication may depend on users, sessions, configuration, security, and audit at the same time. Specifications therefore form a graph through relative Markdown links.

`<spine-root>/README.md` is the entry point into the architecture. It is a curated map, not the semantic parent of every specification.

## Skills

### `specspine-grow`

Creates and evolves a SpecSpine for a greenfield project.

It can:

* initialize specifications from an abstract project idea;
* refine an existing specification;
* identify specifications affected by a requested change;
* propose new specification files;
* split broad concepts into focused specifications;
* merge overlapping specifications;
* maintain cross-links;
* preserve unresolved questions;
* prepare minimal architecture context handoffs for downstream work.

It works only with specifications and does not modify source code.

### `specspine-map`

Builds a SpecSpine for an existing brownfield project by progressively mapping the codebase from a high-level overview toward selected implementation details.

It records observed repository evidence separately from intended architectural
decisions, preserves disagreements, and can prepare the same neutral context
handoff as `specspine-grow`.

## Installation

Install `specspine-grow` from this repository:

```bash
npx skills add bulbigood/specspine --skill specspine-grow
```

Install `specspine-map` independently:

```bash
npx skills add bulbigood/specspine --skill specspine-map
```

List the available skills:

```bash
npx skills add bulbigood/specspine --list
```

Install all available SpecSpine skills:

```bash
npx skills add bulbigood/specspine --skill '*'
```

For local development:

```bash
git clone https://github.com/bulbigood/specspine.git
cd specspine

npx skills add . --list
npx skills add . --skill specspine-grow
npx skills add . --skill specspine-map
```

## Usage

The skill is designed to work through natural-language requests. Users do not need to learn a command workflow.

### Start a project

```text
Create a SpecSpine for a small SaaS application that lets teams manage
customers, subscriptions, and invoices.
```

The skill creates the smallest useful architecture instead of attempting to design the entire system immediately.

A possible initial result:

```text
<spine-root>/
├── README.md
├── application.md
├── identity.md
├── billing.md
└── operations.md
```

Early specifications may be intentionally short and contain open questions.

### Refine an area

```text
Refine the authentication architecture.
```

The skill follows the existing links, expands the relevant specification, and proposes a split only when separate responsibilities have emerged.

For example:

```text
authentication.md
```

may eventually evolve into:

```text
authentication.md
password-authentication.md
external-identity.md
account-linking.md
session-management.md
```

The original `authentication.md` remains a concise overview and navigation point.

### Add a cross-cutting capability

```text
Add Google Sign-In.
```

Before changing the specification structure, the skill presents an impact proposal:

```text
Affected specifications

Create:
- <spine-root>/account-linking.md

Modify:
- <spine-root>/authentication.md
- <spine-root>/external-identity.md
- <spine-root>/session-management.md
- <spine-root>/users.md
- <spine-root>/configuration.md

Reason:
Account linking has independent behavior shared by external identity
providers and user-account management.

Open decisions:
- Should an existing account be linked automatically by verified email?

Proceed with these specification changes?
```

The human approves the architectural change before it is applied.

### Prepare an architecture context handoff

```text
Prepare an architecture context handoff for adding Google Sign-In.
```

The skill identifies the smallest useful context set:

```text
Change intent:
- add external authentication without changing application-session semantics

Primary specification:
- external-identity.md

Required specifications:
- authentication.md
- account-linking.md
- session-management.md

Potentially affected specifications:
- users.md
- configuration.md

Architectural decisions and constraints:
- application sessions remain provider-independent;
- external provider tokens are not stored;
- account linking requires an explicit policy.

Blocking questions:
- automatic versus explicit account linking.

Expected architectural outcome:
- a verified external identity establishes a local identity and then creates a
  normal application session.
```

A downstream workflow can use this handoff while remaining responsible for
feature requirements, acceptance criteria, planning, tasks, tests, and
implementation.

## Specification philosophy

### One canonical home per concept

An important responsibility, rule, or decision should be defined primarily in one specification.

Other specifications link to it rather than maintaining competing copies.

### Specifications form a graph

Hierarchy is useful, but it is not mandatory.

Specifications can represent:

* subsystems;
* capabilities;
* policies;
* shared infrastructure;
* cross-cutting concerns;
* architectural decisions.

Relationships are expressed through ordinary Markdown links.

### Split by responsibility, not file size

A separate specification is useful when a concept:

* has an independent responsibility;
* contains meaningful decisions;
* has its own boundaries or behavior;
* is referenced by several other specifications;
* can evolve independently.

A long document is not automatically a bad document, and a short concept does not automatically deserve a separate file.

### Preserve uncertainty

Missing information must not be silently replaced with assumptions.

Unresolved decisions remain visible under `Open questions` until the human accepts a direction.

### Distinguish statement semantics

SpecSpine uses a small semantic model without requiring a schema:

* `Decisions` are accepted architectural choices.
* `Constraints` restrict acceptable architecture or implementation.
* `Observed` records facts supported by current repository evidence.
* `Inferred` records unconfirmed interpretations of evidence.
* `Open questions` preserves unresolved uncertainty.

Decisions and constraints describe intended architecture, but do not imply that
the code implements it. Observations do not override intended architecture. A
disagreement remains explicit until resolved by the user or a downstream
workflow.

### Keep feature artifacts downstream

SpecSpine owns stable responsibilities, ownership boundaries, architectural
relationships, long-lived decisions, and constraints expected to remain useful
across multiple changes.

Feature-specific deltas, temporary scope, acceptance criteria, implementation
tasks, implementation status, release scope, and pull-request-specific details
belong to downstream workflows.

```text
SpecSpine:
Webhook processing must be idempotent.

Downstream workflow:
Given the same webhook event twice, the second request returns 200 without
creating another transaction.
```

### Do not reproduce source code

Specifications should describe:

* responsibilities;
* boundaries;
* significant behavior;
* dependencies;
* accepted decisions;
* architectural constraints.

They should not describe:

* local function calls;
* obvious control flow;
* framework boilerplate;
* variable-level implementation;
* algorithms that are already clear from the code.

The specification should stop where implementation becomes the cheaper and clearer representation.

## Example specification

```markdown
# Session management

Creates and maintains application sessions independently of the
authentication method used to establish identity.

## Responsibility

- create authenticated application sessions;
- rotate refresh credentials;
- revoke individual or all user sessions;
- expose the authenticated identity context to the application.

## Boundaries

Session management does not validate passwords or external identity
provider tokens.

Those responsibilities belong to:

- [Password authentication](password-authentication.md)
- [External identity](external-identity.md)

## Behavior

After an authentication method establishes a valid user identity,
session management creates a provider-independent application session.

Revoked refresh credentials cannot be reused.

## Relationships

### Part of

- [Authentication](authentication.md)

### Depends on

- [User accounts](users.md)
- [Security](security.md)

### Used by

- [API server](api-server.md)

## Decisions

- Application sessions are independent of identity providers.
- Refresh credentials are rotated after successful use.
- External provider access tokens are not stored as session credentials.

## Open questions

- Should users be able to view and revoke individual active sessions?
```

Sections are optional. Empty sections should not be added merely to satisfy a template.

## Repository structure

```text
specspine/
├── README.md
├── LICENSE
├── skills/
│   ├── specspine-grow/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── spec-format.md
│   │   │   ├── spec-semantics.md
│   │   │   ├── context-handoff.md
│   │   │   └── examples.md
│   │   └── assets/
│   │       └── templates/
│   │           ├── architecture-index.md
│   │           └── specification.md
│   └── specspine-map/
│       ├── SKILL.md
│       ├── references/
│       │   ├── mapping-method.md
│       │   ├── spec-format.md
│       │   ├── spec-semantics.md
│       │   ├── context-handoff.md
│       │   └── examples.md
│       └── assets/
│           └── templates/
│               ├── architecture-index.md
│               └── specification.md
├── examples/
│   └── minimal-saas/
└── tests/
    └── scenarios/
```

Each skill is self-contained and can be installed independently.

## What SpecSpine is not

SpecSpine is not:

* a formal architecture-description language;
* a code generator;
* a replacement for source-code exploration;
* a feature-change or task-management framework;
* a full software-delivery methodology;
* an acceptance-testing or regression-testing system;
* an implementation or release-status tracker;
* a guarantee that documentation and code are synchronized;
* a replacement for human architectural judgment.

It is a lightweight architectural memory and navigation layer for humans and coding agents.

## Relationship to other SDD tools

SpecSpine does not attempt to replace tools such as OpenSpec, spec-kit, BMAD,
or execution-oriented agent frameworks.

Those tools generally organize work around a feature, change, plan, or implementation workflow.

SpecSpine focuses on the long-lived architectural context from which those changes can be understood:

```text
SpecSpine architecture
        ↓
Feature or change workflow
        ↓
Coding agent
        ↓
Source code
```

SpecSpine is conceptually compatible with OpenSpec, spec-kit, and direct
coding-agent workflows through its neutral context handoff. This is not a
formal integration: SpecSpine currently provides no adapters, artifact
conversion, or compatibility guarantee.

It can also be used independently as architectural memory and navigation when a
full SDD workflow would add unnecessary ceremony.

## Project status

SpecSpine is experimental.

The current goal is to test whether a small agent skill can maintain a useful linked architecture across repeated project changes without introducing a formal schema or custom runtime.

The most important success criterion is:

> Can a new agent with no conversation history use the SpecSpine to locate the
> correct architectural area and obtain sufficient context for downstream work
> without importing unrelated or feature-level detail?

## Roadmap

* [x] Define the SpecSpine principles
* [x] Create `specspine-grow`
* [ ] Add example greenfield projects
* [ ] Add repeatable evaluation scenarios
* [ ] Test across multiple coding agents
* [ ] Improve impact proposals and decomposition behavior
* [x] Create `specspine-map` for brownfield projects
* [ ] Add optional broken-link and graph-visualization tools

The core workflow will remain Markdown-first and lightweight.

## Contributing

Contributions are welcome, especially:

* realistic example projects;
* difficult decomposition scenarios;
* cross-cutting architecture changes;
* regression cases where an agent duplicated or misplaced a concept;
* evaluations across different coding agents;
* improvements that preserve the minimal nature of the project.

Avoid adding formal schemas, mandatory runtimes, or complex workflows unless they solve a demonstrated problem that cannot be addressed by the skill itself.

## License

MIT
