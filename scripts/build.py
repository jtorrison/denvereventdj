#!/usr/bin/env python3
"""
One maintenance script, run before every push. Despite "no build step" for
the live site (GitHub Pages still serves these files exactly as committed
— nothing runs server-side), a few things need to stay in sync by hand
otherwise, so this does them mechanically instead:

  1. Inject partials/header.html and partials/footer.html into every
     page's <!-- PARTIAL:HEADER --> / <!-- PARTIAL:FOOTER --> regions.
  2. Regenerate sitemap.xml from whatever pages currently exist.
  3. Regenerate llms.txt from the sitemap.
  4. Sync each story/guide page's visible "Updated <Month Year>" text and
     its Article schema's dateModified with its own
     <!-- updated: YYYY-MM-DD --> marker.

Usage:
  python3 scripts/build.py          # write the changes
  python3 scripts/build.py --check  # exit 1 if running it would change
                                     # anything (wired into CI)
"""
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARTIALS = ROOT / "partials"

EXCLUDE_DIR_NAMES = {".git", ".github", "partials", "scripts", "_inbox", "_docs", "assets"}

HEADER_RE = re.compile(r"<!-- PARTIAL:HEADER -->.*?<!-- /PARTIAL:HEADER -->", re.DOTALL)
FOOTER_RE = re.compile(r"<!-- PARTIAL:FOOTER -->.*?<!-- /PARTIAL:FOOTER -->", re.DOTALL)
UPDATED_MARKER_RE = re.compile(r"<!-- updated:\s*(\d{4}-\d{2}-\d{2})\s*-->")
DATE_MODIFIED_RE = re.compile(r'("dateModified":\s*")[^"]*(")')
UPDATED_TEXT_RE = re.compile(r"(<span data-updated-text>)[^<]*(</span>)")
NOINDEX_RE = re.compile(r'<meta\s+name="robots"\s+content="noindex', re.IGNORECASE)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL)


def discover_pages():
    """Every index.html (root + subfolders) plus root 404.html."""
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


def load_partial(name):
    text = (PARTIALS / name).read_text(encoding="utf-8")
    # Strip the leading documentation comment (everything up to its closing -->).
    return text.split("-->", 1)[1].strip()


def inject_partials(text, header_md, footer_md):
    text = HEADER_RE.sub(
        lambda _: f"<!-- PARTIAL:HEADER -->\n{header_md}\n<!-- /PARTIAL:HEADER -->", text
    )
    text = FOOTER_RE.sub(
        lambda _: f"<!-- PARTIAL:FOOTER -->\n{footer_md}\n<!-- /PARTIAL:FOOTER -->", text
    )
    return text


def sync_updated_date(text):
    m = UPDATED_MARKER_RE.search(text)
    if not m:
        return text
    iso_date = m.group(1)
    month_year = date.fromisoformat(iso_date).strftime("%B %Y")
    text = DATE_MODIFIED_RE.sub(rf"\g<1>{iso_date}\g<2>", text)
    text = UPDATED_TEXT_RE.sub(rf"\g<1>{month_year}\g<2>", text)
    return text


def url_for(page_path):
    rel = page_path.relative_to(ROOT)
    if rel.name == "404.html":
        return None  # never in the sitemap
    if rel == Path("index.html"):
        return "/"
    folder = rel.parent.as_posix()
    return f"/{folder}/"


def git_lastmod(page_path):
    rel = page_path.relative_to(ROOT)
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", str(rel)],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        out = ""
    return out or date.today().isoformat()


def build_sitemap(pages):
    entries = []
    for page in pages:
        text = page.read_text(encoding="utf-8")
        if NOINDEX_RE.search(text):
            continue
        url = url_for(page)
        if url is None:
            continue
        lastmod = git_lastmod(page)
        priority = "1.0" if url == "/" else "0.7"
        entries.append((url, lastmod, priority))

    entries.sort(key=lambda e: e[0])
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, lastmod, priority in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>https://denvereventdj.com{url}</loc>")
        lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append("    <changefreq>monthly</changefreq>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")
    return "\n".join(lines) + "\n", entries


def build_llms_txt(entries, pages_by_url):
    lines = [
        "# Denver Event DJ",
        "",
        "Wedding and event DJ serving Denver and all of Colorado since 2011.",
        "Josh Torrison provides DJ, MC, and lighting services for weddings,",
        "corporate events, and private parties.",
        "",
        "## Pages",
        "",
    ]
    for url, _lastmod, _priority in entries:
        page = pages_by_url[url]
        text = page.read_text(encoding="utf-8")
        m = TITLE_RE.search(text)
        title = m.group(1).strip() if m else url
        lines.append(f"- https://denvereventdj.com{url} — {title}")
    return "\n".join(lines) + "\n"


def main():
    check_mode = "--check" in sys.argv
    pages = discover_pages()
    header_md = load_partial("header.html")
    footer_md = load_partial("footer.html")

    changed_files = []

    for page in pages:
        original = page.read_text(encoding="utf-8")
        updated = inject_partials(original, header_md, footer_md)
        updated = sync_updated_date(updated)
        if updated != original:
            changed_files.append(page.relative_to(ROOT))
            if not check_mode:
                page.write_text(updated, encoding="utf-8")

    # Sitemap + llms.txt need the (possibly just-rewritten) page contents,
    # so re-read from disk in write mode, or use the in-memory `updated`
    # text in check mode by re-running discovery against freshly read files.
    pages = discover_pages()
    sitemap_text, entries = build_sitemap(pages)
    pages_by_url = {url_for(p): p for p in pages if url_for(p)}
    llms_text = build_llms_txt(entries, pages_by_url)

    sitemap_path = ROOT / "sitemap.xml"
    llms_path = ROOT / "llms.txt"

    if sitemap_path.exists() and sitemap_path.read_text(encoding="utf-8") != sitemap_text:
        changed_files.append(sitemap_path.relative_to(ROOT))
        if not check_mode:
            sitemap_path.write_text(sitemap_text, encoding="utf-8")
    elif not sitemap_path.exists():
        changed_files.append(sitemap_path.relative_to(ROOT))
        if not check_mode:
            sitemap_path.write_text(sitemap_text, encoding="utf-8")

    if not llms_path.exists() or llms_path.read_text(encoding="utf-8") != llms_text:
        changed_files.append(llms_path.relative_to(ROOT))
        if not check_mode:
            llms_path.write_text(llms_text, encoding="utf-8")

    if check_mode:
        if changed_files:
            print("Build drift detected — run `python3 scripts/build.py` and commit the result:")
            for f in changed_files:
                print(f"  - {f}")
            sys.exit(1)
        print("OK: build is up to date, no drift.")
        return

    if changed_files:
        print(f"Updated {len(changed_files)} file(s):")
        for f in changed_files:
            print(f"  - {f}")
    else:
        print("OK: nothing to update.")


if __name__ == "__main__":
    main()
