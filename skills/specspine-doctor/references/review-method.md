# SpecSpine diagnostic method

Use this method with the bundled semantics. Load the full format rules only
when the finding depends on them.

## Mechanical findings

Use the bundled checker as the source of reproducible findings and severity.
Its errors cover defects that prevent navigation or resolution of an explicitly
used semantic address. Warnings and notes cover non-blocking provenance,
structure, readability, optional conventions, and diagnostic limits.

Only internal SpecSpine targets participate in link validity and reachability.
Treat links outside `<spine-root>` as unchecked; do not inspect their targets.
General Markdown, HTML, template, and style validation are outside this pass.

## Semantic review

Look for architectural risks supported by the inspected specifications:

- competing canonical owners or duplicated detailed definitions;
- contradictory decisions or constraints;
- observations or inferences presented as accepted intent;
- decisions without evidence of acceptance;
- open questions silently answered elsewhere;
- specifications mixing independently evolving responsibilities;
- fragmentation without independent responsibility or navigation value;
- a flat root whose growing list of specifications has become hard to scan even
  though several documents form stable, cohesive subject areas;
- stale overview text or links after decomposition;
- important direct relationships hidden behind unnecessary navigation hops;
- feature-specific scope, acceptance criteria, tasks, or status;
- source-level walkthroughs and fragile implementation inventories;
- missing architecturally significant edge or failure behavior required by the
  specification's stated responsibility;
- non-trivial topology, interaction, lifecycle, or data relationships that
  prose makes the reader reconstruct despite the format's visual criterion;
- diagrams that are the only source of important meaning;
- semantic IDs used indiscriminately or changed after external reference.

Describe each material risk with its evidence, likely impact, confidence, and a
next action. Use framework terms when they clarify the issue, but do not force a
fixed taxonomy or report template. A broad specification may be a candidate
for decomposition without being defective. When one specification mixes
independently evolving responsibilities, explicitly say whether decomposition
is a useful next action or why the current evidence is insufficient to decide.
Repeated ownership claims do not authorize Doctor to select an owner. Plausible
implementation evidence does not turn an inference into accepted intent.

Review directory decomposition independently from specification decomposition.
For a whole-Spine review, inspect the distribution of Markdown files by
directory and the root index's navigation surface. A large root-level file
count is a prompt to inspect navigation, not a defect or a fixed threshold.
Report a directory-decomposition risk only when the flat layout creates
concrete orientation cost and the documents provide evidence for a few stable,
cohesive areas.

Directories are navigation aids, not ownership, containment, or architectural
hierarchy. Do not require every specification to belong to a directory, mirror
the source tree, recursively classify concepts, or infer relationships from
paths. Prefer a small number of broad subject directories and keep cross-area
graph links explicit. A mixed flat-and-grouped layout is valid when it is
easier to navigate.

When directories exist, review every specification's placement. Derive the
document's subject from its declared responsibility, boundaries, summary, and
canonical claims; derive a directory's navigation purpose from the documents
it contains and any explicit overview text; do not infer either from the path
name alone. Classify each inspected document as:

- clearly aligned with its directory;
- clearly misplaced relative to an established cohesive area;
- cross-cutting or intentionally root-level; or
- ambiguous because the directory purpose or document responsibility is not
  sufficiently established.

Report only evidence-backed mismatches. A dependency on another area,
cross-area relationship, or implementation location does not by itself make a
document misplaced. For a whole-Spine review, do not claim directory-placement
coverage until every Markdown specification has been classified.

Use absence sparingly. Missing detail is a finding only when the document's
stated purpose and the loaded stopping rules require it.

## Progressive coverage

For a whole-Spine check, build the coverage set from all Markdown
specifications under `<spine-root>`, not only reachable documents. Start with
`README.md`, then inspect bounded graph-neighborhood batches so ownership and
relationships remain visible. Track each path as pending or inspected in the
working context; do not create a tracking file in the Spine.

At a checkpoint:

1. report inspected and remaining paths;
2. consolidate supported findings from the completed batches;
3. propose one repair batch with exact files and changes;
4. request operator approval before writing; and
5. after any approved repair, rerun affected checks and continue with pending
   paths.

Choose batch size from document length and relationship density. Do not sample,
stop after the first clean batch, or infer whole-Spine health from the
deterministic checker. Avoid confirmation overhead by grouping independent,
meaning-preserving repairs. An explicit current request to make a named
correction already supplies approval for that correction.

## Repair boundary

Propose transformations that are unambiguous and preserve meaning, but write
only after operator approval. This includes adding a clearly supported missing
relationship and repairing mechanical defects. A reorganization proposal must
make ownership, navigation, and affected paths explicit. Ask for a decision
when a repair would choose ownership or boundaries, change a decision or
constraint, resolve a conflict or open question, or infer intent from
repository evidence.

For directory decomposition, propose the exact moves and every affected
Markdown link. Preserve document IDs, canonical ownership, accepted claims, and
graph relationships. Do not introduce directory index files or new
containment relationships unless they add independently justified navigation
value. Moving an already coherent set of specifications is
meaning-preserving; deciding ambiguous group membership requires operator
approval.

A clearly misplaced document may be included in an approved repair batch only
when one existing destination directory has an established matching navigation
purpose. If several destinations are plausible, the current directory has no
established purpose, or moving the document would decide an architectural
boundary, present the alternatives and request an operator decision.

Keep mechanical results separate from semantic judgments. Semantic review is
necessarily incomplete; absence of findings does not establish validity,
completeness, correct decomposition, impact coverage, or code conformance.
