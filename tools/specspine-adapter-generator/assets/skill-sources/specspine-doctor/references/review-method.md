# SpecSpine diagnostic method

Use this method with the bundled semantic rules. Load the full format rules only
when a finding or repair depends on them.

## Severity

- `error` — a preflight failure, direct contradiction, or mechanical defect
  that prevents deterministic navigation or resolution of an explicitly used
  interoperable address;
- `warning` — provenance, readability, or structural defect that does not make
  navigation or address resolution unsafe;
- `note` — maintainability risk, optional-format preference, out-of-scope
  reference, or incomplete diagnostic coverage.

Confidence is separate from severity: `high`, `medium`, or `low`.

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

## Semantic pass

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

List mechanical findings compactly with their checker code, severity, location,
and message. For semantic findings, add report-local labels, confidence,
evidence, impact, and repair disposition when useful. Omit empty severity
groups. End with checked and unchecked scope. Finding labels are ephemeral.
