#!/usr/bin/env python3
"""
WCAG color-contrast checker. Reads the :root custom properties from
styles.css and checks a fixed list of foreground/background pairs that
the design actually uses (body text, muted text, gold accents, buttons).

Add a pair to PAIRS when a new color combination is introduced in the CSS.

Usage: python3 scripts/check_contrast.py
Exit code is non-zero if any pair fails its WCAG AA threshold.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS_FILE = ROOT / "styles.css"

# (label, foreground var, background var, "normal" | "large", min required)
# "large" = 18pt+/14pt-bold+ (buttons, headings, eyebrows) -> AA threshold 3:1
# "normal" = body copy -> AA threshold 4.5:1
PAIRS = [
    ("body text on bg",           "--text",  "--bg",       "normal"),
    ("muted text on bg",          "--muted", "--bg",       "normal"),
    ("muted text on surface",     "--muted", "--surface",  "normal"),
    ("gold eyebrow on bg",        "--gold",  "--bg",       "large"),
    ("gold eyebrow on surface",   "--gold",  "--surface",  "large"),
    ("btn-primary text on gold",  "--bg",    "--gold",     "large"),
    ("text on surface",           "--text",  "--surface",  "normal"),
    ("text on surface2",          "--text",  "--surface2", "normal"),
]

THRESHOLDS = {"normal": 4.5, "large": 3.0}


def parse_root_vars(css_text):
    root_block = re.search(r":root\s*{([^}]*)}", css_text, re.S)
    if not root_block:
        print("Could not find :root block in styles.css")
        sys.exit(1)
    vars_ = {}
    for name, value in re.findall(r"(--[\w-]+)\s*:\s*([^;]+);", root_block.group(1)):
        vars_[name.strip()] = value.strip()
    return vars_


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))


def relative_luminance(rgb):
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(hex_a, hex_b):
    lum_a = relative_luminance(hex_to_rgb(hex_a))
    lum_b = relative_luminance(hex_to_rgb(hex_b))
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def main():
    if not CSS_FILE.exists():
        print(f"{CSS_FILE} not found")
        sys.exit(1)

    css_vars = parse_root_vars(CSS_FILE.read_text(encoding="utf-8"))
    failures = []

    print(f"{'Pair':<28} {'Ratio':>7}  {'Needs':>6}  Result")
    print("-" * 56)
    for label, fg_var, bg_var, size in PAIRS:
        fg = css_vars.get(fg_var)
        bg = css_vars.get(bg_var)
        if not fg or not bg:
            print(f"{label:<28} -- missing CSS var {fg_var} or {bg_var}")
            continue
        ratio = contrast_ratio(fg, bg)
        needed = THRESHOLDS[size]
        ok = ratio >= needed
        status = "PASS" if ok else "FAIL"
        print(f"{label:<28} {ratio:>6.2f}  {needed:>5.1f}  {status}")
        if not ok:
            failures.append(f"{label}: {ratio:.2f}:1 < required {needed}:1 ({fg_var} on {bg_var})")

    print()
    if failures:
        print(f"FAILED: {len(failures)} pair(s) below WCAG AA.")
        for f in failures:
            print(f"  x  {f}")
        sys.exit(1)

    print(f"OK: all {len(PAIRS)} checked pairs meet WCAG AA.")


if __name__ == "__main__":
    main()
