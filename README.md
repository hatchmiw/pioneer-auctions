# Pioneer Auctions

Public working repository for Pioneer Auction Service / HiBid auction research.

## Workflow

1. Open the auction on the main HiBid domain, for example:
   `https://hibid.com/catalog/776304/beach-living-estate-auction`
2. Open Chrome DevTools → Console.
3. Run the launcher below.
4. The latest exporter is loaded from this repository.
5. The exporter queries HiBid's public GraphQL catalog data and downloads:
   - `summary.md`
   - `lots.json`
   - `summary.csv`
6. Put those three files under `auctions/<auction-id>/`.
7. Run the **Mirror auction photos** GitHub Action for that auction ID if a durable photo mirror is wanted.

## Console launcher

```javascript
fetch(
  "https://raw.githubusercontent.com/hatchmiw/pioneer-auctions/main/pioneer-exporter.js?ts=" + Date.now()
)
  .then(r => {
    if (!r.ok) throw new Error(`Exporter load failed: HTTP ${r.status}`);
    return r.text();
  })
  .then(code => {
    console.log("Loaded Pioneer/HiBid exporter from GitHub.");
    (0, eval)(code);
  })
  .catch(err => console.error("EXPORTER ERROR:", err));
```

## Current test auction

- Auction ID: **776304**
- Name: **Beach Living Estate Auction**
- Auctioneer: **Pioneer Auction Service**
- Catalog size at setup: **1,153 lots**

## Export contents

`lots.json` is the primary research file. It includes, when HiBid provides them:

- lot number and HiBid lot ID
- title and description
- category
- current high bid and minimum next bid
- bid count
- price realized after closing
- lot status and countdown
- shipping flag
- lot URL
- featured image
- **all lot images returned by HiBid's `pictures` field**
- auction-level metadata

`summary.csv` is a compact lot index. `summary.md` is a human-readable snapshot with direct photo links.

## Photo mirror

The photo workflow reads `auctions/<auction-id>/lots.json`, downloads every image recorded for each lot, normalizes it to JPEG (up to 1600 px on the long edge), and writes galleries under:

`auctions/<auction-id>/photos/<lot>/`

The original HiBid image URL is retained in `photos/manifest.json` and each lot gallery.

## Notes

- Run the exporter from the main `hibid.com` catalog URL rather than a regional or auctioneer portal when possible.
- Auction data is a snapshot at the time the exporter is run.
- The exporter sets `countAsView: false` so retrieval does not intentionally inflate HiBid lot view counts.
- No HiBid password, buyer token, or bidding credential is stored in this repository.
- HiBid can change its GraphQL schema or Cloudflare behavior; if the exporter stops working, update the query rather than falling back immediately to manual lot-by-lot collection.
