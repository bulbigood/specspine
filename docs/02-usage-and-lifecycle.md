# Usage and lifecycle

## Tool-independent use

Every committed Spine is readable without SpecSpine skills. Start at the
`<spine-root>` directory, read `README.md`, then follow `_INDEX.md` contents to
the canonical owner for the task,
then inspect its accepted claims, boundaries, relationships, blockers, and
known divergences. `specspine.json` carries completeness and machine-readable
assets.

Project instructions should contain only the root directory, documentation
language, optional retrieval route, and compact authority rules. General
framework documentation belongs in the root `README.md` and this documentation,
not in every-agent instructions.

## Runtime skills

- `specspine-doctor` connects a Spine and checks or repairs its health.
- `specspine-extract` retrieves a minimal task-specific closure.
- `specspine-evolve` creates or changes accepted durable intent.
- `specspine-map` compares repository evidence with accepted intent.
- `specspine-verify` assesses implementation or reconstruction conformance.

Skills are optional interfaces to the format. Their disposable state belongs
under the ignored workspace-local `.specspine/<skill>` directory.

## Connect

Install the recommended downstream pair:

```bash
npx skills add bulbigood/specspine --skill specspine-doctor
npx skills add bulbigood/specspine --skill specspine-extract
```

Ask Doctor:

```text
Expose this project's SpecSpine to agents through persistent project instructions.
```

Doctor creates missing root `README.md`, `_INDEX.md`, and `specspine.json`
files, installs one bounded managed block containing the root directory in the
selected project instruction file, and runs the mechanical checker. It does
not overwrite an existing root or create concept
specifications.

## Evolve accepted intent

Use Evolve to create a small intended architecture, refine an owner, or apply
an accepted durable change. Evolve treats the request and existing Spine as the
project-specific authorities. It does not inspect source code by default and
does not infer acceptance from existing implementation.

Developers update SpecSpine when a change alters an owner responsibility,
boundary input or output, control, data authority, relationship, observable
failure, compatibility promise, quality constraint, or explicit architecture
constraint. Refactoring private mechanisms behind an unchanged contract needs
no SpecSpine edit. Reviewers discuss contracts and ownership in the Spine and
implementation choices in code review.

An SDD or other authorized workflow owns a proposed delta until acceptance.
Promote its durable requirements, guarantees, invariants, relationships, and
reusable verification into canonical owners before or with implementation.
Implementation-only changes do not require artificial specification growth.

## Compare a repository

Use Map for one bounded owner-relative repository comparison. Each request
either refines one existing owner or expands one adjacent frontier candidate.

Map discovers owner-relative boundaries rather than documenting code structure.
It compares evidence with accepted intent and retains an `OBS` only when it:

- exposes a boundary-significant intent gap;
- supports a confirmed divergence;
- affects an unresolved architectural question; or
- provides necessary navigation to a surprising owner or boundary.

Map omits evidence already represented by intent and compatible implementation
freedom. It records bounded inspection coverage separately instead of creating
a duplicate observation. Neither inspection coverage nor absence of `OBS`
proves conformance.

Repository-wide documentation grows through repeated one-step Map operations.
Adjacent owner candidates persist in ordered `specspine.json.mapping.frontier`.
Each expansion consumes at most one candidate and may append later candidates
without pursuing them. Mapped owners connect through OBS-backed
`mapping.observed_edges`, which remain distinct from accepted typed
`Relationships`.

Evolve uses the same `refine` and `expand` owner operations, but requires
explicit accepted intent before creating a canonical owner or relationship.
Map frontier alone is never architectural approval.

For AI agents, the Spine answers what must remain true and who owns it. Source
inspection answers how the current implementation achieves it. An agent must
not treat missing internal detail as a documentation gap or expand a contract
into a source walkthrough.

## Retrieve task context

Extract returns the primary owner, required neighbors, applicable accepted
claims and assets, completeness and blockers, known divergences, relevant
exception evidence, unresolved questions, and explicit omissions. Its Markdown
handoff is a disposable projection; canonical meaning remains in the Spine.

When Extract is unavailable, follow `_INDEX.md` and typed relationships
directly.

## Check and verify

Doctor separates deterministic mechanical findings from advisory semantic
risks. Repairs require authorization and never manufacture intent. Repository
comparison belongs to Map.

Verify assesses current implementation or blind reconstruction against the
selected normative closure and registered verification surface. It may report
conformance or gaps, but it does not create intent or delivery state.

Exact installation options and natural-language operation contracts live with
the individual skills. The storage and semantic rules remain
tool-independent.
