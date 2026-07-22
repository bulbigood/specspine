# Data mappings

Data mappings convert trigger, workflow, and prior-step values into schema-valid connector action inputs.

## Responsibility

They own typed field selection, renaming, defaults, structural projection, validation, and deterministic transformation expressions.

## Boundaries

- Source and target contracts belong to [connector triggers](connector-triggers.md) and [connector actions](connector-actions.md).
- Mapping attachment belongs to [workflow actions](workflow-actions.md).
- Runtime values and failures belong to [step executions](step-executions.md).

## Behavior

Publishing validates mappings against pinned source and destination schemas. Runtime evaluation is deterministic for the same captured inputs and produces either a valid action input or a classified mapping failure before external calls occur.

## Constraints

- Mapping expressions cannot perform network access, retrieve arbitrary secrets, or mutate workflow state.
- Sensitive values remain marked through transformation so history serialization can redact them.


