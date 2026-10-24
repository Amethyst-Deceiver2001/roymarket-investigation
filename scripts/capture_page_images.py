#!/usr/bin/env python3
"""Capture the pictures of a saved web page, with the caption and chapter each sits under.

    python3 scripts/capture_page_images.py plan <page.html> <prefix> [--host H]
    python3 scripts/capture_page_images.py download <manifest.json> [--delay 1.0] [--limit N]

`plan` is local: it reads a page already saved in data/sources/ and writes `<prefix>-images-manifest.json` beside it,
one record per picture in page order (`n`, `role`, `url`, `chapter`, `caption`, `before`, `width`, `height`, `file`).
Roles: `content` (an <img> in a figure, shown at page size) and `gallery_full` (the full-size target of a gallery link;
its thumbnail is skipped). Icons, share pictures and thumbnails are left out.

`download` is a live job against a third-party site: one request per picture, `--delay` seconds apart, files written
through source_files.write_new() so nothing is overwritten. Hand it to the user as a command (CLAUDE.md, live jobs at
scale). Re-running skips pictures already on disk and retries the rest.

First use: the ФБК «Он вам не Димон» page (notes/source_fbk_dimon_2017.md).
"""
import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from source_files import write_new  # noqa: E402

SOURCES = Path(__file__).resolve().parent.parent / "data" / "sources"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15"
MEDIA = re.compile(r"/media/cache/")


def _text(tag, n=160):
    return re.sub(r"\s+", " ", tag.get_text(" ", strip=True))[:n]


def plan_images(html: str, host: str | None = None) -> list[dict]:
    """Pictures of the page in document order. `host` limits them to one image host (substring of the URL)."""
    soup = BeautifulSoup(html, "html.parser")
    out, seen, chapter, before = [], set(), "", ""

    def keep(url):
        return bool(url) and MEDIA.search(url) and (host is None or host in url) and url not in seen

    for el in soup.find_all(True):
        cls = el.get("class") or []
        if "post__heading" in cls or "chapter-name" in cls:
            chapter = _text(el, 120) or chapter
        elif el.name == "p" and ("post__text" in cls):
            before = _text(el)
        elif el.name == "img" and el.parent is not None and el.parent.name == "figure":
            url = el.get("data-src") or el.get("src")
            if keep(url):
                cap = el.parent.find("figcaption")
                seen.add(url)
                out.append({"role": "content", "url": url, "chapter": chapter, "caption": _text(cap) if cap else "",
                            "before": before, "width": el.get("width"), "height": el.get("height")})
        elif el.name == "a" and el.get("data-thumb"):
            url = el.get("href")
            if keep(url):
                seen.add(url)
                out.append({"role": "gallery_full", "url": url, "chapter": chapter, "caption": "", "before": before,
                            "width": None, "height": None})
    for i, r in enumerate(out, 1):
        ext = Path(r["url"].split("?")[0]).suffix.lower() or ".jpg"
        r["n"] = i
        r["file"] = None  # filled by plan(): needs the prefix
        r["_ext"] = ext
    return out


def plan(page: Path, prefix: str, host: str | None) -> Path:
    rows = plan_images(page.read_text(encoding="utf-8", errors="ignore"), host)
    for r in rows:
        h = hashlib.sha1(r["url"].encode()).hexdigest()[:8]
        r["file"] = f"{prefix}-img{r['n']:03d}-{r['role']}-{h}{r.pop('_ext')}"
    man = {"page": page.name, "prefix": prefix, "count": len(rows), "images": rows}
    path = page.parent / f"{prefix}-images-manifest.json"
    write_new(path, json.dumps(man, ensure_ascii=False, indent=1) + "\n")
    roles = {}
    for r in rows:
        roles[r["role"]] = roles.get(r["role"], 0) + 1
    print(f"{len(rows)} pictures {roles} -> {path.name}")
    return path


def download(manifest: Path, delay: float, limit: int | None) -> None:
    man = json.loads(manifest.read_text(encoding="utf-8"))
    done = failed = skipped = 0
    for r in man["images"]:
        if limit is not None and done >= limit:
            break
        target = manifest.parent / r["file"]
        if target.exists():
            skipped += 1
            continue
        try:
            req = urllib.request.Request(r["url"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp:
                kind = resp.headers.get("Content-Type", "")
                data = resp.read()
            if not kind.startswith("image/") or len(data) < 500:
                raise ValueError(f"not a picture ({kind}, {len(data)} bytes)")
            write_new(target, data)
            done += 1
        except Exception as exc:  # noqa: BLE001 - report and carry on; a re-run retries
            failed += 1
            print(f"FAIL {r['n']:03d} {r['url']}: {exc}")
        time.sleep(delay)
    print(f"saved {done}, already on disk {skipped}, failed {failed}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("plan")
    p.add_argument("page", type=Path)
    p.add_argument("prefix")
    p.add_argument("--host")
    d = sub.add_parser("download")
    d.add_argument("manifest", type=Path)
    d.add_argument("--delay", type=float, default=1.0)
    d.add_argument("--limit", type=int)
    a = ap.parse_args()
    if a.cmd == "plan":
        plan(a.page, a.prefix, a.host)
    else:
        download(a.manifest, a.delay, a.limit)


if __name__ == "__main__":
    main()
