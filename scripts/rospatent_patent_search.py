#!/usr/bin/env python3
"""Patent/utility-model discovery sweep via Rospatent's open-data bulk exports.

Companion to rospatent_tm_search.py (trademarks) — same host, same monthly-
CSV-dump mechanism, no query cap, no API key. Two separate datasets:
  -iz  изобретения       (inventions / full patents,   DB=RUPAT)
  -pm  полезные модели   (utility models,               DB=RUPM)
found via https://rospatent.gov.ru/opendata (index page lists every dataset
this agency publishes; filenames rotate monthly, same data-YYYYMMDD-
structure-... pattern as the trademark dump).

Unlike the trademark CSV, these have NO ИНН/ОГРН column — "patent holders"
and "authors" are free-text name fields only. So matching is by normalized
name (reusing id_patterns.norm(), the same fuzzy-dedup helper mine_leads.py
and scan_sources.py already use) against every registry entity's name_ru/
name_latin/brand_ru and every person's fio_ru — not an ИНН lookup.

Rospatent's TLS chain is missing an intermediate cert (same issue already
documented in rospatent_tm_search.py) — verification is disabled for this
host specifically, not globally.

**This is a live network job at scale (both dumps run several hundred
thousand rows each) — per CLAUDE.md's crawling-jobs policy, run it
yourself; do not have the assistant execute or background it.** Individual
lookups (a known patent number via fips_patent_lookup.py or a single
patents.google.com/patent/<id> read) remain fine to do inline.

Usage:
    python3 scripts/rospatent_patent_search.py --sweep-registry
    python3 scripts/rospatent_patent_search.py --sweep-registry --out data/registry/_patent_sweep.json
"""
import csv
import io
import json
import ssl
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
PEOPLE = REPO / "data" / "registry" / "people.json"
sys.path.insert(0, str(REPO / "scripts"))
from id_patterns import norm  # noqa: E402

_UNVERIFIED_CTX = ssl.create_default_context()
_UNVERIFIED_CTX.check_hostname = False
_UNVERIFIED_CTX.verify_mode = ssl.CERT_NONE

DATASETS = {
    "iz": ("https://rospatent.gov.ru/opendata/7730176088-iz/"
           "data-20260805-structure-20180828.csv", "RUPAT"),
    "pm": ("https://rospatent.gov.ru/opendata/7730176088-pm/"
           "data-20260805-structure-20180828.csv", "RUPM"),
}

COL_REG_NUMBER = 0
COL_AUTHORS = 4
COL_HOLDERS = 6
COL_NAME = 10


def build_name_index():
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    people = json.loads(PEOPLE.read_text(encoding="utf-8"))

    name_to_slugs = {}
    for e in entities:
        for field in ("name_ru", "name_latin", "brand_ru", "brand_latin"):
            v = e.get(field)
            if v:
                name_to_slugs.setdefault(norm(v), []).append(("entity", e.get("slug")))

    for p in people:
        v = p.get("fio_ru")
        if v:
            name_to_slugs.setdefault(norm(v), []).append(("person", p.get("slug")))

    return name_to_slugs


def sweep_one(url: str, name_index: dict, results: dict, label: str):
    print(f"Streaming {label} dump: {url}", file=sys.stderr)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    rows_seen = 0
    with urllib.request.urlopen(req, timeout=60, context=_UNVERIFIED_CTX) as resp:
        wrapper = io.TextIOWrapper(resp, encoding="utf-8-sig", errors="replace")
        reader = csv.reader(wrapper)
        next(reader, None)  # header
        for row in reader:
            rows_seen += 1
            if len(row) <= COL_NAME:
                continue
            holders_raw = row[COL_HOLDERS] or ""
            authors_raw = row[COL_AUTHORS] or ""
            candidate_lines = holders_raw.split("\n") + authors_raw.split("\n")
            matched_keys = set()
            for line in candidate_lines:
                line = line.strip()
                if not line:
                    continue
                key = norm(line)
                if key in name_index:
                    matched_keys.add(key)
            if not matched_keys:
                continue
            for key in matched_keys:
                for kind, slug in name_index[key]:
                    results.setdefault(slug, []).append({
                        "dataset": label,
                        "reg_number": row[COL_REG_NUMBER],
                        "name": row[COL_NAME] if len(row) > COL_NAME else "",
                        "holders": holders_raw.replace("\n", "; "),
                        "authors": authors_raw.replace("\n", "; "),
                        "matched_as": kind,
                        "matched_name": key,
                    })
            if rows_seen % 200_000 == 0:
                print(f"  ...{rows_seen} rows scanned, {len(results)} slugs matched so far",
                      file=sys.stderr)
    print(f"{label}: {rows_seen} rows scanned", file=sys.stderr)


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sweep-registry", action="store_true", required=True,
                     help="required flag, makes the live-network-job intent explicit")
    ap.add_argument("--out", default="data/registry/_patent_sweep.json")
    ap.add_argument("--dataset", choices=["iz", "pm", "both"], default="both")
    args = ap.parse_args()

    name_index = build_name_index()
    print(f"Matching against {len(name_index)} normalized names "
          f"(entities + people)", file=sys.stderr)

    results = {}
    targets = DATASETS.items() if args.dataset == "both" else [(args.dataset, DATASETS[args.dataset])]
    for label, (url, _db) in targets:
        sweep_one(url, name_index, results, label)

    out_path = REPO / args.out
    out_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Done: {len(results)} entity/person slugs with >=1 patent/utility-model hit")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
