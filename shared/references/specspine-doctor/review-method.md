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
- stale overview text or links after decomposition;
- important direct relationships hidden behind unnecessary navigation hops;
- feature-specific scope, acceptance criteria, tasks, or status;
- source-level walkthroughs and fragile implementation inventories;
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

Use absence sparingly. Missing detail is a finding only when the document's
stated purpose and the loaded stopping rules require it.

## Progressive coverage

For a whole-Spine audit, build the coverage set from all Markdown
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

Keep mechanical results separate from semantic judgments. Semantic review is
necessarily incomplete; absence of findings does not establish validity,
completeness, correct decomposition, impact coverage, or code conformance.
