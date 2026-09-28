# Update Watchlist Bids verification status

Status: **OPEN — closure criteria not yet fully satisfied**

Last updated from GitHub verification on 2026-09-28.

## Intended path

- Source watchlist: `watchlists/latest.json`
- Direct updater: `scripts/update_watchlist_bids.py`
- Output: `watchlists/live.json`
- Workflow: `.github/workflows/update-watchlist-bids.yml`
- Required direct schedule: every 15 minutes (`*/15 * * * *`)
- Workflow permission: `contents: write`

## Root cause found

The direct watchlist workflow originally had the 15-minute schedule. Commit
`671d2bab69b062beb7de3e4d8c8813674a90e2f0` added it.

Commit `06afdd21f5ebe88692a798b015155b9d134e75cf` later removed the
`schedule:` trigger with the message:

> Disable legacy scheduled watchlist updater in favor of all-lot refresh

That left `Update Watchlist Bids` with only `workflow_dispatch` and path-limited
`push` triggers. The separate `Update All Pioneer Lot Bids` workflow continued
running on schedule and rebuilding `watchlists/live.json` as a compatibility
view, which explains why `live.json` can exist even when the named direct
watchlist workflow has no recent scheduled runs.

## Repair

Commit `7ad5d497fc9a0f45503e02de7284acf303997103` restored:

```yaml
schedule:
  - cron: "*/15 * * * *"
```

The repair deliberately leaves the functioning all-lot updater intact.

## Verified after repair

Push-triggered run:

- Run ID: `36441460762`
- Event: `push`
- Result: `success`
- Started: 2026-09-28T15:09:39Z
- Completed: 2026-09-28T15:13:10Z
- Head SHA: `7ad5d497fc9a0f45503e02de7284acf303997103`

Run log result:

```
Refreshed 2/2 tracked lots; active=2, closed=0, changed=2, missing=0
```

The run committed `watchlists/live.json` as commit
`42d1bccd7a709b423648f5447bb963762b454927`.

At that refresh:

- `trackedLots = 2`
- `retrievedLots = 2`
- `missingLots = 0`
- both tracked lots had `retrievalStatus = "ok"`
- `checkedAt = 2026-09-28T15:13:05Z`

Lot `322874070` (lot 321) currently shows `highBid = 4`, `bidCount = 3`,
and `nextBid = 5`. The authoritative watchlist export snapshot recorded that
same lot at `highBid = 3`, `bidCount = 2`, and `nextBid = 4`, demonstrating
that an actual bid-state change has occurred since the watchlist export.

Historical GitHub Actions history also contains successful true scheduled
invocations of this exact workflow on 2026-09-24, including run
`36033923575`, whose log reported:

```
Refreshed 2/2 tracked lots; active=2, closed=0, changed=2, missing=0
```

Those historical runs confirm the cron form is valid, but they predate the
repair and therefore do not by themselves close the current verification task.

## Still required before closure

Do **not** mark this task closed until both are verified after the repair:

1. A normal `Update Watchlist Bids` run appears with `event = "schedule"`
   and completes successfully using the restored cron.
2. A real bid change on a watched lot is subsequently captured in
   `watchlists/live.json` / repository history, with the before/after bid
   fields attributable to the direct updater.

After both are verified, present the evidence to the user and ask for explicit
closure confirmation.
