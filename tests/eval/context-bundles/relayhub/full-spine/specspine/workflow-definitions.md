# Workflow definitions

Workflow definitions are tenant-owned, versioned integration programs that connect triggers to ordered or branching actions.

## Responsibility

They own workflow identity, editable draft, immutable published revisions, graph validation, referenced connector versions, and activation state.

## Boundaries

- Entry conditions belong to [workflow triggers](workflow-triggers.md).
- Step configuration belongs to [workflow actions](workflow-actions.md).
- Runtime state belongs to [workflow executions](workflow-executions.md).
- Environment placement belongs to [tenant environments](tenant-environments.md).

## Lifecycle

A workflow is draft, active, paused, or archived. Publishing creates an immutable revision after validating graph reachability, schemas, connection references, and entitlement. Existing executions retain their captured revision when a later draft is published.

## Constraints

- Every execution references one immutable workflow revision.
- A workflow cannot reference connections from another organization or environment.


