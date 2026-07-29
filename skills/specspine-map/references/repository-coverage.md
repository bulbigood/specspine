# SpecSpine Map repository-coverage contract

Audit only a whole-repository exhaustive topic plan for missing architectural
roots. Read the compact coverage packet, current topic plan, existing Spine,
and repository topology. Inspect manifests, deployables, runtime entry points,
composition and registration roots, independently configured modules, plugin
families, persistence owners, deployment descriptors, and external contract
registries. Read narrow code excerpts only to decide whether a suspicious root
is already represented.

Do not review prose quality, topic granularity, individual files, or local
implementation detail. Do not require every directory or production file to be
covered. A gap is an in-scope independently owned runtime, subsystem,
capability, data owner, integration, or operational boundary absent from the
topic plan and existing Spine.

Write one result:

```json
{
  "status": "clear",
  "reason": "Every architecture-significant topology root is represented.",
  "inspected_roots": ["workspace manifests", "runtime entry points"],
  "open_leads": []
}
```

Use `status: gaps` with nonempty `open_leads` when work remains. Each lead has
exactly `id`, `title`, `question`, `reason`, and up to 40 concrete
repository-relative `seed_files`. Do not edit the repository, Spine, campaign,
packet, or final review. Finalize the private draft with the supplied coverage
script and fix every validation error before reporting completion.
