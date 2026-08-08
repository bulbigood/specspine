---
specspine: 5
title: Indexing
kind: component
summary: Owns the durable contract for constructing a file index.
facets:
  architecture: complete
  behavior: partial
  interfaces: not-applicable
  data: partial
  failure: partial
  quality: not-applicable
  verification: partial
coverage:
  external-boundary: open
blockers: []
implementation_freedom: contract-equivalent
---

# Indexing

## Responsibility

Own construction of an index from an operator-selected source.

## Requirements

- REQ-selected-source — Indexing uses the source selected by the operator.

## Verification

- VER-selected-source — A focused scenario checks that indexing uses the selected source.
