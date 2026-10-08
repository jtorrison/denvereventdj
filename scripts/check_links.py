#!/usr/bin/env python3
"""
Link checker for the static site. Crawls every *.html file and verifies:
  - in-page anchor links (#id) resolve to an element with that id
  - relative links resolve to a real file (honoring folder/index.html
    GitHub Pages URLs, e.g. /weddings/ -> weddings/index.html)
  - external http(s) links return a non-error status (best effort; a
    timeout or network hiccup is reported as a warning, not a failure)

Links to paths listed in PLANNED_PAGES are reported as informational
notices, not failures — docs/site-plan.md defines pages that don't exist
yet and will land in a later phase.

Usage: python3 scripts/check_links.py
Exit code is non-zero only on broken internal links or malformed anchors.
"""
import html.parser
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Pages from docs/site-plan.md's page map that aren't built yet (Phase 1-3).
# Referencing one of these today is expected, not a bug.
PLANNED_PAGES = {
    "/weddings/", "/corporate-events/", "/parties/", "/pricing/", "/about/",
    "/mixes/", "/reviews/", "/faq/", "/contact/", "/stories/", "/venues/",
    "/venues/denver/", "/venues/mountain-weddings/", "/venues/outdoor-weddings/",
    "/guides/", "/guides/choosing-a-wedding-dj/", "/guides/playlist-vs-live-dj/",
    "/privacy/",
}

SKIP_SCHEMES = ("mailto:", "tel:", "javascript:")


class LinkExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []  # (tag, attr_value)
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(("href", attrs["href"]))
        if tag == "img" and attrs.get("src"):
            self.links.append(("src", attrs["src"]))
        if tag == "link" and attrs.get("href"):
            self.links.append(("href", attrs["href"]))
        if tag == "script" and attrs.get("src"):
            self.links.append(("src", attrs["src"]))


def resolve_local_path(link, page_path):
    """Resolve a relative/absolute local link to a filesystem path, or None."""
    if link.startswith("/"):
        candidate = ROOT / link.lstrip("/")
    else:
        candidate = (page_path.parent / link).resolve()
    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate


def check_file(page_path, external_checks, errors, warnings, notices):
    text = page_path.read_text(encoding="utf-8", errors="replace")
    parser = LinkExtractor()
    parser.feed(text)
    rel = page_path.relative_to(ROOT)

    for kind, link in parser.links:
        link = link.strip()
        if not link or link.startswith(SKIP_SCHEMES) or link.startswith("#"):
            if link.startswith("#") and len(link) > 1:
                anchor = link[1:]
                if anchor not in parser.ids:
                    errors.append(f"{rel}: broken anchor link '{link}' (no id=\"{anchor}\" on this page)")
            continue
        if link.startswith("http://") or link.startswith("https://"):
            if external_checks:
                check_external(link, rel, warnings)
            continue
        if link.startswith("data:"):
            continue

        path_only = link.split("#")[0].split("?")[0]
        if not path_only:
            continue

        if path_only in PLANNED_PAGES:
            notices.append(f"{rel}: links to planned page '{path_only}' (not built yet, see docs/site-plan.md)")
            continue

        target = resolve_local_path(path_only, page_path)
        if not target.exists():
            errors.append(f"{rel}: broken {kind}='{link}' -> {target.relative_to(ROOT)} does not exist")


def check_external(url, rel, warnings):
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "link-checker"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status >= 400:
                warnings.append(f"{rel}: external link {url} returned {resp.status}")
    except urllib.error.HTTPError as e:
        if e.code >= 400 and e.code != 403:  # many sites 403 HEAD requests from bots
            warnings.append(f"{rel}: external link {url} returned {e.code}")
    except Exception as e:  # noqa: BLE001 - best effort, never fail the build on network flake
        warnings.append(f"{rel}: could not verify external link {url} ({e})")


def main():
    external_checks = "--external" in sys.argv
    html_files = sorted(ROOT.rglob("*.html"))
    html_files = [
        p for p in html_files
        if "_inbox" not in p.parts and "node_modules" not in p.parts and "partials" not in p.parts
    ]

    errors, warnings, notices = [], [], []
    for page in html_files:
        check_file(page, external_checks, errors, warnings, notices)

    if notices:
        print(f"Notices ({len(notices)}):")
        for n in notices:
            print(f"  i  {n}")
        print()

    if warnings:
        print(f"Warnings ({len(warnings)}):")
        for w in warnings:
            print(f"  !  {w}")
        print()

    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  x  {e}")
        print()
        print(f"FAILED: {len(errors)} broken link(s) across {len(html_files)} page(s).")
        sys.exit(1)

    print(f"OK: checked {len(html_files)} page(s), no broken internal links.")


if __name__ == "__main__":
    main()
