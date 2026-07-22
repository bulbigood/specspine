# Scenario: make an architectural rule traceable

## Existing specification

`<spine-root>/job-processing.md` describes retries and job states in prose. A
downstream change needs to reference the retry constraint, and representative
repository evidence supports the currently observed retry behavior.

## User request

```text
Make the important retry rule traceable across the existing specifications and
attach representative repository evidence for the observed retry behavior.
Preserve the existing prose lifecycle description. Add a visual only if it
materially improves readability.
```

## Expected behavior

The skill should:

- keep the existing prose and canonical ownership;
- add a readable semantic ID only to the externally referenced rule;
- keep that ID scoped to `job-processing.md`;
- format the cross-specification reference as an ID-shaped Markdown link whose
  destination is the canonical specification;
- cite representative repository-relative evidence for an observed claim;
- avoid treating the evidence as proof of complete code/spec conformance;
- avoid adding feature requirements, acceptance criteria, or implementation
  tasks.

## Failure indicators

- every paragraph or bullet receives an ID;
- a reference leaves the ID outside the Markdown link;
- a reference link contains prose in addition to its exact target ID;
- a list-item ID is incorrectly treated as a Markdown URL fragment;
- an evidence path is presented as proof of complete code/spec conformance;
- a custom schema or mandatory frontmatter is introduced;
- the specification duplicates a canonical rule owned elsewhere.
