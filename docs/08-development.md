# Development and maintenance

## Repository organization

```text
specspine/
├── README.md
├── LICENSE
├── docs/
│   └── reference/
├── shared/
│   ├── references/
│   └── scripts/
├── skills/
│   ├── specspine-doctor/
│   ├── specspine-extract/
│   ├── specspine-evolve/
│   ├── specspine-map/
│   └── specspine-verify/
├── tools/
│   └── specspine-extract/
├── examples/
└── tests/
```

The five publishable packages under `skills/`, normative prose under
`docs/reference/`, the manifest schema under `shared/references/`, and
deterministic common tools under `shared/scripts/` are the repository sources
of truth.

Shared resources appear in consuming skills as relative symbolic links.
A private execution protocol stays in its owning skill rather than under
`shared/`.

`shared/references/vocabulary.json` is the single source of reserved format
tokens. Regenerate and verify its human-readable glossary with:

```bash
python3 shared/scripts/render_vocabulary.py --write
python3 shared/scripts/render_vocabulary.py
```

Scripts read the vocabulary through `shared/scripts/spec_contract.py`; do not
repeat token sets or identifier-prefix tables in consumers.

`tools/specspine-extract/` contains repository-only diagnostics for the
optional retrieval index and evaluation telemetry. It imports the production
search implementation from `skills/specspine-extract/`; it is never required
at runtime.

## Local installation

```bash
git clone https://github.com/bulbigood/specspine.git
cd specspine

npx skills add . --list
npx skills add . --skill specspine-doctor
npx skills add . --skill specspine-extract
npx skills add . --skill specspine-evolve
npx skills add . --skill specspine-map
npx skills add . --skill specspine-verify
```

## Validation

Run mechanical tests:

```bash
python3 tests/run_mechanical.py
```

The runner executes individual tests in parallel and defaults to one fewer
worker than the number of CPUs reported by the operating system. Pass
`--jobs N` to override the worker count.

The test suite includes mechanical regression tests, lifecycle scenarios,
retrieval corpora, and agent evaluations. Multilingual fixtures are test data
and do not set the language of framework documentation.

## Pre-publish checklist

No shared resource needs to be copied manually into individual skills.
Normative references, the schema, the vocabulary, and common scripts appear in
the skill directories as relative symbolic links. `npx skills add --copy`
resolves them into self-contained installed packages.

When `shared/references/vocabulary.json` changes, regenerate the
human-readable glossary:

```bash
python3 shared/scripts/render_vocabulary.py --write
```

Before publishing any skill, run the complete gate:

```bash
python3 shared/scripts/prepublish.py
```

The gate:

1. verifies that `docs/reference/glossary.md` matches the canonical vocabulary;
2. runs all mechanical tests, including vocabulary, JSON Schema, and
   executable-contract consistency checks;
3. installs every published skill twice through `npx skills add --copy` in an
   isolated workspace and verifies that each installed package contains its
   glossary and machine vocabulary.

The command is read-only by default and fails when generated documentation is
stale. To regenerate the glossary and then run the same gate:

```bash
python3 shared/scripts/prepublish.py --update-generated
```

For a faster local check that deliberately omits the standalone installation
test:

```bash
python3 shared/scripts/prepublish.py --skip-npx
```

Do not use `--skip-npx` as the final publication gate.

## Evaluation

SpecSpine is experimental. Its falsifiable hypothesis is that, for the same
documented repository, change request, and coding agent, a relevant architecture
handoff reduces architectural violations and irrelevant repository exploration
without reducing functional correctness.

Link validity, document shape, and skill behavior are regression properties;
they are not evidence that the product hypothesis is true.

Important evaluation targets include:

- canonical-owner recall;
- critical constraint and decision recall;
- required-neighbor recall;
- potentially affected precision;
- context-token reduction;
- irrelevant source exploration;
- downstream functional correctness;
- architecture violations.

## Relationship to downstream frameworks

SpecSpine does not replace OpenSpec, spec-kit, BMAD, or execution-oriented
agent frameworks. Those systems own feature deltas, plans, and implementation
workflows. SpecSpine supplies long-lived architectural context through a neutral
handoff.

Canonical skills do not inspect framework conventions, convert feature
specifications, or guarantee compatibility. Downstream frameworks may consume
the neutral handoff without becoming part of the SpecSpine runtime.

## Contribution guidance

Useful contributions include:

- realistic example projects;
- difficult ownership and decomposition cases;
- cross-cutting architecture changes;
- regressions where an agent duplicated or misplaced a concept;
- evaluations across agents and repositories;
- improvements that preserve the Markdown-first model.

Avoid formal schemas, mandatory runtimes, and complex workflows unless evidence
shows that the existing contract cannot solve the problem.

## Current direction

Completed foundations include the five runtime skills, persistent project-agent
bootstrap, mechanical checks, deterministic retrieval acceleration with native
Accelerated Markdown retrieval, exhaustive brownfield orchestration, and
evaluation harnesses.
