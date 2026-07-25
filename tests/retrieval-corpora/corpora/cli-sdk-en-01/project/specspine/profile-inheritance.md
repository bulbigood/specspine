# Profile inheritance

**ID:** `profile-inheritance` · **Kind:** `concept`

Owns the durable architectural concept `profile-inheritance`.

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

| Relation | Target | Meaning |
|---|---|---|
| `related-to` | [Configuration resolution](configuration-resolution.md) | Provides neighboring architectural context |
| `related-to` | [Telemetry](telemetry.md) | Provides neighboring architectural context |
