# Pioneer Auctions

Public working repository for Pioneer Auction Service / HiBid auction research.

## Normal workflow: one button

1. In GitHub, open **Actions → Run Pioneer Auction**.
2. Click **Run workflow**, enter the HiBid auction ID, and start it.
3. GitHub exports all auction lots and their available photo links.
4. The workflow splits the auction into **100-lot photo batches** and stores each batch as a temporary Actions artifact, for example `pioneer-<auction-id>-photos-0001-0100`.
5. The auction's permanent metadata is committed to `auctions/<auction-id>/`:
   - `README.md`
   - `summary.md`
   - `summary.csv`
   - `lots.json`
   - `photo-batches.json`

`photo-batches.json` records exactly which lot belongs to which temporary artifact. This keeps each archive small enough for selective retrieval and review instead of requiring a multi-gigabyte download.

**Photo expiration is based on the auction closing time, not the workflow start.** A separate **Purge expired auction photos** Action runs every six hours and removes every photo batch for an auction after `bidCloseDateTime + 7 days`. It also removes visible photo folders committed by earlier versions of the workflow. The metadata files, batch map, and original HiBid image links remain.

HiBid timestamps without an explicit timezone are interpreted as `America/Detroit`, the Pioneer auction timezone. GitHub Actions schedules may run late; cleanup is not guaranteed to occur at the exact expiration minute. GitHub caps artifact retention at 90 days, so photos for an auction more than 90 days away may expire early and should be refreshed closer to the closing date.

## Scheduled prices for every lot

The **Update All Pioneer Lot Bids** Action (`.github/workflows/update-all-lot-bids.yml`)
is the primary price updater. It reads every numbered auction directory that has
`auctions/<auction-id>/lots.json`, queries HiBid's **public** auction details and
lot pages, and stores the latest bid/status data for **all lots**, not just the
watchlist. It does not require a HiBid login or bidding credentials.

**Where to look for current prices:**

- `auctions/<auction-id>/live.json` — latest per-auction live state, timestamp,
  lot ID/number/title, high and next bids, bid count, remaining time, open/closed
  status, price realized, reserve state, and changes since the previous check.
  The `summary` reports total, active, closed, and changed lots; `changes` lists
  the changed fields. A new live file is created after the first successful
  eligible refresh.
- `auctions/<auction-id>/lots.json`, `summary.csv`, and `summary.md` — **export
  snapshots**, useful for descriptions, categories, photos, and initial research.
  Their bid amounts can become stale. Match a catalog lot's `id` to live
  `hibidLotId` when combining metadata and current prices.
- `watchlists/latest.json` — the most recently exported personal watchlist.
  `watchlists/live.json` remains a **compatibility view** containing only its
  tracked lots. The all-lot updater rebuilds this view whenever it refreshes
  at least one auction. If a watchlist lot belongs to an auction without
  `live.json`, it is marked missing from live auctions; check its own
  `checkedAt` and `retrievalStatus` before treating its price as current.

**Refresh cadence:** The workflow wakes every ten minutes via a GitHub Actions
UTC cron (`*/10 * * * *`); the Python updater decides which auctions are due,
using the **America/Detroit** auction timezone. Before the calendar day of the
auction's scheduled close, it targets **hourly** updates (eligible after about
50 minutes). On the scheduled closing day it targets **every ten minutes**
(eligible after about nine minutes). It continues at ten-minute intervals while
HiBid reports open lots or during the first twelve hours after the scheduled
close. Afterward it stops refreshing auctions whose saved live state says all
lots are closed. Previously closed auctions **more than twelve hours old**
without an existing live file are skipped, rather than backfilled. If HiBid
provides no close time, the fallback interval is hourly.

These are target intervals, **not guaranteed exact run times**: GitHub may
delay or skip scheduled runs, and HiBid can be temporarily unavailable.
The updater rejects incomplete auction pagination rather than replacing a
previous good live file with a partial catalog. For an auction review, inspect
`checkedAt` in its `live.json` to assess freshness.

**Run manually:** Open [Actions → Update All Pioneer Lot Bids](./.github/workflows/update-all-lot-bids.yml)
in GitHub, choose **Run workflow** on `main`, then inspect its job summary and
the `auctions/<auction-id>/live.json` commit. Manual runs **also respect the
per-auction due-time checks**; running it again immediately after a successful
refresh may legitimately skip that auction. A normal catalog export using
**Run Pioneer Auction** is still required to register a newly discovered
auction in the repository; the price updater does not discover unexported
Pioneer auctions or re-download auction photos.

**Legacy watchlist updater:** The older **Update Watchlist Bids** Action no
longer has a 15-minute schedule. It remains available via manual dispatch and
its existing push triggers (watchlist or legacy-script changes) as a fallback;
it also writes `watchlists/live.json`. Avoid starting the old and new jobs
concurrently because they can conflict when committing that shared file.
Updating `watchlists/latest.json` changes the watchlist view, **not** the
all-lot updater's auction coverage.

## Troubleshooting workflows

- **Export HiBid auction:** metadata-only export and commit.
- **Mirror auction photos:** regenerate the temporary 100-lot photo artifacts from the existing `lots.json`, without adding photos to Git history.
- **Purge expired auction photos:** may be triggered manually to clear expired auctions without waiting for its scheduled check.
- **Update All Pioneer Lot Bids:** inspect the refresh log, skipped-auction reason, retrieved counts, and commit step. A missing `live.json` can mean the auction is ineligible (e.g., long closed), the scheduled run was delayed, or HiBid failed.

## Legacy browser exporter

The `pioneer-exporter.js` browser console launcher remains available as a backup. Normal operation no longer requires a browser console, ZIP downloads, or manual file moving.

## Export contents

`lots.json` includes, when HiBid provides them:

- lot number, HiBid lot ID, title and description
- category and shipping information
- high bid, minimum next bid, bid count, price realized, status
- lot URL, auction metadata, featured image and all images returned by HiBid

`summary.csv` is a compact index and `summary.md` is a human-readable snapshot with original photo links. The mirror normalizes downloaded photos to JPEG (long edge at most 1600 px), preserving the original HiBid URLs in its temporary `manifest.json`.

## Exported auctions

- Auction ID **779190**, Living Estate of Patricia Freed. Current prices, when available: [live.json](./auctions/779190/live.json). The full catalog and photos are retained separately.
- Auction ID **776304**, Beach Living Estate Auction
- Export snapshot: **1,159 lots**, **9,759 photo references**
- Photos from the older workflow were committed directly to Git and will be removed from the visible tree after auction close + seven days. Removing them does **not** reclaim the historic Git blobs. For future auctions, photo artifacts avoid adding these blobs to Git history.

No HiBid password, buyer token, or bidding credential is stored in this repository.
