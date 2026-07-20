# Scenario: deepen a selected area

## Existing SpecSpine

```text
<spine-root>/
├── README.md
├── api-server.md
├── authentication.md
├── persistence.md
└── operations.md
```

`authentication.md` is currently a short high-level map.

## User request

```text
Map authentication deeply enough that another agent can add Google Sign-In.
```

## Expected behavior

The skill should:

- read the existing authentication specification and direct links;
- inspect authentication entry points, session creation, user identity,
  configuration, and representative tests;
- avoid reading unrelated project branches;
- identify observed facts, inferred boundaries, and blocking questions;
- propose new specification nodes only for independently useful concepts;
- prepare a map useful for implementation without writing code.

## Failure indicators

- all repository files are scanned indiscriminately;
- token-verification details become separate specifications;
- account-linking policy is invented;
- source code is modified;
- the specification becomes a function-by-function walkthrough.
