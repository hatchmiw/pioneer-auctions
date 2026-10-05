#!/usr/bin/env python3
"""Build one compact review sheet per Pioneer/HiBid lot."""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

THUMB_W = 360
THUMB_H = 270
LABEL_H = 44
COLS = 3
MARGIN = 18
BG = "white"


def natural_key(value: str):
    parts = re.split(r"(\d+)", value)
    return [(0, int(part)) if part.isdigit() else (1, part.lower()) for part in parts]


def fit_image(path: Path):
    image = Image.open(path).convert("RGB")
    image = ImageOps.exif_transpose(image)
    image.thumbnail((THUMB_W, THUMB_H), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (THUMB_W, THUMB_H), BG)
    x = (THUMB_W - image.width) // 2
    y = (THUMB_H - image.height) // 2
    canvas.paste(image, (x, y))
    return canvas


def main() -> int:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: build_contact_sheets.py <auction_id>")

    auction_id = str(sys.argv[1]).strip()
    root = Path("auctions") / auction_id / "photos"
    if not root.is_dir():
        raise SystemExit(f"Missing {root}")

    lot_dirs = sorted([path for path in root.iterdir() if path.is_dir()], key=lambda p: natural_key(p.name))
    made = 0

    for lot_dir in lot_dirs:
        photos = sorted(
            [
                path
                for path in lot_dir.glob("*.jpg")
                if path.name not in {"contact.jpg", "review.jpg"}
            ],
            key=lambda p: p.name,
        )
        if not photos:
            continue

        rows = math.ceil(len(photos) / COLS)
        cell_w = THUMB_W
        cell_h = THUMB_H + LABEL_H
        sheet_w = MARGIN * 2 + COLS * cell_w
        sheet_h = MARGIN * 2 + rows * cell_h
        sheet = Image.new("RGB", (sheet_w, sheet_h), BG)
        draw = ImageDraw.Draw(sheet)

        for index, photo in enumerate(photos):
            row = index // COLS
            col = index % COLS
            x = MARGIN + col * cell_w
            y = MARGIN + row * cell_h
            tile = fit_image(photo)
            sheet.paste(tile, (x, y))
            draw.rectangle(
                (x, y + THUMB_H, x + cell_w - 1, y + cell_h - 1),
                fill=(245, 245, 245),
            )
            draw.text(
                (x + 12, y + THUMB_H + 10),
                f"Lot {lot_dir.name} — Photo {index + 1} ({photo.name})",
                fill="black",
            )

        output = lot_dir / "review.jpg"
        sheet.save(output, "JPEG", quality=72, optimize=True, progressive=True)
        print(output)
        made += 1

    print(f"Created {made} review sheets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
