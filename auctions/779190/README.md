# Living Estate of Patricia Freed

- Auction ID: **779190**
- Auctioneer: **Pioneer Auction Service**
- Last export: **2026-09-23T01:50:25Z**
- Lots: **1381**
- Photos referenced: **10244**

Files:

- [summary.md](./summary.md)
- [summary.csv](./summary.csv)
- [lots.json](./lots.json) — complete catalog snapshot; bid values reflect export time
- [live.json](./live.json) — updated public bids and status for every lot (generated separately by Update All Pioneer Lot Bids)
- [photo-batches.json](./photo-batches.json) — maps each lot to its temporary photo artifact

Run the repository's **Run Pioneer Auction** GitHub Action again to refresh the catalog snapshot and its temporary photo batches. The **Update All Pioneer Lot Bids** Action independently refreshes `live.json` on its auction-aware schedule. For prices during bidding, check `live.json` and its `checkedAt` timestamp.
