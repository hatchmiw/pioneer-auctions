# Pioneer 784296 — Oct 18 live vs baseline audit (20:04:31Z)

Source: original repo snapshot `auctions/784296/summary.csv` exported **2026-10-18T13:50:28Z** and most recent confirmed successful **Update All Pioneer Lot Bids** file `auctions/784296/live.json` at **2026-10-18T20:04:31Z** (GitHub Actions run **39161615653**, conclusion SUCCESS). Cross-check was performed over every row and exact stable HiBid lot ID and exact title text, not a sample.

- Baseline lot count: **1307**. Current update: **1307**, **1307 open**, **0 closed**.
- New lot numbers **0**; disappeared lot numbers **0**; changed stable HiBid lot IDs **0**; changed exact title strings **0**. The 1,307 rows match on number, ID, and title as of this updater.
- **150** of 1,307 lots changed bid amount and/or bid count compared with baseline. These changes are expected bidding activity, not evidence of catalog photo/description edits.
- The generic updater counter `changedLotsSincePreviousCheck=1307` is dominated by countdown time changes; **not** an accurate count of new lots or meaningful bid edits.
- **Critical limits:** Current live data does not expose *listing descriptions, full photo inventory, photo-order signatures or changes in terms*. Identical ID/title/count is NOT proof listing content unchanged. The seller's general "More lots coming soon" notice remains visible publicly. A true metadata/photo-signature check still needs a fresh catalog-side extraction and stable-photo comparison, preserving historical photos and already-reviewed work.
- Normalized complete 1,307-row preclosing bid snapshot committed to `price-history/784296-20261018T200431Z-preclose.csv`. These are **current/high bids at the observation time**, not hammer/realized sold values; no user bidding authorized.
- Priority watch re-assessed from this exact snapshot: `screening/784296/candidate-bidwatch-2026-10-18T200431Z.csv` (48 condition-dependent candidates, including #721 MOTU). #5 snowblower high bid rose $2→$21 compared with the 17:07Z watch; next $22 exceeds prior $12 tested planning cap — pass at present price. #1200 shop-vac $2→$3. Other 36 earlier watchlist current bids unchanged during that comparison.

Do not run a full download of all 10,331 source photos merely because live countdown clocks update; preserve baseline artifacts until the already-known 2026-10-28 cleanup.
