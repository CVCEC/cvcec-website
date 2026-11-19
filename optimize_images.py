#!/usr/bin/env python3
"""Make light web versions of the photos: docs/images/w/<name>.webp (max 1600 px).

The originals in docs/images/ are kept as an archive (and for social-media
previews). build.py uses the light version automatically when it exists.
Needs Pillow:  pip install pillow
"""
from pathlib import Path
from PIL import Image, ImageOps

SRC = Path(__file__).parent / "docs" / "images"
OUT = SRC / "w"
MAX = 1600


def main():
    OUT.mkdir(exist_ok=True)
    made = 0
    for f in sorted(SRC.iterdir()):
        if not f.is_file():
            continue
        target = OUT / (f.stem + ".webp")
        if target.exists() and target.stat().st_mtime >= f.stat().st_mtime:
            continue
        with Image.open(f) as im:
            im = ImageOps.exif_transpose(im)
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA" if "transparency" in im.info or im.mode in ("LA", "P") else "RGB")
            if im.width > MAX:
                im = im.resize((MAX, round(im.height * MAX / im.width)), Image.LANCZOS)
            im.save(target, "WEBP", quality=80, method=6)
            made += 1
    total = sum(p.stat().st_size for p in OUT.iterdir()) / 1024 / 1024
    print(f"Made {made} web images; folder size {total:.1f} MB")


if __name__ == "__main__":
    main()
