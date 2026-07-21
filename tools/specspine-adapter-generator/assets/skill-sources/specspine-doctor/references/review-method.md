# SpecSpine diagnostic method

Use this method with the bundled semantic rules. Load the full format rules only
when a finding or repair depends on them.

## Mechanical severity

- `error` — a reproducible preflight or mechanical defect that prevents
  deterministic navigation or resolution of an explicitly used interoperable
  address;
- `warning` — provenance, readability, or structural defect that does not make
  navigation or address resolution unsafe;
- `note` — maintainability risk, optional-format preference, out-of-scope
  reference, or incomplete diagnostic coverage.

Mechanical findings do not use confidence. The checker reproduces them from the
same files and rules.

## Advisory semantic impact

- `critical` — a likely contradiction or ownership conflict that can misdirect
  downstream work;
- `warning` — a likely semantic, structural, or provenance risk;
- `note` — a maintainability concern or review limitation.

Every advisory finding uses confidence `high`, `medium`, or `low`. Impact and
confidence never produce a semantic PASS/FAIL result.

## Mechanical pass

Use the bundled checker for reproducible findings. Its interoperability checks
cover:

- index presence and specification reachability;
- relative Markdown link targets;
- semantic-ID definitions, sections, uniqueness, and references;
- semantic-ID marker regions and evidence-baseline syntax.

It may also report headings, empty sections, naming conventions, provenance,
and reachability as warnings or notes. Treat these as advisory unless the
requested operation gives them concrete semantic or navigation impact. Do not
manually re-check advisory findings merely to reproduce the script.

Only internal SpecSpine targets participate in link validity and reachability.
Report a relative link that resolves outside `<spine-root>` as unchecked scope;
do not inspect its target. General Markdown, HTML, template-origin, and style
validation are outside this mechanical pass.

Do not promote optional-format preferences into errors.

## Repair discipline

In repair mode, fix a finding directly only when the transformation is
unambiguous and preserves meaning. Re-run the checker after edits. A plausible
repair is not an accepted architecture decision: stop for user judgment when a
repair would choose canonical ownership, change a decision or constraint,
resolve a conflict or open question, or infer intent from repository evidence.

## Advisory semantic review

This review is evidence-backed but necessarily incomplete. It does not prove
architecture consistency, completeness, correct decomposition, complete impact
analysis, or code conformance. Absence of findings is not semantic validation.

Look for:

- competing canonical owners or duplicated detailed definitions;
- contradictions between decisions or constraints;
- observations or inferences presented as accepted intent;
- decisions presented without evidence of user acceptance;
- open questions silently answered elsewhere;
- broad specifications containing independently evolving responsibilities;
- fragmented specifications without independent responsibility or navigation
  value;
- stale overview text or links after decomposition;
- important direct relationships hidden behind several navigation hops;
- feature-specific requirements, tasks, status, or release scope;
- source-level walkthroughs and fragile inventories;
- diagrams that are the only source of important meaning;
- semantic IDs applied indiscriminately or changed after external reference.

Use absence sparingly. Missing detail is a defect only when the loaded stopping
rules require it for the specification's current purpose.

## Handoff pass

Check that the handoff:

- names one canonical primary owner when one exists;
- uses repository-root-relative specification addresses that include the
  resolved spine root;
- separates required, potentially affected, and merely related context;
- preserves claim kinds and existing semantic IDs;
- treats external decision sources as provenance rather than new authority;
- includes blocking questions without answering them;
- excludes acceptance criteria, plans, tasks, estimates, and implementation
  status;
- is sufficient for the requested change without copying unrelated branches.

## Report shape

Report `Mechanical integrity: PASS|FAIL` from checker errors only and list its
findings compactly with code, severity, location, and message. Then report
`Advisory semantic findings` with report-local labels, impact, confidence,
evidence, and repair disposition when useful. End with checked scope, unchecked
scope, and review limitations. Finding labels are ephemeral.
