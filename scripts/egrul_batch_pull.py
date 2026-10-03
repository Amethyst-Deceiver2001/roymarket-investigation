#!/usr/bin/env python3
"""Batch-pull egrul.nalog.ru's open lookup for every registry entity that
has an ИНН, so the roster shares ONE baseline снапshot date instead of the
current scattered coverage (5 of 114 entities have any EGRUL pull on file,
spanning six different dates from 14 to 20 August).

**This is a live network job against a third-party service — per
CLAUDE.md's crawling-jobs policy, run it yourself; it should not be run in
the background or executed directly by the assistant.** It was tested
inline on a handful of entities first (ordinary reconnaissance), but a
systematic pass across the whole roster is exactly the "real work at scale"
case that policy exists for — repeated automated calls risk rate-limiting
or blocking your own IP against a service you'll want to keep using.

What it does, per entity: two-step lookup (POST for a search token, GET the
result), matched by exact ИНН, then writes ONE file per entity —
`data/sources/EGRULAPI_<INN>_<YYYYMMDD>_<slug>.json` — holding the raw
response (name, ИНН, ОГРН, director, registration date, region). This is
lighter-weight than a full signed EGRUL PDF extract (no full founder list,
no ОКВЭД codes) but gives every entity the same kind of baseline fact —
current legal name, director, ОГРН — as of the same day, which the deeper
per-entity PDF pulls can layer on top of later without needing to be
resynchronized to match.

After running this, refresh the pipeline so the new files are picked up:
    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
    python3 scripts/inventory_sources.py
    python3 scripts/extract_registry.py
    python3 scripts/check_registry.py

Usage:
    python3 scripts/egrul_batch_pull.py                 # all entities with an ИНН, skip already-pulled today
    python3 scripts/egrul_batch_pull.py --limit 5        # first 5 only, for a quick check
    python3 scripts/egrul_batch_pull.py --inn 9704241986 # one specific ИНН
    python3 scripts/egrul_batch_pull.py --force          # re-pull even if today's file already exists
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from source_files import write_new  # never overwrite a catalogued source

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
SOURCES = REPO / "data" / "sources"

EGRUL_BASE = "https://egrul.nalog.ru"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
             "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# Politeness delay between calls — this is a batch job against a shared
# government service, not a burst of one-off lookups. Slower on purpose.
DELAY_SECONDS = 2.5


def slugify(name: str) -> str:
    table = {
        "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
        "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
        "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
        "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
        "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    }
    out = []
    for ch in unicodedata.normalize("NFKC", name).lower():
        if ch in table:
            out.append(table[ch])
        elif ch.isalnum():
            out.append(ch)
        else:
            out.append("-")
    return re.sub(r"-+", "-", "".join(out)).strip("-")[:50]


def http(url: str, data: bytes | None = None) -> bytes:
    req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def lookup(inn: str) -> dict | None:
    """Two-step egrul.nalog.ru open search: POST for a token, GET the result."""
    body = urllib.parse.urlencode({
        "vyp3CaptchaToken": "", "query": inn, "region": "",
        "PreventChromeAutocomplete": "",
    }).encode()
    resp = json.loads(http(EGRUL_BASE + "/", body))
    token = resp.get("t")
    if not token:
        return None

    time.sleep(1)
    result = json.loads(http(f"{EGRUL_BASE}/search-result/{token}"))
    rows = result.get("rows") or []
    for row in rows:
        if row.get("i") == inn or row.get("p") == inn:
            return row
    return rows[0] if len(rows) == 1 else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--inn", default=None, help="pull just this one ИНН")
    ap.add_argument("--tier", default=None,
                    help="pull only entities with this tier (e.g. manufacturer)")
    ap.add_argument("--force", action="store_true",
                    help="re-pull even if today's file already exists")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    today = date.today().strftime("%Y%m%d")

    targets = [e for e in entities if e.get("inn")]
    if args.tier:
        targets = [e for e in targets if e.get("tier") == args.tier]
    if args.inn:
        targets = [e for e in targets if e["inn"] == args.inn]
    if args.limit is not None:
        targets = targets[:args.limit]

    print(f"{len(targets)} entities to pull (baseline date {today})")

    ok = mismatch = failed = skipped = 0
    for i, e in enumerate(targets, 1):
        inn, slug = e["inn"], e.get("slug") or slugify(e["name_ru"])
        out_path = SOURCES / f"EGRULAPI_{inn}_{today}_{slug}.json"

        if out_path.exists() and not args.force:
            skipped += 1
            continue

        try:
            row = lookup(inn)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as ex:
            print(f"  [{i}/{len(targets)}] FAILED  {inn}  {e['name_ru'][:40]}  ({ex})")
            failed += 1
            time.sleep(DELAY_SECONDS)
            continue

        if row is None:
            print(f"  [{i}/{len(targets)}] NO MATCH  {inn}  {e['name_ru'][:40]}")
            mismatch += 1
            time.sleep(DELAY_SECONDS)
            continue

        out_path = write_new(out_path, json.dumps({"queried_inn": inn, "queried_slug": slug,
                       "queried_name": e["name_ru"], "pulled_date": today,
                       "raw": row}, ensure_ascii=False, indent=2) + "\n")
        ok += 1
        if i % 10 == 0 or i == len(targets):
            print(f"  [{i}/{len(targets)}] {ok} ok, {mismatch} no-match, "
                 f"{failed} failed, {skipped} already had today's file")

        time.sleep(DELAY_SECONDS)

    print(f"\ndone: {ok} pulled, {mismatch} no exact ИНН match, "
         f"{failed} failed, {skipped} skipped (already had today's file)")
    print("\nNow refresh the pipeline:")
    print("  python3 scripts/scan_sources.py --out data/sources/MANIFEST.md")
    print("  python3 scripts/inventory_sources.py")
    print("  python3 scripts/extract_registry.py")
    print("  python3 scripts/check_registry.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
