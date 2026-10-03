#!/usr/bin/env python3
"""Screen every registry entity's ИНН against ФНС's Реестр обеспечительных
мер (service.nalog.ru/rom/) — the public register of active tax-enforcement
asset-securing measures (restrictions on alienating/pledging assets while a
tax dispute or penalty is being enforced). No ЕСИА/login required; a plain
public JSON POST. Confirmed working 2026-08-22 (10-entity smoke test, all
zero-result but structurally valid — distinct queryHash/timing per query).

Writes `securing_measures[]` and `securing_measures_checked_at` directly
onto each entity in data/registry/entities.json (fetched screening data,
same category as egrul_flags/sanctions — not a hand correction, so this
does NOT go through corrections.json). A real hit also gets archived as a
primary-source snapshot in data/sources/ (ROM_<INN>_<YYYYMMDD>_<slug>.json)
the same way scripts/egrul_batch_pull.py archives its EGRUL pulls, since a
securing-measure listing is evidence worth keeping independent of the
registry record that cites it.

**Live network job against a third-party (if unauthenticated) government
service — per CLAUDE.md's crawling-jobs policy, tested inline on 10 entities
first (see roymarket_project memory), full-roster sweep should be handed to
the user to run themselves rather than executed in the background.**

After running this, refresh the pipeline:
    python3 scripts/check_registry.py

Usage:
    python3 scripts/screen_rom.py                  # all entities with an ИНН, skip already-checked today
    python3 scripts/screen_rom.py --limit 5         # first 5 only
    python3 scripts/screen_rom.py --inn 9704241986  # one specific ИНН
    python3 scripts/screen_rom.py --force           # re-check even if already checked today
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from source_files import write_new  # never overwrite a catalogued source

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
SOURCES = REPO / "data" / "sources"

ROM_URL = "https://service.nalog.ru/rom/search-proc.json"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

DELAY_SECONDS = 1.5  # politeness delay — shared government service, batch job not one-off


def slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    ascii_name = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name).strip("-").lower()
    return ascii_name or "entity"


def query_rom(inn: str) -> dict:
    data = f"query={inn}&page=1&pageSize=100".encode("ascii")
    req = urllib.request.Request(
        ROM_URL, data=data, method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--inn", default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    today = date.today().isoformat()

    targets = [e for e in entities if e.get("inn")]
    if args.inn:
        targets = [e for e in targets if e["inn"] == args.inn]
    if not args.force:
        targets = [e for e in targets if e.get("securing_measures_checked_at") != today]
    if args.limit:
        targets = targets[: args.limit]

    if not targets:
        print("Nothing to do (all entities already checked today — use --force to re-check).")
        return

    print(f"Screening {len(targets)} entities against {ROM_URL} ...")
    hits_found = 0
    for i, ent in enumerate(targets, 1):
        inn = ent["inn"]
        try:
            result = query_rom(inn)
        except urllib.error.URLError as e:
            print(f"  {i}/{len(targets)}  {inn}  ERROR: {e}")
            continue

        rows = result.get("data") or []
        ent["securing_measures"] = rows
        ent["securing_measures_checked_at"] = today

        if rows:
            hits_found += 1
            slug = ent.get("slug") or slugify(ent.get("name_ru", inn))
            out = SOURCES / f"ROM_{inn}_{today.replace('-', '')}_{slug}.json"
            out = write_new(out, json.dumps(result, ensure_ascii=False, indent=2))
            print(f"  {i}/{len(targets)}  {inn}  *** {len(rows)} active securing measure(s) — saved {out.name} ***")
        else:
            print(f"  {i}/{len(targets)}  {inn}  clean (0)")

        ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        time.sleep(DELAY_SECONDS)

    print(f"\nDone. {hits_found} entit(y/ies) with active securing measures found out of {len(targets)} checked.")
    if hits_found:
        print("Re-run scripts/check_registry.py, and fold any hit into the relevant entity's open_questions/litigation.")


if __name__ == "__main__":
    main()
