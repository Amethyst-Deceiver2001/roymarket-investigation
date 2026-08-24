#!/usr/bin/env python3
"""Trademark lookup via Rospatent's open-data bulk registry export.

Rospatent publishes a full monthly CSV dump of the Russian trademark
register at rospatent.gov.ru/opendata/7730176088-tz — no query limit, no
API key, unlike the interactive searchplatform.rospatent.gov.ru/trademarks
frontend (capped at 100 searches/day). This streams that CSV over HTTPS
and greps it, without saving the ~700MB file to disk.

CSV has no header row; columns (by position, 0-indexed) confirmed against a
sample row (Рустехдрон, №982517):
  0  reg_number       registration number
  1  reg_date         YYYYMMDD
  2  appl_number
  3  filing_date      YYYYMMDD
  26 expiry_date      YYYYMMDD
  27 holder_name      right holder
  29 holder_address
  30 holder_country
  31 ogrn
  32 inn
  33 correspondence_address (often the patent-attorney firm)
  37 colors
  -1 doc_url          fips_servlet link (last column)

Many columns in between are per-record-type flags (mostly empty/false for
a typical registration) — not enumerated here; the script prints select
fields, not the full row, so check the raw CSV directly for anything not
surfaced.

Usage:
    python3 scripts/rospatent_tm_search.py "Рустехдрон"
    python3 scripts/rospatent_tm_search.py --inn 5003155499
    python3 scripts/rospatent_tm_search.py --csv-url <alternate dump URL> "query"

The dump URL rotates monthly (data-YYYYMMDD-structure-...csv) — check
https://rospatent.gov.ru/opendata/7730176088-tz for the current filename
if the default below 404s; pass --csv-url to override without editing.
"""
import argparse
import csv
import io
import json
import re
import ssl
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"

# rospatent.gov.ru serves an incomplete cert chain (missing intermediate) —
# curl -k needed too when testing manually; skip verification for this host.
_UNVERIFIED_CTX = ssl.create_default_context()
_UNVERIFIED_CTX.check_hostname = False
_UNVERIFIED_CTX.verify_mode = ssl.CERT_NONE

DEFAULT_CSV_URL = (
    "https://rospatent.gov.ru/opendata/7730176088-tz/"
    "data-20260805-structure-20180828.csv"
)


def stream_matches(url: str, pattern: re.Pattern, max_hits: int):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    hits = []
    with urllib.request.urlopen(req, timeout=60, context=_UNVERIFIED_CTX) as resp:
        wrapper = io.TextIOWrapper(resp, encoding="utf-8", errors="replace")
        reader = csv.reader(wrapper)
        for row in reader:
            line = ",".join(row)
            if pattern.search(line):
                hits.append(row)
                if len(hits) >= max_hits:
                    break
    return hits


def format_hit(row: list) -> str:
    reg_number = row[0] if len(row) > 0 else "?"
    filing_date = row[3] if len(row) > 3 else "?"
    expiry = row[26] if len(row) > 26 else "?"
    holder = row[27] if len(row) > 27 else "?"
    ogrn = row[31] if len(row) > 31 else ""
    inn = row[32] if len(row) > 32 else ""
    doc_url = row[-1] if row else ""
    lines = [f"№{reg_number} | filed {filing_date} | expires {expiry}", f"  holder: {holder}"]
    if ogrn or inn:
        lines.append(f"  ОГРН {ogrn} / ИНН {inn}")
    lines.append(f"  {doc_url}")
    return "\n".join(lines)


def sweep_registry(url: str, out_path: Path) -> None:
    """One pass over the CSV, matched against every registry entity's ИНН at
    once — O(1) dict lookup per row instead of one full stream per entity.
    Use this for a full-roster sweep instead of looping single queries."""
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    inn_to_slugs: dict[str, list[str]] = {}
    for e in entities:
        inn = e.get("inn")
        if inn:
            inn_to_slugs.setdefault(inn, []).append(e.get("slug") or inn)

    print(f"Sweeping {len(inn_to_slugs)} entity ИНН against {url} ...", file=sys.stderr)

    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    results: dict[str, list[list]] = {}
    rows_seen = 0
    with urllib.request.urlopen(req, timeout=60, context=_UNVERIFIED_CTX) as resp:
        wrapper = io.TextIOWrapper(resp, encoding="utf-8", errors="replace")
        reader = csv.reader(wrapper)
        for row in reader:
            rows_seen += 1
            inn = row[32] if len(row) > 32 else ""
            if inn in inn_to_slugs:
                for slug in inn_to_slugs[inn]:
                    results.setdefault(slug, []).append(row)
            if rows_seen % 200_000 == 0:
                print(f"  ...{rows_seen} rows scanned, {len(results)} entities matched so far", file=sys.stderr)

    print(f"Done: {rows_seen} rows scanned, {len(results)}/{len(inn_to_slugs)} entities with >=1 trademark", file=sys.stderr)
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out_path}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("query", nargs="?", help="text to search for (company name, etc.)")
    ap.add_argument("--inn", help="search by ИНН instead of free text")
    ap.add_argument("--csv-url", default=DEFAULT_CSV_URL)
    ap.add_argument("--max-hits", type=int, default=20)
    ap.add_argument("--sweep-registry", action="store_true",
                    help="one-pass full-roster sweep against every entities.json ИНН "
                         "(instead of one streamed pass per query) — use this for the "
                         "full manufacturer-tier run, not a loop of single queries")
    ap.add_argument("--out", default="data/registry/_rospatent_sweep.json",
                    help="output path for --sweep-registry")
    args = ap.parse_args()

    if args.sweep_registry:
        sweep_registry(args.csv_url, Path(args.out))
        return

    term = args.inn or args.query
    if not term:
        sys.exit("Provide a query string, --inn, or --sweep-registry")

    pattern = re.compile(re.escape(term), re.IGNORECASE)
    print(f"Streaming {args.csv_url} ...", file=sys.stderr)
    hits = stream_matches(args.csv_url, pattern, args.max_hits)

    if not hits:
        print("No matches.")
        return

    for row in hits:
        print(format_hit(row))
        print()

    print(f"--- {len(hits)} match(es), capped at {args.max_hits} ---", file=sys.stderr)


if __name__ == "__main__":
    main()
