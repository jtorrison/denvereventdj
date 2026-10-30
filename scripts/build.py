#!/usr/bin/env python3
"""
One maintenance script, run before every push. Despite "no build step" for
the live site (GitHub Pages still serves these files exactly as committed
— nothing runs server-side), a few things need to stay in sync by hand
otherwise, so this does them mechanically instead:

  1. Inject each file in PARTIALS_MAP into every page's matching
     <!-- PARTIAL:NAME --> / <!-- /PARTIAL:NAME --> region (header, footer,
     and the shared contact form, which appears on both / and /contact/).
  2. Regenerate sitemap.xml from whatever pages currently exist.
  3. Regenerate llms.txt from the sitemap.
  4. Sync each story/guide page's visible "Updated <Month Year>" text and
     its Article schema's dateModified with its own
     <!-- updated: YYYY-MM-DD --> marker.
  5. Give every <img> that uses a photo from assets/photos/ a srcset
     listing the smaller copies in assets/photos/sizes/ (made by
     scripts/make_image_sizes.py) plus the original, so phones download a
     small file. A tag with no sizes attribute gets a default one. Photos
     without smaller copies are left alone.

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

# marker name -> source file in partials/. Add a new pair here for any
# future shared block; inject_partials() handles all of them generically.
PARTIALS_MAP = {
    "HEADER": "header.html",
    "FOOTER": "footer.html",
    "CONTACT_FORM": "contact-form.html",
}
UPDATED_MARKER_RE = re.compile(r"<!-- updated:\s*(\d{4}-\d{2}-\d{2})\s*-->")
DATE_MODIFIED_RE = re.compile(r'("dateModified":\s*")[^"]*(")')
UPDATED_TEXT_RE = re.compile(r"(<span data-updated-text>)[^<]*(</span>)")
NOINDEX_RE = re.compile(r'<meta\s+name="robots"\s+content="noindex', re.IGNORECASE)
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.DOTALL)
IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.DOTALL)
PHOTO_SRC_RE = re.compile(r'\ssrc="(/assets/photos/([^"/]+)\.webp)"')
SRCSET_RE = re.compile(r'\ssrcset="[^"]*"')
SIZE_FILE_RE = re.compile(r"-(\d+)w\.webp$")
# Most photos sit in a column up to 720px wide. Full-width photos and cards
# set their own sizes attribute in the HTML.
DEFAULT_SIZES = "(max-width: 760px) calc(100vw - 40px), 720px"


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


def inject_partials(text, partial_contents):
    """partial_contents: {marker_name: rendered_content}. Only markers that
    actually appear in this page are touched — a page without a
    PARTIAL:CONTACT_FORM region (e.g. 404.html) is left alone for that one."""
    for marker_name, content in partial_contents.items():
        pattern = re.compile(
            rf"<!-- PARTIAL:{marker_name} -->.*?<!-- /PARTIAL:{marker_name} -->", re.DOTALL
        )
        replacement = f"<!-- PARTIAL:{marker_name} -->\n{content}\n<!-- /PARTIAL:{marker_name} -->"
        text = pattern.sub(lambda _, r=replacement: r, text)
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


def webp_size(path):
    """(width, height) of a .webp file from its header, or None."""
    data = Path(path).read_bytes()[:30]
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk = data[12:16]
    if chunk == b"VP8X":
        return (int.from_bytes(data[24:27], "little") + 1, int.from_bytes(data[27:30], "little") + 1)
    if chunk == b"VP8 ":
        return (int.from_bytes(data[26:28], "little") & 0x3FFF, int.from_bytes(data[28:30], "little") & 0x3FFF)
    if chunk == b"VP8L":
        bits = int.from_bytes(data[21:25], "little")
        return ((bits & 0x3FFF) + 1, ((bits >> 14) & 0x3FFF) + 1)
    return None


_srcset_cache = {}


def srcset_for(src, stem):
    if stem not in _srcset_cache:
        sizes_dir = ROOT / "assets" / "photos" / "sizes"
        variants = []
        for f in sizes_dir.glob(f"{stem}-*w.webp") if sizes_dir.is_dir() else []:
            m = SIZE_FILE_RE.search(f.name)
            if m and f.name == f"{stem}-{m.group(1)}w.webp":
                variants.append((int(m.group(1)), f"/assets/photos/sizes/{f.name}"))
        original = ROOT / src.lstrip("/")
        dims = webp_size(original) if original.exists() else None
        if not variants or not dims:
            _srcset_cache[stem] = None
        else:
            variants.sort()
            parts = [f"{url} {w}w" for w, url in variants] + [f"{src} {dims[0]}w"]
            _srcset_cache[stem] = ", ".join(parts)
    return _srcset_cache[stem]


def sync_srcsets(text):
    def fix(m):
        tag = m.group(0)
        if not PHOTO_SRC_RE.search(tag):
            return tag
        tag = SRCSET_RE.sub("", tag)
        src_m = PHOTO_SRC_RE.search(tag)
        srcset = srcset_for(src_m.group(1), src_m.group(2))
        if not srcset:
            return tag
        insert = f' srcset="{srcset}"'
        if " sizes=" not in tag:
            insert += f' sizes="{DEFAULT_SIZES}"'
        return tag[:src_m.end()] + insert + tag[src_m.end():]
    return IMG_TAG_RE.sub(fix, text)


def url_for(page_path):
    rel = page_path.relative_to(ROOT)
    if rel.name == "404.html":
        return None  # never in the sitemap
    if rel == Path("index.html"):
        return "/"
    folder = rel.parent.as_posix()
    return f"/{folder}/"


def git_lastmod(page_path):
    """
    Last-modified date for the sitemap. This script normally runs BEFORE
    the commit that will actually land, so a plain `git log -1` would give
    the *previous* commit's date locally, then disagree with CI's `git
    log` once the new commit exists (CI checks out the finished commit,
    where the file is no longer dirty) — permanent drift on every commit
    that touches a sitemapped page. Dodge it: if the file has uncommitted
    changes right now, it's about to be committed *today*, so use today's
    date, matching what CI will see once that commit lands (same
    calendar day). Only fall back to git history for untouched files.
    """
    rel = page_path.relative_to(ROOT)
    status = subprocess.run(
        ["git", "status", "--porcelain", "--", str(rel)],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout.strip()
    if status:
        return date.today().isoformat()
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
    partial_contents = {name: load_partial(fname) for name, fname in PARTIALS_MAP.items()}

    changed_files = []

    for page in pages:
        original = page.read_text(encoding="utf-8")
        updated = inject_partials(original, partial_contents)
        updated = sync_updated_date(updated)
        updated = sync_srcsets(updated)
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
