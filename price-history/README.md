# Auction Price History

Normalized snapshots and closing results used to calibrate future auction reviews.

## Evidence classes
- `current_bid`: interim observed bid. It is **not** market value and not a sold comp.
- `realized`: final hammer/realized price after a lot closes. This is preferred local-auction calibration evidence.
- External research should separately label auction sold, private-party sold, private ask, and dealer ask evidence.

## Auction 779190 files
- `779190-2026-09-30-preclose.csv`: existing pre-close snapshot.
- `779190-current.jsonl`: richer machine-readable pre-close observations captured from the live updater; each row includes observation time and `isFinal:false`.
- After closing, preserve a separate final closing-results dataset rather than overwriting either pre-close file.

## Price semantics
Store hammer/high bid separately from buyer premium, tax, transport, repair, and other acquisition costs. For auction 779190, the official terms state 10% buyer premium for cash/check and 13% for credit/debit. Those premiums belong in landed-cost calculations, not in the stored hammer-price field.

Every reusable observation should retain auctioneer, auction ID/name, lot number, stable lot ID, title, observation time, price type, amount, currency, bid count when available, final/non-final flag, and source.

## Why this matters
Future screening can compare a candidate against actual local auction outcomes without confusing asking prices, interim bids, or fee-adjusted totals with realized hammer value.
