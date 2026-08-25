#!/usr/bin/env python3
"""Screen every registry entity's own ИНН against Wildberries seller records,
writing raw `wb_matches[]` + `wb_screened_at` directly onto entities.json.

Local file read only (a sibling repo's already-scraped SQLite DB) — no
network call, safe to run directly/repeatedly. This is the raw-evidence half
of the `wb_overlap` split decided in the rebuild plan (Phase 3.5 §1):
`wb_matches[]` is what this script finds (a direct ИНН hit or none), and
`wb_overlap` stays a **human-set conclusion only** (`confirmed_direct` /
`confirmed_reseller` / `none_found` / `not_checked`), written via
corrections.json — a reseller relationship (a seller selling the product
under a *different* legal entity's ИНН, e.g. the Тримикс/Макс 911 case) is
not something an ИНН join can find, and needs the same brand-name-search +
primary-source verification this project already applies everywhere else.

Per CLAUDE.md's carry-forward rule: `wb_matches`/`wb_screened_at` must be
written directly onto entities.json (not via corrections.json, which can't
set carry-forward screening fields), then extract_registry.py carries them
forward on every future regeneration.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES_PATH = REPO / "data" / "registry" / "entities.json"
DEFAULT_WB_WATCH_DB = Path.home() / "Downloads" / "wb_watch" / "data" / "wb_watch.db"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--wb-watch-db", type=Path, default=DEFAULT_WB_WATCH_DB,
                     help=f"path to wb_watch's sellers DB (default: {DEFAULT_WB_WATCH_DB})")
    ap.add_argument("--dry-run", action="store_true", help="report matches, write nothing")
    args = ap.parse_args()

    if not args.wb_watch_db.exists():
        print(f"error: {args.wb_watch_db} not found — pass --wb-watch-db, or "
              f"this screen needs the wb_watch sibling repo's scraped DB",
              file=sys.stderr)
        return 1

    entities = json.loads(ENTITIES_PATH.read_text(encoding="utf-8"))
    entities_with_inn = [e for e in entities if e.get("inn")]

    conn = sqlite3.connect(str(args.wb_watch_db))
    conn.row_factory = sqlite3.Row
    sellers = conn.execute(
        "SELECT supplier_id, name, full_name, inn, ogrnip, trademark, "
        "supplier_rating FROM sellers WHERE inn IS NOT NULL AND inn != ''"
    ).fetchall()
    by_inn: dict[str, list[sqlite3.Row]] = {}
    for row in sellers:
        by_inn.setdefault(row["inn"], []).append(row)

    today = date.today().isoformat()
    matched = 0
    for e in entities_with_inn:
        rows = by_inn.get(e["inn"], [])
        e["wb_matches"] = [
            {
                "supplier_id": r["supplier_id"],
                "seller_name": r["name"],
                "seller_full_name": r["full_name"],
                "ogrnip": r["ogrnip"],
                "trademark": r["trademark"],
                "supplier_rating": r["supplier_rating"],
            }
            for r in rows
        ]
        e["wb_screened_at"] = today
        if rows:
            matched += 1
            print(f"MATCH  {e['name_ru']} ({e['inn']}) -> "
                  f"{', '.join(r['name'] for r in rows)}")

    print(f"\n{len(entities_with_inn)} entities screened (own ИНН against "
          f"{len(sellers)} WB sellers with an ИНН on file), {matched} direct match(es).")
    print("Reminder: this only finds a seller trading under the entity's OWN "
          "ИНН. A reseller trading under a different entity (see the Тримикс/"
          "Макс 911 case) needs a brand-name search + primary-source check, "
          "same as before — wb_overlap conclusions are still set by hand via "
          "corrections.json.")

    if not args.dry_run:
        ENTITIES_PATH.write_text(
            json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"\nwrote wb_matches/wb_screened_at directly to {ENTITIES_PATH}")
    else:
        print("\n--dry-run: nothing written")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
