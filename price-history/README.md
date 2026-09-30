# Auction Price History

Normalized snapshots and closing results used to calibrate future auction reviews.

- `779190-2026-09-30-preclose.csv` is a pre-close snapshot, **not final realized-price data**.
- After the auction closes, capture a final snapshot and preserve it separately as a closing-results file.
- Hammer/high-bid data should not be mixed with buyer-premium/tax-adjusted cost. Store hammer first; calculate acquisition cost separately using that auction's terms.
- Keep source auction ID, lot ID and title so future comparisons remain auditable.
