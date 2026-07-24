# Map-Deep orchestration

## Scope and authority

Map exactly the scope requested by the operator: one focused concern, several
areas, or the whole repository. Treat the scope the same way as SpecSpine Map;
Map-Deep changes execution strategy, not mapping semantics.

Repository evidence may establish observations and support inferences, but
never establishes accepted decisions or constraints. Do not modify production
code, claim complete code/spec conformance, or apply semantic Doctor repairs
without approval.

Resolve the repository root and `<spine-root>`. Read the Spine index and
relevant existing specifications before planning work. Discover repository
evidence adaptively with the tools and depth appropriate to the requested
scope. Do not prescribe a universal listing command, fixed traversal depth,
document count, or initial backlog size.

For a focused request, follow the connected architectural boundary as far as
repository evidence remains relevant. For a whole-repository request, first
identify the system shape and material areas, then deepen each area. In either
case, prefer architectural questions about stable responsibilities,
boundaries, interfaces, runtime and data flows, persistence, integrations,
configuration, deployment, security, failure behavior, and observability over
questions that merely reproduce directories or implementation detail.

## Prepare producers

Create a unique disposable run root outside the live `<spine-root>` and one
private staging root per active producer. This state belongs only to the
current invocation. Do not create a ledger, checkpoint, recovery manifest,
source inventory, or resumable run protocol. Already published Spine files are
the durable mapping result. If execution is interrupted, report any remaining
staging paths; a later invocation rediscovers coverage from the current Spine.

Build the complete Map instruction bundle once at
`<run-root>/producer-instructions.md`:

```text
python3 <map-deep-skill-root>/scripts/bundle_skill.py \
  <map-skill-root> <run-root>/producer-instructions.md --print
```

The builder includes the Map body and every UTF-8 file under Map `references/`,
saves the bundle, and emits the same text. Capture stdout directly; do not read
the generated file or assemble references manually. Embed this complete bundle
in every producer command so producers do not load skills, references,
templates, or orchestration instructions themselves.

Split the requested scope into independent coherent architectural questions.
Avoid competing ownership of the same concept. A question may include tightly
related subquestions, but do not combine unrelated areas merely to reduce
producer startup. Dispatch independent questions concurrently when the
environment supports it. Agent lifecycle, routing, and concurrency mechanics
belong to the execution environment.

Use this self-contained producer command with resolved placeholders:

```text
You are a SpecSpine mapping producer.

<complete-generated-map-instructions>

Producer execution override:

All Map instructions and references needed for this assignment are embedded
above. Do not load or invoke any skill, reference, template, or instruction
file.

Map the assigned architectural question as deeply as repository evidence
supports. Inspect only relevant evidence. Create publish-ready Markdown only
under the writable output root. Keep source, tests, configuration, the live
Spine, and every other staging root read-only. The writable root mirrors
`<spine-root>`: place every new candidate at its exact final relative path.

Create a document only when it adds useful architectural knowledge. If the
live Spine already answers the question, evidence cannot support a useful
node, or further detail would merely reproduce implementation, create nothing
and report `no useful node` with a concise reason. Never manufacture output to
keep the mapping branch alive.

Put a short summary immediately below each H1. Cite every repository evidence
path inline as code, never as a Markdown link outside the Spine. Preserve the
difference between accepted intent, observations, and unconfirmed inferences.
Do not run a checker, reread candidates, or perform final validation.

After writing candidates, return a compact report containing only:

- evidence inspected;
- created files and their final relative destinations;
- mapped responsibilities, boundaries, and relationships;
- related existing Spine paths and evidence-supported navigation targets;
- material follow-up architectural questions within the requested scope,
  including prerequisites;
- unresolved inferences or drift;
- `no useful node` and its reason when no file was created.

Report a follow-up only when inspected evidence indicates that another Map
operation could add useful architecture documentation. Do not repeat document
prose or speculate merely to extend the queue. Return the report as the agent
result; never write control files into staging.

Repository: <repository-root>
Live Spine, read-only: <spine-root>
Requested mapping scope: <operator-scope>
Shared repository and Spine context: <shared-context>

Assignment:
Writable output root mirroring the Spine: <private-staging-root>
Final namespace: <relative-destination>
Architectural question: <question>
```

When subagents are unavailable, run the same producer command locally for one
question at a time. The current agent performs orchestrator, producer, and
consumer roles; only concurrency changes.

## Consume and publish

Consume each completed producer report without rereading candidate prose or
repeating its source investigation. If the producer reports `no useful node`
and staging is empty, close that branch. Otherwise run the deterministic
checker once against the producer's complete staging root:

```text
python3 <checker-path>/check_spine.py <spine-root> \
  --candidates <private-staging-root> --json
```

Resolve checker findings through a focused producer correction. Publish only
after candidate mode returns no findings. The producer owns semantic fitness
and source evidence for its question; the orchestrator must not re-investigate
them.

Move every accepted candidate unchanged to the same relative path under the
live Spine using a filesystem move or rename tool. Never reconstruct a file by
reading and rewriting it, reread it after moving, overwrite an existing path,
or add an arbitrary numeric suffix after a collision. Remove empty private
staging roots after publication.

Defer index reachability and reciprocal navigation updates until final
normalization so producers never compete over shared overview files.

## Continue to architectural saturation

Treat useful producer reports as the discovery mechanism after the initial
plan. Add every material, independent, in-scope follow-up question that could
produce useful architecture documentation. Deduplicate it against active,
completed, and already documented questions. Continue each branch after a
successful document instead of treating the first output as sufficient.

After completing every reported follow-up in a branch, enqueue one terminal
depth probe asking Map whether any material architecture documentation remains
within that branch. A useful result reopens the branch and contributes its own
follow-ups. Close the branch only when this probe creates no document and
reports `no useful node`. Do not repeat a terminal probe after that refusal.

A branch is saturated only when:

- its terminal depth probe creates no document because the Spine already answers it,
  available evidence cannot support a useful node, or further depth would
  reproduce implementation;
- every reported material follow-up has already been answered, is outside the
  requested scope, or requires unavailable evidence or operator authority.

The run is saturated only when no producer is active, no actionable question
remains, and every branch of the requested scope has reached that terminal
condition. Do not stop at a predetermined number of documents or at shallow
overview coverage. Do not invent questions solely to prove depth.

Do not invoke SpecSpine Doctor, reorganize the live Spine, or perform final
normalization while mapping questions remain.

## Normalize once

After saturation, perform one sequential navigation pass using producer
reports, published destinations, the Spine index, and only relevant overview
documents:

1. Keep the established layout unless stable cohesive clusters make navigation
   materially difficult. Never mirror the source tree.
2. Add every new document to curated `README.md` navigation.
3. Apply evidence-supported reciprocal links to named overview documents and
   update affected relative links.
4. Preserve producer prose, claim semantics, semantic IDs, unresolved
   inferences, and open questions.
5. Run the full deterministic checker once over the normalized Spine.

Remove known disposable run artifacts after success. Report the requested
scope, published files, mapped responsibilities and relationships, terminal
branches, unresolved questions or drift, execution limitations, normalization,
and mechanical-check results.

Run SpecSpine Doctor only when the operator explicitly requests a post-map
semantic review. Run it after saturation, normalization, and mechanical
checking; apply semantic repairs only with operator approval.
