#!/usr/bin/env python3
"""
Make smaller copies of every photo in assets/photos/ for responsive images.

For each assets/photos/<name>.webp this writes
assets/photos/sizes/<name>-480w.webp, -800w and -1200w (only the widths
smaller than the original). Existing copies are left alone, so it's safe
to re-run after adding new photos. Then run scripts/build.py, which adds a
matching srcset to every <img> that uses the photo.

Uses Pillow if it's installed, otherwise the cwebp command-line tool
(`brew install webp`).

Usage:
  python3 scripts/make_image_sizes.py           # make any missing sizes
  python3 scripts/make_image_sizes.py --force   # remake all of them
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PHOTOS = ROOT / "assets" / "photos"
SIZES = PHOTOS / "sizes"
WIDTHS = (480, 800, 1200)
QUALITIES = (78, 70, 62, 55)  # tried in order until the copy is small enough

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import webp_size  # noqa: E402

try:
    from PIL import Image
except ImportError:  # fall back to cwebp
    Image = None


def encode(src, dst, width, quality):
    if Image is not None:
        with Image.open(src) as im:
            h = round(im.height * width / im.width)
            im.resize((width, h), Image.LANCZOS).save(dst, "WEBP", quality=quality, method=6)
        return
    if not shutil.which("cwebp"):
        sys.exit("Need Pillow (pip3 install pillow) or cwebp (brew install webp).")
    subprocess.run(["cwebp", "-quiet", "-q", str(quality), "-resize", str(width), "0",
                    str(src), "-o", str(dst)], check=True)


def resize(src, dst, width, orig_width):
    """Smaller copy at the best quality that still saves real bytes: at
    most the original's size scaled by (width / orig_width) ** 1.5."""
    budget = src.stat().st_size * (width / orig_width) ** 1.5
    for q in QUALITIES:
        encode(src, dst, width, q)
        if dst.stat().st_size <= budget:
            return


def main():
    force = "--force" in sys.argv
    SIZES.mkdir(exist_ok=True)
    made = 0
    for src in sorted(PHOTOS.glob("*.webp")):
        dims = webp_size(src)
        if not dims:
            print(f"  skip (can't read size): {src.name}")
            continue
        for w in WIDTHS:
            if w >= dims[0]:
                continue
            dst = SIZES / f"{src.stem}-{w}w.webp"
            if dst.exists() and not force:
                continue
            resize(src, dst, w, dims[0])
            made += 1
            print(f"  {dst.relative_to(ROOT)}  {dst.stat().st_size // 1024} KB")
    print(f"Made {made} image size(s). Now run: python3 scripts/build.py")


if __name__ == "__main__":
    main()
