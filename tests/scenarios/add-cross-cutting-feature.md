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
Add Google Sign-In to the existing external-provider authentication
responsibility. Keep provider-independent session and runtime-configuration
architecture unchanged. Preserve account linking as unresolved.
```

## Expected behavior

The impact proposal should distinguish:

- the primary owner of external provider authentication;
- specifications whose behavior actually changes;
- related context that usually only needs to be read, while allowing one
  meaning-preserving relationship or navigation update when useful;
- unresolved account-linking policy.

The skill should avoid creating `google-sign-in.md` when Google is only one
provider inside the existing external identity concept.

A new `account-linking.md` should be proposed only when linking has independent
rules or several consumers.

## Failure indicators

- every discovered related specification is modified;
- token-validation details are split into several tiny files;
- account linking is silently decided;
- the skill resolves ambiguous ownership or account-linking policy without a
  user decision.
