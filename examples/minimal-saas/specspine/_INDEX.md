# minimal-saas architecture

**ID:** `project-architecture` · **Kind:** `index`

SpecSpine is the project's long-lived, linked specification and architectural memory used to reconstruct contract-equivalent implementations.

This directory contains the project's long-lived architectural intent and architecture-relevant repository observations.

## How to use this Spine

- Start with `Contents`, then follow links to the canonical owner of the area relevant to the task. Preserve stable document IDs when files move.
- SpecSpine owns accepted durable intent; source code owns the current implementation. Neither alone proves that implementation conforms to intent.
- `specspine.json` records areas, completeness, inspection coverage, blockers, and registered contract or verification assets.
- `DEC`, `CON`, `REQ`, `GUA`, `INV`, `QLT`, and `VER` identify accepted claims. `OBS` records confirmed implementation evidence, `INF` an unconfirmed inference, and `OQ` an unresolved question.
- `Known divergences` links accepted intent to conflicting observations. Do not silently turn code, `OBS`, or `INF` into accepted intent.
- Update the canonical owner instead of copying a claim into another document; preserve unresolved conflicts and blocking questions explicitly.

## Contents

- [application.md](application.md)
- [billing.md](billing.md)
- [identity.md](identity.md)
- [operations.md](operations.md)
- [specspine.json](specspine.json)
