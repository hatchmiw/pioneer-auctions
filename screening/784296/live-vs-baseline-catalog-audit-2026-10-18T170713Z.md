# Pioneer 784296 — baseline catalog vs scheduled live updater (October 18, 2026)

- Baseline metadata export: **2026-10-18 13:50:28 UTC**, **1307** rows.
- Scheduled all-lot updater: **2026-10-18T17:07:13Z**, **1307** successfully retrieved, **1307** open, **0** closed.
- Lot-number set: **0** newly seen / **0** absent relative to original snapshot; **0** changed HiBid stable lot IDs; **0** changed title strings. Baseline vs live title comparison is exact for all 1,307.
- **130** lot current bid amounts or bid counts differ from initial catalog export; this is expected and does not imply edited descriptions/photos.
- Updater's generic “changedLotsSincePreviousCheck=1307” is **not a count of meaningful bid edits or catalog modifications**. 1265 lot change flags reflect only the decreasing countdown (42 other-field changes in the compared updater result). Do not issue catalog-change alerts on countdown drift alone.
- **IMPORTANT LIMITATION:** Neither live lot state nor catalog title counts verify that any **description, photo file, photo order, quantity or listing terms** are unchanged. The auctioneer's “More lots coming soon” language may be generic; a true photo/description signature audit requires a new HiBid metadata-only export/diff, not re-reading this live file. Keep the Oct 18 frozen catalog/photo work intact.
- Normalized **1307**-row price observation file: `price-history/784296-2026-10-18T170713Z-preclose.csv`. `price_type=current_bid_not_final`, never market sold/realized. Buyer premiums and taxes excluded from price column.
- User has **not authorized bids or purchases**.
