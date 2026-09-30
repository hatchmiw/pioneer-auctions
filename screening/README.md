# Auction screening pipeline

This directory is the durable source of truth for whole-auction screening. Conversation progress notes are not authoritative.

## Workflow
1. **Stage 1 — high-recall triage:** score every live lot using title/description signals tied to the owner's farm, shop, automotive, trailer, construction, property, food-preservation and selective value interests. Low bid/no bid can increase review priority, but never establishes value.
2. **Stage 2 — evidence review:** every retained lot is checked for identity, usefulness, duplication, condition/completeness, power/fuel, transport, current price, and obvious risk. Keyword score is only a routing signal.
3. **Photo review:** inspect original-resolution photos for survivors where photos can change identity, condition, completeness, model or value.
4. **Market research:** research promising/uncertain survivors and distinguish sold/auction/private ask/dealer ask evidence.
5. **Anomaly audit:** independently scan the Stage-1 IGNORE pool for vague titles, recognized brands, heavy equipment, unusually low bids, quantities, or other signals that Stage 1 could miss.
6. **Final shortlist:** actionable survivors only, sorted primarily by closing time.

## Price history
Price observations are stored separately under `price-history/`. A pre-close bid is an **observation**, not a market comp. After an auction closes, realized hammer prices should be appended/updated as `priceType: "realized"`, `isFinal: true`. This allows later auctions to use actual local auction outcomes without confusing asking prices or interim bids with realized value.

## Current run
Auction 779190 Stage 1 screened all 1383 live lots at 2026-09-30T12:08:05Z. Counts: 13 STRONG_TARGET, 118 GOOD_OPPORTUNITY, 79 PRICE_DEPENDENT, 1173 IGNORE. Retained 210 for Stage 2.

The scoring intentionally favors false positives over false negatives. A STRONG_TARGET label at Stage 1 does **not** mean “bid”; it means “review first.”
