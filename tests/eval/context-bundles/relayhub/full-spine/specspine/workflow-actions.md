# Workflow actions

Workflow actions describe the durable step graph within a published workflow revision.

## Responsibility

They own step identity, connector action reference, connection binding, input mapping, dependencies, conditional execution, and declared output name.

## Boundaries

- Connector operation contracts belong to [connector actions](connector-actions.md).
- Transformation semantics belong to [data mappings](data-mappings.md).
- Runtime attempts belong to [step executions](step-executions.md).

## Behavior

Publishing validates that dependencies form an executable acyclic graph, required inputs can be produced, and all referenced capabilities are available in the target environment. Conditions may skip a step but cannot mutate the immutable revision.

## Constraints

- Secrets are referenced through connections and never embedded in workflow revisions.
- Step outputs are addressable only within the execution of their owning workflow revision.


