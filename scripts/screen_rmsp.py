#!/usr/bin/env python3
"""Screen every entity with an ИНН against rmsp.nalog.ru's Единый реестр
субъектов МСП (SME registry) — a single unauthenticated GET, no captcha, no
polling. Confirmed working 2026-09-05 (see notes/SOURCE_REGISTER.md #45).

`GET https://rmsp.nalog.ru/search-proc.json?query=<ИНН>` returns a `data[]`
array (usually 0 or 1 row) carrying: `category` (1/2/3 = micro/small/medium),
`is_active`, `is_hitech` (a self-reported/certified high-tech flag — new to
this project's toolkit), `has_licenses`, `has_contracts` (booleans on
government-contract/licence history, corroborating but not a substitute for
`government_contracts[]`/`licences[]`), `od2_sschr` (headcount as reported
to this registry — a second data point alongside `workforce_history[]`),
`dtregistry` (date first entered the SME registry), and `name_ex`.

No hit at all means either the entity is NOT a registered SME (plausible for
a large prime, a fund/АНО, or a foreign-owned entity excluded by law) or the
ИНН wasn't found — this script does not try to distinguish those, same as
any other negative-result registry check in this project.

Writes `rmsp_hit`/`rmsp_checked_at` onto each entity in
data/registry/entities.json. Fetched screening data, not a hand correction —
must NOT be set via corrections_entities.json (see CLAUDE.md's carry-forward-
fields rule); extract_registry.py must be taught to carry these two fields
forward the same way it already does for other screen_*.py outputs before
this survives a regeneration untouched.

Live network job against a third-party (government) service, but a single
unauthenticated GET per ИНН with no auth/polling/captcha — same class as
`screen_egrip_ip.py`/`screen_subsidiary.py`. `--slug`/`--inn` is ordinary
inline reconnaissance; a full-roster sweep (no `--slug`/`--limit`) is handed
to the user per CLAUDE.md's crawling-jobs policy.

Usage:
    python3 scripts/screen_rmsp.py --slug ooo-boevye-tekhnologii
    python3 scripts/screen_rmsp.py --inn 5262393781
    python3 scripts/screen_rmsp.py --limit 20
    python3 scripts/screen_rmsp.py --force
"""
from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"

BASE_URL = "https://rmsp.nalog.ru/search-proc.json"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CONNECT_TIMEOUT = 10
DELAY_BETWEEN_QUERIES = 1.5


def query(inn: str) -> list[dict]:
    url = f"{BASE_URL}?query={inn}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result.get("data") or []


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None)
    ap.add_argument("--inn", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    today = date.today().isoformat()

    targets = [e for e in entities if e.get("inn")]
    if args.slug:
        targets = [e for e in targets if e["slug"] == args.slug]
    elif args.inn:
        targets = [e for e in targets if e["inn"] == args.inn]
    if not args.force:
        targets = [e for e in targets if e.get("rmsp_checked_at") != today]
    if args.limit:
        targets = targets[: args.limit]

    if not targets:
        print("Nothing to do (everyone already checked today — use --force).")
        return

    print(f"Screening {len(targets)} entities against {BASE_URL} ...")
    for i, entity in enumerate(targets, 1):
        inn = entity["inn"]
        label = f"{entity['slug']} ({inn})"
        try:
            rows = query(inn)
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  {i}/{len(targets)}  {label}  ERROR: {e}")
            continue

        entity["rmsp_hit"] = rows[0] if rows else None
        entity["rmsp_checked_at"] = today
        ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        if rows:
            row = rows[0]
            flag = " *** is_hitech ***" if row.get("is_hitech") else ""
            print(f"  {i}/{len(targets)}  {label}  category={row.get('category')} "
                  f"active={row.get('is_active')} headcount={row.get('od2_sschr')} "
                  f"licences={row.get('has_licenses')} contracts={row.get('has_contracts')}{flag}")
        else:
            print(f"  {i}/{len(targets)}  {label}  no hit (not in SME registry, or ИНН not found)")
        time.sleep(DELAY_BETWEEN_QUERIES)

    print("\nDone. A hit corroborates but never substitutes for "
          "government_contracts[]/licences[]/workforce_history[] — cross-check before wiring in.")


if __name__ == "__main__":
    main()
