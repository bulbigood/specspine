# SpecSpine

**Durable boundary contracts and architectural ownership for AI-assisted
software development.**

SpecSpine preserves accepted durable intent as a graph of canonical owners and
their owner-relative boundary contracts. Source code owns internal mechanisms
and current implementation reality; SpecSpine does not mirror source or claim
that implementation conforms to intent.

A sufficiently specified area can be independently reimplemented from its
normative closure and checked against implementation-independent verification.

## Model

- Each architectural concept has one canonical owner.
- Responsibilities, boundary inputs and outputs, controls, data authority,
  observable behavior, and typed relationships express accepted durable intent.
- `OBS` records only boundary-significant exception evidence: a material
  intent gap, confirmed divergence, unresolved question, or surprising
  ownership boundary. It is not an implementation inventory.
- `Known divergences` links accepted intent to conflicting `OBS` evidence
  without silently preferring either side.
- `specspine.json` records completeness, blockers, inspection coverage,
  implementation freedom, and normative assets.
- Root `README.md` explains SpecSpine; every `_INDEX.md`, including the root,
  provides the same deterministic physical-navigation structure. Skills
  accelerate retrieval and maintenance but are not required to read a Spine.

`ready` means the specification has no declared completeness gap or blocker for
its required facets. It is not evidence that current code conforms. Verification
and blind reconstruction assess those separate claims.

## Quick start

Install Doctor and Extract for project connection and task-oriented retrieval:

```bash
npx skills add bulbigood/specspine --skill specspine-doctor
npx skills add bulbigood/specspine --skill specspine-extract
```

Optional skills evolve accepted intent, compare a brownfield repository, and
verify conformance:

```bash
npx skills add bulbigood/specspine --skill specspine-evolve
npx skills add bulbigood/specspine --skill specspine-map
npx skills add bulbigood/specspine --skill specspine-verify
```

Ask Doctor:

```text
Expose this project's SpecSpine to agents through persistent project instructions.
```

Without installed skills, open the `<spine-root>` directory, read its
`README.md`, then use `_INDEX.md` and follow links to the
canonical owner relevant to the task.

## Documentation

- [Core model](docs/01-core-model.md)
- [Usage and lifecycle](docs/02-usage-and-lifecycle.md)
- [Acceptance and reconstruction](docs/03-acceptance-and-reconstruction.md)
- [Normative reference](docs/README.md)
- [Glossary](docs/reference/glossary.md)
- [Development and maintenance](docs/08-development.md)

Maintainers should run `python3 shared/scripts/prepublish.py` before publishing
skills.

SpecSpine is experimental. See the development guide for evaluation and
contribution details.

## License

MIT
