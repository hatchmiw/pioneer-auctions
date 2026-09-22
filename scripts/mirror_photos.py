#!/usr/bin/env python3
"""Mirror HiBid/Pioneer lot photos into this GitHub repository.

Usage:
    python scripts/mirror_photos.py 776304
    python scripts/mirror_photos.py 776304 0 100

With start/end indexes, only that zero-based slice of lots.json is mirrored.
This is used by GitHub Actions to keep each photo artifact small enough for
selective retrieval.

Reads:
    auctions/<auction_id>/lots.json

Writes:
    auctions/<auction_id>/photos/<lot>/01.jpg ...
    auctions/<auction_id>/photos/<lot>/README.md
    auctions/<auction_id>/photos/manifest.json
    auctions/<auction_id>/photos/README.md

The original HiBid CDN URL is preserved in the manifest. Images are normalized
for repository use; the original URL remains available when more detail is needed.
"""

from __future__ import annotations

import io
import json
import re
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image, ImageOps

MAX_EDGE = 1600
JPEG_QUALITY = 82
WORKERS = 8
RETRIES = 3
USER_AGENT = "Mozilla/5.0 PioneerAuctionMirror/1.0"


def download_bytes(url: str) -> bytes:
    last_error = None
    for attempt in range(1, RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                    "Referer": "https://hibid.com/",
                },
            )
            with urllib.request.urlopen(req, timeout=45) as response:
                return response.read()
        except Exception as exc:
            last_error = exc
            if attempt < RETRIES:
                time.sleep(attempt * 2)
    raise RuntimeError(f"Failed after {RETRIES} attempts: {url} ({last_error})")


def normalize_image(raw: bytes, output_path: Path) -> dict:
    with Image.open(io.BytesIO(raw)) as image:
        source_width, source_height = image.size
        image = ImageOps.exif_transpose(image)

        if image.mode not in ("RGB", "L"):
            if "A" in image.getbands():
                background = Image.new("RGB", image.size, "white")
                alpha = image.getchannel("A")
                background.paste(image.convert("RGB"), mask=alpha)
                image = background
            else:
                image = image.convert("RGB")
        elif image.mode == "L":
            image = image.convert("RGB")

        image.thumbnail((MAX_EDGE, MAX_EDGE), Image.Resampling.LANCZOS)
        width, height = image.size
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(
            output_path,
            format="JPEG",
            quality=JPEG_QUALITY,
            optimize=True,
            progressive=True,
        )

    return {
        "source_width": source_width,
        "source_height": source_height,
        "width": width,
        "height": height,
        "bytes": output_path.stat().st_size,
    }


def clean(value) -> str:
    return " ".join(str(value or "").split())


def safe_lot_dir(value) -> str:
    value = clean(value) or "unknown"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._") or "unknown"


def natural_key(value: str):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", value)]


def mirror_one(task: dict) -> dict:
    output_path: Path = task["output_path"]
    if output_path.exists() and output_path.stat().st_size > 0:
        with Image.open(output_path) as image:
            width, height = image.size
        return {
            **task,
            "status": "existing",
            "width": width,
            "height": height,
            "bytes": output_path.stat().st_size,
        }

    raw = download_bytes(task["source_url"])
    meta = normalize_image(raw, output_path)
    return {**task, **meta, "status": "downloaded"}


def main() -> int:
    if len(sys.argv) not in (2, 4):
        print(
            "Usage: python scripts/mirror_photos.py <auction_id> [start_index end_index]",
            file=sys.stderr,
        )
        return 2

    auction_id = str(sys.argv[1]).strip()
    start_index = None
    end_index = None
    if len(sys.argv) == 4:
        start_index = int(sys.argv[2])
        end_index = int(sys.argv[3])
        if start_index < 0 or end_index <= start_index:
            print("Invalid lot slice", file=sys.stderr)
            return 2
    auction_dir = Path("auctions") / auction_id
    lots_path = auction_dir / "lots.json"

    if not lots_path.exists():
        print(f"Missing {lots_path}", file=sys.stderr)
        return 2

    with lots_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    all_lots = data.get("lots", [])
    if start_index is None:
        lots = all_lots
        photo_root = auction_dir / "photos"
        batch_label = None
    else:
        if start_index >= len(all_lots):
            print(f"Start index {start_index} is outside {len(all_lots)} lots", file=sys.stderr)
            return 2
        end_index = min(end_index, len(all_lots))
        lots = all_lots[start_index:end_index]
        batch_label = f"{start_index + 1:04d}-{end_index:04d}"
        photo_root = auction_dir / "photo_batches" / batch_label

    photo_root.mkdir(parents=True, exist_ok=True)

    tasks = []
    for lot in lots:
        lot_number = str(
            lot.get("lot_number")
            or lot.get("requested_lot_number")
            or lot.get("id")
            or "unknown"
        )
        lot_dir = safe_lot_dir(lot_number)
        for index, image in enumerate(lot.get("images") or [], start=1):
            source_url = (
                image.get("large_path")
                or image.get("fullSizeLocation")
                or image.get("small_path")
                or image.get("thumbnailLocation")
            )
            if not source_url:
                continue
            tasks.append(
                {
                    "lot": lot_number,
                    "lot_dir": lot_dir,
                    "index": index,
                    "source_url": source_url,
                    "output_path": photo_root / lot_dir / f"{index:02d}.jpg",
                }
            )

    scope = (
        f"batch {batch_label}" if batch_label else "full auction"
    )
    print(
        f"Auction {auction_id} ({scope}): {len(lots)} selected lots, "
        f"{len(tasks)} photos"
    )

    results = []
    errors = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(mirror_one, task): task for task in tasks}
        for future in as_completed(futures):
            task = futures[future]
            try:
                result = future.result()
                results.append(result)
                print(
                    f"[{result['status']}] lot {result['lot']} photo "
                    f"{result['index']:02d} -> {result['output_path']}"
                )
            except Exception as exc:
                errors.append(
                    {
                        "lot": task["lot"],
                        "index": task["index"],
                        "source_url": task["source_url"],
                        "error": str(exc),
                    }
                )
                print(
                    f"[ERROR] lot {task['lot']} photo {task['index']:02d}: {exc}",
                    file=sys.stderr,
                )

    results.sort(key=lambda x: (natural_key(x["lot"]), x["index"]))

    lots_by_number = {}
    for lot in lots:
        lot_number = str(
            lot.get("lot_number")
            or lot.get("requested_lot_number")
            or lot.get("id")
            or "unknown"
        )
        lots_by_number[lot_number] = lot

    for lot_number, lot in lots_by_number.items():
        lot_results = [r for r in results if r["lot"] == lot_number]
        if not lot_results:
            continue

        lines = [
            f"# Lot {lot_number}",
            "",
            clean(lot.get("title")),
            "",
            f"- Snapshot bid: {lot.get('current_bid', lot.get('amount', ''))}",
            f"- Price realized: {lot.get('price_realized', '')}",
            f"- Bid count: {lot.get('bid_count', '')}",
            f"- Mirrored photos: {len(lot_results)}",
            f"- HiBid page: {lot.get('lot_url', '')}",
            "",
        ]

        for result in lot_results:
            filename = Path(result["output_path"]).name
            lines += [
                f"## Photo {result['index']}",
                "",
                f"![Lot {lot_number} photo {result['index']}]({filename})",
                "",
                f"[Original HiBid image]({result['source_url']})",
                "",
            ]

        lot_readme = photo_root / safe_lot_dir(lot_number) / "README.md"
        lot_readme.write_text("\n".join(lines), encoding="utf-8")

    manifest = {
        "auction_id": int(auction_id) if auction_id.isdigit() else auction_id,
        "source_snapshot": str(lots_path),
        "lot_count": len(lots),
        "total_auction_lot_count": len(all_lots),
        "batch_label": batch_label,
        "start_index": start_index,
        "end_index": end_index,
        "photo_count": len(results),
        "error_count": len(errors),
        "max_edge": MAX_EDGE,
        "jpeg_quality": JPEG_QUALITY,
        "photos": [
            {
                "lot": result["lot"],
                "index": result["index"],
                "source_url": result["source_url"],
                "repo_path": str(result["output_path"]).replace("\\", "/"),
                "width": result.get("width"),
                "height": result.get("height"),
                "bytes": result.get("bytes"),
            }
            for result in results
        ],
        "errors": errors,
    }

    (photo_root / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    index_lines = [
        f"# Pioneer / HiBid Auction {auction_id} Photo Mirror"
        + (f" — Batch {batch_label}" if batch_label else ""),
        "",
        f"- Lots in this archive: {len(lots)}",
        f"- Total lots in auction snapshot: {len(all_lots)}",
        f"- Photos mirrored: {len(results)}",
        f"- Errors: {len(errors)}",
        "",
        "Each lot below has its own folder and gallery page.",
        "",
    ]

    for lot_number in sorted(lots_by_number, key=natural_key):
        lot = lots_by_number[lot_number]
        count = sum(1 for result in results if result["lot"] == lot_number)
        if not count:
            continue
        title = clean(lot.get("title"))
        index_lines.append(
            f"- [Lot {lot_number}](./{safe_lot_dir(lot_number)}/README.md) — {count} photos — {title}"
        )

    (photo_root / "README.md").write_text(
        "\n".join(index_lines) + "\n",
        encoding="utf-8",
    )

    print("")
    print(f"DONE: {len(results)} photos mirrored; {len(errors)} errors.")
    if errors:
        print("See photos/manifest.json for failures.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
