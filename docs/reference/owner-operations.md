# SpecSpine owner operations

This protocol is the single source of truth for selecting and applying
operations that change specification owners. Skills supply authority and claim
semantics; this protocol supplies owner mechanics.

## Action model

Every ordinary documentation-growth operation selects one action:

- `refine` changes durable meaning or evidence owned by one existing document;
- `expand` creates one independently useful adjacent owner;
- `decompose-layer` expands every selected frontier owner by exactly one
  immediate layer and publishes the complete sibling set atomically.

Initialization and explicitly approved structural operations are separate
actions. They may affect more than one owner when their semantics require an
atomic graph rewrite.

Choose `refine` when the request names an existing owner facet, question, claim,
refresh boundary, or disagreement. Choose `expand` when the request explicitly
names a missing responsibility or the active skill is authorized to consume an
applicable persisted frontier lead. Choose `decompose-layer` for “deepen”,
“decompose”, “cover the next level”, or an equivalent request. A skill must not
interpret a discovery lead as accepted architecture unless its authority
permits that promotion.

## Owner test

Create an owner only for a stable, independently evolving responsibility. It
should have meaningful boundary inputs, outputs, consumers, state, authority,
controls, lifecycle, failures, or constraints and should be more stable than
the repository layout.

Do not create an owner merely for a directory, layer, class, endpoint, utility,
framework adapter, generated artifact, delivery phase, or long document.

Reuse an existing owner when the requested meaning fits its responsibility.
Use `expand`, `split`, or another structural primitive only when independent
ownership improves addressability without reproducing implementation layout.

## Refine

1. Select exactly one write owner.
2. Treat related owners needed only for understanding as read-only.
3. Apply the smallest coherent owner-local change authorized by the active
   skill.
4. Preserve identity, path, unrelated meaning, relationships, assets, and
   completeness unless the request and skill authority explicitly change them.
5. Do not create a document as a side effect of refinement.

## Expand

1. Select one adjacent responsibility and its existing context owner.
2. Confirm that the candidate passes the owner test and is not already owned.
3. Choose a stable globally unique ID, concise title, kind, and semantic path.
4. Start from the active skill's specification template.
5. Create exactly one content document and exactly one manifest area.
6. Connect it to the existing graph using the edge representation authorized
   by the active skill.
7. Apply the canonical directory-density rules before finalizing its path.
8. Rebuild deterministic indexes; never edit `_INDEX.md` manually.

If evidence or accepted intent does not establish an independently useful
boundary, do not create the owner. Disposition any selected frontier according
to the active skill's authority.

## Decompose one layer

`decompose-layer` bounds depth, not width. It may create many sibling owners,
but MUST NOT recursively decompose any owner created by the operation.

1. Resolve the owners responsible for the requested scope.
2. Select every resolved owner whose immediate decomposition remains
   `frontier`. Exclude an `expanded` overview and a reviewed `terminal` owner.
3. Discover the complete immediate child set for every selected parent.
   Children collectively explain how the parent responsibility is divided;
   dependencies and consumers are neighbors unless they own part of that
   responsibility.
4. Compare all proposed siblings globally before writing. Keep peers separate
   when inputs, outputs, consumers, state, controls, lifecycle, failures, or
   reasons to change differ. Merge only when one boundary contract genuinely
   owns them. Never create children for private stages, facets, classes,
   functions, directories, or shared framework machinery.
5. Reuse existing owners before creating files. Create and fill every missing
   immediate child, then connect the complete layer using the edge authority of
   the active skill.
6. Mark each parent `expanded`. Mark each new or reviewed child `frontier` when
   it has a plausible next owner layer, otherwise `terminal`. Record a concise
   reason for every decomposition status.
7. Rebuild indexes and validate the whole Spine once after the coherent batch.

An overview owner is `expanded` when it owns cross-child coordination or
explains the combined boundary and delegates local contracts to children.
Pure physical navigation belongs in `_INDEX.md`, not an empty overview.

A `terminal` owner has no independently useful child boundary: further detail
would be private algorithms, helpers, framework hooks, internal state, or
source layout. Terminal is a reviewed stopping judgment, not a claim that the
owner can never evolve.

Draft documents MAY be created in disposable staging to establish identities
and links before parallel filling. Empty drafts MUST NOT enter the canonical
Spine. Publish the whole layer only after every draft is filled and the global
sibling review is clean. If the layer cannot be completed, leave the canonical
Spine unchanged and report the blocker.

## Structural primitives

Structural operations use only these primitives:

- `create`: add one new owner as defined by `expand`;
- `split`: replace part of one owner's meaning with one or more independently
  addressable owners;
- `merge`: consolidate owners whose responsibilities are no longer independent;
- `move`: change document path without changing identity;
- `rename`: change human-facing naming while preserving identity unless the
  accepted concept itself is replaced;
- `link`: add navigation, a semantic reference, or one directed typed edge;
- `remove`: delete an owner only when its meaning is obsolete, merged, or
  preserved by an explicit successor.

For every structural operation:

1. Resolve all affected owners before writing.
2. Preserve stable document and statement IDs; use tombstones and successors
   where the canonical format requires them.
3. Move owned claims and registered assets with their canonical meaning.
4. Rewrite affected relative links and relationships once.
5. Preserve root reachability and nested-Spine boundaries.
6. Rebuild all affected deterministic indexes.
7. Validate the whole Spine after one coherent batch.

An active skill may authorize only a subset of these primitives. Lack of
authority is a hard stop, not permission to approximate the operation.

## Verification

Review the complete diff and confirm:

- the selected action and write owners match;
- no unrelated owner changed;
- each semantic claim and asset still has one canonical owner;
- new IDs and paths are stable, unique, and reachable;
- edge representation matches the active skill's authority;
- every touched area has a justified decomposition status;
- a layer operation published all immediate siblings or none;
- manifest areas match non-index documents;
- deterministic indexes were rebuilt;
- the whole-Spine checker passes.

Report the action, affected owners, structural primitives, changed
Spine-relative paths, checker result, and unresolved ownership questions.
