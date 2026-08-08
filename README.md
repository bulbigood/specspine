# Specspine

**Durable boundary contracts and architectural ownership for AI-assisted
software development.**

Specspine preserves accepted, durable intent as a graph of canonical
specification owners and their boundary contracts. Source code owns internal
mechanisms and current implementation reality; Specspine owns what the system is
expected to mean and do. It neither mirrors the source tree nor assumes that the
implementation conforms to the specification.

A sufficiently specified area can be understood or independently reimplemented
from its normative closure, then checked with implementation-independent
verification criteria. This gives humans and coding agents a stable source of
architectural intent instead of asking them to reconstruct it from whichever
code happens to exist today.

## Principles

- One IWE document is the canonical owner of one durable software boundary.
- Accepted intent and observed implementation evidence remain distinct.
- A link-only paragraph is structural inclusion; an inline link is a
  non-structural reference.
- Directories organize files but carry no architectural meaning.
- Specspine follows IWE's native relationship model as it evolves instead of
  maintaining parallel relationship metadata.

## Workflows

| Skill | Purpose |
| --- | --- |
| **🚀 BOOTSTRAP** | — |
| `iwe-spec-setup` | Initialize or repair the one-time Specspine workspace configuration. |
| **🎯 CORE** | — |
| `iwe-spec-specify` | Create or refine accepted requirements and architecture. |
| `iwe-spec-map` | Record boundary-significant implementation evidence without inventing intent. |
| `iwe-spec-implement` | Bring implementation into conformance without weakening the specification. |
| **🛠️ SUPPORT** | — |
| `iwe-spec-audit` | Audit format conformance and semantic readiness without changing files. |
| `iwe-spec-verify` | Compare implementation evidence with accepted specifications without editing specifications or code. |

## Setup

The current Specspine skills use IWE as their document, graph, and validation
backend. The specification model could be adapted to another backend, but simply
removing IWE references would not make these skills backend-independent: an
equivalent project, key, relationship, document-operation, and schema-validation
adapter would still be required.

Complete the following bootstrap before using any Specspine workflow.

Install Specspine, including its setup and workflow skills:

```bash
npx skills add bulbigood/specspine
```

To install one workflow explicitly, use `--skill`, for example:

```bash
npx skills add bulbigood/specspine --skill iwe-spec-map
```

Specspine does not require a particular IWE skill name. Setup uses the official
[`iwe-org/skills`](https://github.com/iwe-org/skills) repository as its skill
catalog and installation source, and selects the candidate whose declared IWE
CLI version is the best match. Specspine requires both an IWE installation and a
version-compatible agent skill capable of operating it. Start with setup in all
of these states:

- if both are available, setup uses them without reinstalling either one;
- if IWE is installed but no suitable IWE skill is available, setup selects the
  best version-compatible candidate from the official catalog and asks for
  explicit approval before installing that skill;
- if an IWE skill is available but IWE itself is missing, that skill supplies
  current installation guidance and setup asks for approval before installation;
- if neither is available, setup selects the catalog's current recommended
  skill first and then lets it install the IWE CLI version it supports.

Setup reads CLI compatibility from the candidate's name or metadata, including
the repository's `metadata.version` convention. It prefers an exact installed
CLI match, then an explicitly compatible range. It does not silently change an
installed IWE version when no compatible skill exists.

If no suitable skill can be found, or the agent has no skill-discovery or
installation capability, setup reports the missing prerequisite and stops
without improvising direct IWE operations. If the agent runtime cannot load a
newly installed skill in the current session, restart or reload the agent and
invoke setup again; it will reuse the now-installed skill and continue.

Run the guided setup from the workspace root:

> Use `$iwe-spec-setup` to prepare this project for Specspine.

The setup skill finds or, with explicit approval, installs an applicable
IWE-capable skill and gives it the desired workspace outcome and bundled
Specspine assets. The IWE skill owns IWE installation guidance, project
initialization, configuration operations, and validation.

The setup establishes:

1. the intended IWE workspace and Markdown library;
2. a Specspine directory strictly inside that library;
3. matching library-relative template and schema prefixes;
4. the canonical Specspine schema and a valid final workspace.

It reuses explicit values already supplied by the user, asks only for unresolved
or consequential choices, preserves unrelated settings, and does not overwrite
conflicting Specspine configuration without approval.

The workflow skills assume that setup is complete; they do not install or
repair IWE or Specspine configuration. If one reports a missing IWE capability,
run setup instead of asking that workflow to operate IWE directly.

## Documentation

- [Core model](docs/01-core-model.md)
- [Usage and lifecycle](docs/02-usage-and-lifecycle.md)
- [Acceptance and reconstruction](docs/03-acceptance-and-reconstruction.md)
- [Format v5](docs/reference/format.md)
- [Semantics](docs/reference/semantics.md)
- [Conformance](docs/reference/conformance.md)
- [Semantic audit](docs/reference/audit.md)
- [Glossary](docs/reference/glossary.md)

## License

MIT
