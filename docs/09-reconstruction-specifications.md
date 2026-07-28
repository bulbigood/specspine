# Reconstruction specifications

SpecSpine targets independent, contract-equivalent reconstruction. It does not
promise reproduction of source text, private identifiers, incidental layout,
or undocumented implementation choices.

A reconstruction succeeds when it satisfies applicable `DEC`, `CON`, `REQ`,
`GUA`, `INV`, `QLT`, and `VER` claims; implements registered normative assets;
preserves required boundaries; passes independent conformance checks; and
invents no policy hidden behind a blocker.

`OBS` and `INF` may orient implementation but never establish conformance.

## Bundle

Markdown owns semantic meaning and navigation. `specspine.json` owns:

- allowed implementation freedom;
- one seven-facet profile per non-index owner;
- exact blocking `OQ-*` IDs;
- the complete non-Markdown asset registry.

Every asset has one Markdown owner and is linked from it. Implementation source,
build output, plans, delivery state, and implementation-specific tests remain
outside the bundle.

## Readiness

Status is derived:

- `blocked` if the selected area's blocker list is nonempty;
- `ready` if every facet is complete or reviewed as not applicable;
- `incomplete` otherwise.

`ready` is specification completeness, not current-code conformance.

## Promotion

An SDD owns a proposed delta. After acceptance:

1. move durable requirements and contracts to canonical owners;
2. preserve stable IDs or leave supersession tombstones;
3. register reusable exact assets and black-box verification;
4. leave tasks, status, and implementation-specific tests downstream;
5. update facets and blockers only when supported by accepted material;
6. run whole-Spine validation.

Repository mapping never performs promotion. Existing behavior becomes
normative only through explicit acceptance.

## Blind benchmark

1. Select a bounded `ready` vertical slice.
2. Give an isolated agent only its extracted closure and standard toolchains.
3. Implement in an empty workspace without original source access.
4. Run an independently held conformance suite.
5. Record every invented policy or contract as a specification gap.

Code similarity is not a metric. Contract, invariant, quality, architecture,
and verification conformance are.
