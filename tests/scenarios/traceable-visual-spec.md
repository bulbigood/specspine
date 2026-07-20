# Scenario: add traceability and a lifecycle view

## Existing specification

`<spine-root>/job-processing.md` describes retries and job states in prose. A
downstream change needs to reference the retry constraint, repository evidence
supports current retry behavior, and the lifecycle is difficult to scan.

## User request

```text
Make the important retry rule traceable and add a readable lifecycle diagram.
```

## Expected behavior

The skill should:

- keep the existing prose and canonical ownership;
- add a readable semantic ID only to the externally referenced rule;
- keep that ID scoped to `job-processing.md`;
- format a cross-specification reference as an ID-shaped Markdown link whose
  destination is the canonical specification;
- cite representative repository-relative evidence for an observed claim;
- use Mermaid `stateDiagram-v2` for the lifecycle when it improves clarity;
- state the important lifecycle meaning outside the diagram;
- avoid adding feature requirements, acceptance criteria, or implementation
  tasks;
- avoid ASCII diagrams.

## Failure indicators

- every paragraph or bullet receives an ID;
- a reference leaves the ID outside the Markdown link;
- a reference link contains prose in addition to its exact target ID;
- a list-item ID is incorrectly treated as a Markdown URL fragment;
- an evidence path is presented as proof of complete code/spec conformance;
- the diagram is the only description of lifecycle meaning;
- a custom schema, mandatory frontmatter, or ASCII diagram is introduced;
- the specification duplicates a canonical rule owned elsewhere.
