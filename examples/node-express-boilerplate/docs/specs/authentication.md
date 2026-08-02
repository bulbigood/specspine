---
specspine: 5
title: Authentication
kind: capability
summary: Authenticates credentials and owns token issuance behavior.
facets:
  architecture: complete
  behavior: complete
  interfaces: complete
  data: partial
  failure: complete
  quality: partial
  verification: complete
coverage:
  external-boundary: open
blockers: []
implementation_freedom: contract-equivalent
---

# Authentication

## Responsibility

Turn valid credentials into an authenticated subject and renewable tokens.

## Boundaries

User identity is owned by [User management](user-management.md), not by this
capability.

## Requirements

- REQ-valid-credentials — Valid credentials produce access and refresh tokens.
- REQ-invalid-credentials — Invalid credentials reveal no account secrets.

## Verification

- VER-login — Black-box login tests cover success and invalid credentials.
