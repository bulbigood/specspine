# SpecSpine Doctor operation modes

- `setup` — create the first managed project connection and a minimal Spine
  root index when absent.
- `connect` — validate and idempotently refresh an existing managed connection
  without changing recognized settings.
- `reconfigure` — change selected connection settings: root, documentation
  language, or instruction file.
- `disconnect` — remove only the managed project-instruction block; preserve
  the Spine and instruction file.
- `audit` — read-only integrity review of the requested Spine scope, including
  mechanical findings and any explicitly requested semantic review.
- `diagnose` — read-only investigation of a stated health problem or selected
  area.
- `repair` — propose and, after required approval, apply bounded corrections
  under the Spine root.
