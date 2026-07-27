# Coverage, validation, and views

## Documentation coverage

The root index reports qualitative coverage:

```markdown
## Coverage

### Mapped

- Order processing and payments.

### Partially mapped

- Inventory — responsibility and interfaces are known; failure behavior and
  deployment constraints remain incomplete.

### Unmapped

- Reporting.
```

- `Mapped` means the area has a canonical owner, useful boundaries and
  relationships, applicable intent and uncertainty, and enough documented
  context for task closure.
- `Partially mapped` means useful architecture exists but material concerns are
  missing or unresolved.
- `Unmapped` means the area is known but lacks a useful architectural owner or
  context.

Coverage is a documentation claim, not a proof of completeness or conformance.
`complete` retrieval is allowed only for affected `Mapped` scope.

Production coverage is tracked separately during brownfield mapping. It answers
which production work units were inspected and verified, not whether the
architecture is semantically complete.

## Mechanical checks

Deterministic checks may report reproducible errors and warnings.

Errors include defects that prevent required navigation or resolution, such as:

- missing or duplicate document IDs;
- invalid required node shape;
- unresolved internal links;
- duplicate or unresolved semantic IDs;
- malformed semantic-ID regions;
- malformed relationship rows;
- invalid Known divergence references;
- unreachable specifications when reachability is required.

Warnings include non-blocking risks such as:

- unknown core-like kinds or relations;
- excessive `related-to`;
- weak or missing provenance;
- non-canonical filenames;
- incomplete index structure or coverage;
- suspicious duplication;
- generated artifacts inside the canonical Spine.

Mechanical PASS/FAIL applies only to deterministic rules. It MUST NOT be
presented as semantic validity, architectural completeness, correct
decomposition, complete impact analysis, or code/spec conformance.

## Semantic review

Semantic review is advisory and evidence-backed. It looks for:

- competing canonical owners or duplicated definitions;
- contradictory or unaccepted intent;
- observations or inferences presented as accepted intent;
- open questions silently answered elsewhere;
- mixed independently evolving responsibilities;
- fragmentation without independent ownership or navigation value;
- stale overview text after decomposition;
- hidden direct relationships;
- feature artifacts, task status, or source-level walkthroughs;
- missing architecturally significant failure or edge behavior;
- topology, lifecycle, or data relationships that prose makes readers
  reconstruct;
- diagrams that are the only source of meaning;
- unstable or indiscriminate semantic IDs;
- confirmed drift not represented as a Known divergence.

Each finding states location, evidence, impact, confidence, and a useful next
action. Absence of findings does not certify the Spine.

## Diagrams and review lenses

Important meaning MUST remain understandable in prose and tables.

Authored Mermaid diagrams MAY clarify non-trivial topology, sequence, state,
data, or lifecycle relationships. They MUST NOT be the only carrier of
architectural meaning. ASCII diagrams SHOULD NOT be used in canonical
specifications because wrapping and automated editing make them fragile.

Generated diagrams and reports are disposable views:

- C4 may project system topology;
- arc42 may serve as a review lens for missing concerns;
- ICOM may serve as a functional diagnostic lens;
- backlinks, dependency maps, and impact reports may be derived from typed
  relationships.

None is the canonical storage model.

## Graceful degradation

If SQLite FTS5 or the retrieval cache is unavailable:

1. open the root `README.md`;
2. inspect `Coverage`;
3. use the architecture map;
4. follow relative Markdown links;
5. read Responsibility, Boundaries, Relationships, and applicable Known
   divergences;
6. assemble the minimal context manually.

If a parser does not understand a new relation type, the Markdown remains
readable, the relationship is preserved, the checker warns, and the target
remains reachable as an ordinary link.

If generated views are missing, canonical prose and tables retain all required
meaning. Deleting a derived database or cache MUST NOT lose architecture data
and MUST allow complete rebuilding.
