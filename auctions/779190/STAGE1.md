# Auction 779190 — Stage 1 machine screen

Generated from the permanent catalog plus live bid state on 2026-09-30.

This is a permissive triage layer, not the final bidding judgment. False positives are intentionally preferred over false negatives. Lots classified STRONG TARGET, GOOD OPPORTUNITY, PRICE-DEPENDENT, or REVIEW advance to human/photo/market review as appropriate. Existing researched bid caps override machine scoring.

## Counts

- REVIEW: 653
- PRICE-DEPENDENT: 198
- GOOD OPPORTUNITY: 79
- STRONG TARGET: 104
- IGNORE: 350
- Total records screened: 1384
- Permanent catalog records: 1381
- Live records: 1383

## Rules

The score prioritizes farm, shop, automotive/trailer, property-maintenance and recognized-value terms; gives a small boost to zero-bid and photo-rich lots; and suppresses common low-priority decor/collectible terms. It does **not** infer condition or market value from title alone.

Source of truth: `stage1-screen.csv`. Deep-review findings should be recorded separately and linked by lot number/HiBid lot ID rather than overwriting the raw triage evidence.
