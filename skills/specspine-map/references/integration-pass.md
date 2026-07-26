# Exhaustive graph integration

Run this root-only pass after producer publications settle and again before the
final documentation pass. Candidate acceptance proves mechanical validity; it
does not prove that independently produced nodes form the best connected
architecture graph.

## Integrate publications

The root orchestrator must:

1. Inspect every branch with published paths or reported relationships.
2. Read the affected documents, their canonical owners, and relevant graph
   neighbors.
3. Add or correct ordinary navigation links needed for reachability and local
   comprehension.
4. Add missing architectural edges through canonical `Relationships` tables.
   Store each directed fact once in the document that owns its source side; do
   not manufacture reciprocal rows merely for navigation.
5. Use a semantic ID as the complete link label when the edge targets a
   particular statement. Preserve the target document path without a fragment.
6. Resolve duplicate definitions by keeping one canonical owner and replacing
   other definitions with short context plus a link. Ask before choosing among
   materially different plausible owners.
7. Run the full live checker without deferred reachability findings.

The root may edit live navigation and existing specifications during this pass.
Producers may not.

## Review file organization

Keep the flat layout while it remains easy to navigate. Introduce or reorganize
directories only when several documents form a stable cohesive area and the
flat list has become materially difficult to use. Directory names organize
files; they do not define ownership or mirror source directories.

Perform moves only after producers stop writing candidates. Preserve document
and semantic IDs, update every incoming and outgoing relative link, rerun the
checker, and ensure `README.md` or another reachable owner still exposes the
moved nodes.

## Record the pass

Save a report covering every live Markdown document:

```json
{
  "evidence_inspected": ["README.md", "identity.md", "sessions.md"],
  "relationship_review": [
    {
      "branch": "identity-sessions",
      "disposition": "integrated",
      "reason": "Added the canonical consumes edge and overview navigation"
    }
  ],
  "organization": {
    "status": "flat_sufficient",
    "reason": "The current node count remains navigable from three overview owners"
  }
}
```

Allowed relationship dispositions are `integrated`, `already_canonical`,
`navigation_only`, and `not_architectural`. Every branch that published a path
or reported a relationship requires one disposition.

Organization status is `flat_sufficient`, `directories_sufficient`, or
`reorganized`.

Record and mechanically verify the result:

```text
python3 <map-skill-root>/scripts/campaign.py integration-pass \
  <campaign> <spine-root> <integration-report.json>
```

The command requires all non-root branches to be complete, verifies a complete
Markdown inventory, runs the live checker, records document digests, and binds
the result to the current frontier epoch. Later publications, new branches, or
repairs invalidate it. Finalization rejects documentation changed after the
recorded integration.
