#!/usr/bin/env python3
"""Refresh public HiBid bid state for the lots in watchlists/latest.json.

The watchlist snapshot is the authoritative list of lots to track. This script
uses HiBid's public GraphQL API to refresh price/status fields without needing a
HiBid login, then writes watchlists/live.json for ChatGPT/review tooling.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

from curl_cffi import requests

GRAPHQL_URL = "https://hibid.com/graphql"
HIBID_HOME = "https://hibid.com/"
SOURCE_PATH = Path("watchlists/latest.json")
OUTPUT_PATH = Path("watchlists/live.json")
CHUNK_SIZE = 75
UPDATER_VERSION = "1.0.0"

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

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://hibid.com",
    "referer": "https://hibid.com/",
    "apollographql-client-name": "hibid-web",
    "apollographql-client-version": "1.19.1.1",
}


def now_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def clean(value: Any) -> str:
    return " ".join(str(value or "").split())


def load_json(path: Path, required: bool = True) -> dict:
    if not path.exists():
        if required:
            raise RuntimeError(f"Missing required file: {path}")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def source_hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def extract_lot_id(lot: dict) -> int | None:
    for key in ("hibidLotId", "hibid_lot_id", "id"):
        value = lot.get(key)
        if value is None:
            continue
        try:
            return int(str(value).strip())
        except ValueError:
            continue
    return None


def graphql(session: requests.Session, variables: dict) -> dict:
    response = session.post(
        GRAPHQL_URL,
        headers=HEADERS,
        json={
            "operationName": "LotSearchLotOnly",
            "variables": variables,
            "query": LOT_SEARCH_QUERY,
        },
        timeout=90,
    )
    response.raise_for_status()
    text = response.text.lstrip()
    if not text.startswith("{"):
        raise RuntimeError("HiBid returned a non-JSON response (possible Cloudflare challenge)")
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(f"HiBid GraphQL errors: {payload['errors']}")
    return payload.get("data") or {}


def fetch_ids(session: requests.Session, ids: list[int]) -> dict[int, dict]:
    found: dict[int, dict] = {}
    for start in range(0, len(ids), CHUNK_SIZE):
        chunk = ids[start : start + CHUNK_SIZE]
        variables = {
            "auctionId": None,
            "pageNumber": 1,
            "pageLength": max(len(chunk), 1),
            "status": "ALL",
            "sortOrder": "LOT_NUMBER",
            "filter": "ALL",
            "isArchive": False,
            "countAsView": False,
            "hideGoogle": False,
            "eventItemIds": chunk,
        }
        data = graphql(session, variables)
        paged = ((data.get("lotSearch") or {}).get("pagedResults") or {})
        for lot in paged.get("results") or []:
            try:
                found[int(lot.get("id"))] = lot
            except (TypeError, ValueError):
                continue
        if start + CHUNK_SIZE < len(ids):
            time.sleep(0.5)
    return found


def normalize_public(raw: dict) -> dict:
    state = raw.get("lotState") or {}
    auction = raw.get("auction") or {}
    return {
        "hibidLotId": str(raw.get("id")) if raw.get("id") is not None else None,
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
        "lotUrl": f"https://hibid.com/lot/{raw.get('id')}" if raw.get("id") is not None else None,
    }


def comparable(lot: dict | None) -> dict:
    if not lot:
        return {}
    keys = (
        "highBid",
        "nextBid",
        "bidCount",
        "status",
        "timeLeftSeconds",
        "isClosed",
        "isLive",
        "priceRealized",
        "reserveSatisfied",
    )
    return {key: lot.get(key) for key in keys}


def main() -> int:
    if not SOURCE_PATH.exists():
        print(f"ERROR: {SOURCE_PATH} does not exist", file=sys.stderr)
        return 2

    source_raw = SOURCE_PATH.read_bytes()
    source = json.loads(source_raw.decode("utf-8"))
    source_lots = source.get("lots") or []
    if not isinstance(source_lots, list) or not source_lots:
        print("ERROR: watchlists/latest.json has no lots array", file=sys.stderr)
        return 2

    tracked: list[tuple[int, dict]] = []
    invalid = []
    seen = set()
    for index, lot in enumerate(source_lots):
        lot_id = extract_lot_id(lot if isinstance(lot, dict) else {})
        if lot_id is None:
            invalid.append(index)
            continue
        if lot_id in seen:
            continue
        seen.add(lot_id)
        tracked.append((lot_id, lot))

    if not tracked:
        print("ERROR: no usable HiBid lot IDs were found", file=sys.stderr)
        return 2

    previous = load_json(OUTPUT_PATH, required=False)
    previous_map = {
        str(lot.get("hibidLotId")): lot
        for lot in (previous.get("lots") or [])
        if isinstance(lot, dict) and lot.get("hibidLotId") is not None
    }

    session = requests.Session(impersonate="chrome")
    session.get(HIBID_HOME, timeout=60)
    public = fetch_ids(session, [lot_id for lot_id, _ in tracked])

    checked_at = now_utc()
    output_lots = []
    changes = []
    missing = []

    for lot_id, source_lot in tracked:
        raw = public.get(lot_id)
        source_copy = dict(source_lot)
        source_copy["hibidLotId"] = str(lot_id)

        if raw is None:
            missing.append(str(lot_id))
            output_lots.append({
                **source_copy,
                "checkedAt": checked_at,
                "retrievalStatus": "missing-from-public-query",
            })
            continue

        current = normalize_public(raw)
        previous_lot = previous_map.get(str(lot_id))
        prior = comparable(previous_lot)
        current_cmp = comparable(current)

        changed_fields = {
            key: {"from": prior.get(key), "to": current_cmp.get(key)}
            for key in current_cmp
            if previous_lot is not None and prior.get(key) != current_cmp.get(key)
        }

        if previous_lot is None:
            source_high = source_lot.get("highBid")
            if source_high != current.get("highBid"):
                changed_fields["highBid"] = {"from": source_high, "to": current.get("highBid")}
            source_count = source_lot.get("bidCount")
            if source_count != current.get("bidCount"):
                changed_fields["bidCount"] = {"from": source_count, "to": current.get("bidCount")}

        merged = {
            **source_copy,
            **current,
            "checkedAt": checked_at,
            "retrievalStatus": "ok",
            "sourceSnapshotHighBid": source_lot.get("highBid"),
            "sourceSnapshotBidCount": source_lot.get("bidCount"),
            "sourceSnapshotNextBid": source_lot.get("nextBid"),
            "changedSincePreviousCheck": bool(changed_fields),
            "changedFields": changed_fields,
        }
        output_lots.append(merged)

        if changed_fields:
            changes.append({
                "hibidLotId": str(lot_id),
                "lotNumber": current.get("lotNumber") or source_lot.get("lotNumber"),
                "title": current.get("title") or source_lot.get("title"),
                "auctionId": current.get("auctionId") or source_lot.get("auctionId"),
                "fields": changed_fields,
            })

    active_count = sum(
        1 for lot in output_lots
        if lot.get("retrievalStatus") == "ok" and lot.get("isClosed") is not True
    )
    closed_count = sum(
        1 for lot in output_lots
        if lot.get("retrievalStatus") == "ok" and lot.get("isClosed") is True
    )

    src_hash = source_hash(source_raw)
    result = {
        "schemaVersion": "1.0",
        "updater": "Pioneer HiBid Watchlist Bid Updater",
        "updaterVersion": UPDATER_VERSION,
        "checkedAt": checked_at,
        "sourceWatchlist": {
            "path": str(SOURCE_PATH),
            "exportedAt": source.get("exportedAt"),
            "reportedLotCount": source.get("lotCount"),
            "capturedLotCount": len(source_lots),
            "sha256": src_hash,
        },
        "summary": {
            "trackedLots": len(tracked),
            "retrievedLots": len(tracked) - len(missing),
            "missingLots": len(missing),
            "activeLots": active_count,
            "closedLots": closed_count,
            "changedLotsSincePreviousCheck": len(changes),
            "invalidSourceRows": len(invalid),
        },
        "changes": changes,
        "missingLotIds": missing,
        "lots": output_lots,
    }

    previous_source_hash = (previous.get("sourceWatchlist") or {}).get("sha256")
    previous_active = (previous.get("summary") or {}).get("activeLots")
    if (
        previous
        and active_count == 0
        and previous_active == 0
        and previous_source_hash == src_hash
        and not changes
        and not missing
    ):
        print("All tracked lots are already closed and unchanged; leaving live.json untouched.")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    print(
        f"Refreshed {len(tracked) - len(missing)}/{len(tracked)} tracked lots; "
        f"active={active_count}, closed={closed_count}, changed={len(changes)}, missing={len(missing)}"
    )
    if missing:
        print("Missing IDs: " + ", ".join(missing))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
