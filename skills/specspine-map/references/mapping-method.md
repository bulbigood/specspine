# SpecSpine brownfield mapping method

Discover durable architecture without reproducing the source tree.

## Search from shape to detail

Read only enough evidence to resolve architectural boundaries:

1. Existing SpecSpine and repository architecture documentation.
2. Workspace, build, and package manifests.
3. Runtime entry points and composition roots.
4. Deployment and runtime configuration.
5. Public interfaces, consumers, schedulers, and commands.
6. Owned schemas, migrations, and contracts.
7. Representative integration and failure tests.
8. Local implementation required by a remaining architectural question.

Prefer sources that expose ownership, runtime shape, interfaces, state,
lifecycle, cross-component behavior, or failure handling. Documentation may be
stale; package and directory boundaries may be incidental; test structure may
reflect fixtures.

## Choose semantic topics

Prefer independently evolving responsibilities:

- deployable runtime components;
- domain or capability ownership;
- persistence and contract ownership;
- significant external integrations;
- project-specific cross-cutting behavior.

Reject topics based only on generic layers, utilities, individual
classes/endpoints, framework wiring, generated code, or one-off scripts.

For each candidate ask:

1. Does it own a distinct responsibility?
2. Would an agent navigate here for a class of changes?
3. Does it have meaningful boundaries, relationships, state, or decisions?
4. Can it evolve independently?
5. Is it more stable than the file layout?

If most answers are no, merge it into a broader owner. Apply the canonical
decomposition rules from `spec-format.md`.

## Apply the operation policy

For `survey`, establish a small linked skeleton of major runtime, capability,
ownership, and data-flow boundaries. For `deepen`, start from an existing owner
and its direct relationships. For `refresh` or `drift`, inspect only affected
specifications and source areas, preserve accepted intent, and record
unresolved disagreement.

An increment settles one initial discovery layer and defers directly exposed
continuations. Exhaustive work expands every in-scope lead by one semantic
level until the frontier closes. A flat file inventory may seed repository
scope but never defines topics.

Each scout proposes only directly exposed child questions. Synthesis merges
the complete corpus by responsibility, checks each topic against existing
canonical SpecSpine claims, and accounts for every evidence file. A path match,
navigation entry, or broad neighboring owner is not coverage.

One topic does not imply one document. Several topics may converge on one
canonical owner; one topic may expose multiple independent owners. Producers
verify assigned topics and may suggest narrower questions, but root decides
final ownership.

Dispatch source topics breadth-first: establish runtimes, manifests,
composition, command entry points, and peer families before leaf depth. Do not
let alphabetical path order or one large subtree define the system skeleton.

## Preserve evidence semantics

Use `spec-semantics.md` as the sole authority for observation, intent,
interpretation, and uncertainty. Repetition in code does not establish accepted
intent. Preserve normative questions verbatim; repository evidence cannot
answer what the system should guarantee.

Cite representative concrete paths that support non-obvious claims or future
navigation. Paths are evidence, not document structure. Stop reading when
ownership, boundaries, significant behavior, dependencies, state, and failure
surfaces are understood and further detail would reproduce implementation.

Use the compression criteria in `spec-format.md` qualitatively. Documentation
must add non-local information and remain sufficient for reconstruction; never
pad prose to meet a word or source ratio.
