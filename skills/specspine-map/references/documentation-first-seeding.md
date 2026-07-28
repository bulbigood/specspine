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
Spine to suggest candidate owners for every synthesized semantic topic.

The command accepts only a current v3 root pair: a missing index or manifest,
an invalid manifest envelope, any manifest version other than integer `3`, and
legacy/unknown manifest keys are setup blockers. There is no legacy
documentation adapter or migration path.

For a recognized v3 Spine, the command runs the current checker, including
repository-relative evidence validation when the campaign has a repository
root, and records remaining findings as the immutable input baseline. These v3
defects do not block discovery. Later publication and integration may remove
baseline findings but reject any new finding. Do not create a cosmetic
replacement manifest, downgrade findings, or rerun with a permissive checker.
Resolve baseline defects through evidence-backed producer output or root
integration; finalization requires a clean v3 checker result.

New bounded directions come only from producer checkpoints and root
integration. Root integration must reread each settled result, persist every
accepted unresolved direction as ToDo, and may add an anchored ToDo exposed by
the integrated graph.
