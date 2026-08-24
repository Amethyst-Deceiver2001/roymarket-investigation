#!/usr/bin/env python3
"""Phase 1 verification, first pass: automated cross-check of every entity
in data/registry/entities.json against its already-pulled
data/sources/EGRULAPI_<INN>_*.json snapshot (114 of 114 entities with an
ИНН already have one, from the earlier egrul_batch_pull.py sweep).

This is NOT full verification — it does not read a primary document beyond
the lightweight open-API snapshot, and does not touch fields EGRULAPI
doesn't carry (founders, ОКВЭД, charter capital, address). It's the
highest-leverage first move: instead of a human reading 130 records cold,
this surfaces only the ones where the registry disagrees with EGRUL, so
manual attention goes to actual discrepancies (data-entry errors, stale
director info, transposed digits — the ОГРН-checksum bug this project has
already caught twice) rather than re-confirming things that already match.

A CLEAN entity is marked `_egrul_crosschecked: <date>` — a weaker claim
than `_verified: true` (which still needs a primary EGRUL PDF / БФО / Устав
read per entity), but a real, durable signal that at minimum name/ОГРН/
director/registration-date are internally consistent as of the snapshot
date. `_verified` is left for a human to set after that fuller check.

A LIQUIDATOR line (in place of a director) is flagged separately — it
means the entity is in or has completed liquidation, a status fact worth
its own open_question rather than a silent director mismatch.

Local file processing only — reads already-pulled snapshots, no network
calls. Safe to run directly/repeatedly, same category as check_registry.py.

Usage:
    python3 scripts/crosscheck_egrul.py                # report to stdout
    python3 scripts/crosscheck_egrul.py --write         # also write
                                                          # _egrul_crosschecked
                                                          # onto clean entities
"""
from __future__ import annotations

import argparse
import glob
import json
import re
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
SOURCES = REPO / "data" / "sources"

ROLE_RE = re.compile(r"^([^:]+):\s*(.+)$")
CORE_NAME_RE = re.compile(r'["«]([^"»]+)["»]')


def norm_name(s: str | None) -> str:
    if not s:
        return ""
    s = s.upper().replace("Ё", "Е")
    s = re.sub(r'["«»\']', "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def core_name(s: str | None) -> str:
    """Extract just the distinguishing name from a legal-entity string —
    registry stores short quoted forms ('АО «Стратим»'), EGRUL spells out
    the full legal form ('АКЦИОНЕРНОЕ ОБЩЕСТВО "СТРАТИМ"'). Comparing full
    strings makes every entity look like a mismatch; comparing just the
    quoted core (or the whole string if nothing is quoted) is the actual
    useful check."""
    if not s:
        return ""
    m = CORE_NAME_RE.search(s)
    core = m.group(1) if m else s
    return norm_name(core)


def load_egrul_snapshots() -> dict[str, dict]:
    """inn -> most recently pulled snapshot (by pulled_date in the filename)."""
    by_inn: dict[str, dict] = {}
    for path in glob.glob(str(SOURCES / "EGRULAPI_*.json")):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        inn = data.get("queried_inn")
        if not inn:
            continue
        pulled = data.get("pulled_date", "")
        existing = by_inn.get(inn)
        if existing is None or pulled > existing.get("pulled_date", ""):
            data["_path"] = path
            by_inn[inn] = data
    return by_inn


def parse_director_line(g: str) -> tuple[str | None, str | None]:
    """Returns (role, name) from EGRULAPI's 'g' field, or (None, None) if empty."""
    g = (g or "").strip()
    if not g:
        return None, None
    m = ROLE_RE.match(g)
    if m:
        return m.group(1), m.group(2).strip()
    return None, g


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true",
                     help="write _egrul_crosschecked onto clean entities")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    snapshots = load_egrul_snapshots()
    today = date.today().isoformat()

    n_clean = 0
    n_mismatch = 0
    n_no_snapshot = 0
    mismatches = []
    liquidations = []

    for e in entities:
        inn = e.get("inn")
        if not inn:
            continue
        snap = snapshots.get(inn)
        if snap is None:
            n_no_snapshot += 1
            continue

        raw = snap["raw"]
        problems = []

        if e.get("ogrn") and raw.get("o") and e["ogrn"] != raw["o"]:
            problems.append(f"ОГРН: registry={e['ogrn']!r} vs EGRUL={raw['o']!r}")

        if e.get("registered") and raw.get("r") and e["registered"] != raw["r"]:
            problems.append(f"registered: registry={e['registered']!r} vs EGRUL={raw['r']!r}")

        reg_name = core_name(e.get("name_ru"))
        egr_name = core_name(raw.get("n"))
        if reg_name and egr_name and reg_name != egr_name:
            problems.append(f"name: registry={e.get('name_ru')!r} vs EGRUL={raw.get('n')!r}")

        role, egr_director = parse_director_line(raw.get("g", ""))
        if role and "ЛИКВИДАТОР" in role.upper():
            liquidations.append((e.get("slug"), inn, e.get("name_ru"), egr_director))
        elif e.get("director") and egr_director:
            reg_dir = norm_name(e["director"])
            egr_dir = norm_name(egr_director)
            # Loose containment check — registry director strings are often
            # "Surname I.O." while EGRUL states the full ФИО, or vice versa.
            surname_reg = reg_dir.split()[0] if reg_dir else ""
            if surname_reg and surname_reg not in egr_dir:
                problems.append(f"director: registry={e['director']!r} vs EGRUL={egr_director!r}")

        if problems:
            n_mismatch += 1
            mismatches.append((e.get("slug"), inn, e.get("name_ru"), problems))
        else:
            n_clean += 1
            if args.write:
                e["_egrul_crosschecked"] = today

    print(f"Cross-checked {n_clean + n_mismatch} entities against EGRULAPI snapshots "
          f"({n_no_snapshot} have an ИНН but no snapshot on file).\n")

    print(f"CLEAN: {n_clean}")
    print(f"MISMATCH: {n_mismatch}")
    print(f"IN LIQUIDATION: {len(liquidations)}\n")

    if liquidations:
        print("--- Liquidation status (not a mismatch, but a fact worth an open_question) ---")
        for slug, inn, name, liquidator in liquidations:
            print(f"  {slug:35} {inn}  {name}  liquidator: {liquidator}")
        print()

    if mismatches:
        print("--- Mismatches (need a human to resolve) ---")
        for slug, inn, name, problems in mismatches:
            print(f"  {slug} ({inn}, {name})")
            for p in problems:
                print(f"    - {p}")
        print()

    if args.write:
        ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote _egrul_crosschecked onto {n_clean} clean entities.")
    else:
        print("(dry run — pass --write to record _egrul_crosschecked on clean entities)")


if __name__ == "__main__":
    main()
