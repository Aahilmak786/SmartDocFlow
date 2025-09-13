#!/usr/bin/env python3
import os
from pathlib import Path
import cairosvg

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'docs' / 'media'
OUT = SRC / 'png'

SVG_FILES = [
    ('logo.svg', [1, 2, 3]),               # 1x, 2x, 3x scale
    ('banner.svg', [1]),                   # full size
    ('social-card.svg', [1]),              # 1200x630
    ('thumbnail.svg', [1]),                # 1280x720
]

OUT.mkdir(parents=True, exist_ok=True)

for filename, scales in SVG_FILES:
    svg_path = SRC / filename
    if not svg_path.exists():
        print(f"Skipping missing {svg_path}")
        continue

    svg_bytes = svg_path.read_bytes()

    for scale in scales:
        out_name = f"{svg_path.stem}@{scale}x.png" if scale != 1 else f"{svg_path.stem}.png"
        out_path = OUT / out_name
        try:
            cairosvg.svg2png(bytestring=svg_bytes, write_to=str(out_path), scale=scale)
            print(f"✅ Wrote {out_path}")
        except Exception as e:
            print(f"❌ Failed to export {svg_path} at {scale}x: {e}")

print("Done.")


