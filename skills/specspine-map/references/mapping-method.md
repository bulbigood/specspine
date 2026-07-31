# SpecSpine incremental graph mapping

Map one semantic frontier without reproducing the source tree.

## Select refinement or expansion

`refine` adds material repository evidence about one existing owner.
`expand` turns one adjacent candidate responsibility into one new
observation-only owner.

Prefer `expand` for a generic continuation request when the current owner has a
durable frontier lead. Prefer `refine` only when the user names a facet,
question, suspected drift, or refresh boundary. The mere existence of an
existing owner must not cause every continuation to refine it.

During expansion, treat the frontier candidate as the write target. The owner
that exposed it is context, not the target.

## Search from boundary to evidence

Inspect only the strongest signals needed to understand the selected boundary:

1. Existing SpecSpine intent, mapping frontier, and observed edges.
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

Once evidence exposes another independently useful responsibility, add one
frontier entry and stop expanding it.

## Recognize an independent owner

A useful owner represents an independently evolving responsibility:

- a deployable runtime component;
- a domain or capability;
- persistence or contract ownership;
- a significant external integration;
- a reusable project-specific mechanism with its own boundary and lifecycle;
- project-specific cross-cutting behavior.

Reject candidates based only on generic layers, utilities, individual
classes/endpoints, framework wiring, generated code, or one-off scripts.

Ask:

1. Does it own a distinct responsibility?
2. Would an agent navigate here for a class of changes?
3. Does it have meaningful boundary inputs, outputs, state, failures, or
   consumers?
4. Can it evolve independently?
5. Is it more stable than the file layout?

If most answers are no, keep the evidence with the current owner. If yes,
persist it in `mapping.frontier`; do not bury it in the final response.

## Apply the inspection mode

- `survey`: create one starting owner and its immediate frontier.
- `deepen`: refine one named facet or expand one persisted frontier lead.
- `refresh`: recheck one owner against a newer evidence baseline.
- `drift`: inspect one suspected code/intent disagreement.

No mode recursively maps more than one owner or implies scope completeness.

## Classify evidence

Compare each significant fact with the selected owner's accepted model:

- `covered-by-intent`: accepted intent already represents it; update inspection
  coverage without an `OBS`.
- `implementation-freedom`: it is a compatible implementation choice.
- `retain-observation`: it exposes a boundary-significant gap, interaction,
  unresolved question, or surprising owner/boundary.
- `retain-divergence`: it contradicts an addressable normative claim.
- `retain-inference`: it is a useful but unconfirmed boundary interpretation.
- `retain-open-question`: repository evidence cannot answer required intent or
  ownership.
- `implementation-detail`: it is private source detail.
- `frontier-candidate`: it appears to own an independently useful adjacent
  boundary that a later Map step should inspect.

Apply the replacement test:

> If a replacement behind the same boundary could change the fact without
> affecting a consumer, neighbor, operator, verifier, or explicit architecture
> constraint, discard it as implementation detail.

Lack of accepted intent does not turn internal detail into a contract. Repeated
implementation does not establish accepted intent.

## Build the observed graph

Keep canonical `Relationships` reserved for accepted architecture. Represent
repository-discovered topology in `mapping.observed_edges`.

Each observed edge:

- connects two existing non-index owner IDs;
- points from `source_owner` to `target_owner` according to the interaction;
- references one `OBS` defined by either endpoint;
- derives its meaning and evidence exclusively from that `OBS`;
- is removed when its observation becomes stale or Evolve promotes its meaning
  into accepted architecture.

An expansion must create at least one observed edge connecting the new owner to
the already mapped graph. If no supported interaction exists, the candidate is
not ready to become a mapped owner.

## Preserve evidence semantics

Use `spec-semantics.md` as the sole authority for observations, inferences,
questions, and disagreement. Repository evidence cannot answer what the system
should guarantee.

Cite a small representative set of complete repository-relative paths. Paths
prove or navigate to evidence; they do not define ownership.

Stop reading when the selected responsibility, boundary interactions, data
authority, controls, lifecycle, and applicable failures are understood. Record
exactly which facets were inspected and leave the others `not-checked`.

## Bound the write

Change at most one content owner. Preserve every existing owner path and
accepted relationship. Apply the canonical path and directory-density rules
to a new owner.

Persist every concrete adjacent lead in the manifest. A lead is not persistent
delivery work and does not make the current step incomplete; it is the
deterministic starting point for the next expansion.
