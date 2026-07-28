# SpecSpine brownfield mapping method

Discover durable architecture without turning SpecSpine into a source-code
catalog. `SKILL.md` defines the scope and stopping point of one Map operation;
the format and semantics references define valid artifacts and claim authority.

## Contents

- [Discovery strategy](#discovery-strategy)
- [Evidence signals](#evidence-signals)
- [Choosing specification nodes](#choosing-specification-nodes)
- [Mapping modes](#mapping-modes)
- [Coverage and depth](#coverage-and-depth)
- [Evidence discipline](#evidence-discipline)
- [Search stopping signals](#search-stopping-signals)
- [Failure modes](#failure-modes)

## Discovery strategy

Start with system shape, then inspect internals only where boundaries remain
unclear. A useful sequence is:

1. Existing SpecSpine documents and repository architecture documentation.
2. Package, workspace, and build manifests.
3. Top-level directories.
4. Runtime entry points and composition roots.
5. Deployment, container, process, and runtime configuration.
6. Public interfaces, routes, consumers, schedulers, and commands.
7. Schemas, migrations, and owned contracts.
8. Representative integration or end-to-end tests.
9. Local implementation needed to resolve remaining architectural questions.

Adapt the order to the requested scope; this is not a checklist.

## Evidence signals

| Source | Usually reveals | Common misreading |
|---|---|---|
| Root documentation | Product purpose, named components, stated architecture | Documentation may be stale |
| Manifests and workspace configuration | Packages, executables, dependencies, technology choices | A package is not automatically an architectural boundary |
| Entry points and composition roots | Runtime components, dependency assembly, public adapters | Framework wiring may obscure the durable responsibility |
| Routes, consumers, schedulers, commands | Capabilities, external inputs, integrations, asynchronous behavior | A handler does not deserve its own specification |
| Schemas and migrations | Durable concepts, ownership clues, lifecycle constraints | A table is not automatically a subsystem |
| Integration and end-to-end tests | Significant behavior, failure cases, hidden contracts | Test structure may reflect fixtures rather than architecture |
| Deployment and operations files | Deployable units, external services, process relationships, scaling boundaries | Infrastructure layout may not express domain ownership |

Prefer sources that expose boundaries, ownership, runtime shape, or
cross-component behavior. Use local implementation only to answer a concrete
architectural uncertainty.

## Choosing specification nodes

Prefer durable architectural concepts such as:

- a deployable runtime component;
- a domain or capability boundary;
- a shared platform responsibility;
- persistence ownership;
- a significant integration;
- a cross-cutting concern with project-specific rules.

Avoid nodes based only on utility directories, generic framework layers,
individual classes or endpoints, generated code, trivial adapters, or one-off
scripts.

For a candidate node, ask:

1. Does it own a distinct responsibility?
2. Would an agent navigate to it for a class of changes?
3. Does it have meaningful boundaries, relationships, or decisions?
4. Can it evolve independently?
5. Is it more stable than the current file layout?

If most answers are no, describe it within a broader specification. Apply the
canonical decomposition and ownership rules from `spec-format.md` when writing
or restructuring files.

## Mapping modes

### Initial survey

Establish a small number of linked entry points covering major runtime,
capability, ownership, and data-flow boundaries. Keep each file concise. Follow
the organization rules and templates routed from `SKILL.md`; do not reproduce
the repository tree.

### Deepening a branch

Start from the existing specification and its direct relationships. Inspect
public entry points, representative behavior tests, owned schemas or contracts,
integration edges, and only then necessary local internals. Update the smallest
affected specification set. Split a node only under the canonical decomposition
rules.

### Refreshing after code changes

Start from affected specifications and the relevant diff or changed areas.
Update observations, preserve accepted intent, and record unresolved drift.
Refresh an evidence baseline only for observations actually rechecked against
the named source. Do not remap the whole repository for a local change.

## Coverage and depth

For exhaustive brownfield mapping, the mechanical inventory emits a flat list
of text production files. It terminally records structurally recognizable
vendored/generated trees, dependency locks, tests, repository support, and
opaque static assets; they remain retrievable evidence but do not independently
justify architecture owners. Tests remain useful evidence for behavior and
failures. Neutral pagination bounds planning-agent context without expressing
architecture. Fresh planning agents propose topics; one final synthesis pass
merges the complete candidate list, checks each topic against existing
canonical SpecSpine coverage, and assigns every production file before
`source-pass` creates producer ToDo only for uncovered topics.

Existing path references produce candidate owners, never terminal coverage.
Each synthesized topic remains open until a one-shot producer either publishes
the missing observation or proves coverage through concrete source evidence
and existing owner semantic IDs. Root must not replace semantic synthesis with
regex ownership, directory-name inference, a broad fallback owner, or prose
classification.

The inventory and its pages are discovery lower bounds, not architecture
models. One synthesized topic does not imply one document: several topics may
converge on one canonical owner, while one topic may expose several genuinely
independent responsibilities. A producer maps only its assigned question and
suggests narrower directions.
Map may deepen repository-observable uncertainty. Preserve questions about what
the system should guarantee verbatim; repository evidence cannot answer them.

Dispatch the frontier breadth-first. Establish repository runtime and
manifests, composition and command entry points, and distinct top-level runtime
families before leaf feature depth or repository tooling. Round-robin peer
families; do not let alphabetical path order make one large subtree define the
system skeleton.

Use the quality and compression criteria in `spec-format.md` as the depth gate.
The primary test is qualitative: ownership is accounted for, normal and
significant edge or failure behavior are understandable, relationships are
navigable, and the documentation adds non-local information without replaying
source. A summary-to-production-source ratio near `1:10` is only a campaign
diagnostic. Never pad prose to reach it or discard useful diagrams, contracts,
constraints, decisions, or questions to stay below it.

## Evidence discipline

Use `spec-semantics.md` as the sole definition of intent, evidence,
interpretation, and uncertainty. Repository repetition does not establish
accepted intent.

Cite only representative locations that support non-obvious claims or help
future navigation. Do not let paths become the main content; record them using
the syntax from `spec-format.md`.

## Search stopping signals

For a focused branch, stop expanding the evidence search when the relevant
production area is classified, the responsibility, boundary, significant
behavior, dependencies, edge and failure surfaces are known, and remaining
detail is local implementation or has low architectural value. A broad survey
does not stop until its directly exposed independent responsibilities are
classified into owners or child branches.

## Failure modes

- **Mirroring directories:** model responsibilities, capabilities, runtimes,
  ownership, and relationships instead.
- **Mapping too deeply too early:** establish system shape before subsystem
  internals.
- **Treating names as intent:** verify names through usage, tests, interfaces,
  and accepted documentation.
- **Canonizing technical debt:** record repository structure as observed unless
  its intended status is established.
- **Excessive path references:** use paths as evidence and navigation aids, not
  as the document structure.
- **Word-target writing:** use compression ratios only to diagnose suspicious
  undercoverage or source duplication, never to allocate prose.
- **Claiming completeness:** report qualitative remaining coverage and
  uncertainty.
