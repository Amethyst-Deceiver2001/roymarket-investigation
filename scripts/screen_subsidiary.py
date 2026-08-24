#!/usr/bin/env python3
"""Screen every person with a personal ИНН against ФНС's Реестр
субсидиарных ответчиков (subsidiary-liability registry — individuals a
court has held personally liable for a company's debts after bankruptcy,
"piercing the corporate veil"; ФНС publishes it as a competitor/creditor
due-diligence tool, currently marked "test mode" on the site itself).

Different infrastructure from pb.nalog.ru's search-proc.json flow — this is
a single synchronous POST to nalog.gov.ru's generic Ajax.html endpoint with
type=rso_data, no polling needed. Confirmed working 2026-08-22 (Бессонов
С.Н. tested clean by ИНН, 0 hits, HTTP 200 `{"Success":true,"Body":[]}`).

**No DOB currently on file for anyone in people.json.** This registry's
search form doesn't even take a DOB field (Фамилия/Имя/Отчество/ИНН only),
so name-based hits here are AT LEAST as prone to same-name false positives
as scripts/screen_disqualified.py — every hit is written with
`needs_verification: true` and must be manually confirmed against the
actual person (region, associated company, case details) before being
treated as a real finding.

Searches BOTH by personal ИНН and by full name split into
Фамилия/Имя/Отчество (the two are not guaranteed to return the same rows —
an ИНН search should be authoritative when it returns something, but a name
search catches the case where the registry's ИНН field is blank/wrong for
a real hit).

Writes `subsidiary_liability_hits[]` + `subsidiary_liability_checked_at`
onto each person in data/registry/people.json. Fetched screening data, not
a hand correction — survives extract_registry.py regeneration via the
preserve-forward merge added alongside securing_measures/other_entities.

**Live network job against a third-party (government) service — per
CLAUDE.md's crawling-jobs policy, tested inline on one person first, full-
roster sweep handed to the user to run themselves.**

Usage:
    python3 scripts/screen_subsidiary.py
    python3 scripts/screen_subsidiary.py --slug bessonov-sergey-nikolaevich
    python3 scripts/screen_subsidiary.py --force
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PEOPLE = REPO / "data" / "registry" / "people.json"

AJAX_URL = "https://www.nalog.gov.ru/rn77/rso/Ajax.html"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")

DELAY_BETWEEN_QUERIES = 1.5


def query_rso(inn: str = "", surname: str = "", name: str = "", middle_name: str = "") -> list[dict]:
    body = urllib.parse.urlencode({
        "type": "rso_data",
        "INN_o": inn, "UL_o": "",
        "Surname_o": surname, "Name_o": name, "MiddleName_o": middle_name,
    }).encode("ascii")
    req = urllib.request.Request(
        AJAX_URL, data=body, method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    if not result.get("Success"):
        raise RuntimeError(f"rso Ajax.html returned Success=false: {result}")
    return result.get("Body") or []


def split_fio(fio: str) -> tuple[str, str, str]:
    parts = fio.split()
    surname = parts[0] if len(parts) > 0 else ""
    name = parts[1] if len(parts) > 1 else ""
    middle = parts[2] if len(parts) > 2 else ""
    return surname, name, middle


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    people = json.loads(PEOPLE.read_text(encoding="utf-8"))
    today = date.today().isoformat()

    targets = [p for p in people if p.get("inn_personal")]
    if args.slug:
        targets = [p for p in targets if p["slug"] == args.slug]
    if not args.force:
        targets = [p for p in targets if p.get("subsidiary_liability_checked_at") != today]

    if not targets:
        print("Nothing to do (everyone already checked today — use --force).")
        return

    print(f"Screening {len(targets)} people against {AJAX_URL} (by ИНН and by ФИО) ...")
    for i, person in enumerate(targets, 1):
        inn = person["inn_personal"]
        fio = person.get("fio_ru", "")
        surname, name, middle = split_fio(fio)
        label = f"{person['slug']} ({fio})"

        try:
            by_inn = query_rso(inn=inn)
            time.sleep(DELAY_BETWEEN_QUERIES)
            by_name = query_rso(surname=surname, name=name, middle_name=middle)
        except (urllib.error.URLError, RuntimeError) as e:
            print(f"  {i}/{len(targets)}  {label}  ERROR: {e}")
            continue

        seen_ids = set()
        hits = []
        for row in by_inn + by_name:
            rid = row.get("Id") or json.dumps(row, sort_keys=True)
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            hits.append(dict(row, needs_verification=True, matched_by=(
                "inn" if row in by_inn else "name")))

        person["subsidiary_liability_hits"] = hits
        person["subsidiary_liability_checked_at"] = today
        PEOPLE.write_text(json.dumps(people, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        flag = " *** SUBSIDIARY LIABILITY HIT — VERIFY BEFORE USE ***" if hits else ""
        print(f"  {i}/{len(targets)}  {label}  {len(hits)} hit(s){flag}")
        time.sleep(DELAY_BETWEEN_QUERIES)

    print("\nDone. Any hit needs manual confirmation (no DOB field in this registry at all) "
          "before it's treated as real — see needs_verification on each hit.")


if __name__ == "__main__":
    main()
