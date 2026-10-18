# Pioneer Auction 784296 — working review status

Updated 2026-10-18, after user-authorized restart. Auction: Richard & Kathy Duynslager Living Trust. **No bids or purchases authorized or placed.**

## Workflow / catalog verification

- Created `auction-requests/784296.txt` on main; bootstrap workflow dispatched the existing `run-pioneer-auction.yml` (no workflow code modification). Initial request commit `6eb3f89747daf16ec7560a102bd17754cc66e2a6`.
- GitHub Actions `Run Pioneer Auction` run **39133274951** completed **success** on 2026-10-18. URL: https://github.com/hatchmiw/pioneer-auctions/actions/runs/39133274951
- Permanent `auctions/784296/lots.json`, `README.md`, `summary.csv`, `summary.md`, `photo-artifact-index.json` all present. Metadata snapshot at 2026-10-18T13:50:28Z, **1307 lots** with **10331 photo references**.
- Full review-sheet artifact contains **1307 review.jpg images** with one per listed lot and a manifest. Photo artifact index confirms **five original-photo shard archives** and 10331 total mirrored photos. Six artifacts (five photo shards, one review-sheets) uploaded and verified. Source photos expire after **2026-10-28 22:00 UTC** (6pm EDT), subject to automated purge schedule and GitHub availability.
- All-lot live bids file exists, `auctions/784296/live.json` checked **2026-10-18T13:59:06Z**, with 1307 reported/retrieved/open lots and zero closed. Bid values remain timestamped observations; not market comparables.
- No lot had zero photo references in the summary CSV, but this does **not** prove every part/attachment was photographed or that the photos prove functionality. Example: lot 1071 pictures the *chain box*, not the chains.
- HiBid auction still says **More lots coming soon**; monitor catalog for new/changed lots without erasing reviewed work. Auction closes by soft close beginning Wed **2026-10-21 at 6pm EDT**, lots close individually over subsequent hours. Preview Mon Oct 19 4-6pm. Pickup Fri Oct 23 4-6pm or Sat Oct 24 9-11am. Pickup is 2720 E Weidman Rd, Rosebush MI. **10% cash/check, 13% credit/debit buyer premium** (excluding any applicable taxes or fuel/time).

## Review coverage

- **Stage 1 title/category scan: 1307/1307** lots, including high-recall keyword signals and a low-tier anomaly audit flag. Current tier labels are routing tools only, not actual valuations or exclusion of later newly listed items.
- **Photo contact/review sheets: 48 distinct lots reviewed** in two documented evidence passes. Every available photo for these lots was visible within the corresponding contact/review sheet; the images for the other **1259 lots were not individually reviewed**. At the original image level, one selected source image each for **lots 981 and 1082** was enlarged/read; the remaining source original images are mirrored but **not yet individually inspected**.
- `stage1_title_category_2026-10-18.csv` is the complete working master with review status and photo-adjusted routing labels. `photo-review-pass-001.csv` and `photo-review-pass-002.csv` document all 48 photo-screened lots, their visual evidence, known unknowns, and **provisional, risk-adjusted hammer caps**.
- `reviewed-lots-bidwatch-snapshot-2026-10-18.csv` merges these 48 lots with the 13:59Z live snapshot and estimated lot-by-lot soft closing times. Its maximum prices are hypothetical discussion numbers, not current bids or authorization. Do **not** assume a lot is functional without testing.
- Photo-based corrections: **1133 is corded electric, not fuel-operated**; 1082 is a Craftsman lawn-tractor accessory **model 610.24600**, not generic 3-point farm hardware; **1037 spool of black material remains unidentified**; **1071 photos show chain box only**; **7 is a wooden armoire**, not a secure armored cabinet.

## Risks / next work

1. Continue the remaining **1259** individual lot photo-sheet reviews, prioritizing practical farm/shop/renovation utility plus anomaly audit among low-ranked titles; preserve row-by-row progress and do not redo already verified reviews.
2. Inspect original-size photo files selectively when model, safety, completeness or price hinges on detail; photo shards 001-005 are available until cleanup. Source shard 004 has been retrieved and some original files extracted for local study; this is not proof that all source photos were personally inspected.
3. Gather defensible **sold-price comps**, condition/test evidence, loading/pickup constraints and the user's actual needs before final Bargain/Good Buy/Absolute Max hammer recommendations. The current ceilings are *preliminary*; no binding bidding advice.
4. Re-export or compare the catalog only when materially changed, preserving photos/review markers where the HiBid lot ID and its photo signature match; keep the 2026-10-18 catalog snapshot for audit.
5. After close, preserve observed hammer prices as historical actual comps, rather than confusing snapshot live bids with sales.

Market-evidence notes: https://www.neilsauctions.com/lots/8988-ryobi-bts10-10-table-saw-lot-229 (different Ryobi model sold $38); https://www.ebay.com/itm/306974895985 (Ryobi BT3100 best offer accepted, exact realized price undisclosed, ask $174.95); https://www.mnwinc.com/craftsman-generator-2 (different working-condition-unknown 3500W Craftsman $125 hammer in Feb); https://www.ebay.com/itm/407229963357 (used Craftsman grinder asking $40). Market prices require condition/model adjustment, and mere asking prices aren't sold comps.
