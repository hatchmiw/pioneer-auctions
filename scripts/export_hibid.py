#!/usr/bin/env python3
"""Export one HiBid auction directly into auctions/<auction_id>/.

Designed for GitHub Actions. It bootstraps a browser-like HiBid session with
curl_cffi, queries HiBid's GraphQL API, and writes:
  - README.md
  - summary.md
  - lots.json
  - summary.csv
"""

from __future__ import annotations

import csv
import html
import json
import re
import sys
import time
from pathlib import Path

from curl_cffi import requests

GRAPHQL_URL = "https://hibid.com/graphql"
HIBID_HOME = "https://hibid.com/"
PAGE_LENGTH = 100

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
      pageLength
      pageNumber
      totalCount
      filteredCount
      results {
        id
        itemId
        lotNumber
        lead
        description
        bidAmount
        pictureCount
        shippingOffered
        featuredPicture { fullSizeLocation thumbnailLocation }
        pictures { fullSizeLocation thumbnailLocation }
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
        category { id categoryName fullCategory }
        auction {
          id
          eventName
          bidCloseDateTime
          bidOpenDateTime
          eventAddress
          eventCity
          eventState
          eventZip
          buyerPremiumRate
          currencyAbbreviation
          auctioneer { id name country }
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
    description
    bidOpenDateTime
    bidCloseDateTime
    eventAddress
    eventCity
    eventState
    eventZip
    eventDateBegin
    eventDateEnd
    buyerPremium
    buyerPremiumRate
    showBuyerPremium
    lotCount
    auctioneer {
      id
      name
      phone
      email
      city
      state
      country
      internetAddress
    }
    auctionState {
      auctionStatus
      openLotCount
    }
    sourceType
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


def clean(value) -> str:
    return " ".join(str(value or "").split())


def natural_key(value: str):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r"(\d+)", value)]


def category_text(category) -> str:
    """Return readable category text whether HiBid sends an object or a list."""
    if isinstance(category, dict):
        return clean(category.get("fullCategory") or category.get("categoryName") or "")
    if isinstance(category, list):
        parts = []
        for item in category:
            if isinstance(item, dict):
                value = clean(item.get("fullCategory") or item.get("categoryName") or "")
            else:
                value = clean(item)
            if value and value not in parts:
                parts.append(value)
        return " | ".join(parts)
    return clean(category)


def graphql(session, operation: str, variables: dict, query: str) -> dict:
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


def normalize_images(lot: dict) -> list[dict]:
    candidates = [lot.get("featuredPicture"), *(lot.get("pictures") or [])]
    images = []
    seen = set()
    for image in candidates:
        if not image:
            continue
        large = image.get("fullSizeLocation") or image.get("thumbnailLocation") or ""
        small = image.get("thumbnailLocation") or image.get("fullSizeLocation") or ""
        key = large or small
        if not key or key in seen:
            continue
        seen.add(key)
        images.append(
            {
                "id": None,
                "large_path": large,
                "small_path": small,
                "fullSizeLocation": image.get("fullSizeLocation"),
                "thumbnailLocation": image.get("thumbnailLocation"),
            }
        )
    return images


def normalize_lot(lot: dict) -> dict:
    images = normalize_images(lot)
    state = lot.get("lotState") or {}
    auction = lot.get("auction") or {}
    number = "" if lot.get("lotNumber") is None else str(lot.get("lotNumber"))
    return {
        "requested_lot_number": number,
        "lot_number": number,
        "id": lot.get("id"),
        "item_id": lot.get("itemId"),
        "title": lot.get("lead") or "",
        "description": lot.get("description") or "",
        "category": lot.get("category"),
        "shipping_offered": lot.get("shippingOffered"),
        "amount": state.get("highBid"),
        "current_bid": state.get("highBid"),
        "min_bid": state.get("minBid"),
        "bid_count": state.get("bidCount"),
        "price_realized": state.get("priceRealized"),
        "status": state.get("status"),
        "is_closed": state.get("isClosed"),
        "is_live": state.get("isLive"),
        "time_left": state.get("timeLeft"),
        "time_left_seconds": state.get("timeLeftSeconds"),
        "reserve_satisfied": state.get("reserveSatisfied"),
        "currency": auction.get("currencyAbbreviation") or "USD",
        "auction": auction,
        "lot_url": f"https://hibid.com/lot/{lot.get('id')}",
        "featured_picture": lot.get("featuredPicture"),
        "images": images,
        "photo_count": len(images),
        "reported_picture_count": lot.get("pictureCount"),
        "bid_amount_raw": lot.get("bidAmount"),
    }


def write_outputs(auction_id: int, auction: dict, lots: list[dict], total_reported: int) -> None:
    output_dir = Path("auctions") / str(auction_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    retrieved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    photo_count = sum(lot["photo_count"] for lot in lots)

    data = {
        "source": "HiBid / Pioneer Auction Service",
        "auction_id": auction_id,
        "retrieved_at": retrieved_at,
        "catalog_url": f"https://hibid.com/catalog/{auction_id}",
        "auction": auction,
        "total_reported": total_reported,
        "total_retrieved": len(lots),
        "total_photos": photo_count,
        "lots": lots,
    }
    (output_dir / "lots.json").write_text(json.dumps(data, indent=2), encoding="utf-8")

    with (output_dir / "summary.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "lot", "hibid_lot_id", "item_id", "current_bid", "price_realized",
            "bid_count", "photo_count", "status", "time_left_seconds",
            "category", "title", "lot_url",
        ])
        for lot in lots:
            category = lot.get("category")
            writer.writerow([
                lot["lot_number"], lot["id"], lot["item_id"], lot["current_bid"],
                lot["price_realized"], lot["bid_count"], lot["photo_count"],
                lot["status"], lot["time_left_seconds"],
                category_text(category),
                clean(lot["title"]), lot["lot_url"],
            ])

    lines = [
        f"# Pioneer / HiBid Auction {auction_id}",
        "",
        f"- Auction: {clean(auction.get('eventName'))}",
        f"- Retrieved: {retrieved_at}",
        f"- Lots reported by HiBid: {total_reported}",
        f"- Lots retrieved: {len(lots)}",
        f"- Photos found: {photo_count}",
    ]
    if auction.get("auctioneer", {}).get("name"):
        lines.append(f"- Auctioneer: {clean(auction['auctioneer']['name'])}")
    if auction.get("bidCloseDateTime"):
        lines.append(f"- Auction close: {auction['bidCloseDateTime']}")
    lines.append("")

    for lot in lots:
        category = lot.get("category")
        lines += [
            "---",
            "",
            f"## Lot {lot['lot_number']} — {clean(lot['title'])}",
            "",
            f"- HiBid lot ID: {lot['id']}",
            f"- Current bid: {lot['current_bid'] if lot['current_bid'] is not None else ''} {lot['currency']}",
            f"- Price realized: {lot['price_realized'] if lot['price_realized'] is not None else ''} {lot['currency']}",
            f"- Bid count: {lot['bid_count'] if lot['bid_count'] is not None else ''}",
            f"- Photo count: {lot['photo_count']}",
            f"- Category: {category_text(category)}",
            f"- Lot page: {lot['lot_url']}",
            "",
        ]
        if clean(lot["description"]):
            lines += [f"**Description:** {clean(lot['description'])}", ""]
        if lot["images"]:
            lines += ["**Photos:**", ""]
            for index, image in enumerate(lot["images"], start=1):
                lines.append(f"- [Photo {index}]({image['large_path']})")
            lines.append("")

    (output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    readme = [
        f"# {clean(auction.get('eventName')) or f'HiBid Auction {auction_id}'}",
        "",
        f"- Auction ID: **{auction_id}**",
        f"- Auctioneer: **{clean((auction.get('auctioneer') or {}).get('name'))}**",
        f"- Last export: **{retrieved_at}**",
        f"- Lots: **{len(lots)}**",
        f"- Photos referenced: **{photo_count}**",
        "",
        "Files:",
        "",
        "- [summary.md](./summary.md)",
        "- [summary.csv](./summary.csv)",
        "- [lots.json](./lots.json) — full catalog snapshot; bid values reflect export time",
        "- [live.json](./live.json) — current bids/status for all lots (created separately by Update All Pioneer Lot Bids; absent until its first eligible refresh)",
        "- [photo-batches.json](./photo-batches.json) — maps each lot to its temporary photo artifact",
        "",
        "Run the repository's **Run Pioneer Auction** GitHub Action again to refresh this catalog snapshot and its temporary photo batches.",
        "The **Update All Pioneer Lot Bids** Action independently refreshes live.json on an auction-aware schedule (roughly hourly beforehand, every ten minutes on auction day); it does not rewrite catalog descriptions or photos.",
    ]
    (output_dir / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    print(f"Wrote {len(lots)} lots and {photo_count} photo references to {output_dir}")


def main() -> int:
    if len(sys.argv) != 2 or not sys.argv[1].isdigit():
        print("Usage: python scripts/export_hibid.py <auction_id>", file=sys.stderr)
        return 2

    auction_id = int(sys.argv[1])
    session = requests.Session(impersonate="chrome")
    session.get(HIBID_HOME, timeout=60)

    auction_data = graphql(
        session,
        "AuctionDetails",
        {"id": auction_id, "countAsView": False},
        AUCTION_DETAILS_QUERY,
    )
    auction = auction_data.get("auction") or {}
    if not auction:
        raise RuntimeError(f"HiBid returned no auction details for {auction_id}")

    first_data = graphql(
        session,
        "LotSearchLotOnly",
        {
            "auctionId": auction_id,
            "pageNumber": 1,
            "pageLength": PAGE_LENGTH,
            "status": "ALL",
            "sortOrder": "LOT_NUMBER",
            "filter": "ALL",
            "isArchive": False,
            "countAsView": False,
            "hideGoogle": False,
            "eventItemIds": None,
        },
        LOT_SEARCH_QUERY,
    )
    first = ((first_data.get("lotSearch") or {}).get("pagedResults") or {})
    total_count = int(first.get("totalCount") or 0)
    raw_lots = list(first.get("results") or [])
    total_pages = max(1, (total_count + PAGE_LENGTH - 1) // PAGE_LENGTH)
    print(f"HiBid auction {auction_id}: {total_count} lots across {total_pages} pages")

    for page in range(2, total_pages + 1):
        time.sleep(1)
        print(f"Fetching page {page}/{total_pages}")
        data = graphql(
            session,
            "LotSearchLotOnly",
            {
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
            },
            LOT_SEARCH_QUERY,
        )
        paged = ((data.get("lotSearch") or {}).get("pagedResults") or {})
        raw_lots.extend(paged.get("results") or [])

    lots = [normalize_lot(lot) for lot in raw_lots]
    lots.sort(key=lambda lot: natural_key(lot["lot_number"]))
    if len(lots) != total_count:
        print(f"WARNING: HiBid reported {total_count} lots but {len(lots)} were retrieved")

    write_outputs(auction_id, auction, lots, total_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
