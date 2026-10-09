#!/usr/bin/env python3
"""
CI helper: submit every sitemap.xml URL to IndexNow. Resubmitting the
full list on every deploy is simpler than diffing "what changed" and is
explicitly fine per the IndexNow spec (idempotent). The key is discovered
from the root-level <32-hex-char>.txt key file rather than hardcoded, so
rotating the key only means swapping that one file.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = "denvereventdj.com"
KEY_RE = re.compile(r"^[0-9a-f]{32}$")


def find_key():
    for path in ROOT.glob("*.txt"):
        if KEY_RE.match(path.stem):
            return path.stem, path.read_text(encoding="utf-8").strip()
    raise SystemExit("No IndexNow key file found at repo root (expected <32-hex-chars>.txt)")


def main():
    key, key_value = find_key()
    if key != key_value:
        raise SystemExit(f"Key file {key}.txt content does not match its filename")

    sitemap_text = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    urls = re.findall(r"<loc>(.*?)</loc>", sitemap_text)
    if not urls:
        print("No URLs in sitemap.xml, nothing to submit.")
        return

    payload = json.dumps({
        "host": HOST,
        "key": key,
        "keyLocation": f"https://{HOST}/{key}.txt",
        "urlList": urls,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"IndexNow accepted {len(urls)} URL(s): HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"IndexNow returned HTTP {e.code}: {e.read().decode(errors='replace')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
