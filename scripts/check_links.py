#!/usr/bin/env python3
"""
Link checker for the static site. Crawls every *.html file and verifies:
  - in-page anchor links (#id) resolve to an element with that id
  - relative/root-relative links resolve to a real file (honoring
    folder/index.html GitHub Pages URLs, e.g. /weddings/ -> weddings/index.html)
  - external http(s) links return a non-error status (best effort; a
    timeout or network hiccup is reported as a warning, not a failure)
  - no internal <a> link ends in .html/index.html, and no folder-style
    internal link is missing its trailing slash (assets, anchors, tel:,
    mailto:, and external URLs are exempt)
  - every page is listed in sitemap.xml and vice versa (noindex pages
    exempt)
  - no stray *.html file sits next to an index.html (every page is
    <folder>/index.html, never <folder>/page.html) — root 404.html and
    anything under partials/scripts/_inbox are exempt

Links to paths listed in PLANNED_PAGES are reported as informational
notices, not failures — _docs/site-plan.md (local, gitignored) defines
pages that don't exist yet and will land in a later phase.

Usage: python3 scripts/check_links.py
Exit code is non-zero on any error (broken link, malformed anchor, bad
URL shape, sitemap mismatch, or stray filename). Warnings/notices don't
fail the build.
"""
import html.parser
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIR_NAMES = {".git", ".github", "partials", "scripts", "_inbox", "_docs", "assets"}

# Pages from _docs/site-plan.md's page map that aren't built yet. Referencing
# one of these today is expected, not a bug.
PLANNED_PAGES = {
    "/weddings/", "/corporate-events/", "/parties/", "/pricing/", "/about/",
    "/mixes/", "/reviews/", "/faq/", "/contact/", "/venues/",
    "/venues/denver/", "/venues/mountain-weddings/", "/venues/outdoor-weddings/",
    "/guides/choosing-a-wedding-dj/", "/guides/playlist-vs-live-dj/",
    "/privacy/",
}

SKIP_SCHEMES = ("mailto:", "tel:", "javascript:")
ASSET_EXTENSIONS = (
    ".css", ".js", ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico",
    ".xml", ".txt", ".pdf", ".json",
)


class LinkExtractor(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []  # (source_tag, attr, value)
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(("a", "href", attrs["href"]))
        if tag == "img" and attrs.get("src"):
            self.links.append(("img", "src", attrs["src"]))
        if tag == "link" and attrs.get("href"):
            self.links.append(("link", "href", attrs["href"]))
        if tag == "script" and attrs.get("src"):
            self.links.append(("script", "src", attrs["src"]))


def resolve_local_path(link, page_path):
    """Resolve a relative/absolute local link to a filesystem path, or None."""
    if link.startswith("/"):
        candidate = ROOT / link.lstrip("/")
    else:
        candidate = (page_path.parent / link).resolve()
    if candidate.is_dir():
        candidate = candidate / "index.html"
    return candidate


def check_url_shape(source_tag, path_only, rel, errors):
    """No visitor-facing URL ever shows .html; folder links need a trailing slash."""
    if source_tag != "a":
        return  # only <a> links are "visitor-facing navigation"
    if path_only.endswith(ASSET_EXTENSIONS):
        return
    if path_only.endswith(".html"):
        errors.append(f"{rel}: internal link '{path_only}' ends in .html — use the trailing-slash folder form")
        return
    if not path_only.endswith("/"):
        errors.append(f"{rel}: internal link '{path_only}' is missing its trailing slash")


def check_file(page_path, external_checks, errors, warnings, notices):
    text = page_path.read_text(encoding="utf-8", errors="replace")
    parser = LinkExtractor()
    parser.feed(text)
    rel = page_path.relative_to(ROOT)

    for source_tag, kind, link in parser.links:
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
            continue  # pure fragment, e.g. "/#booking" already handled via the "/" prefix below

        if path_only in PLANNED_PAGES:
            notices.append(f"{rel}: links to planned page '{path_only}' (not built yet, see _docs/site-plan.md)")
            continue

        check_url_shape(source_tag, path_only, rel, errors)

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


def discover_pages():
    pages = []
    for path in sorted(ROOT.rglob("index.html")):
        rel_parts = path.relative_to(ROOT).parts
        if any(part in EXCLUDE_DIR_NAMES for part in rel_parts):
            continue
        pages.append(path)
    not_found = ROOT / "404.html"
    if not_found.exists():
        pages.append(not_found)
    return pages


def url_for(page_path):
    rel = page_path.relative_to(ROOT)
    if rel.name == "404.html":
        return None
    if rel == Path("index.html"):
        return "/"
    return f"/{rel.parent.as_posix()}/"


def check_sitemap_completeness(pages, errors):
    sitemap_path = ROOT / "sitemap.xml"
    sitemap_urls = set()
    if sitemap_path.exists():
        text = sitemap_path.read_text(encoding="utf-8")
        for loc in re.findall(r"<loc>(.*?)</loc>", text):
            sitemap_urls.add(loc.replace("https://denvereventdj.com", "") or "/")

    page_urls = set()
    for page in pages:
        text = page.read_text(encoding="utf-8", errors="replace")
        if re.search(r'<meta\s+name="robots"\s+content="noindex', text, re.IGNORECASE):
            continue
        url = url_for(page)
        if url:
            page_urls.add(url)

    for url in sorted(page_urls - sitemap_urls):
        errors.append(f"sitemap.xml: missing entry for {url} (run scripts/build.py)")
    for url in sorted(sitemap_urls - page_urls):
        errors.append(f"sitemap.xml: entry for {url} has no corresponding page")


def check_stray_filenames(errors):
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDE_DIR_NAMES for part in rel.parts):
            continue
        if rel.name == "index.html":
            continue
        if rel == Path("404.html"):
            continue
        errors.append(f"{rel}: stray .html file — pages must be <folder>/index.html, not a loose file")


def main():
    external_checks = "--external" in sys.argv
    pages = discover_pages()

    errors, warnings, notices = [], [], []
    for page in pages:
        check_file(page, external_checks, errors, warnings, notices)

    check_sitemap_completeness(pages, errors)
    check_stray_filenames(errors)

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
        print(f"FAILED: {len(errors)} issue(s) across {len(pages)} page(s).")
        sys.exit(1)

    print(f"OK: checked {len(pages)} page(s), no broken links or URL-shape issues.")


if __name__ == "__main__":
    main()
