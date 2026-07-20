# Scenario: add a cross-cutting feature

## Initial state

```text
<spine-root>/
├── README.md
├── authentication.md
├── external-identity.md
├── session-management.md
├── users.md
└── configuration.md
```

## User request

```text
Add Google Sign-In.
```

## Expected behavior

The impact proposal should distinguish:

- the primary owner of external provider authentication;
- specifications whose behavior actually changes;
- related context that only needs to be read;
- unresolved account-linking policy.

The skill should avoid creating `google-sign-in.md` when Google is only one
provider inside the existing external identity concept.

A new `account-linking.md` should be proposed only when linking has independent
rules or several consumers.

## Failure indicators

- every discovered related specification is modified;
- token-validation details are split into several tiny files;
- account linking is silently decided;
- the skill proceeds with a structural change without approval.
