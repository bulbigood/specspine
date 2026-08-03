# Specspine semantic audit

Semantic audit complements `iwe schema validate`; it does not replace IWE or create another parser, graph, readiness store, or lifecycle. Audit the IWE projection of each selected owner and report findings without rewriting files.

## Input

Resolve the IWE project root and `library.path` from `.iwe/config.toml`. Run the schema gate first:

``` bash
iwe schema validate -f json
```

Discover Specspine v5 owners with:

``` bash
iwe find --filter 'specspine: 5' -f keys
```

Project the selected owners in bounded groups by repeating `-k` for their keys:

``` bash
iwe find -k <key> --add-fields 'kind=kind,facets=facets,coverage=coverage,blockers=blockers,implementation_freedom=implementation_freedom,assets=assets,body=$content' -f json
```

Use `iwe <command> --help` and the installed CLI syntax if an option is rejected or deprecated. A whole-workspace audit processes every discovered key; a task-bounded audit lists both the selected keys and any omitted owners.

## Required checks

For every selected owner:

1. Confirm that the frontmatter title equals the first H1.
2. Enumerate semantic definitions in normative and evidence-bearing sections. Confirm that every ID is unique within the owner and its prefix matches its section. The document schema checks statement shape and section placement; audit checks uniqueness across sections.
3. Resolve every `blockers` entry to an owner-local `OQ-*` definition.
4. Confirm kind-dependent facet applicability. Evidence-only `OBS`, `INF`, inspection metadata, and non-normative assets never advance a facet.
5. For `verification: complete`, require an owner-local `VER-*` definition or a normative `verification` asset with a nonempty `verifies` list. Resolve every listed ID to an owner-local `VER-*`. Confirm that every other complete facet has substantive accepted support.
6. For `coverage.external-boundary: exhaustive`, resolve `coverage.basis` to an owner-local `CON-*` definition and confirm that the accepted boundary actually enumerates every allowed network, persistence, file, queue, process, platform, and other external interaction. An open boundary must not contain `basis`.
7. Resolve every asset path from the workspace root. Require a repository-relative path without `..` traversal or backslashes, a regular existing file inside the workspace, a valid owner-local `verifies` target when present, and authority consistent with `normative`.
8. Confirm that readiness declarations agree with accepted content. `blocked` means at least one valid blocker; `ready` means no blockers and all facets are complete or not-applicable; every other state is incomplete.

For a retrieved closure, aggregate `implementation_freedom` to `architecture-constrained` when any applicable governing owner declares it and name that owner in the report.

## Findings

Classify findings as:

- `error` — schema invalidity, duplicate or unresolved semantic IDs, invalid blocker or exhaustive basis, unsafe or missing asset, unsupported complete verification, or a readiness claim contradicted by accepted content;
- `warning` — plausible but insufficient support for a complete non-verification facet, ambiguous ownership, or an exhaustive boundary whose claimed enumeration cannot be established;
- `advisory` — navigation, decomposition, or clarity risk that does not invalidate format or readiness.

Report scope, schema result, findings with owner/key and evidence, computed readiness per selected owner, closure implementation freedom when applicable, and omissions. A read-only audit changes no files. Repair requires a separate explicit workflow and authority.
