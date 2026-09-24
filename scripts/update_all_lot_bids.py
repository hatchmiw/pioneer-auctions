#!/usr/bin/env python3
"""Refresh live public bid state for every lot in active Pioneer HiBid auctions.

The full catalog snapshot (lots.json) remains immutable-ish source data with
photos/descriptions. This updater writes a much smaller auctions/<id>/live.json
containing the current bid/status fields for every lot, and also rebuilds
watchlists/live.json as a compatibility subset.

Cadence is enforced inside the script because GitHub Actions cron itself cannot
express "hourly before auction day, every 10 minutes on auction day" cleanly.
The workflow wakes every 10 minutes; this script skips work until each auction
is due.
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from curl_cffi import requests

GRAPHQL_URL = "https://hibid.com/graphql"
HIBID_HOME = "https://hibid.com/"
AUCTIONS_DIR = Path("auctions")
WATCHLIST_SOURCE = Path("watchlists/latest.json")
WATCHLIST_LIVE = Path("watchlists/live.json")
PAGE_LENGTH = 100
LOCAL_TZ = ZoneInfo("America/Detroit")
UPDATER_VERSION = "2.0.0"

LOT_SEARCH_QUERY = r"""
query LotSearchLotOnly(
  $auctionId: Int = null,
  $pageNumber: Int!,
  $pageLength: Int!,
  $status: AuctionLotStatus = null,
  $sortOrder: EventItemSortOrder = null,
  $filter: AuctionLotFilter = null,
  $isArchive: Boolean = false,
  $countAsView: Boolean = true,
  $hideGoogle: Boolean = false,
  $eventItemIds: [Int!] = null
) {
  lotSearch(
    input: {
      auctionId: $auctionId,
      status: $status,
      sortOrder: $sortOrder,
      filter: $filter,
      isArchive: $isArchive,
      countAsView: $countAsView,
      hideGoogle: $hideGoogle,
      eventItemIds: $eventItemIds
    }
    pageNumber: $pageNumber
    pageLength: $pageLength
    sortDirection: DESC
  ) {
    pagedResults {
      totalCount
      filteredCount
      results {
        id
        itemId
        lotNumber
        lead
        bidAmount
        lotState {
          highBid
          minBid
          bidCount
          status
          timeLeft
          timeLeftSeconds
          isClosed
          isLive
          priceRealized
          reserveSatisfied
        }
        auction {
          id
          eventName
          bidCloseDateTime
          currencyAbbreviation
          auctioneer { id name }
        }
      }
    }
  }
}
"""

AUCTION_DETAILS_QUERY = r"""
query AuctionDetails($id: Int!, $countAsView: Boolean = true) {
  auction(id: $id, countAsView: $countAsView) {
    id
    eventName
    bidOpenDateTime
    bidCloseDateTime
    eventDateBegin
    eventDateEnd
    lotCount
    auctionState {
      auctionStatus
      openLotCount
    }
    auctioneer { id name }
  }
}
"""

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://hibid.com",
    "referer": "https://hibid.com/",
    "apollographql-client-name": "hibid-web",
    "apollographql-client-version": "1.19.1.1",
}


def now_utc_dt() -> datetime:
    return datetime.now(timezone.utc)


def iso_utc(value: datetime | None = None) -> str:
    value = value or now_utc_dt()
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        # HiBid's unqualified auction timestamps for Pioneer are local auction time.
        parsed = parsed.replace(tzinfo=LOCAL_TZ)
    return parsed.astimezone(timezone.utc)


def graphql(session: requests.Session, operation: str, variables: dict, query: str) -> dict:
    response = session.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={"operationName": operation, "variables": variables, "query": query},
        timeout=90,
    )
    response.raise_for_status()
    text = response.text.lstrip()
    if not text.startswith("{"):
        raise RuntimeError(f"{operation}: non-JSON response from HiBid (possible Cloudflare challenge)")
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(f"{operation}: {payload['errors']}")
    return payload.get("data") or {}


def auction_details(session: requests.Session, auction_id: int) -> dict:
    data = graphql(
        session,
        "AuctionDetails",
        {"id": auction_id, "countAsView": False},
        AUCTION_DETAILS_QUERY,
    )
    return data.get("auction") or {}


def discover_auction_ids() -> list[int]:
    ids: list[int] = []
    if not AUCTIONS_DIR.exists():
        return ids
    for path in AUCTIONS_DIR.iterdir():
        if path.is_dir() and path.name.isdigit() and (path / "lots.json").exists():
            ids.append(int(path.name))
    return sorted(ids)


def due_reason(details: dict, previous: dict, now: datetime) -> tuple[bool, str, int]:
    close_dt = parse_dt(details.get("bidCloseDateTime") or details.get("eventDateEnd"))
    previous_checked = parse_dt(previous.get("checkedAt"))
    previous_active = (previous.get("summary") or {}).get("activeLots")
    open_count = ((details.get("auctionState") or {}).get("openLotCount"))

    if close_dt is None:
        interval = 60
        reason = "unknown close time; hourly fallback"
    else:
        local_now = now.astimezone(LOCAL_TZ)
        local_close = close_dt.astimezone(LOCAL_TZ)

        if local_now.date() == local_close.date():
            interval = 10
            reason = "auction day"
        elif now < close_dt:
            interval = 60
            reason = "pre-auction"
        elif open_count not in (None, 0) or now <= close_dt + timedelta(hours=12):
            interval = 10
            reason = "closing/recently closed"
        else:
            # Do not backfill stale auctions just because this new updater was added.
            if not previous:
                return False, "older than 12 hours and no live file", 0
            if previous_active == 0:
                return False, "closed and final live state already stored", 0
            interval = 60
            reason = "past auction with previously active lots"

    if previous_checked is None:
        return True, f"{reason}; no prior live refresh", interval

    elapsed = (now - previous_checked).total_seconds() / 60
    threshold = 9 if interval == 10 else 50
    if elapsed >= threshold:
        return True, f"{reason}; {elapsed:.0f} minutes since last refresh", interval
    return False, f"{reason}; only {elapsed:.0f} minutes since last refresh", interval


def normalize_lot(raw: dict) -> dict:
    state = raw.get("lotState") or {}
    auction = raw.get("auction") or {}
    lot_id = raw.get("id")
    return {
        "hibidLotId": str(lot_id) if lot_id is not None else None,
        "itemId": raw.get("itemId"),
        "lotNumber": None if raw.get("lotNumber") is None else str(raw.get("lotNumber")),
        "title": clean(raw.get("lead")),
        "highBid": state.get("highBid"),
        "nextBid": state.get("minBid"),
        "bidCount": state.get("bidCount"),
        "status": state.get("status"),
        "timeLeft": state.get("timeLeft"),
        "timeLeftSeconds": state.get("timeLeftSeconds"),
        "isClosed": state.get("isClosed"),
        "isLive": state.get("isLive"),
        "priceRealized": state.get("priceRealized"),
        "reserveSatisfied": state.get("reserveSatisfied"),
        "currency": auction.get("currencyAbbreviation") or "USD",
        "auctionId": str(auction.get("id")) if auction.get("id") is not None else None,
        "auctionName": clean(auction.get("eventName")),
        "auctionClose": auction.get("bidCloseDateTime"),
        "auctioneer": clean((auction.get("auctioneer") or {}).get("name")),
        "lotUrl": f"https://hibid.com/lot/{lot_id}" if lot_id is not None else None,
    }


def fetch_all_lots(session: requests.Session, auction_id: int) -> tuple[list[dict], int]:
    results: list[dict] = []
    total = None
    page = 1

    while total is None or len(results) < total:
        variables = {
            "auctionId": auction_id,
            "pageNumber": page,
            "pageLength": PAGE_LENGTH,
            "status": "ALL",
            "sortOrder": "LOT_NUMBER",
            "filter": "ALL",
            "isArchive": False,
            "countAsView": False,
            "hideGoogle": False,
            "eventItemIds": None,
        }
        data = graphql(session, "LotSearchLotOnly", variables, LOT_SEARCH_QUERY)
        paged = ((data.get("lotSearch") or {}).get("pagedResults") or {})
        if total is None:
            total = int(paged.get("totalCount") or paged.get("filteredCount") or 0)
        batch = paged.get("results") or []
        if not batch:
            break
        results.extend(normalize_lot(lot) for lot in batch)
        if len(batch) < PAGE_LENGTH:
            break
        page += 1
        time.sleep(0.20)

    # De-duplicate defensively while preserving lot-number order returned by HiBid.
    deduped: list[dict] = []
    seen: set[str] = set()
    for lot in results:
        key = str(lot.get("hibidLotId"))
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(lot)
    return deduped, total or len(deduped)


def comparable(lot: dict | None) -> dict:
    if not lot:
        return {}
    keys = (
        "highBid", "nextBid", "bidCount", "status", "timeLeftSeconds",
        "isClosed", "isLive", "priceRealized", "reserveSatisfied",
    )
    return {key: lot.get(key) for key in keys}


def build_live(auction_id: int, details: dict, lots: list[dict], reported_total: int, previous: dict) -> dict:
    checked_at = iso_utc()
    previous_map = {
        str(lot.get("hibidLotId")): lot
        for lot in (previous.get("lots") or [])
        if isinstance(lot, dict) and lot.get("hibidLotId") is not None
    }

    changes = []
    for lot in lots:
        prior = previous_map.get(str(lot.get("hibidLotId")))
        before = comparable(prior)
        after = comparable(lot)
        changed = {
            key: {"from": before.get(key), "to": after.get(key)}
            for key in after
            if prior is not None and before.get(key) != after.get(key)
        }
        lot["checkedAt"] = checked_at
        lot["changedSincePreviousCheck"] = bool(changed)
        lot["changedFields"] = changed
        if changed:
            changes.append({
                "hibidLotId": lot.get("hibidLotId"),
                "lotNumber": lot.get("lotNumber"),
                "title": lot.get("title"),
                "fields": changed,
            })

    active = sum(1 for lot in lots if lot.get("isClosed") is not True)
    closed = sum(1 for lot in lots if lot.get("isClosed") is True)
    return {
        "schemaVersion": "2.0",
        "updater": "Pioneer HiBid All-Lot Live Updater",
        "updaterVersion": UPDATER_VERSION,
        "checkedAt": checked_at,
        "auction": {
            "id": str(auction_id),
            "name": clean(details.get("eventName")),
            "bidOpenDateTime": details.get("bidOpenDateTime"),
            "bidCloseDateTime": details.get("bidCloseDateTime"),
            "eventDateBegin": details.get("eventDateBegin"),
            "eventDateEnd": details.get("eventDateEnd"),
            "auctionStatus": (details.get("auctionState") or {}).get("auctionStatus"),
            "openLotCount": (details.get("auctionState") or {}).get("openLotCount"),
            "reportedLotCount": details.get("lotCount") or reported_total,
        },
        "summary": {
            "trackedLots": len(lots),
            "retrievedLots": len(lots),
            "reportedLots": reported_total,
            "activeLots": active,
            "closedLots": closed,
            "changedLotsSincePreviousCheck": len(changes),
        },
        "changes": changes,
        "lots": lots,
    }


def refresh_watchlist_compatibility(all_lots: dict[str, dict], checked_at: str) -> None:
    source = load_json(WATCHLIST_SOURCE)
    source_lots = source.get("lots") or []
    if not source_lots:
        return

    prior = load_json(WATCHLIST_LIVE)
    prior_map = {
        str(lot.get("hibidLotId")): lot
        for lot in (prior.get("lots") or [])
        if isinstance(lot, dict) and lot.get("hibidLotId") is not None
    }

    output = []
    changes = []
    missing = []
    for source_lot in source_lots:
        if not isinstance(source_lot, dict):
            continue
        raw_id = source_lot.get("hibidLotId", source_lot.get("hibid_lot_id", source_lot.get("id")))
        if raw_id is None:
            continue
        lot_id = str(raw_id)
        current = all_lots.get(lot_id)
        if current is None:
            missing.append(lot_id)
            output.append({**source_lot, "hibidLotId": lot_id, "checkedAt": checked_at, "retrievalStatus": "missing-from-live-auctions"})
            continue

        previous = prior_map.get(lot_id)
        before = comparable(previous)
        after = comparable(current)
        changed = {
            key: {"from": before.get(key), "to": after.get(key)}
            for key in after
            if previous is not None and before.get(key) != after.get(key)
        }
        merged = {
            **source_lot,
            **current,
            "hibidLotId": lot_id,
            "checkedAt": checked_at,
            "retrievalStatus": "ok",
            "sourceSnapshotHighBid": source_lot.get("highBid"),
            "sourceSnapshotBidCount": source_lot.get("bidCount"),
            "sourceSnapshotNextBid": source_lot.get("nextBid"),
            "changedSincePreviousCheck": bool(changed),
            "changedFields": changed,
        }
        output.append(merged)
        if changed:
            changes.append({
                "hibidLotId": lot_id,
                "lotNumber": current.get("lotNumber") or source_lot.get("lotNumber"),
                "title": current.get("title") or source_lot.get("title"),
                "auctionId": current.get("auctionId") or source_lot.get("auctionId"),
                "fields": changed,
            })

    result = {
        "schemaVersion": "2.0",
        "updater": "Pioneer HiBid All-Lot Live Updater (watchlist compatibility view)",
        "updaterVersion": UPDATER_VERSION,
        "checkedAt": checked_at,
        "sourceWatchlist": {
            "path": str(WATCHLIST_SOURCE),
            "exportedAt": source.get("exportedAt"),
            "reportedLotCount": source.get("lotCount"),
            "capturedLotCount": len(source_lots),
        },
        "summary": {
            "trackedLots": len(output),
            "retrievedLots": len(output) - len(missing),
            "missingLots": len(missing),
            "activeLots": sum(1 for lot in output if lot.get("retrievalStatus") == "ok" and lot.get("isClosed") is not True),
            "closedLots": sum(1 for lot in output if lot.get("retrievalStatus") == "ok" and lot.get("isClosed") is True),
            "changedLotsSincePreviousCheck": len(changes),
        },
        "changes": changes,
        "missingLotIds": missing,
        "lots": output,
    }
    WATCHLIST_LIVE.parent.mkdir(parents=True, exist_ok=True)
    WATCHLIST_LIVE.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    auction_ids = discover_auction_ids()
    if not auction_ids:
        print("No auction snapshots found under auctions/.", file=sys.stderr)
        return 2

    session = requests.Session(impersonate="chrome")
    session.get(HIBID_HOME, timeout=60)

    now = now_utc_dt()
    refreshed: list[tuple[int, dict]] = []
    skipped: list[tuple[int, str]] = []

    for auction_id in auction_ids:
        live_path = AUCTIONS_DIR / str(auction_id) / "live.json"
        previous = load_json(live_path)
        try:
            details = auction_details(session, auction_id)
        except Exception as exc:
            print(f"WARNING: auction {auction_id}: could not load auction details: {exc}", file=sys.stderr)
            continue

        due, reason, interval = due_reason(details, previous, now)
        if not due:
            skipped.append((auction_id, reason))
            print(f"SKIP {auction_id}: {reason}")
            continue

        print(f"REFRESH {auction_id}: {reason} (target interval {interval} minutes)")
        try:
            lots, reported_total = fetch_all_lots(session, auction_id)
        except Exception as exc:
            print(f"ERROR: auction {auction_id}: lot refresh failed: {exc}", file=sys.stderr)
            return 1

        if not lots and reported_total:
            print(f"ERROR: auction {auction_id}: HiBid reported {reported_total} lots but returned none", file=sys.stderr)
            return 1

        live = build_live(auction_id, details, lots, reported_total, previous)
        live_path.write_text(json.dumps(live, indent=2) + "\n", encoding="utf-8")
        refreshed.append((auction_id, live))
        print(
            f"  {len(lots)} lots; active={live['summary']['activeLots']}; "
            f"closed={live['summary']['closedLots']}; changed={live['summary']['changedLotsSincePreviousCheck']}"
        )

    # Build a single ID map from every available per-auction live file so the old
    # watchlist/live.json consumer continues to receive current values.
    all_lots: dict[str, dict] = {}
    newest_checked = iso_utc(now)
    for auction_id in auction_ids:
        live = load_json(AUCTIONS_DIR / str(auction_id) / "live.json")
        if live.get("checkedAt"):
            newest_checked = max(newest_checked, str(live["checkedAt"]))
        for lot in live.get("lots") or []:
            if isinstance(lot, dict) and lot.get("hibidLotId") is not None:
                all_lots[str(lot["hibidLotId"])] = lot

    if all_lots:
        refresh_watchlist_compatibility(all_lots, newest_checked)

    print(f"Done. Refreshed {len(refreshed)} auction(s); skipped {len(skipped)}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
