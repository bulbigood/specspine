# Scenario: split a broad specification

## Initial state

`authentication.md` contains password authentication, external providers,
session lifecycle, and account linking.

## User request

```text
The authentication specification is becoming hard to navigate. Restructure it.
```

## Expected behavior

The skill should propose a focused decomposition such as:

```text
authentication.md
password-authentication.md
external-identity.md
session-management.md
account-linking.md
```

The proposal should explain:

- the independent responsibility of each extracted concept;
- which content will move;
- which links will change;
- why `authentication.md` remains useful as an overview.

After approval, the skill should remove duplicated definitions and maintain
relative Markdown links.

## Failure indicators

- the skill creates many tiny files for local implementation details;
- `authentication.md` is deleted even though it remains a useful entry point;
- the same rule remains canonical in several files;
- unrelated architecture areas are restructured.
