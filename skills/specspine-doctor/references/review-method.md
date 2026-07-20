# SpecSpine diagnostic method

Use this method after loading the current format and semantic rules from the
installed `specspine-grow` or `specspine-map` companion.

## Severity

- `error` — mechanically invalid reference or a direct contradiction that can
  mislead downstream work;
- `warning` — likely structural or semantic defect requiring judgment;
- `note` — maintainability risk or incomplete diagnostic coverage.

Confidence is separate from severity: `high`, `medium`, or `low`.

## Mechanical pass

Use the bundled checker for reproducible findings. Verify:

- index presence and specification reachability;
- relative Markdown link targets;
- semantic-ID definitions, sections, uniqueness, and references;
- filenames, headings, empty sections, and unresolved placeholders.

Do not promote optional-format preferences into errors.

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

## Repository-aware pass

When authorized, look for representative evidence of:

- observed boundaries that disagree with intended architecture;
- stale evidence paths or changed runtime relationships;
- new durable responsibilities without a canonical specification;
- implementation behavior incorrectly canonized as a decision;
- intended constraints with no claim of implementation status.

Report drift without resolving it. A repository sample establishes evidence,
not completeness.

## Handoff pass

Check that the handoff:

- names one canonical primary owner when one exists;
- separates required, potentially affected, and merely related context;
- preserves claim kinds and existing semantic IDs;
- includes blocking questions without answering them;
- excludes acceptance criteria, plans, tasks, estimates, and implementation
  status;
- is sufficient for the requested change without copying unrelated branches.

## Report shape

```markdown
# SpecSpine health report

## Summary

## Errors

### DOC-001 — Short title

- Severity:
- Confidence:
- Location:
- Evidence:
- Impact:
- Recommended owner:

## Warnings

## Notes

## Scope

- Checked:
- Not checked:
```

Omit empty finding sections. Finding labels are report-local and ephemeral.
