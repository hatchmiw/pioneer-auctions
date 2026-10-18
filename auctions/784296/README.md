# Richard & Kathy Duynslager Living Trust

- Auction ID: **784296**
- Auctioneer: **Pioneer Auction Service**
- Last export: **2026-10-18T13:50:28Z**
- Lots: **1307**
- Photos referenced: **10331**

Files:

- [summary.md](./summary.md)
- [summary.csv](./summary.csv)
- [lots.json](./lots.json) — full catalog snapshot; bid values reflect export time
- [live.json](./live.json) — current bids/status for all lots (created separately by Update All Pioneer Lot Bids; absent until its first eligible refresh)
- [photo-batches.json](./photo-batches.json) — maps each lot to its temporary photo artifact

Run the repository's **Run Pioneer Auction** GitHub Action again to refresh this catalog snapshot and its temporary photo batches.
The **Update All Pioneer Lot Bids** Action independently refreshes live.json on an auction-aware schedule (roughly hourly beforehand, every ten minutes on auction day); it does not rewrite catalog descriptions or photos.
