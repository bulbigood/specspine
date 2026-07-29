# Development and maintenance

## Repository organization

```text
specspine/
├── README.md
├── LICENSE
├── docs/
├── shared/
│   ├── references/
│   └── scripts/
├── skills/
│   ├── specspine-doctor/
│   ├── specspine-extract/
│   ├── specspine-evolve/
│   └── specspine-map/
├── tools/
│   ├── specspine-adapter-generator/
│   └── specspine-extract/
├── examples/
└── tests/
```

The four publishable packages under `skills/`, common instructions under
`shared/references/`, and deterministic common tools under `shared/scripts/`
are the repository sources of truth.

Shared resources appear in consuming skills as relative symbolic links.
`tools/specspine-adapter-generator/scripts/generate_resources.py` registers and
validates those links. A private execution protocol stays in its owning skill;
it must not be registered as a shared resource. The generator also rejects
unshared byte-identical files across skills.

The adapter generator is maintainer-only repository tooling. It may generate
framework-specific SDD adapters, but it contains no canonical copies of runtime
skills and is not installable through `npx skills`.

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
```

## Validation

Validate or repair shared-resource links:

```bash
tools/specspine-adapter-generator/scripts/generate_resources.py
tools/specspine-adapter-generator/scripts/generate_resources.py --check
```

Run mechanical tests:

```bash
python3 -m unittest discover -s tests/mechanical -p 'test_*.py'
```

The test suite includes mechanical regression tests, lifecycle scenarios,
retrieval corpora, and agent evaluations. Multilingual fixtures are test data
and do not set the language of framework documentation.

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

Framework-specific integration belongs to adapters outside the runtime skill
line. Canonical skills do not inspect framework conventions, convert feature
specifications, or guarantee compatibility.

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

Completed foundations include the four runtime skills, persistent project-agent
bootstrap, mechanical checks, deterministic retrieval acceleration with native
Accelerated Markdown retrieval, exhaustive brownfield orchestration, shared-resource
validation, and evaluation harnesses.

Future work may add adapters for popular SDD frameworks while keeping the
runtime skills framework-neutral.
