# SpecSpine examples

These examples demonstrate the expected behavior of `specspine-grow`.

They are behavioral examples, not rigid output requirements.

## Contents

- [Initialize from an abstract idea](#example-1-initialize-from-an-abstract-idea)
- [Refine an existing area](#example-2-refine-an-existing-area)
- [Add a cross-cutting feature](#example-3-add-a-cross-cutting-feature)
- [Avoid duplication](#example-4-avoid-duplication)
- [Preserve uncertainty](#example-5-preserve-uncertainty)
- [Prepare a context handoff](#example-6-prepare-an-architecture-context-handoff)

## Example 1: Initialize from an abstract idea

### User request

```text
Create a SpecSpine for a small SaaS application that lets teams
manage customers, subscriptions, and invoices.
```

### Reasonable initial structure

```text
<spine-root>/
├── README.md
├── application.md
├── identity.md
├── billing.md
└── operations.md
```

The initial files should remain short. Unknown product and architecture
decisions belong in `Open questions`.

Avoid prematurely creating files for every anticipated endpoint, table, or UI
screen.

## Example 2: Refine an existing area

### Existing structure

```text
<spine-root>/
├── README.md
├── authentication.md
└── users.md
```

### User request

```text
Refine authentication. We need passwords, Google Sign-In,
refreshable sessions, and account linking.
```

### Proposed impact

```text
Affected specifications

Create:
- <spine-root>/password-authentication.md
- <spine-root>/external-identity.md
- <spine-root>/session-management.md
- <spine-root>/account-linking.md

Modify:
- <spine-root>/authentication.md
- <spine-root>/users.md
- <spine-root>/README.md

Reason:
Authentication now contains several independently evolving
responsibilities. The original authentication specification should
become an overview and navigation point.

Open decisions:
- Should matching verified email addresses trigger automatic linking?
- Can users unlink their last authentication method?

Proceed with these specification changes?
```

### Expected result

`authentication.md` remains concise and links to the extracted concepts.

The detailed account-linking policy exists only in `account-linking.md`.

## Example 3: Add a cross-cutting feature

### User request

```text
Add Google Sign-In.
```

### Existing concepts

```text
authentication.md
external-identity.md
session-management.md
users.md
configuration.md
```

### Good behavior

The skill should:

- identify `external-identity.md` as the primary specification;
- update session creation only if its contract changes;
- update configuration requirements;
- update user-account linking rules;
- avoid creating `google-sign-in.md` when Google is merely one provider inside
  a general external identity concept;
- propose `account-linking.md` only if account linking has independent rules.

### Bad behavior

Do not create one file for every token check:

```text
google-token-signature.md
google-token-audience.md
google-token-expiry.md
google-token-issuer.md
```

Those details belong in the broader external identity specification unless they
become independently important.

## Example 4: Avoid duplication

### Existing content

`authentication.md`:

```text
Refresh tokens rotate after successful use.
```

`session-management.md`:

```text
Refresh tokens rotate after successful use.
```

### Expected change

Keep the full rule in `session-management.md`.

Replace the duplicate in `authentication.md` with:

```markdown
Session creation and refresh behavior are defined by
[Session management](session-management.md).
```

## Example 5: Preserve uncertainty

### User request

```text
Add enterprise SSO.
```

### Missing decision

The project does not define whether users are provisioned automatically or
must exist before first login.

### Good result

```markdown
## Open questions

- Should enterprise users be provisioned on first successful login,
  or must an administrator create them in advance?
```

### Bad result

Do not silently choose just-in-time provisioning and record it as an accepted
decision.

## Example 6: Prepare an architecture context handoff

### User request

```text
Prepare an architecture context handoff for adding Google Sign-In.
```

### Expected response

```text
Change intent:
- add external authentication without changing application-session semantics

Primary specification:
- external-identity.md

Required specifications:
- authentication.md
- account-linking.md
- session-management.md

Potentially affected specifications:
- users.md
- configuration.md

Architectural decisions and constraints:
- application sessions are provider-independent;
- external provider access tokens are not stored;
- account-linking rules belong to account-linking.md.

Blocking questions:
- Should verified email matches trigger automatic account linking?

Expected architectural outcome:
- A verified Google identity establishes a local user identity and then
  creates a normal application session without changing session semantics.
```

The handoff should be minimal. Do not include unrelated specification branches,
acceptance criteria, implementation tasks, or implementation status.
