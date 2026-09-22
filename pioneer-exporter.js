(() => {
  const catalogMatch = location.pathname.match(/\/catalog\/(\d+)/i);
  const CONFIG = {
    auctionId: Number(catalogMatch?.[1] || 776304),
    pageLength: 100,
    status: "ALL",
    sortOrder: "LOT_NUMBER",
    filter: "ALL",
    pauseMs: 650,
  };

  const GRAPHQL_ENDPOINT = "/graphql";

  const LOT_SEARCH_QUERY = `
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
            featuredPicture {
              fullSizeLocation
              thumbnailLocation
            }
            pictures {
              fullSizeLocation
              thumbnailLocation
            }
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
            category {
              id
              categoryName
              fullCategory
            }
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
              auctioneer {
                id
                name
                country
              }
            }
          }
        }
      }
    }
  `;

  const AUCTION_DETAILS_QUERY = `
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
  `;

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const clean = (v) => String(v ?? "").replace(/\s+/g, " ").trim();
  const md = (v) => clean(v).replace(/</g, "&lt;").replace(/>/g, "&gt;");
  const csv = (v) => '"' + String(v ?? "").replace(/"/g, '""') + '"';

  function download(name, content, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = Object.assign(document.createElement("a"), { href: url, download: name });
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 3000);
  }

  async function graphql(operationName, variables, query) {
    const response = await fetch(GRAPHQL_ENDPOINT, {
      method: "POST",
      credentials: "include",
      headers: {
        accept: "application/json, text/plain, */*",
        "content-type": "application/json",
        "apollographql-client-name": "hibid-web",
      },
      body: JSON.stringify({ operationName, variables, query }),
    });

    const raw = await response.text();
    if (!response.ok) throw new Error(`${operationName}: HTTP ${response.status}`);
    if (!raw.trimStart().startsWith("{")) {
      throw new Error(`${operationName}: HiBid returned a non-JSON response (possible Cloudflare challenge)`);
    }

    const json = JSON.parse(raw);
    if (json.errors?.length) {
      throw new Error(`${operationName}: ${json.errors.map((e) => e.message).join(" | ")}`);
    }
    return json.data ?? {};
  }

  async function fetchAuctionDetails() {
    const data = await graphql(
      "AuctionDetails",
      { id: CONFIG.auctionId, countAsView: false },
      AUCTION_DETAILS_QUERY
    );
    return data.auction ?? null;
  }

  async function fetchLotPage(pageNumber) {
    const data = await graphql(
      "LotSearchLotOnly",
      {
        auctionId: CONFIG.auctionId,
        pageNumber,
        pageLength: CONFIG.pageLength,
        status: CONFIG.status,
        sortOrder: CONFIG.sortOrder,
        filter: CONFIG.filter,
        isArchive: false,
        countAsView: false,
        hideGoogle: false,
        eventItemIds: null,
      },
      LOT_SEARCH_QUERY
    );
    return data?.lotSearch?.pagedResults ?? null;
  }

  function normalizeImages(lot) {
    const candidates = [lot.featuredPicture, ...(lot.pictures ?? [])].filter(Boolean);
    const seen = new Set();
    const images = [];

    for (const image of candidates) {
      const large = image.fullSizeLocation || image.thumbnailLocation || "";
      const small = image.thumbnailLocation || image.fullSizeLocation || "";
      const key = large || small;
      if (!key || seen.has(key)) continue;
      seen.add(key);
      images.push({
        id: null,
        large_path: large,
        small_path: small,
        fullSizeLocation: image.fullSizeLocation ?? null,
        thumbnailLocation: image.thumbnailLocation ?? null,
      });
    }
    return images;
  }

  function normalizeLot(lot) {
    const images = normalizeImages(lot);
    const state = lot.lotState ?? {};
    const auction = lot.auction ?? {};
    return {
      requested_lot_number: lot.lotNumber == null ? "" : String(lot.lotNumber),
      lot_number: lot.lotNumber == null ? "" : String(lot.lotNumber),
      id: lot.id,
      item_id: lot.itemId,
      title: lot.lead ?? "",
      description: lot.description ?? "",
      category: lot.category ?? null,
      shipping_offered: lot.shippingOffered ?? null,
      amount: state.highBid ?? null,
      current_bid: state.highBid ?? null,
      min_bid: state.minBid ?? null,
      bid_count: state.bidCount ?? null,
      price_realized: state.priceRealized ?? null,
      status: state.status ?? null,
      is_closed: state.isClosed ?? null,
      is_live: state.isLive ?? null,
      time_left: state.timeLeft ?? null,
      time_left_seconds: state.timeLeftSeconds ?? null,
      reserve_satisfied: state.reserveSatisfied ?? null,
      currency: auction.currencyAbbreviation ?? "USD",
      auction,
      lot_url: `https://hibid.com/lot/${lot.id}`,
      featured_picture: lot.featuredPicture ?? null,
      images,
      photo_count: images.length,
      source: lot,
    };
  }

  function lotSort(a, b) {
    return String(a.lot_number).localeCompare(String(b.lot_number), undefined, {
      numeric: true,
      sensitivity: "base",
    });
  }

  async function run() {
    if (!/^(?:www\.)?hibid\.com$/i.test(location.hostname)) {
      console.warn(
        "Pioneer exporter works most reliably from https://hibid.com/catalog/<auction-id>/... rather than a regional/auctioneer HiBid portal."
      );
    }

    console.log(`Pioneer/HiBid auction ${CONFIG.auctionId}: retrieving auction details...`);
    const auctionDetails = await fetchAuctionDetails();

    console.log(`Pioneer/HiBid auction ${CONFIG.auctionId}: retrieving lot page 1...`);
    const first = await fetchLotPage(1);
    if (!first) throw new Error("No lotSearch.pagedResults returned for page 1");

    const totalCount = Number(first.totalCount ?? 0);
    const totalPages = Math.max(1, Math.ceil(totalCount / CONFIG.pageLength));
    const rawLots = [...(first.results ?? [])];

    console.log(`Auction reports ${totalCount} lots across ${totalPages} API pages.`);

    for (let page = 2; page <= totalPages; page++) {
      await sleep(CONFIG.pauseMs);
      console.log(`Retrieving lot page ${page}/${totalPages}...`);
      const result = await fetchLotPage(page);
      if (!result) throw new Error(`No lotSearch.pagedResults returned for page ${page}`);
      rawLots.push(...(result.results ?? []));
    }

    const lots = rawLots.map(normalizeLot).sort(lotSort);
    const retrievedAt = new Date().toISOString();
    const photoCount = lots.reduce((sum, lot) => sum + lot.photo_count, 0);

    const data = {
      source: "HiBid / Pioneer Auction Service",
      auction_id: CONFIG.auctionId,
      retrieved_at: retrievedAt,
      catalog_url: location.href,
      auction: auctionDetails,
      total_reported: totalCount,
      total_retrieved: lots.length,
      total_photos: photoCount,
      lots,
    };

    let summary = `# Pioneer / HiBid Auction ${CONFIG.auctionId}\n\n`;
    summary += `- Auction: ${md(auctionDetails?.eventName || "")}\n`;
    summary += `- Retrieved: ${retrievedAt}\n`;
    summary += `- Lots reported by HiBid: ${totalCount}\n`;
    summary += `- Lots retrieved: ${lots.length}\n`;
    summary += `- Photos found: ${photoCount}\n`;
    if (auctionDetails?.auctioneer?.name) summary += `- Auctioneer: ${md(auctionDetails.auctioneer.name)}\n`;
    if (auctionDetails?.bidCloseDateTime) summary += `- Auction close: ${md(auctionDetails.bidCloseDateTime)}\n`;
    summary += "\n";

    for (const lot of lots) {
      summary += `---\n\n## Lot ${md(lot.lot_number)} — ${md(lot.title)}\n\n`;
      summary += `- HiBid lot ID: ${lot.id ?? ""}\n`;
      summary += `- Current bid: ${lot.current_bid ?? ""} ${md(lot.currency)}\n`;
      summary += `- Price realized: ${lot.price_realized ?? ""} ${md(lot.currency)}\n`;
      summary += `- Bid count: ${lot.bid_count ?? ""}\n`;
      summary += `- Photo count: ${lot.photo_count}\n`;
      summary += `- Category: ${md(lot.category?.fullCategory || lot.category?.categoryName || "")}\n`;
      summary += `- Lot page: ${lot.lot_url}\n\n`;

      if (clean(lot.description)) summary += `**Description:** ${md(lot.description)}\n\n`;

      if (lot.images.length) {
        summary += "**Photos:**\n\n";
        lot.images.forEach((image, index) => {
          summary += `- [Photo ${index + 1}](${image.large_path})\n`;
        });
        summary += "\n";
      }
    }

    const rows = [[
      "lot",
      "hibid_lot_id",
      "item_id",
      "current_bid",
      "price_realized",
      "bid_count",
      "photo_count",
      "status",
      "time_left_seconds",
      "category",
      "title",
      "lot_url",
    ].map(csv).join(",")];

    for (const lot of lots) {
      rows.push([
        lot.lot_number,
        lot.id,
        lot.item_id,
        lot.current_bid,
        lot.price_realized,
        lot.bid_count,
        lot.photo_count,
        lot.status,
        lot.time_left_seconds,
        lot.category?.fullCategory || lot.category?.categoryName || "",
        clean(lot.title),
        lot.lot_url,
      ].map(csv).join(","));
    }

    download("summary.md", summary, "text/markdown;charset=utf-8");
    download("lots.json", JSON.stringify(data, null, 2), "application/json;charset=utf-8");
    download("summary.csv", rows.join("\r\n"), "text/csv;charset=utf-8");

    console.log(
      `DONE — ${lots.length}/${totalCount} lots retrieved with ${photoCount} photos. Downloaded summary.md, lots.json, and summary.csv.`
    );
  }

  run().catch((error) => {
    console.error("PIONEER EXPORTER ERROR:", error);
    console.error(
      "If this was run from a regional or auctioneer HiBid portal, reopen the auction on https://hibid.com/catalog/... and run the launcher again."
    );
  });
})();