# SpecSpine Map examples

These examples demonstrate expected behavior for brownfield mapping.

They are examples of judgment, not rigid output formats.

## Example 1: Initial repository survey

### Repository signals

```text
apps/web/
apps/api/
apps/worker/
packages/database/
packages/document-processing/
docker-compose.yml
README.md
```

### User request

```text
Create a SpecSpine for this existing project.
```

### Good mapping proposal

```text
Mapping proposal

Create:
- specs/README.md
- specs/web-application.md
- specs/api-server.md
- specs/background-processing.md
- specs/document-processing.md
- specs/persistence.md

Evidence inspected:
- root README
- workspace manifest
- API and worker entry points
- Docker Compose services
- database package
- representative processing tests

Inferred structure:
- API and worker are separate runtime components.
- Document processing is shared application behavior used by both.

Unresolved:
- Search indexing may be part of document processing or a separate capability.

Proceed with these specification changes?
```

### Bad mapping

```text
specs/apps.md
specs/packages.md
specs/controllers.md
specs/repositories.md
specs/utils.md
```

This mirrors source layout without identifying useful responsibilities.

## Example 2: Observed versus inferred

### Repository evidence

- `apps/api/src/main.ts` starts an HTTP server.
- `apps/worker/src/main.ts` starts a queue consumer.
- Both import `packages/database`.
- Deployment configuration declares separate API and worker processes.

### Good specification

```markdown
## Observed

- The API and worker have separate runtime entry points.
- Both use the shared database package.
- Deployment configuration starts them as separate processes.

## Inferred

- API serving and background work are intended as independently scalable
  runtime components.
```

### Bad specification

```markdown
## Decisions

- API and workers must always be deployed and scaled independently.
```

The repository supports an inference, not necessarily an accepted invariant.

## Example 3: Deepen authentication

### User request

```text
Map authentication deeply enough that another agent can add Google Sign-In.
```

### Expected inspection

The skill should prioritize:

- authentication entry points;
- session creation;
- user identity model;
- existing provider abstractions;
- account lookup and linking behavior;
- configuration;
- representative authentication tests.

It should not read unrelated billing or reporting internals.

### Reasonable output

```text
Primary:
- authentication.md

Create:
- external-identity.md
- session-management.md
- account-linking.md

Modify:
- users.md
- configuration.md

Observed:
- Password login and session creation are currently coupled in one module.
- Session tokens are provider-independent after creation.
- No external identity table exists.

Inferred:
- External identity should be a separate authentication method.
- Account linking requires an explicit policy rather than provider-specific
  behavior.

Open questions:
- Should verified email matches link automatically?
```

The skill proposes structure. It does not implement Google Sign-In.

## Example 4: Do not canonize technical debt

### Repository evidence

A controller writes directly to the audit table during every mutation.

An ADR says audit events should be delivered asynchronously.

### Good specification

```markdown
## Observed

- Current mutation handlers write audit records synchronously.

## Decisions

- ADR-004 defines asynchronous audit delivery as the intended architecture.

## Open questions

- Is the synchronous implementation temporary technical debt, or has ADR-004
  been superseded?
```

### Bad specification

```markdown
## Decisions

- Audit records are synchronously persisted by request handlers.
```

Existing code alone does not prove intentional architecture.

## Example 5: Avoid exhaustive documentation

### User request

```text
Map the billing subsystem.
```

### Good result

The specification describes:

- subscription ownership;
- payment-provider integration;
- webhook processing;
- idempotency behavior;
- persistence dependency;
- consumers;
- important open questions.

### Bad result

The specification lists:

- every controller;
- every DTO;
- every repository method;
- every error class;
- every migration column.

Those details remain in code.

## Example 6: Refresh after a local change

### Existing SpecSpine

```text
specs/
├── README.md
├── api-server.md
├── background-processing.md
└── persistence.md
```

### Repository change

A new queue and worker process were added for email delivery.

### User request

```text
Update the SpecSpine for the new email worker.
```

### Expected behavior

The skill should inspect the changed runtime and its integration edges.

It may propose:

```text
Create:
- specs/notification-delivery.md

Modify:
- specs/background-processing.md
- specs/operations.md
- specs/README.md
```

It should not remap the entire repository.

## Example 7: Mapping status

A useful `specs/README.md` section:

```markdown
## Mapping status

- High-level runtime map complete
- Deepened: authentication, document processing
- Partially mapped: billing
- Not mapped: internal administration tools
```

Avoid percentages or claims of formal coverage.
