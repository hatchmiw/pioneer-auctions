#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

LOCAL_TZ = ZoneInfo("America/Detroit")
KEEP_AFTER_CLOSE = timedelta(days=7)
MAX_ARTIFACT_RETENTION_DAYS = 90


def parse_close(raw: str) -> datetime:
    if not raw:
        raise ValueError("Missing auction bidCloseDateTime")
    close = datetime.fromisoformat(raw.strip().replace("Z", "+00:00"))
    if close.tzinfo is None:
        close = close.replace(tzinfo=LOCAL_TZ)
    return close


def load_info(lots_path: Path):
    data = json.loads(lots_path.read_text(encoding="utf-8"))
    auction_id = str(data.get("auction_id") or lots_path.parent.name)
    auction = data.get("auction") or {}
    close = parse_close(str(auction.get("bidCloseDateTime") or ""))
    cleanup = close + KEEP_AFTER_CLOSE
    return auction_id, close, cleanup


def one_auction(auction_id: str) -> int:
    lots_path = Path("auctions") / auction_id / "lots.json"
    if not lots_path.exists():
        print(f"Missing {lots_path}", file=sys.stderr)
        return 2

    _, close, cleanup = load_info(lots_path)
    now = datetime.now(timezone.utc)
    seconds = (cleanup.astimezone(timezone.utc) - now).total_seconds()
    days = max(1, math.ceil(seconds / 86400))
    retention_days = min(days, MAX_ARTIFACT_RETENTION_DAYS)
    expired = now >= cleanup.astimezone(timezone.utc)

    if days > MAX_ARTIFACT_RETENTION_DAYS:
        print(
            f"WARNING: cleanup is {days} days away; GitHub artifact retention is capped at "
            f"{MAX_ARTIFACT_RETENTION_DAYS} days.",
            file=sys.stderr,
        )

    print(f"expired={'true' if expired else 'false'}")
    print(f"cleanup_at={cleanup.astimezone(timezone.utc).isoformat()}")
    print(f"retention_days={retention_days}")
    print(f"auction_close={close.astimezone(timezone.utc).isoformat()}")
    return 0


def due_auctions() -> int:
    now = datetime.now(timezone.utc)
    for lots_path in sorted(Path("auctions").glob("*/lots.json")):
        try:
            auction_id, _, cleanup = load_info(lots_path)
        except Exception as exc:
            print(f"WARNING: {lots_path}: {exc}", file=sys.stderr)
            continue
        if now >= cleanup.astimezone(timezone.utc):
            print(auction_id)
    return 0


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--due":
        return due_auctions()
    if len(sys.argv) == 2:
        return one_auction(sys.argv[1].strip())
    print("Usage: photo_retention.py <auction_id> | --due", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
