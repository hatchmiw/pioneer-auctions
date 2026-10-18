# Pioneer Auction 784296 — review status and resumability (2026-10-18)

## Immutable baseline
- Auction: **Richard & Kathy Duynslager Living Trust**; Pioneer Auction Service, HiBid ID **784296**.
- The **existing** GitHub Actions `run-pioneer-auction.yml` was launched through `auction-requests/784296.txt` and the existing bootstrap dispatcher. Run **39133274951** finished **success**: https://github.com/hatchmiw/pioneer-auctions/actions/runs/39133274951
- Catalog snapshot **2026-10-18T13:50:28Z**: **1,307** lots, **10,331** listing-photo references. Confirmed six retained Actions artifacts: **one artifact with 1,307 per-lot review contact sheets**, **five original-photo ZIP shards**. The workflow reported zero photo-mirror failures. This is a baseline, not proof the auctioneer won't add/change lots.
- Original-photo shards have automatic cleanup scheduled around **Oct 28 at 6pm EDT**, so do not rely on them being permanent.
- Newer automated `Update All Pioneer Lot Bids` jobs have been observed completing successfully Oct 18 (latest observed run 39142551210); the recorded catalog `live.json` should be re-read before using prices. Neither past bids nor asks are reliable comparable **sold** prices.
- Buyer premium: **10% cash/check, 13% card**, plus any tax, pickup and repair. The sale begins **Wed Oct 21 at 6pm EDT** with individual soft close; preview is **Mon Oct 19 4–6pm**, pickup Fri Oct 23 4–6pm / Sat Oct 24 9–11am, **2720 E Weidman Rd, Rosebush MI**. Verify terms again prior to decisions.

## Work fully preserved on main
- All **1,307 / 1,307** catalog titles/categories received permissive routing, not final appraisal.
- **722 unique lots** had their **individual reduced-resolution contact sheets** visually examined, **585 remain**. Count reconciled in `review-coverage-2026-10-18.json`, with the list of all individually reviewed lot IDs and the hashes of review-pass sources.
- Reviews are in `photo-review-batch-001.md`, `photo-review-batch-002.md`, plus `photo-review-pass-001.csv` onward through `photo-review-pass-014.csv`, including lettered passes. Each reviewed lot records photo evidence/identity, practical utility and unresolved condition/completeness; many are dismissed as bulky or low-fit home decor without spending resale research time. These are **thumbnail reviews**; they do not establish that all original-resolution images were inspected or that items work.
- At least **five** lots have original images separately examined in detail: `650` Lodge Smokey skillet; `981` old Sears generator; `1082` Craftsman lawn-tractor lift-kit manual; `639` and `640` Edison cylinder records. The separate `edison-cylinder-original-audit-2026-10-18.md` audits **7 full-size photographs for 639** and **9 for 640**, including visibly damaged records in 640 and several relevant SOLD comparable records.
- `preliminary-risk-adjusted-maxima-2026-10-18.md` includes thirteen conditional, conservative hammer figures with tested/untested distinctions and source notes; `all-reviewed-lots-live-snapshot-2026-10-18.csv` was created earlier with only **113** reviewed lots, so **DO NOT mistake that older snapshot for current complete review coverage or current bids**.
- Other important catalog correction flags: lot **1133** is corded/electric, not gasoline-fueled; lot **1082** a lawn tractor model accessory, not a Kubota tractor implement; lot **1071** photos show a tire-chain BOX but do not prove chains present; lot **1037** title says wire but actual coiled material not identified. Safety-critical hoists/jacks, gas heaters, vintage extinguisher and used helmets require non-photo checks and can be no-bids. No purchases/bids made.

## Next work (preserve completion markers)
1. Continue all **585** image-sheet records, not blanket or inferred photo approvals. Prioritize farm, shop, renovation, tools, older audio/collectibles where **exceptional bargain** potential exists. Many unreviewed listings are jewelry, bedding, holiday decor and tableware.
2. Cross-check all **1,307 unique HiBid IDs and photos** for late additions, removals or material description/photo changes. Only re-open a reviewed entry when materially changed.
3. For true shortlisted candidates, inspect selected original photographs at full size (model labels, cracks, rust, missing parts), verify tested operation, **actual sold** value and local sell-through, then assign **Bargain / Good Buy / Absolute Max** hammer prices after adding fees, repair, pickup, duplication and storage.
4. Save normalized bid/history snapshots as the auction approaches; never confuse `live.json` export-time bid with market value or realized hammer. Auction participation is undecided.
5. **DO NOT place bids or buy**, absent a new explicit user authorization.

Tracking records: Active Projects Dashboard row for auction review tooling; reminder **REM-008**; Auction History **784296**. Store progress there and verify dependent dashboard counts after updates.
