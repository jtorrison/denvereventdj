#!/usr/bin/env python3
"""
CI helper: print one path per line — the homepage, plus the first entry
(if any) under /stories/, /guides/, /tools/ — for Lighthouse to test.
Reads sitemap.xml so it automatically starts covering real content the
moment the first story/guide/tool is published, with no workflow edits.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    text = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    locs = re.findall(r"<loc>(.*?)</loc>", text)
    paths = [loc.replace("https://denvereventdj.com", "") or "/" for loc in locs]

    urls = ["/"]
    for prefix in ("/stories/", "/guides/", "/tools/"):
        entries = sorted(p for p in paths if p.startswith(prefix) and p != prefix)
        if entries:
            urls.append(entries[0])

    for url in urls:
        print(url)


if __name__ == "__main__":
    main()
