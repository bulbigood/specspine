# SpecSpine owner operations

This protocol is the single source of truth for selecting and applying
operations that change specification owners. Skills supply authority and claim
semantics; this protocol supplies owner mechanics.

## Action model

Every ordinary documentation-growth operation selects exactly one action:

- `refine` changes durable meaning or evidence owned by one existing document;
- `expand` creates exactly one independently useful adjacent owner.

Initialization and explicitly approved structural operations are separate
actions. They may affect more than one owner when their semantics require an
atomic graph rewrite.

Choose `refine` when the request names an existing owner facet, question, claim,
refresh boundary, or disagreement. Choose `expand` when the request explicitly
names a missing responsibility or the active skill is authorized to consume an
applicable persisted frontier lead. A skill must not interpret a discovery lead
as accepted architecture unless its authority permits that promotion.

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
- manifest areas match non-index documents;
- deterministic indexes were rebuilt;
- the whole-Spine checker passes.

Report the action, affected owners, structural primitives, changed
Spine-relative paths, checker result, and unresolved ownership questions.
