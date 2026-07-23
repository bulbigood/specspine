# Profile inheritance

## Responsibility

Named profiles compose reusable groups of non-secret settings.

## Rules

A profile may extend one parent. Parent fields are copied first and child
fields override them. Cycles and missing parents are configuration errors.
Profile inheritance does not determine whether flags, environment variables,
or files win; source precedence belongs to configuration resolution.

The word profile also appears in performance profiling and telemetry
discussions, but those usages do not define named configuration profiles.

## Relationships

- [Configuration resolution](configuration-resolution.md)
- [Telemetry](telemetry.md)
