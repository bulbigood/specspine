---
name: specspine-doctor
description: Configure and diagnose a Specspine v5 library running on IWE. Use for setup, schema validation, graph diagnostics, and project-agent connection.
---

# Specspine Doctor

Specspine v5 delegates documents and graph integrity to IWE.

## Diagnose

1. Run `iwe --version` and require IWE 0.17 or newer.
2. Resolve the project containing `.iwe/config.toml`.
3. Read `library.path`; do not guess a Spine root from filenames.
4. Run `iwe schema validate`.
5. Run `iwe tree -f json` to inspect inclusion roots.
6. Use `iwe find --references`, `--referenced-by`, `--includes`, or
   `--included-by` for focused graph checks.

The IWE key is document identity. A standalone link is structural inclusion;
an inline link is a reference. Never create `_INDEX.md`, `specspine.json`, or a
parallel link index.

## Configure

Install `assets/iwe/config.toml` as `.iwe/config.toml` and
`assets/iwe/schemas/specification.yaml` as
`.iwe/schemas/specification.yaml`. Preserve an existing IWE configuration and
merge only the `[library]`, `[templates.specification]`, and
`[schemas.specification]` settings after showing the user the change.

Validate after any configuration or specification edit:

```bash
iwe schema validate
```
