# Installation and usage

## Runtime skills

SpecSpine is delivered as four coordinated skills:

- `specspine-doctor` connects a Spine to project agents and diagnoses or
  repairs specification health.
- `specspine-extract` retrieves the smallest task-specific architecture
  closure.
- `specspine-grow` creates and evolves accepted intended architecture.
- `specspine-map` records observed brownfield architecture from repository
  evidence.

The skills use natural-language requests; users do not need to learn a command
workflow.

## Installation

The recommended minimum for downstream use is Doctor plus Extract:

```bash
npx skills add bulbigood/specspine --skill specspine-doctor
npx skills add bulbigood/specspine --skill specspine-extract
```

Doctor installs the persistent retrieval route. If Extract is unavailable, the
route degrades to direct navigation from the Markdown index.

Install another individual skill:

```bash
npx skills add bulbigood/specspine --skill specspine-grow
npx skills add bulbigood/specspine --skill specspine-map
```

List available skills:

```bash
npx skills add bulbigood/specspine --list
```

Install all runtime skills:

```bash
npx skills add bulbigood/specspine --skill specspine-doctor
npx skills add bulbigood/specspine --skill specspine-extract
npx skills add bulbigood/specspine --skill specspine-grow
npx skills add bulbigood/specspine --skill specspine-map
```

## Connect a project

Ask Doctor:

```text
Expose this project's SpecSpine to agents through persistent project instructions.
```

Doctor asks for the Spine root (`specspine` by default), documentation language,
and project instruction file (`AGENTS.md` by default). It creates a missing root
index but does not modify an existing index or create concept specifications.
It installs one bounded managed bootstrap and runs the mechanical checker.

Connection administration and health review are separate operations.

The managed project-instruction block contains only the index location,
documentation language, retrieval route, and compact authority rules. The root
index contains only project-specific architectural context and coverage.
General explanations of the SpecSpine framework remain in this documentation
and are not copied into either project artifact.

## Start or evolve intended architecture

Ask Grow to initialize a small Spine:

```text
Create a SpecSpine for a SaaS application that lets teams manage customers,
subscriptions, and invoices.
```

Grow creates the smallest useful initial architecture. Early specifications may
be intentionally short and preserve open questions.

Refine an area:

```text
Refine the authentication architecture.
```

Grow follows existing links and proposes a split only after independent
responsibilities emerge. An overview may remain as a concise navigation point.

Apply a cross-cutting accepted change:

```text
Add Google Sign-In.
```

Grow identifies the smallest justified create/modify set. It asks for a
decision only when the request does not establish required intent, canonical
ownership is genuinely ambiguous, or a conflict must be resolved.

By default, Grow treats the user request and files under `<spine-root>` as the
only project-specific authorities. It may consult general external references
but does not inspect project code or modify source files.

## Map a brownfield repository

Request one bounded mapping step:

```text
Survey this repository and create a high-level SpecSpine.
```

Request exhaustive recursive coverage explicitly:

```text
Use specspine-map to cover this whole project exhaustively.
```

Bounded mode advances one shallowest useful step. Exhaustive mode inventories
production work mechanically, assigns each verification ToDo to a fresh
one-shot producer, integrates receipts or drafts centrally, and continues until
the inventory is verified. If fresh producers cannot be created, exhaustive
mode reports that limitation instead of simulating full coverage in one long
context.

Map keeps repository observations separate from accepted decisions, preserves
uncertainty and drift, and recommends a separate Doctor review after an
exhaustive run.

## Extract task context

Ask Extract:

```text
Prepare an architecture context handoff for adding Google Sign-In.
```

Extract identifies:

- the primary owner;
- required and potentially affected specifications;
- applicable decisions and constraints;
- coverage and confidence;
- known divergences;
- relevant observations and inferences;
- blocking questions;
- omitted information and sources;
- one closure status.

The machine-readable closure is normative. The Markdown handoff is a temporary
projection for a downstream feature, SDD, review, or coding workflow. That
workflow remains responsible for requirements, acceptance criteria, planning,
implementation, tests, and delivery.

## Diagnose a Spine

Ask Doctor:

```text
Check this SpecSpine for mechanical and semantic problems.
```

Doctor reports deterministic mechanical findings separately from advisory
semantic risks. Diagnosis is read-only. Repairs require approval and never
guess architectural intent. Repository drift analysis belongs to Map.

For handoff-specific diagnosis, Doctor may invoke Extract directly. Extract is
the preferred downstream retrieval gateway, not a mandatory intermediary for
every Grow, Map, or Doctor operation.
