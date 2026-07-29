# Installation and usage

## Runtime skills

SpecSpine is delivered as five coordinated skills:

- `specspine-doctor` connects or disconnects a Spine and checks or repairs
  specification health.
- `specspine-extract` retrieves the smallest task-specific architecture
  closure.
- `specspine-evolve` creates and evolves accepted architecture and durable
  system specifications.
- `specspine-map` records observed brownfield architecture from repository
  evidence.
- `specspine-verify` checks implementation or blind-reconstruction conformance
  without creating intent.

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
npx skills add bulbigood/specspine --skill specspine-evolve
npx skills add bulbigood/specspine --skill specspine-map
npx skills add bulbigood/specspine --skill specspine-verify
```

List available skills:

```bash
npx skills add bulbigood/specspine --list
```

Install all runtime skills:

```bash
npx skills add bulbigood/specspine --skill specspine-doctor
npx skills add bulbigood/specspine --skill specspine-extract
npx skills add bulbigood/specspine --skill specspine-evolve
npx skills add bulbigood/specspine --skill specspine-map
npx skills add bulbigood/specspine --skill specspine-verify
```

## Connect a project

Ask Doctor:

```text
Expose this project's SpecSpine to agents through persistent project instructions.
```

Doctor asks for the Spine root (`specspine` by default), documentation language,
and project instruction file (`AGENTS.md` by default). It creates a missing
root index and `specspine.json` together but does not modify an existing root
or create concept specifications.
When the project workspace is a Git repository root, Doctor also adds the exact
`.specspine` rule to its `.gitignore` without changing existing rules. It does
not create or modify `.gitignore` outside a Git repository root. Doctor then
installs one bounded managed bootstrap and runs the mechanical checker.

`.specspine` is workspace-local disposable state for SpecSpine skills. Agents
improving the framework should keep temporary files there, namespaced by skill
(for example, `.specspine/map`), rather than in the repository tree or a global
temporary directory.

Connection administration and health review are separate operations.

The managed project-instruction block contains only the index location,
documentation language, retrieval route, and compact authority rules. The root
index contains only project-specific architectural context; completeness lives
in `specspine.json`.
General explanations of the SpecSpine framework remain in this documentation
and are not copied into either project artifact.

## Start or evolve intended architecture

Ask Evolve to initialize a small Spine:

```text
Create a SpecSpine for a SaaS application that lets teams manage customers,
subscriptions, and invoices.
```

Evolve creates the smallest useful initial architecture. Early specifications may
be intentionally short and preserve open questions.

Refine an area:

```text
Refine the authentication architecture.
```

Evolve follows existing links and proposes a split only after independent
responsibilities emerge. An overview may remain as a concise navigation point.

Apply a cross-cutting accepted change:

```text
Add Google Sign-In.
```

Evolve identifies the smallest justified create/modify set. It asks for a
decision only when the request does not establish required intent, canonical
ownership is genuinely ambiguous, or a conflict must be resolved.

By default, Evolve treats the user request and files under `<spine-root>` as the
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
- applicable normative claims and owned contracts;
- computed status, facets, and blockers;
- known divergences;
- relevant observations and inferences;
- blocking questions;
- omitted information and sources;
- one computed status with facets and blockers.

The machine-readable closure is deterministic. The Markdown handoff is a
temporary projection for a downstream feature, SDD, review, reconstruction, or
coding workflow. SpecSpine owns accepted durable requirements and reusable
black-box verification; downstream owns proposed deltas, temporary delivery
acceptance, planning, implementation, implementation-specific tests, and
delivery.

## Check a Spine

Ask Doctor:

```text
Check this SpecSpine for mechanical and semantic problems.
```

Doctor reports deterministic mechanical findings separately from advisory
semantic risks. Check is read-only. Repairs require approval and never
guess architectural intent. Repository drift analysis belongs to Map.

For a handoff-specific check, Doctor may invoke Extract directly. Extract is
the preferred downstream retrieval gateway, not a mandatory intermediary for
every Evolve, Map, or Doctor operation.
