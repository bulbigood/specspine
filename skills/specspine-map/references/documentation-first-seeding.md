# Mechanical documentation seed

Use this step when exhaustive Map starts with an existing Spine.

Do not ask the root model to invent a documentation-gap plan or claim that it
read every node. Record the complete Markdown inventory mechanically:

```text
python3 <map-skill-root>/scripts/campaign.py seed-from-spine \
  <campaign> <spine-root>
```

The command stores every live Markdown hash. It adds no ToDo and grants no
coverage. `source-pass` later uses literal evidence references from the whole
Spine to suggest candidate owners for every production unit.

New bounded directions come only from producer checkpoints and root
integration. Root integration must reread each settled result, persist every
accepted unresolved direction as ToDo, and may add an anchored ToDo exposed by
the integrated graph.
