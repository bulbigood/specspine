# SpecSpine resource generation contract

## Canonical packages

The publishable packages under `<repo-root>/skills/specspine-*`, normative
references under `<repo-root>/docs/reference/`, and common machine resources
under `<repo-root>/shared/` are the canonical runtime sources. Edit private
skill resources under `skills/`, normative prose under `docs/reference/`, and
shared schema, scripts, or assets under `shared/`.

The maintainer tool must not contain copies or snapshots of those packages. It
reads canonical skills directly and generates only resources that must be
duplicated between separately published members of the coordinated suite.

## Shared rules

`docs/reference/` owns normative prose reused by multiple skills:

- `format.md`, exposed to skills as `spec-format.md`;
- `semantics.md`, exposed to skills as `spec-semantics.md`.

`shared/references/` owns the common manifest schema.

Each consuming skill exposes a shared reference through a relative symbolic
link. A private reference that defines only one skill's execution remains a
regular file in that skill and is not registered with this generator. The
generator validates or atomically repairs only registered shared links; it
never copies their contents. Every file under `shared/` must have at least two
registered skill consumers. Byte-identical regular files in different skills
must instead have one shared owner and relative symbolic links. Selecting
`--skill` limits link validation or repair to that skill; ownership validation
always covers the repository. Run the full check before a release.

## Framework-adapter boundary

Canonical runtime skills know only SpecSpine artifacts, the neutral context
handoff, and the persistent agent bootstrap. They must not contain
framework-specific commands, stages, artifact paths, naming rules, templates,
or compatibility branches.

Framework-specific integration skills are generated and maintained only by
this tool. An adapter may translate the neutral handoff into a framework's
native workflow, but must not redefine SpecSpine semantics or turn downstream
artifacts into architectural authority.

The connection-administration mode of `specspine-doctor` owns only the
framework-neutral managed block in persistent project-agent instructions. It
does not discover SDD frameworks or generate bindings and adapters.

## Safety properties

- Use deterministic relative symbolic links; never use an LLM rewrite.
- Repair links through temporary siblings and atomic replacement.
- Make `--check` read-only and return a non-zero exit code for drift.
- Never create canonical skill instructions from files under `tools/`.
- Never persist full skill copies under `tools/`.

## Required gates

Before publishing:

1. edit skill-specific files under `skills/`, normative prose under
   `docs/reference/`, and machine resources under `shared/`;
2. repair shared-resource links;
3. run generation in `--check` mode;
4. validate every canonical skill with an available native validator;
5. run unit tests and the eval-manifest audit;
6. run deterministic scripts on representative valid and invalid fixtures;
7. inspect the generated diff for unintended prompt growth;
8. record the release version through the repository's release mechanism.

Generation and testing do not authorize external publishing.

The generator enforces maximum word counts for the always-loaded bootstrap and
latency-sensitive `doctor` skill body. Change a budget only with an explicit
architectural reason and a before and after runtime-cost comparison.
