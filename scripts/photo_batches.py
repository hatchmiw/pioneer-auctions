#!/usr/bin/env python3
"""Build fixed-size photo batches from an auction lots.json.

Usage:
    python scripts/photo_batches.py <auction_id> [batch_size]

Prints GitHub Actions outputs:
    matrix=<json>
    batch_count=<n>
    lot_count=<n>

Batches are based on lot sequence in lots.json, not numeric lot value, so
alphanumeric lot numbers and gaps are handled correctly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def safe_text(value) -> str:
    return str(value or "").strip()


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("Usage: photo_batches.py <auction_id> [batch_size]", file=sys.stderr)
        return 2

    auction_id = safe_text(sys.argv[1])
    batch_size = int(sys.argv[2]) if len(sys.argv) == 3 else 100
    if batch_size < 1:
        print("batch_size must be positive", file=sys.stderr)
        return 2

    lots_path = Path("auctions") / auction_id / "lots.json"
    if not lots_path.exists():
        print(f"Missing {lots_path}", file=sys.stderr)
        return 2

    data = json.loads(lots_path.read_text(encoding="utf-8"))
    lots = data.get("lots") or []

    batches = []
    for start in range(0, len(lots), batch_size):
        end = min(start + batch_size, len(lots))
        first = lots[start] if start < len(lots) else {}
        last = lots[end - 1] if end else {}
        first_lot = safe_text(
            first.get("lot_number")
            or first.get("requested_lot_number")
            or first.get("id")
        )
        last_lot = safe_text(
            last.get("lot_number")
            or last.get("requested_lot_number")
            or last.get("id")
        )
        label = f"{start + 1:04d}-{end:04d}"
        batches.append(
            {
                "start": start,
                "end": end,
                "label": label,
                "first_lot": first_lot,
                "last_lot": last_lot,
            }
        )

    for batch in batches:
        start = batch["start"]
        end = batch["end"]
        batch["artifact_name"] = f"pioneer-{auction_id}-photos-{batch['label']}"
        batch["lots"] = [
            safe_text(
                lot.get("lot_number")
                or lot.get("requested_lot_number")
                or lot.get("id")
            )
            for lot in lots[start:end]
        ]

    plan = {
        "auction_id": int(auction_id) if auction_id.isdigit() else auction_id,
        "batch_size": batch_size,
        "lot_count": len(lots),
        "batch_count": len(batches),
        "batches": batches,
    }
    plan_path = Path("auctions") / auction_id / "photo-batches.json"
    plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

    matrix = {
        "batch": [
            {
                "start": batch["start"],
                "end": batch["end"],
                "label": batch["label"],
                "first_lot": batch["first_lot"],
                "last_lot": batch["last_lot"],
                "artifact_name": batch["artifact_name"],
            }
            for batch in batches
        ]
    }
    print("matrix=" + json.dumps(matrix, separators=(",", ":")))
    print(f"batch_count={len(batches)}")
    print(f"lot_count={len(lots)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
