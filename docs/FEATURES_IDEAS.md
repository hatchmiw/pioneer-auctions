# Features / Ideas Backlog

This document preserves auction-review ideas that should be considered when the scoring/bidding algorithm is reworked. It is a backlog, **not** a description of current implemented behavior.

## Bid-analysis fields to add

### Condition
Capture the item's observed condition separately from value.

Suggested structure:
- condition class: `verified_good`, `likely_good`, `unknown`, `rough`, `damaged_or_incomplete`
- condition confidence
- photo-review completeness / evidence source
- important visible defects, missing parts, testing status, and repair uncertainty

A catalog title or nominal market value must not substitute for photo-based condition evidence. If all available photos were not actually reviewed, the analysis should say so.

### Intent
Classify why the item is being considered. At minimum:
- `personal_use`
- `resale`
- `speculative`
- `parts_or_project`

Intent should materially affect the bid recommendation.

### EV — Expected Value
Estimate realistic expected value rather than only favorable-case market value.

EV should account for relevant uncertainty, including:
- probability the item works / is complete
- repair or cleanup cost
- missing parts
- resale friction and likely negotiation
- fees/shipping/listing effort when resale is the intent
- value if the item fails and becomes parts/scrap/project material

Personal-use EV and resale EV may differ and should not be conflated.

### Bargain
Add an explicit bargain indicator, preferably derived from the relationship among price, condition, confidence, intent, and EV.

The purpose is to identify items where the downside is strongly protected — not merely items priced below an abstract market value.

### Risk-Adjusted Bid
Add a bid amount that reflects the user's acceptable downside if the condition thesis is wrong.

This is especially important for untested or visibly rough items. A high favorable-case value does **not** imply that the buyer should bid near that value when failure risk is substantial.

### Personal Stretch
Add a separate optional ceiling for items genuinely wanted for personal use.

Use only when:
- the item solves a real need or is specifically wanted,
- condition confidence is sufficient for the amount at risk, and
- used cost remains attractive versus realistic replacement cost.

This should not be applied to ordinary resale inventory.

### Absolute Ceiling
Keep an absolute hammer-price ceiling.

Important: the absolute ceiling is a **stop point, not a target price**. Post-auction reviews should not criticize a buyer merely for stopping below the ceiling when the bargain or risk-adjusted thesis disappeared.

## Behavioral / decision principles

- The default objective is **bargain acquisition with downside protection**, not maximizing win rate.
- For resale, require meaningful margin. A narrow spread (for example, paying roughly $50 to hope to sell near $65) is generally unattractive once uncertainty, time, fees, storage, negotiation, and failed-sale risk are considered.
- Unknown-condition items should often be governed by: **"How much am I comfortable losing if this is junk?"**
- Personal-use items may justify a higher bid when condition is known and replacement cost supports it.
- A lot closing one bid increment above the user's max does **not** mean one more bid would have won. HiBid proxy bidding hides the winner's actual maximum.
- Do not use hindsight realized prices alone to label a decision good or bad.
- Condition evidence and intended use should be stated explicitly when recommending or criticizing a bid.
- When the analysis and the user's judgment differ, surface the disagreement and the evidence rather than automatically agreeing or treating the algorithm as authoritative.
- The system should call out genuinely weak bidding behavior when evidence supports it, while remaining explicit about uncertainty and photo/model-identification limitations.

## Future workflow ideas

A future bidding board could display, per lot:

`Condition | Condition Confidence | Intent | EV | Bargain | Risk-Adjusted Bid | Personal Stretch | Absolute Ceiling`

Additional useful fields to consider later:
- photo review status / number of photos reviewed
- tested / untested / unknown
- repair-cost estimate
- resale friction / liquidity
- replacement cost for personal-use items
- downside / salvage value
- reasoning / condition gates
- confidence in maker/model identification

## Open work

The broader auction-screening / scoring algorithm still needs a separate review and correction. Do not treat the fields above as a complete redesign. Preserve them for that future work so they are not lost when the algorithm is revisited.
