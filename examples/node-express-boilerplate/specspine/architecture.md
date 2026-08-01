---
specspine: 5
title: API architecture
kind: system
summary: Owns the public API boundary and its principal capabilities.
facets:
  architecture: complete
  behavior: partial
  interfaces: complete
  data: partial
  failure: partial
  quality: partial
  verification: partial
blockers: []
implementation_freedom: contract-equivalent
---

# API architecture

## Responsibility

Provide the HTTP API boundary and coordinate its independently owned
capabilities.

## Boundaries

[Authentication](authentication.md)

[User management](user-management.md)
