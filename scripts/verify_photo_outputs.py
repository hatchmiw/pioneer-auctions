#!/usr/bin/env python3
"""Verify that a mirrored Pioneer/HiBid photo workspace exactly matches lots.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from mirror_photos import safe_lot_dir


def lot_number(lot: dict) -> str:
    return str(
        lot.get("lot_number")
        or lot.get("requested_lot_number")
        or lot.get("id")
        or "unknown"
    )


def image_url(image: dict) -> str:
    return str(
        image.get("large_path")
        or image.get("fullSizeLocation")
        or image.get("small_path")
        or image.get("thumbnailLocation")
        or ""
    )


def expected_photos(lots: list[dict]) -> list[tuple[str, int, str]]:
    rows = []
    for lot in lots:
        number = lot_number(lot)
        for index, image in enumerate(lot.get("images") or [], start=1):
            url = image_url(image)
            if url:
                rows.append((number, index, url))
    return rows


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: verify_photo_outputs.py <auction_id>")

    auction_id = str(sys.argv[1]).strip()
    auction_dir = Path("auctions") / auction_id
    lots_path = auction_dir / "lots.json"
    photo_root = auction_dir / "photos"
    manifest_path = photo_root / "manifest.json"

    if not lots_path.is_file() or not manifest_path.is_file():
        raise SystemExit("Missing lots.json or photos/manifest.json")

    data = json.loads(lots_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    lots = data.get("lots") or []
    expected = expected_photos(lots)
    expected_set = set(expected)

    manifest_rows = manifest.get("photos") or []
    actual_set = {
        (str(row.get("lot")), int(row.get("index")), str(row.get("source_url")))
        for row in manifest_rows
    }

    problems = []
    if manifest.get("lot_count") != len(lots):
        problems.append(f"manifest lot_count={manifest.get('lot_count')} expected={len(lots)}")
    if manifest.get("photo_count") != len(expected):
        problems.append(f"manifest photo_count={manifest.get('photo_count')} expected={len(expected)}")
    if manifest.get("error_count"):
        problems.append(f"manifest error_count={manifest.get('error_count')}")
    if len(manifest_rows) != len(expected):
        problems.append(f"manifest rows={len(manifest_rows)} expected={len(expected)}")
    if actual_set != expected_set:
        missing = len(expected_set - actual_set)
        extra = len(actual_set - expected_set)
        problems.append(f"manifest photo mapping mismatch: {missing} missing, {extra} extra")

    expected_files = {
        photo_root / safe_lot_dir(number) / f"{index:02d}.jpg"
        for number, index, _ in expected
    }
    missing_files = [
        path for path in expected_files if not path.is_file() or path.stat().st_size == 0
    ]
    if missing_files:
        problems.append(f"{len(missing_files)} expected image files missing/empty")

    extra_files = {
        path
        for path in photo_root.rglob("*.jpg")
        if path.name not in {"review.jpg", "contact.jpg"} and path not in expected_files
    }
    if extra_files:
        problems.append(f"{len(extra_files)} stale/extra image files")

    expected_dirs = {safe_lot_dir(number) for number, _, _ in expected}
    actual_dirs = {path.name for path in photo_root.iterdir() if path.is_dir()}
    if actual_dirs != expected_dirs:
        missing = expected_dirs - actual_dirs
        extra = actual_dirs - expected_dirs
        problems.append(
            f"photo directory mismatch: {len(missing)} missing, {len(extra)} stale/extra"
        )

    missing_reviews = [
        lot_dir for lot_dir in sorted(expected_dirs)
        if not (photo_root / lot_dir / "review.jpg").is_file()
    ]
    if missing_reviews:
        problems.append(f"{len(missing_reviews)} lots are missing review.jpg")

    if problems:
        raise SystemExit("Photo artifact verification failed: " + "; ".join(problems))

    print(
        f"Verified clean photo workspace: {len(lots)} lots, "
        f"{len(expected)} photos, {len(expected_dirs)} review sheets."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
