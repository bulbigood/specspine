# SpecSpine bounded mapping method

Map one owner-relative semantic frontier without reproducing the source tree.

## Search from boundary to evidence

Start from the scoped owner or responsibility, then inspect only the strongest
signals needed to understand its boundary:

1. Existing SpecSpine intent and direct relationships.
2. Architecture documentation specific to the target.
3. Target manifests, runtime entry points, and composition roots.
4. Boundary interfaces, consumers, commands, events, and schedulers.
5. Owned schemas, migrations, and external contracts.
6. Deployment or runtime configuration affecting the boundary.
7. Representative integration and failure tests.
8. Local implementation required by one remaining boundary question.

Prefer evidence exposing responsibility, inputs, outputs, consumers, data
authority, controls, observable lifecycle, or boundary failures. Documentation
may be stale, directories incidental, and tests fixture-shaped.

Direct neighbor evidence may establish what crosses the target boundary. Once a
neighbor exposes an independently useful responsibility, record it as a
deferred lead and stop expanding it.

## Choose one target

A useful owner represents an independently evolving responsibility:

- a deployable runtime component;
- a domain or capability;
- persistence or contract ownership;
- a significant external integration;
- project-specific cross-cutting behavior.

Reject targets based only on generic layers, utilities, individual
classes/endpoints, framework wiring, generated code, or one-off scripts.

Ask:

1. Does it own a distinct responsibility?
2. Would an agent navigate here for a class of changes?
3. Does it have meaningful boundary inputs, outputs, state, failures, or
   consumers?
4. Can it evolve independently?
5. Is it more stable than the file layout?

If most answers are no, keep the evidence with the broader target. If two
independent owners are required, map one and defer the other.

## Apply the inspection intent

- `survey`: inspect a shallow initial boundary for one starting responsibility.
- `deepen`: begin with one owner and fill one selected repository-facing gap.
- `refresh`: recheck one owner against a newer evidence baseline.
- `drift`: inspect one suspected code/intent disagreement.

All intents close only the selected owner's immediate semantic frontier. They
never recurse into an adjacent responsibility or imply scope completeness.

## Classify evidence

Compare each significant fact with the target owner's accepted model:

- `covered-by-intent`: accepted intent already represents it; update inspection
  coverage without an `OBS`.
- `implementation-freedom`: it is a compatible implementation choice.
- `retain-observation`: it exposes a boundary-significant intent gap, unresolved
  question, or surprising owner/boundary.
- `retain-divergence`: it contradicts an addressable normative claim.
- `retain-inference`: it is a useful but unconfirmed boundary interpretation.
- `retain-open-question`: repository evidence cannot answer required intent or
  ownership.
- `implementation-detail`: it is private source detail.

Apply the replacement test before retaining anything:

> If a replacement behind the same boundary could change the fact without
> affecting a consumer, neighbor, operator, verifier, or explicit architecture
> constraint, discard it as implementation detail.

Lack of accepted intent does not turn internal code detail into a contract.
Repeated implementation does not establish accepted intent.

## Preserve evidence semantics

Use `spec-semantics.md` as the sole authority for observations, inferences,
questions, and disagreement. Repository evidence cannot answer what the system
should guarantee.

Cite a small representative set of complete repository-relative paths. Paths
prove or navigate to evidence; they do not define ownership or document
structure.

Do not retain a fact merely because it was inspected. Stop reading when the
target's responsibility, boundary interactions, data authority, controls,
observable lifecycle, and applicable failures are understood. Record exactly
which facets were inspected and leave the others `not-checked`.

## Bound the write

Change at most one content owner. Preserve every existing owner path and every
accepted relationship. For a new owner, apply the path and directory-density
rules in `spec-format.md`, but do not create sibling owners to make the map look
complete.

The final report may list adjacent responsibilities as deferred leads. Those
leads are navigation for a future Map invocation, not persistent delivery work
and not evidence that the current step failed.
