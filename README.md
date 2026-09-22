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

## Troubleshooting workflows

- **Export HiBid auction:** metadata-only export and commit.
- **Mirror auction photos:** regenerate temporary photo artifact from the existing `lots.json`, without adding photos to Git history.
- **Purge expired auction photos:** may be triggered manually to clear expired auctions without waiting for its scheduled check.

## Legacy browser exporter

The `pioneer-exporter.js` browser console launcher remains available as a backup. Normal operation no longer requires a browser console, ZIP downloads, or manual file moving.

## Export contents

`lots.json` includes, when HiBid provides them:

- lot number, HiBid lot ID, title and description
- category and shipping information
- high bid, minimum next bid, bid count, price realized, status
- lot URL, auction metadata, featured image and all images returned by HiBid

`summary.csv` is a compact index and `summary.md` is a human-readable snapshot with original photo links. The mirror normalizes downloaded photos to JPEG (long edge at most 1600 px), preserving the original HiBid URLs in its temporary `manifest.json`.

## Existing auction

- Auction ID **776304**, Beach Living Estate Auction
- Export snapshot: **1,159 lots**, **9,759 photo references**
- Photos from the older workflow were committed directly to Git and will be removed from the visible tree after auction close + seven days. Removing them does **not** reclaim the historic Git blobs. For future auctions, photo artifacts avoid adding these blobs to Git history.

No HiBid password, buyer token, or bidding credential is stored in this repository.
