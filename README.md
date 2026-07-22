# SpecSpine

**An architectural context and memory layer for AI-assisted software development.**

SpecSpine helps humans and coding agents maintain long-lived architectural
memory as a network of linked Markdown specifications and project the smallest
useful architectural context into downstream work.

The specifications form an architectural spine for the project: they describe responsibilities, boundaries, important behavior, decisions, and relationships between system concepts without duplicating the source code.

SpecSpine is intentionally lightweight:

* Markdown-only persistent architecture
* no required frontmatter, schema language, or DSL
* optional mechanical lint instead of claims of formal validation
* no required CLI
* optional disposable retrieval acceleration
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

SpecSpine consumes accepted architectural intent but does not own its approval
process; an external ADR or SDD workflow may own approval and provenance.
SpecSpine does not guarantee code conformance. It preserves disagreements
until the user decides or an explicitly authorized workflow records the
resolution.

SpecSpine is a supporting layer for SDD and direct coding-agent workflows, not
an implementation-oriented SDD framework. It does not own feature requirements,
acceptance criteria, planning, implementation, testing, or delivery.

## Core hypothesis

Given the same documented repository, change request, and coding agent, a
relevant SpecSpine handoff should reduce architectural violations and
irrelevant repository exploration relative to the repository's native
documentation without reducing functional correctness. For
architecture-significant changes, a minimal context handoff should provide at
least as much downstream value as navigating the full Spine at lower context
cost.

This is an experimental, falsifiable product claim. Link validity, document
shape, and skill behavior are regression properties; they are not evidence that
the hypothesis is true.

## Guarantees and limits

SpecSpine can preserve accepted architectural claims, repository observations,
explicit uncertainty, navigable links, and stable handoff fields. Its optional
checker can reproduce mechanical integrity findings.

SpecSpine does not guarantee semantic completeness, correct decomposition,
complete impact analysis, code conformance, implementation readiness, or a
better downstream result. Those are review findings or evaluation outcomes,
not framework invariants.

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

Start with a flat directory. A larger Spine may add a few broad directories for
stable cohesive areas; directories organize navigation but do not define the
architecture.

Software architecture is rarely a strict tree. A concept such as authentication may depend on users, sessions, configuration, security, and audit at the same time. Specifications therefore form a graph through relative Markdown links.

`<spine-root>/README.md` is the entry point into the architecture. It is a curated map, not the semantic parent of every specification.

`specspine-extract` may derive a local SQLite FTS5 index and link graph to find
candidate documents efficiently in a large Spine. This index is disposable,
stored outside the Spine, and never becomes an architecture source. If Python,
SQLite FTS5, command execution, or a usable cache is unavailable, extraction
continues by navigating the same Markdown links directly.

## Skills

### `specspine-connect`

This does not create a SpecSpine. It connects an existing SpecSpine to the
project's persistent agent instructions with one short, framework-neutral
retrieval block. Architecture-relevant downstream work is routed through
`specspine-extract` when installed, with direct Markdown navigation as fallback.
Connect does not inspect or adapt SDD workflows and never generates bindings or
other skills.

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
* preserve unresolved questions.

By default it treats the user request and files under `<spine-root>` as the only
authoritative project evidence. It may use skills, MCP servers, internet search,
and external documentation for general reference, but does not inspect
project-specific material outside the spine unless explicitly requested and
never modifies source code.

### `specspine-map`

Builds a SpecSpine for an existing brownfield project by progressively mapping the codebase from a high-level overview toward selected implementation details.

It records observed repository evidence separately from intended architectural
decisions and preserves disagreements.

### `specspine-extract`

Extracts the smallest temporary architecture context handoff needed by a
downstream feature, SDD, review, or coding workflow. It reads the SpecSpine,
preserves claim semantics and uncertainty, and does not modify persistent
specifications or create implementation artifacts. Its optional local search
index reduces irrelevant reading without being required for extraction.

### `specspine-doctor`

Checks reproducible mechanical integrity and performs a separate advisory
semantic review without guessing architectural intent. Mechanical findings can
produce PASS/FAIL; semantic findings describe evidence-backed risks and never
certify architecture validity or completeness. It includes a deterministic
checker for links, reachability, semantic IDs, and evidence baselines.

For handoff diagnosis or repair, Doctor may directly invoke
`specspine-extract`. Grow, Map, and Doctor retain their specialized operations
over the Spine; Extract is the preferred retrieval gateway for downstream work,
not a mandatory intermediary for every internal skill operation.

### Adapter generator

The five publishable packages under `skills/` are the source of truth.
Repository-only tooling under `tools/specspine-adapter-generator/` synchronizes
references shared by the coordinated packages and is the only place
for generating framework-specific SDD adapters. Runtime skills remain
framework-neutral. The tool contains no canonical skill copies, never generates
canonical skills from files under `tools/`, and is intentionally not
discoverable or installable through `npx skills`.

### Extract diagnostics

Repository-only tooling under `tools/specspine-extract/` observes the optional
retrieval index for mechanical tests and eval telemetry. It imports the
production search implementation from `skills/specspine-extract/`; it is not
installed with the skill and is never required for extraction.

## Installation

The recommended minimum for downstream use is `specspine-connect` plus
`specspine-extract`:

```bash
npx skills add bulbigood/specspine --skill specspine-connect
npx skills add bulbigood/specspine --skill specspine-extract
```

Connect installs the persistent retrieval route. If Extract is absent or
cannot run, that route degrades to direct navigation from the Markdown index.

Install `specspine-connect` from this repository:

```bash
npx skills add bulbigood/specspine --skill specspine-connect
```

Install `specspine-grow` from this repository:

```bash
npx skills add bulbigood/specspine --skill specspine-grow
```

Install `specspine-extract` from this repository:

```bash
npx skills add bulbigood/specspine --skill specspine-extract
```

Install `specspine-map` from this repository:

```bash
npx skills add bulbigood/specspine --skill specspine-map
```

Install `specspine-doctor` from this repository:

```bash
npx skills add bulbigood/specspine --skill specspine-doctor
```

List the available skills:

```bash
npx skills add bulbigood/specspine --list
```

Install all runtime SpecSpine skills without the maintainer-only generator:

```bash
npx skills add bulbigood/specspine --skill specspine-connect
npx skills add bulbigood/specspine --skill specspine-extract
npx skills add bulbigood/specspine --skill specspine-grow
npx skills add bulbigood/specspine --skill specspine-map
npx skills add bulbigood/specspine --skill specspine-doctor
```

For local development:

```bash
git clone https://github.com/bulbigood/specspine.git
cd specspine

npx skills add . --list
npx skills add . --skill specspine-connect
npx skills add . --skill specspine-extract
npx skills add . --skill specspine-grow
npx skills add . --skill specspine-map
npx skills add . --skill specspine-doctor
```

Maintainers synchronize shared package resources, verify that derived copies
match their canonical owner under `skills/`, and run mechanical tests:

```bash
tools/specspine-adapter-generator/scripts/generate_resources.py
tools/specspine-adapter-generator/scripts/generate_resources.py --check
python3 -m unittest discover -s tests/mechanical -p 'test_*.py'
```

## Usage

The skills work through natural-language requests. Users do not need to learn a
command workflow.

### Connect SpecSpine to project agents

```text
Expose this project's SpecSpine to agents through persistent project instructions.
```

`specspine-connect` installs one managed bootstrap in the applicable persistent
project-agent instructions. The bootstrap prefers `specspine-extract` for
architecture-relevant downstream retrieval and retains direct index-and-link
navigation as fallback. Connect creates no additional artifact, discovers no
SDD framework, and persists the SpecSpine documentation language using existing
project context when unambiguous.

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

The skill determines and applies the smallest justified impact because the
explicit change request already authorizes meaning-preserving specification
maintenance:

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

Applied from the explicit request; no redundant confirmation is required.
```

The agent asks only when the request does not decide a normative choice,
canonical ownership is genuinely ambiguous, or a conflict must be resolved.

### Prepare an architecture context handoff

Use `specspine-extract`:

```text
Prepare an architecture context handoff for adding Google Sign-In.
```

The skill identifies the smallest useful context set:

```text
Change intent:
- add external authentication without changing application-session semantics

Primary specification:
- specspine/external-identity.md

Required specifications:
- specspine/authentication.md
- specspine/account-linking.md
- specspine/session-management.md

Potentially affected specifications:
- specspine/users.md
- specspine/configuration.md

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

### Diagnose the specification network

```text
Check this SpecSpine for mechanical and semantic problems.
```

`specspine-doctor` runs deterministic integrity checks, reviews canonical
ownership and claim semantics, and reports findings without modifying the
Spine. Repository drift analysis belongs to `specspine-map`.

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

### Keep important statements addressable

Decisions, constraints, observations, and other claims may use a short semantic
ID when another specification or downstream workflow must reference that exact
statement. IDs remain optional and do not turn Markdown into a formal schema.

```markdown
- **CON-retry-limit** — Retries stop after the configured limit.
- Job processing must preserve [CON-retry-limit](job-processing.md).
```

Bold IDs define statements; linked IDs reference them. The link combines the
target file and ID in one machine-readable Markdown node without adding custom
syntax.

Repository observations may cite representative evidence paths. Such citations
support provenance and navigation but do not prove code/spec conformance.

### Use readable visual representations

Specifications may use lists, Markdown tables, and focused Mermaid flowcharts,
sequence diagrams, state diagrams, ER diagrams, class diagrams, or mind maps.
The important meaning must also remain clear in nearby prose. ASCII diagrams
are not allowed because wrapping and automated edits make them unreliable.

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
│   ├── specspine-connect/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   └── bootstrap-contract.md
│   │   └── assets/
│   │       └── templates/
│   │           └── agent-bootstrap.md
│   ├── specspine-extract/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   └── context-handoff.md
│   │   └── scripts/
│   │       └── search_spine.py
│   ├── specspine-grow/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── spec-format.md
│   │   │   ├── spec-semantics.md
│   │   │   └── examples.md
│   │   └── assets/
│   │       └── templates/
│   │           ├── architecture-index.md
│   │           └── specification.md
│   ├── specspine-map/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── mapping-method.md
│   │   │   ├── spec-format.md
│   │   │   ├── spec-semantics.md
│   │   │   └── examples.md
│   │   └── assets/
│   │       └── templates/
│   │           ├── architecture-index.md
│   │           └── specification.md
│   └── specspine-doctor/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   │   ├── spec-format.md
│   │   │   ├── spec-semantics.md
│   │   │   └── review-method.md
│   │   └── scripts/
│   │       └── check_spine.py
├── tools/
│   └── specspine-adapter-generator/
│       ├── MAINTAINER.md
│       ├── references/
│       │   └── generation-contract.md
│       ├── scripts/
│       │   └── generate_resources.py
├── examples/
│   └── minimal-saas/
└── tests/
    ├── README.md
    ├── mechanical/
    │   ├── benchmark_extract_search.py
    │   ├── test_extract_benchmark.py
    │   └── test_extract_search.py
    └── scenarios/
```

The five runtime skills form a coordinated suite with explicit scope and
degraded-operation boundaries. Each package keeps its own required resources,
while the connected downstream path prefers `specspine-extract` and falls back
to the Markdown graph. `specspine-adapter-generator` is maintainer-only tooling:
it keeps shared rules synchronized and owns framework-specific adapter
generation without adding environment knowledge or mandatory runtime
dependencies to canonical skills.

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

It is an architectural context and memory layer for humans and coding agents.

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
coding-agent workflows through the neutral handoff produced by
`specspine-extract`. Framework-specific integration belongs to adapters produced
outside the runtime skill line by `tools/specspine-adapter-generator/`.
Canonical skills do not inspect framework conventions, convert specifications,
or guarantee compatibility.

It can also be used independently as architectural memory and navigation when a
full SDD workflow would add unnecessary ceremony.

## Project status

SpecSpine is experimental.

The current goal is to test whether linked architectural memory and minimal
context handoffs improve downstream coding-agent outcomes across repeated
project changes without introducing a formal schema or mandatory runtime.

The most important success criterion is:

> Can a new agent with no conversation history use the SpecSpine to locate the
> correct architectural area and obtain sufficient context for downstream work
> without importing unrelated or feature-level detail?

## Roadmap

* [x] Define the SpecSpine principles
* [x] Create `specspine-connect` for the project-agent bootstrap
* [x] Create `specspine-extract` for context handoffs
* [x] Create `specspine-grow`
* [x] Add a repeatable evaluation harness
* [x] Create `specspine-map` for brownfield projects
* [x] Create `specspine-doctor` for integrity diagnosis and guarded repair
* [x] Coordinate canonical runtime skills through explicit handoff and fallback contracts
* [x] Add optional mechanical integrity checks
* [x] Add optional local retrieval acceleration with native link fallback
* [ ] Add connectors to popular SDD frameworks

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
