# Environment promotion

Environment promotion copies an approved integration definition between tenant environments while preserving reviewable provenance.

## Responsibility

It owns promotion packages, source revision, destination validation, connection remapping requirements, approval evidence, and result history.

## Boundaries

- Environment isolation belongs to [tenant environments](tenant-environments.md).
- Workflow revision ownership belongs to [workflow definitions](workflow-definitions.md).
- Runtime credentials remain with destination [connections](connections.md).

## Behavior

A package snapshots immutable definitions but references logical connection requirements rather than source secrets. Destination validation requires compatible connector versions, entitlements, schemas, and explicitly mapped connections. Applying promotion creates destination drafts; activation remains a separate authorized operation.

## Constraints

- Promotion cannot copy secret material or live execution state.
- Every applied artifact records its source environment and revision.


