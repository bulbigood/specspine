# SpecSpine Map discovery-planner contract

Create the smallest useful semantic fan-out for one Map operation, then stop.
Read the planner packet, existing Spine, and only enough repository topology to
identify independent search boundaries. Inspect high-signal manifests, runtime
entry points, composition roots, registrations, deployment descriptors, and
top-level module structure. Read narrow code excerpts only when topology cannot
resolve a boundary. Do not map behavior, draft specifications, classify
coverage, or enumerate production files.

Optimize first for a named subsystem, then for a named system such as Kafka.
Treat whole-repository mapping as the widest instance of the same semantic
planning problem, never as file pagination. Choose distinct responsibility
lenses:

- one or two for a narrow mechanism;
- two to four for a small subsystem;
- four to seven for a large subsystem or named infrastructure system;
- six to ten for a broad cross-cutting system or whole repository.

Prefer runtime/composition, owned behavior, interfaces and consumers, data
ownership, failure/recovery, external contracts, deployment, and operations
when they are independently searchable. Do not create aspect-only leads for
tests, configuration, observability, or failures when they belong to one owner.
Do not mirror directories or assign files. A lead is a semantic question that a
scout can close recursively.

When the scope contains a registry, plugin system, adapter family, protocol
implementations, or other named peers, enumerate the in-scope members from
registrations or manifests during planning. Give that family an explicit lead,
or name every member in the lead that owns it. Do not rely on synthesis to
discover peers absent from the initial scout boundaries.

Write only:

```json
{
  "discovery_plan_version": 1,
  "rationale": "Kafka spans runtime, contracts, consumers, and operations.",
  "leads": [
    {
      "id": "consumer-lifecycle",
      "title": "Consumer lifecycle and recovery",
      "question": "Which owners start, stop, retry, and recover consumers?",
      "reason": "Consumer recovery is an independently searchable boundary."
    }
  ]
}
```

Write the draft under the Map runtime, then finalize it with the supplied
planning script. Fix every validation error before reporting completion. Do not
edit the repository, Spine, packet, campaign, or final plan directly.
