# SpecSpine one-layer repository mapping

Map the complete immediate owner layer without reproducing the source tree.

## Find the layer

Start from the canonical owners responsible for the requested scope. A parent
is frontier when its immediate responsibility decomposition is unreviewed or
known but unpublished. Existing `mapping.frontier` entries seed discovery; they
do not limit it.

Search boundary-first:

1. Existing intent, observations, decomposition status, and mapping graph.
2. Target architecture documentation, manifests, and composition roots.
3. Boundary interfaces, inputs, outputs, consumers, controls, and owned data.
4. Observable lifecycle, failures, compatibility, and representative tests.
5. Local implementation needed to resolve one boundary question.

Discover all immediate children before deeply documenting any one child. Stop
at grandchildren except for the shallow terminal/frontier judgment.

## Distinguish children from neighbors

A child owns a stable part of the parent's responsibility. A dependency,
consumer, external integration, or shared mechanism is a neighbor unless the
parent explicitly delegates part of its outcome to it.

A useful child has a distinct responsibility, boundary contract, navigation
value, and reason to change. Reject source directories, layers, individual
classes/functions, generic adapters, private stages, and facets.

Compare every sibling pair. Keep peers separate when input model,
configuration, state, lifecycle, failures, consumers, or change drivers differ.
A shared registry, builder, renderer, host, framework, package, or helper is
not shared ownership. Conversely, keep configuration, failure, interfaces,
tests, and private stages with one owner when they describe facets of the same
contract.

The siblings should collectively explain the parent's delegated
responsibility without duplicating neighboring ownership.

## Apply the replacement test

Retain a fact only when a replacement behind the same owner boundary would
still be constrained by it or when it supplies evidence for an observed edge,
uncertainty, or divergence. Otherwise classify it as implementation detail.

Repository evidence cannot establish accepted intent. Lack of accepted intent
does not make private mechanics a contract.

## Classify decomposition depth

- `frontier`: a plausible independently useful child layer remains.
- `expanded`: the complete immediate child layer is published; overview
  coordination may remain in the parent.
- `terminal`: further division yields only private mechanics or source shape.

An overview is useful only when it owns cross-child coordination or explains
their combined boundary. Pure navigation belongs in `_INDEX.md`.

## Publish atomically

Draft identities and links in disposable staging if useful. Fill every
immediate child before publication. Empty placeholders never enter canonical
Markdown. If context, evidence, or ownership uncertainty prevents completion
of the whole sibling set, publish none of the layer.

Preserve every existing owner path. Apply the canonical path and
directory-density rules only to new child owners; Map never reorganizes
accepted topology.

Persist only:

- material `OBS`, `INF`, `OQ`, or divergence;
- OBS-backed observed edges;
- next-layer frontier candidates;
- accurate inspection and decomposition state;
- bounded implementation navigation anchors.

One invocation advances selected scope depth by exactly one owner layer,
regardless of sibling count.
