# SpecSpine Map topic-planning contract

Handle exactly one neutral inventory page in a fresh isolated context. The page
is transport pagination, not an architectural group. Inspect every listed file
and follow imports, registrations, callers, manifests, schemas, or entry points
outside the page only as needed to understand responsibility and boundaries.
Do not edit the repository, Spine, campaign, packet, or another result.

Repository evidence may establish only observations. Propose stable
responsibilities, capabilities, runtimes, integrations, data ownership, or
cross-cutting project-specific contracts. Do not mirror directories, generic
`models`/`utils`/`services` layers, individual classes, static assets, or local
implementation details. Several page files may belong to one topic; one file
may support multiple topics. Use `supporting` only when a file has no durable
architectural responsibility after inspecting its use.

Write `<planning-results>/page-NNNN.json` with exactly:

```json
{
  "page": 1,
  "topics": [
    {
      "id": "provisional-session-lifecycle",
      "title": "Session lifecycle",
      "responsibility": "Creates, validates, renews, and revokes application sessions.",
      "reason": "Entry points and persistence calls establish one durable lifecycle owner.",
      "files": ["src/session/service.go", "src/session/store.go"]
    }
  ],
  "supporting": [
    {
      "reason": "Local adapter with no independent lifecycle or contract.",
      "files": ["src/session/format.go"]
    }
  ]
}
```

IDs are provisional lowercase kebab-case. Every packet file must occur in at
least one topic or exactly one supporting entry. Topic overlap is allowed;
topic/supporting overlap is forbidden. Use only files from the packet. Reread
the result for missing files, source-shaped topics, duplicated responsibility,
and unsupported intent, then terminate without messaging other agents.
