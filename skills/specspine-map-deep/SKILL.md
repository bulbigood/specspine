---
name: specspine-map-deep
description: Recursively deepen evidence-backed architecture documentation for an operator-specified brownfield repository scope through branch-affine Map producer sessions, centrally scheduled forks, continuous publication, and final normalization. Use only when the operator explicitly invokes $specspine-map-deep to exhaust useful architectural depth in one area, several areas, or the whole project. Works with concurrent producers or one local producer.
---

# SpecSpine Map Deep

Map the operator's requested scope through repeated SpecSpine Map operations
until every evidence-backed architectural branch is saturated. Accept the same
scope as `specspine-map`; use orchestration and recursive depth instead of one
agent's bounded pass.

## Resources

- Read [references/orchestration.md](references/orchestration.md) completely
  before starting. It owns adaptive discovery, producer-command composition,
  staging, publication, recursive saturation, normalization, and optional
  post-map Doctor behavior.
- Run `scripts/bundle_skill.py --print` once with the installed
  `specspine-map` root and a destination under the disposable run root. It
  strips Map frontmatter and concatenates its body with every UTF-8 file under
  Map `references/`. Embed the returned bundle in the initial command for every
  new producer session, but never resend it when resuming that session.
  Producers must not load skills or references themselves.

## Authority

Repository evidence may establish observations and support inferences, but
never establishes accepted decisions or constraints. Do not modify production
code, claim complete code/spec conformance, or apply semantic Doctor repairs
without approval.

## Workflow

1. Resolve the repository, `<spine-root>`, and exact user-requested mapping
   scope. Read existing Spine context, resolve one shared evidence baseline, and
   discover repository evidence adaptively; prescribe no survey command or depth.
2. Decompose the scope into independent architectural branches and keep their
   queued, active, locally saturated, and complete states in an in-memory ToDo
   tree. The orchestrator alone accepts forks, owns slots, and starts producers.
3. Assign each branch to one producer session. Send its initial command the
   complete Map bundle, shared context, and private writable staging root.
   Resume that same session for continuations of the same branch without
   resending immutable instructions; never repurpose it for an unrelated branch.
4. Consume checkpoints continuously. Mechanically preflight useful candidates
   and move them unchanged into the live Spine without rereading or
   reconstructing them. Resume the producer only after its staging root is
   empty again.
5. Keep same-boundary continuations with their current producer. Deduplicate and
   enqueue material independent in-scope fork candidates. Fill every free slot
   with a ready continuation or queued branch without waiting for a batch.
   Producers propose forks but never create producers.
6. Continue every producer session until its branch reaches a terminal Map
   refusal because the Spine already answers it, evidence cannot support a
   useful node, or further depth would reproduce implementation. A branch is
   complete only when it is locally saturated and all accepted child branches
   are complete.
7. Stop only when every requested branch is complete and no actionable branch
   remains. Normalize navigation once and run the full mechanical checker.
8. When subagents are unavailable, execute the same branch protocol locally.
   The current agent performs all roles; only concurrency changes.
9. Report scope, files, relationships, saturated branches, unresolved drift,
   limitations, normalization, and checks. Include the literal `no useful node`
   terminal reason for every saturated branch.

An explicit invocation approves staged mapping, move-based publication, and
final navigation normalization. Ask only before changing accepted intent,
choosing among materially different canonical owners, or applying semantic
Doctor repairs.
