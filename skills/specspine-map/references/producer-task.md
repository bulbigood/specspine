# SpecSpine Map one-shot producer contract

A producer handles exactly one bounded architectural ToDo. It reads only the
immutable task packet, relevant existing specifications, and evidence needed
for that question. It writes publish-ready Markdown only under its private
staging root, returns one checkpoint, and terminates.

The producer does not:

- edit the live Spine, `README.md`, source, tests, or campaign state;
- continue to another question;
- add ToDo items directly;
- decide repository coverage, quality-gate passage, or saturation;
- integrate navigation or choose between materially different canonical owners.

The task packet supplies:

```json
{
  "id": "sso-settings",
  "question": "Who owns provider settings persistence and reload?",
  "reason": "The source inventory exposes a durable service boundary",
  "evidence": ["pkg/services/ssosettings"],
  "documents": ["identity-access.md", "authentication-sessions.md"],
  "excludes": ["login orchestration", "session token lifecycle"],
  "anchor": null
}
```

Use one checkpoint status:

- `draft_ready` — staging contains one coherent publish-ready change;
- `no_architectural_value` — inspected evidence belongs to an existing owner or
  contains no durable architecture;
- `needs_more_evidence` — a fresh producer should retry the same ToDo with the
  listed additional evidence;
- `blocked` — external authority, unavailable evidence, or an ownership choice
  prevents progress.

Checkpoint shape:

```json
{
  "status": "draft_ready",
  "evidence_inspected": [
    "pkg/services/ssosettings/ssosettings.go",
    "pkg/services/ssosettings/api/api.go"
  ],
  "findings": [
    "The service owns provider-scoped CRUD, fallback resolution and reload"
  ],
  "candidates": [
    {"path": "sso-settings.md", "operation": "create"}
  ],
  "discovered_directions": [
    {
      "id": "sso-secret-redaction",
      "question": "Where is SSO secret redaction enforced?",
      "reason": "The public API returns a distinct redacted representation",
      "evidence": ["pkg/services/ssosettings"],
      "documents": ["sso-settings.md"],
      "excludes": ["general secret storage"],
      "anchor": {
        "document": "sso-settings.md",
        "location": "Interfaces / redacted reads",
        "known": "Read endpoints expose a redacted representation"
      }
    }
  ],
  "required_evidence": [],
  "terminal_reason": null
}
```

`draft_ready` requires candidates. Other statuses prohibit candidates.
`needs_more_evidence` requires a nonempty `required_evidence`. A
`no_architectural_value` reason starts with `no architectural value: `.

Discovered directions are suggestions only. The root orchestrator must
disposition every suggestion while integrating the published documents and
must create an explicit persistent ToDo for each accepted direction.
