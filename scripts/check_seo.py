#!/usr/bin/env python3
"""
Per-page SEO/metadata checker. For every page (see discover_pages):
  - exactly one non-empty <title>, <=60 chars
  - exactly one non-empty <meta name="description">, <=155 chars
  - exactly one <link rel="canonical">, matching the page's expected URL
    (404.html is exempt — it isn't a real indexable URL)
  - exactly one <h1>
  - no two pages sharing the same title text, description text, or
    canonical URL
  - every <img> has non-empty alt
  - every local asset reference (src/href on link/script/img, and CSS
    url() in styles.css) is root-relative

Usage: python3 scripts/check_seo.py
Exit code is non-zero on any violation.
"""
import html.parser
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXCLUDE_DIR_NAMES = {".git", ".github", "partials", "scripts", "_inbox", "_docs", "assets"}

TITLE_MAX = 60
DESC_MAX = 155


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


def is_root_relative_or_exempt(value):
    return (
        value.startswith("/")
        or value.startswith("http://")
        or value.startswith("https://")
        or value.startswith("data:")
        or value.startswith("#")
        or value.startswith("mailto:")
        or value.startswith("tel:")
    )


class PageParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        self.titles = []
        self.descriptions = []
        self.canonicals = []
        self.h1_count = 0
        self._in_h1 = False
        self._in_title = False
        self._title_text = ""
        self.imgs = []  # (src, alt_or_None)
        self.asset_refs = []  # (tag, attr, value)

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "title":
            self._in_title = True
            self._title_text = ""
        if tag == "h1":
            self.h1_count += 1
        if tag == "meta" and d.get("name") == "description":
            self.descriptions.append(d.get("content", ""))
        if tag == "link" and d.get("rel") == "canonical":
            self.canonicals.append(d.get("href", ""))
        if tag == "img":
            self.imgs.append((d.get("src", ""), d.get("alt")))
        if tag in ("link", "script", "img") and (d.get("src") or d.get("href")):
            value = d.get("src") or d.get("href")
            self.asset_refs.append((tag, "src" if d.get("src") else "href", value))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            self.titles.append(self._title_text.strip())

    def handle_data(self, data):
        if self._in_title:
            self._title_text += data


def check_page(page_path, errors, seen_titles, seen_descriptions, seen_canonicals):
    rel = page_path.relative_to(ROOT)
    text = page_path.read_text(encoding="utf-8", errors="replace")
    parser = PageParser()
    parser.feed(text)

    if len(parser.titles) != 1 or not parser.titles[0]:
        errors.append(f"{rel}: expected exactly one non-empty <title>, found {len(parser.titles)}")
    else:
        title = parser.titles[0]
        if len(title) > TITLE_MAX:
            errors.append(f"{rel}: <title> is {len(title)} chars, over the {TITLE_MAX} limit: \"{title}\"")
        if title in seen_titles:
            errors.append(f"{rel}: <title> \"{title}\" duplicates {seen_titles[title]}")
        else:
            seen_titles[title] = rel

    if len(parser.descriptions) != 1 or not parser.descriptions[0]:
        errors.append(f"{rel}: expected exactly one non-empty meta description, found {len(parser.descriptions)}")
    else:
        desc = parser.descriptions[0]
        if len(desc) > DESC_MAX:
            errors.append(f"{rel}: meta description is {len(desc)} chars, over the {DESC_MAX} limit")
        if desc in seen_descriptions:
            errors.append(f"{rel}: meta description duplicates {seen_descriptions[desc]}")
        else:
            seen_descriptions[desc] = rel

    if rel.name != "404.html":
        expected = f"https://denvereventdj.com{url_for(page_path)}"
        if len(parser.canonicals) != 1:
            errors.append(f"{rel}: expected exactly one <link rel=\"canonical\">, found {len(parser.canonicals)}")
        elif parser.canonicals[0] != expected:
            errors.append(f"{rel}: canonical is \"{parser.canonicals[0]}\", expected \"{expected}\"")
        else:
            canon = parser.canonicals[0]
            if canon in seen_canonicals:
                errors.append(f"{rel}: canonical \"{canon}\" duplicates {seen_canonicals[canon]}")
            else:
                seen_canonicals[canon] = rel

    if parser.h1_count != 1:
        errors.append(f"{rel}: expected exactly one <h1>, found {parser.h1_count}")

    for src, alt in parser.imgs:
        if not alt:
            errors.append(f"{rel}: <img src=\"{src}\"> has no alt text")

    for tag, attr, value in parser.asset_refs:
        if not is_root_relative_or_exempt(value):
            errors.append(f"{rel}: <{tag} {attr}=\"{value}\"> is not root-relative")


def check_styles_css(errors):
    css_path = ROOT / "styles.css"
    if not css_path.exists():
        return
    text = css_path.read_text(encoding="utf-8")
    for match in re.finditer(r"url\((['\"]?)([^'\")]+)\1\)", text):
        value = match.group(2)
        if not is_root_relative_or_exempt(value):
            errors.append(f"styles.css: url({value}) is not root-relative")


def main():
    pages = discover_pages()
    errors = []
    seen_titles, seen_descriptions, seen_canonicals = {}, {}, {}

    for page in pages:
        check_page(page, errors, seen_titles, seen_descriptions, seen_canonicals)

    check_styles_css(errors)

    if errors:
        print(f"Errors ({len(errors)}):")
        for e in errors:
            print(f"  x  {e}")
        print()
        print(f"FAILED: {len(errors)} SEO issue(s) across {len(pages)} page(s).")
        sys.exit(1)

    print(f"OK: checked {len(pages)} page(s), no SEO issues.")


if __name__ == "__main__":
    main()
