# SpecSpine brownfield mapping method

Discover durable architecture without reproducing the source tree.

## Search from shape to detail

Read only enough evidence to resolve owner-relative boundary contracts:

1. Existing SpecSpine and repository architecture documentation.
2. Workspace, build, and package manifests.
3. Runtime entry points and composition roots.
4. Deployment and runtime configuration.
5. Public interfaces, consumers, schedulers, and commands.
6. Owned schemas, migrations, and contracts.
7. Representative integration and failure tests.
8. Local implementation required by a remaining architectural question.

Prefer sources that expose ownership, boundary inputs and outputs, consumers,
data authority, controls, observable lifecycle, or boundary failures. Documentation may be
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
3. Does it have meaningful inputs, outputs, consumers, data authority,
   lifecycle, failures, or relationships?
4. Can it evolve independently?
5. Is it more stable than the file layout?

If most answers are no, merge it into a broader owner. Apply the canonical
decomposition rules from `spec-format.md`.

## Apply the operation policy

For `survey`, establish a linked skeleton of durable owners and their
interaction boundaries. For `deepen`, start from one existing
owner, its manifest facets, and direct relationships; investigate its partial
or missing boundary behavior, interfaces, data, and failure
surfaces without widening into a general survey. For `refresh` or `drift`,
inspect only affected specifications and source areas, preserve accepted
intent, and record unresolved disagreement.

An increment settles one initial discovery layer and defers directly exposed
continuations. An exhaustive scout recursively closes its assigned semantic
search boundary inside one run. Every scope begins with a semantic plan;
whole-repository mapping is merely the widest search boundary, never file
pagination.

An exhaustive scout returns an unresolved question only when it needs an
independent large investigation, exceeds safe context, or crosses into a
separately owned boundary. Curate and dispatch those questions as targeted
fallback, not as mandatory breadth-first levels. Synthesis merges the complete
corpus by responsibility, checks each topic against existing canonical
SpecSpine claims, and accounts for every evidence file. A path match,
navigation entry, or broad neighboring owner is not coverage.

Compare each significant repository fact with its owner's accepted model:
`covered-by-intent`, `implementation-freedom`, `retain-observation`,
`retain-divergence` (only against an addressable normative claim),
`retain-inference`, `retain-open-question`, or `implementation-detail`. Only
the retain dispositions produce Markdown evidence. Apply the replacement test
before retaining anything: if a replacement behind the same boundary could
change the fact without affecting a consumer, neighbor, operator, verifier, or
explicit architecture constraint, classify it as `implementation-detail`.
`covered-by-intent` updates bounded inspection coverage and never asserts
conformance. Lack of accepted intent does not turn internal code detail into a
candidate contract.

One topic does not imply one document. Several topics may converge on one
canonical owner; one topic may expose multiple independent owners. Producers
verify assigned topics and may suggest narrower questions, but root decides
final ownership.

Within each exhaustive packet, establish runtimes, manifests, composition,
command entry points, and peer families before local detail. Do not let
alphabetical path order or one large subtree define the system skeleton.

## Preserve evidence semantics

Use `spec-semantics.md` as the sole authority for observation, intent,
interpretation, and uncertainty. Repetition in code does not establish accepted
intent. Preserve normative questions verbatim; repository evidence cannot
answer what the system should guarantee.

Cite a small set of representative paths that proves a boundary claim or
provides future navigation. Paths are evidence, not document structure. Stop
reading when responsibility, boundary interactions, data authority, controls,
observable lifecycle, and failures are understood. Never continue merely to
document how the owner works internally.

Do not write a repository fact as `Observed` merely because it was inspected.
If accepted intent already fully represents it, preserve the intent, record the
inspected facets in `specspine.json`, and omit the duplicate fact.

Use the compression criteria in `spec-format.md` qualitatively. Documentation
must add non-local information and remain sufficient for reconstruction; never
pad prose to meet a word or source ratio.
