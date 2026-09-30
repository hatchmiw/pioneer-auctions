# Auction Screening Pipeline

## Goal
Screen every lot cheaply and reproducibly, then spend photo/market-research effort only on survivors.

1. Merge permanent catalog and live bid state by lot number/HiBid ID.
2. Stage 1 permissive relevance/value screen. Prefer false positives over false negatives.
3. Anomaly pass: vague descriptions, zero/low bids, recognized brands, large/heavy lots, unusual quantities, and categories where titles are unreliable.
4. Deep review survivors: original photos, identity/model, completeness, condition, power/fuel, transport, duplicates, repair burden, local used value and resale liquidity.
5. Assign final classification and Bargain / Good Buy / Absolute Max hammer levels.
6. Before/after auction, save normalized price snapshots. After close, realized prices become historical comps for future auctions.

## Durable fields
Stage 1 retains catalog entry, lot number, HiBid ID, title/description/category, photo count, current/next bid, bid count, status, score/classification/reasons and lot URL. Deep review should add photo_reviewed, model_identity, condition, completeness, estimated_value_low/high, bargain_max, good_buy_max, absolute_max, transport, power, risk, research_sources and notes.

## Price-history policy
Never discard an auction's closing data. Store one normalized CSV under `price-history/` keyed by auction ID/date. Preserve auctioneer, title, lot IDs, high/realized price, bid count and status. Future screening can match by normalized title/category/brand/model and distinguish auction hammer from private-party/dealer asking prices.
