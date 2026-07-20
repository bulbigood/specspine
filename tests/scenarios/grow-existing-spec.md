# Scenario: grow an existing specification

## Initial state

```text
<spine-root>/
├── README.md
├── authentication.md
└── users.md
```

`authentication.md` briefly describes password-based login and application
sessions.

## User request

```text
Refine authentication. Add refreshable sessions and the ability to revoke
all sessions for a user.
```

## Expected behavior

The skill should:

- read the architecture index first;
- determine whether session management now deserves its own specification;
- show an impact proposal before a structural split;
- keep authentication as an overview if a split is accepted;
- place session-specific behavior in one canonical file;
- preserve unresolved security decisions as open questions;
- avoid changing source code.

## Failure indicators

- session behavior is duplicated across several files;
- the split is based only on file length;
- the agent invents token formats or storage technologies;
- unrelated specifications are rewritten.
