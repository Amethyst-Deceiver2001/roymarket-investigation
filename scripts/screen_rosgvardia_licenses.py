#!/usr/bin/env python3
"""Cross-check entity/person ИНН against Rosgvardia's 5 open-data license
registries (rosguard.gov.ru/page/index/proverka-otkrytyx-dannyx-licenzij):

    th    - оружие: хранение/торговля (weapons storage/trade)
    tgso  - оружие+запчасти: хранение/торговля (weapons+parts storage/trade)
    tgsp  - боеприпасы: хранение/торговля (ammunition storage/trade)
    choop - частная охранная деятельность (private security, ЧОП)
    chd   - частная детективная деятельность (private detective, personal)

Each is a single daily-snapshot CSV at a predictable URL
(data-<YYYYMMDD>-structure-20230811.csv), confirmed working 2026-09-05/06.
`choop` alone is ~89MB (thousands of ЧОП companies nationwide) — this is a
SINGLE bulk download per registry, not a per-entity network loop, so it's
safe to run directly/repeatedly like scan_sources.py, but budget a minute
or two of download time, especially for `choop`.

ИНН position differs by registry (organization ИНН for th/tgso/tgsp/choop,
personal ИНН for chd) and even varies within a registry's own column
layout in places — rather than hardcode column indices, this searches every
field of every row for an exact ИНН-string match, which is robust to that.

A hit means the ИНН appears in a real Rosgvardia license record (status,
order number/date, issuing ЦЛРР office) — a lead to verify and wire via
corrections_entities.json/corrections_people.json, not an automatic fact.
As of 2026-09-05 a full sweep of all 174 entities + all personal ИНН in
people.json against all 5 registries returned zero hits — rerun after the
roster grows or when a specific entity/person is suspected of holding a
weapons/security license.

Usage:
    python3 scripts/screen_rosgvardia_licenses.py
    python3 scripts/screen_rosgvardia_licenses.py --registries choop,chd
    python3 scripts/screen_rosgvardia_licenses.py --slug ooo-example --date 20260905
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import urllib.error
import urllib.request
from datetime import date, timedelta
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
PEOPLE = REPO / "data" / "registry" / "people.json"
OUT = REPO / "data" / "registry" / "_rosgvardia_license_hits.json"

BASE = "https://rosguard.gov.ru/opendata/7722377866-{slug}/data-{date}-structure-20230811.csv"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

REGISTRIES = ["th", "tgso", "tgsp", "choop", "chd"]
LOOKBACK_DAYS = 5  # snapshots aren't guaranteed to regenerate every calendar day


def fetch_csv_rows(slug: str, forced_date: str | None) -> tuple[list[list[str]], str]:
    dates_to_try = [forced_date] if forced_date else [
        (date.today() - timedelta(days=d)).strftime("%Y%m%d") for d in range(LOOKBACK_DAYS)
    ]
    last_err = None
    for d in dates_to_try:
        url = BASE.format(slug=slug, date=d)
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                raw = resp.read().decode("utf-8", errors="ignore")
            return list(csv.reader(io.StringIO(raw), delimiter=";")), d
        except urllib.error.HTTPError as e:
            last_err = e
            continue
        except urllib.error.URLError as e:
            last_err = e
            continue
    raise RuntimeError(f"no snapshot found for {slug} in last {LOOKBACK_DAYS} days ({last_err})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registries", default=",".join(REGISTRIES))
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--date", default=None, help="force a specific YYYYMMDD snapshot instead of auto-detecting latest")
    args = ap.parse_args()
    registries = [r.strip() for r in args.registries.split(",") if r.strip()]

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    people = json.loads(PEOPLE.read_text(encoding="utf-8"))

    entity_targets = [e for e in entities if e.get("inn")]
    person_targets = [p for p in people if p.get("inn_personal")]
    if args.slug:
        entity_targets = [e for e in entity_targets if e["slug"] in args.slug]
        person_targets = [p for p in person_targets if p["slug"] in args.slug]

    inn_index: dict[str, list[dict]] = {}
    for e in entity_targets:
        inn_index.setdefault(e["inn"], []).append({"kind": "entity", "slug": e["slug"], "name": e.get("name_ru")})
    for p in person_targets:
        inn_index.setdefault(p["inn_personal"], []).append({"kind": "person", "slug": p["slug"], "name": p.get("fio_ru")})

    print(f"Checking {len(inn_index)} distinct ИНН against Rosgvardia registries: {', '.join(registries)}")

    all_hits = []
    for slug in registries:
        print(f"\n[{slug}] fetching snapshot ...")
        try:
            rows, snapshot_date = fetch_csv_rows(slug, args.date)
        except RuntimeError as e:
            print(f"  ERROR: {e}")
            continue
        print(f"  {len(rows)} rows (snapshot {snapshot_date}), scanning ...")
        for row in rows:
            row_fields = set(f.strip() for f in row)
            matched_inns = row_fields & inn_index.keys()
            for inn in matched_inns:
                for target in inn_index[inn]:
                    hit = {"registry": slug, "snapshot_date": snapshot_date, "inn": inn, **target, "row": row}
                    all_hits.append(hit)
                    print(f"  HIT [{slug}] {target['kind']} {target['slug']} ({inn})")

    print(f"\n{len(all_hits)} hit(s) total across {len(registries)} registries")
    OUT.write_text(json.dumps(all_hits, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
