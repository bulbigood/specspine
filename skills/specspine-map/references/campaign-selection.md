# Exhaustive campaign selection

Use one stable user-private campaign home per platform. In Codex use the
current Codex home plus `specspine-map-runs`; do not scan an arbitrary home
directory, temporary storage, or the repository. Keep repository-specific runs
below that home, but match them by recorded canonical repository root rather
than directory names.

Before `init` in a new session, unless the operator already selected an exact
ledger, run:

```text
python3 <map-skill-root>/scripts/campaign.py discover \
  <campaign-home> <repository-root> --recent-hours 24
```

Discovery is read-only. It ignores completed, terminally blocked, unrelated,
unbound, invalid, and symlinked ledgers. `source_current: false` means the
immutable source snapshot changed and the campaign cannot be resumed.

If no campaign is returned, initialize a new one. If one or more incomplete
campaigns are returned, do not initialize or edit the Spine. Show each exact
ledger, scope, human-readable last-activity age, task-state counts, and source
freshness, then ask the operator to choose:

- resume one exact campaign; or
- start a new campaign and leave every prior run inert.

Always require this choice. Recommend `resume` when activity is at most 24
hours old and the source snapshot is current. Recommend `new` when it is older
or the snapshot changed. Never silently choose the newest directory. If several
campaigns exist, require an exact ledger selection.

After the operator chooses resume, run:

```text
python3 <map-skill-root>/scripts/campaign.py resume-session <campaign>
python3 <map-skill-root>/scripts/campaign.py next-action <campaign>
```

`resume-session` refuses a changed source snapshot and returns every `assigned`
task to `todo`, because producer handles from another session are not live in
the new session. Preserve their private work packages for diagnosis and use
fresh producers. If recorded contract metadata differs from the current
contract, create a unique new run and do not modify the old ledger.
