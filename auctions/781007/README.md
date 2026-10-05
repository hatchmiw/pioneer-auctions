# Advanced Glass Business Liquidation

- Auction ID: **781007**
- Auctioneer: **Pioneer Auction Service**
- Last export: **2026-10-05T22:01:27Z**
- Lots: **580**
- Photos referenced: **2727**

Files:

- [summary.md](./summary.md)
- [summary.csv](./summary.csv)
- [lots.json](./lots.json) — full catalog snapshot; bid values reflect export time
- [live.json](./live.json) — current bids/status for all lots (created separately by Update All Pioneer Lot Bids; absent until its first eligible refresh)
- [photo-batches.json](./photo-batches.json) — maps each lot to its temporary photo artifact

Run the repository's **Run Pioneer Auction** GitHub Action again to refresh this catalog snapshot and its temporary photo batches.
The **Update All Pioneer Lot Bids** Action independently refreshes live.json on an auction-aware schedule (roughly hourly beforehand, every ten minutes on auction day); it does not rewrite catalog descriptions or photos.
