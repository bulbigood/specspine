# SpecSpine incremental graph mapping

Map one semantic frontier without reproducing the source tree.

## Select refinement or expansion

`refine` adds material repository evidence about one existing owner. `expand`
turns one adjacent candidate into one observation-only owner.

Prefer `expand` for a generic continuation when the current owner has a durable
frontier lead. Prefer `refine` when the user names a facet, question, suspected
drift, or refresh boundary. An existing owner must not cause every continuation
to refine it.

During expansion, the candidate is the write target. Its `anchor_owner` is
context, not the target.

## Search boundary-first

Inspect only the strongest signals needed:

1. Existing intent, mapping frontier, and observed edges.
2. Architecture documentation specific to the target.
3. Target manifests, runtime entry points, and composition roots.
4. Boundary interfaces, consumers, commands, events, and schedulers.
5. Owned schemas, migrations, and external contracts.
6. Configuration affecting the boundary.
7. Representative integration and failure tests.
8. Local implementation required by one remaining boundary question.

Stop when the selected boundary is classifiable. When evidence exposes another
independently useful responsibility, persist a frontier lead and do not pursue
it.

## Recognize an independent owner

A useful owner represents an independently evolving responsibility: a runtime
component, capability, persistence or contract authority, external integration,
project-specific mechanism, or cross-cutting behavior.

Reject generic layers, utilities, individual classes/endpoints, framework
wiring, generated code, and one-off scripts. Ask whether it has a distinct
responsibility, meaningful boundary, navigation value, independent lifecycle,
and greater stability than the file layout.

An adjacent candidate need not be a child. Dependencies, consumers, peers,
integrations, and shared authorities are valid graph growth when independently
useful.

## Classify evidence

- `covered-by-intent`: accepted intent already represents it.
- `implementation-freedom`: compatible private implementation choice.
- `retain-observation`: material gap, interaction, question, or surprising
  boundary.
- `retain-divergence`: conflict with an addressable normative claim.
- `retain-inference`: useful but unconfirmed boundary interpretation.
- `retain-open-question`: evidence cannot answer required intent or ownership.
- `implementation-detail`: private source detail.
- `frontier-candidate`: independently useful adjacent responsibility.

Apply the replacement test:

> If a replacement behind the same boundary could change the fact without
> affecting a consumer, neighbor, operator, verifier, or explicit architecture
> constraint, discard it as implementation detail.

## Build the observed graph

Keep canonical `Relationships` reserved for accepted architecture. Each
`mapping.observed_edges` entry:

- connects two existing non-index owner IDs;
- follows the direction stated by its interaction;
- references one `OBS` defined by either endpoint;
- derives meaning and evidence from that `OBS`;
- is removed when stale or promoted by Evolve.

An expansion must add at least one supported observed edge connecting the new
owner to the mapped graph.

## Bound the operation

Change at most one content owner. Preserve every existing owner path and
accepted relationship. Apply canonical path and directory-density rules only
to a new owner.

Frontier leads are hypotheses and deterministic starting points, not coverage,
accepted topology, or delivery work. A missing seed path makes a lead stale; it
does not invalidate unrelated Spine content. Refresh or disposition that lead
when selected.
