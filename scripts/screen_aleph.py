#!/usr/bin/env python3
"""Screen every registry entity and person against OCCRP Aleph's entity
search (aleph.occrp.org/api/2/entities) — cross-references leaked documents,
corporate registries, sanctions lists, procurement records and investigative
datasets across ~190 countries.

Confirmed working 2026-08-24 (OCCRP_ALEPH_API in .env, tested inline with a
free-text query — 200 OK, real structured results with dataset provenance).

**Live network job against a third-party API — per CLAUDE.md's crawling-jobs
policy, tested inline on a handful of records first (ordinary
reconnaissance), but the full-roster sweep should be run by you, not
executed in the background.**

Aleph's plain entity search is free-text relevance-ranked, not a scored
identity match like OpenSanctions' /match endpoint — so this is inherently
noisier (see the "Medvedev" test query, which surfaced an unrelated Moldovan
company and a random procurement contract alongside real hits). Every result
is written to `aleph_matches[]` + `aleph_screened_at` directly onto
entities.json/people.json (screened data, not a hand correction — same
pattern as screen_rom.py's securing_measures[], NOT routed through
corrections.json). Treat this as a triage list, not a source, same as this
project's other automated-scan outputs (mine_leads.py, scan_sources.py) —
every hit still needs a human to open the Aleph UI link and read the
underlying document before it goes anywhere near sanctions[]/litigation[]/
foreign_components[].

Queries by ИНН first (precise, low-noise) when available, falling back to
name search only when there's no ИНН to key on (mostly people, and money-
layer/plumbing entities already ИНН-complete after 2026-08-24's verification
pass barely need the fallback).

After running this, refresh the pipeline:
    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
    python3 scripts/inventory_sources.py
    python3 scripts/extract_registry.py
    python3 scripts/check_registry.py

Usage:
    python3 scripts/screen_aleph.py                  # everyone, skip already-screened today
    python3 scripts/screen_aleph.py --limit 5         # first 5 only
    python3 scripts/screen_aleph.py --kind people
    python3 scripts/screen_aleph.py --kind entities
    python3 scripts/screen_aleph.py --force
    python3 scripts/screen_aleph.py --only slug-a,slug-b   # just these records
"""
from __future__ import annotations

import argparse
import json
import os
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
PEOPLE = REPO / "data" / "registry" / "people.json"
SOURCES = REPO / "data" / "sources"
ENV_FILE = REPO / ".env"

API_BASE = "https://aleph.occrp.org/api/2/entities"
DELAY_SECONDS = 1.0
RESULT_LIMIT = 5
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def load_api_key() -> str:
    key = os.environ.get("OCCRP_ALEPH_API")
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("OCCRP_ALEPH_API="):
                return line.split("=", 1)[1].strip()
    sys.exit("OCCRP_ALEPH_API not found in environment or .env")


def slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    ascii_name = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name).strip("-").lower()
    return ascii_name or "record"


def search(api_key: str, query: str) -> dict:
    url = f"{API_BASE}?{urllib.parse.urlencode({'q': query, 'limit': RESULT_LIMIT})}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"ApiKey {api_key}",
        "User-Agent": USER_AGENT,
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def query_for(r: dict, kind: str) -> str | None:
    if kind == "entities":
        return r.get("inn") or r.get("name_ru")
    return r.get("inn_personal") or r.get("fio_ru")


def process(records: list, kind: str, api_key: str, today: str, force: bool,
            only: set | None = None) -> int:
    field_screened = "aleph_screened_at"
    field_matches = "aleph_matches"

    targets = []
    for r in records:
        if only is not None:
            if r.get("slug") not in only:
                continue
        elif not force and r.get(field_screened) == today:
            continue
        q = query_for(r, kind)
        if not q:
            continue
        targets.append((r, q))

    if not targets:
        print(f"  [{kind}] nothing to do (all already screened today, use --force to re-screen)")
        return 0

    print(f"  [{kind}] screening {len(targets)} record(s) ...")
    hit_count = 0
    for i, (r, q) in enumerate(targets, 1):
        slug = r.get("slug") or slugify(r.get("name_ru") or r.get("fio_ru") or "record")
        try:
            resp = search(api_key, q)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as ex:
            print(f"    [{i}/{len(targets)}] {slug} FAILED: {ex}")
            time.sleep(DELAY_SECONDS)
            continue

        results = resp.get("results", [])
        matches = []
        for m in results:
            coll = m.get("collection") or {}
            matches.append({
                "entity_id": m.get("id"),
                "caption": m.get("names", [None])[0] if m.get("names") else (m.get("properties") or {}).get("name", [None])[0],
                "schema": m.get("schema"),
                "score": round(m.get("score", 0), 4),
                "dataset_label": coll.get("label"),
                "dataset_category": coll.get("category"),
                "countries": m.get("countries", []),
                "ui_link": (m.get("links") or {}).get("ui"),
            })

        r[field_matches] = matches
        r[field_screened] = today

        if matches:
            hit_count += 1
            out = SOURCES / f"ALEPH_{r.get('inn') or r.get('inn_personal') or slug}_{today.replace('-', '')}_{slug}.json"
            out = write_new(out, json.dumps({"query": q, "response": resp}, ensure_ascii=False, indent=2))
            print(f"    [{i}/{len(targets)}] {slug}: {len(matches)} result(s), top: "
                  f"{matches[0]['caption']} ({matches[0]['dataset_label']}) — saved {out.name}")
        else:
            print(f"    [{i}/{len(targets)}] {slug}: 0 results")

        time.sleep(DELAY_SECONDS)

    return hit_count


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--kind", choices=["entities", "people", "both"], default="both")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", help="comma-separated slugs (entities or people) to screen, whatever their "
                                   "screen date (the status board's daily queue uses this)")
    args = ap.parse_args()

    api_key = load_api_key()
    today = date.today().isoformat()
    only = set(args.only.split(",")) if args.only else None

    total_hits = 0

    if args.kind in ("entities", "both"):
        entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
        targets = entities if args.limit is None else entities[:args.limit]
        total_hits += process(targets, "entities", api_key, today, args.force, only)
        ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.kind in ("people", "both"):
        people = json.loads(PEOPLE.read_text(encoding="utf-8"))
        targets = people if args.limit is None else people[:args.limit]
        total_hits += process(targets, "people", api_key, today, args.force, only)
        PEOPLE.write_text(json.dumps(people, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nDone. {total_hits} record(s) with >=1 Aleph result archived to data/sources/.")
    print("Every screened record now carries aleph_matches[] + aleph_screened_at.")
    print("Re-run scripts/check_registry.py, then hand-review matches — Aleph search is noisy free text, not a scored identity match.")


if __name__ == "__main__":
    main()
