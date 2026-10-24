#!/usr/bin/env python3
"""Screen every person in the registry against leader-id.ru's participant
search -- see leader_id_ru_users_api memory for the full API writeup.

Unlike rk.2035.university and the Rospatent trademark search, this endpoint
IS genuinely login-gated (confirmed via a clean 401 without credentials).
Access here uses a live Bearer JWT pulled from the user's own logged-in
browser session (LEADER_ID_BEARER_TOKEN in .env) -- not an API key, a
personal session token. It expires; if this script starts getting 401s,
the token needs refreshing the same way it was obtained (DevTools -> Copy
as cURL on a live leader-id.ru/api/v4/... request while logged in).

**Live network job against a third-party site using a personal login
session -- per CLAUDE.md's crawling-jobs policy, tested inline on a
handful of records first. Given this authenticates as a real person's
account (not an anonymous/API-key client), the full-roster sweep should
still be run by you, not executed in the background, and should stay
throttled.**

Search is name-only (no ИНН/ОГРН field on this platform), so **there is no
identifier to cross-check against** the way rk.2035.university or GUR
allow -- every hit here is a name-collision risk by construction. This
script writes raw candidates only; nothing here should be promoted to a
person record without independently corroborating a specific field
(employer name, city, a role title) against something already documented,
never on name alone.

Writes `leader_id_matches[]` (raw evidence, list of {query, user_id,
last_name, first_name, father_name, employment_company, employment_position,
city, region, last_seen}) + `leader_id_screened_at` directly onto
people.json (screened data, not a hand correction -- same pattern as
screen_gur.py; add to PEOPLE_CARRY_FORWARD_FIELDS in extract_registry.py in
the same change this script is introduced).

After running this, refresh the pipeline:
    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
    python3 scripts/inventory_sources.py
    python3 scripts/extract_registry.py
    python3 scripts/check_registry.py

Usage:
    python3 scripts/screen_leader_id.py                 # everyone, skip already-screened today
    python3 scripts/screen_leader_id.py --limit 5        # first 5 only
    python3 scripts/screen_leader_id.py --force          # re-screen even if already done today
    python3 scripts/screen_leader_id.py --slug sokolov-german-olegovich
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PEOPLE = REPO / "data" / "registry" / "people.json"
ENV_FILE = REPO / ".env"

BASE = "https://leader-id.ru"
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36")
DELAY_SECONDS = 2.0


def load_token() -> str:
    token = os.environ.get("LEADER_ID_BEARER_TOKEN")
    if token:
        return token
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("LEADER_ID_BEARER_TOKEN="):
                return line.split("=", 1)[1].strip()
    raise SystemExit("LEADER_ID_BEARER_TOKEN not set in environment or .env")


def strip_role(fio: str) -> str:
    # people.json fio_ru is "Фамилия Имя Отчество" -- pass through
    return fio.strip()


def search(token: str, query: str) -> list[dict]:
    params = {
        "paginationPage": 1,
        "paginationSize": 10,
        "query": query,
    }
    url = f"{BASE}/api/v4/users/search?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "Referer": f"{BASE}/users",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        obj = json.loads(resp.read().decode("utf-8", errors="replace"))
    return (obj.get("data") or {}).get("_items") or []


def flatten_hit(query: str, hit: dict) -> dict:
    emp = hit.get("employment") or {}
    addr = hit.get("address") or {}
    return {
        "query": query,
        "user_id": hit.get("id"),
        "last_name": hit.get("last_name"),
        "first_name": hit.get("first_name"),
        "father_name": hit.get("father_name"),
        "employment_company": emp.get("company"),
        "employment_position": emp.get("position"),
        "city": (addr.get("titles") or {}).get("city"),
        "region": (addr.get("titles") or {}).get("region"),
        "last_seen": hit.get("last_seen"),
    }


def process(people: list[dict], token: str, today: str, force: bool, limit: int | None) -> int:
    targets = []
    for p in people:
        if p.get("_merged_into"):
            continue
        if not force and p.get("leader_id_screened_at") == today:
            continue
        if p.get("fio_ru"):
            targets.append(p)
    if limit is not None:
        targets = targets[:limit]

    if not targets:
        print("nothing to do (all already screened today, use --force to re-screen)")
        return 0

    print(f"screening {len(targets)} people ...")
    hit_count = 0
    for i, p in enumerate(targets, 1):
        slug = p.get("slug")
        query = strip_role(p.get("fio_ru", ""))
        try:
            hits = search(token, query)
        except urllib.error.HTTPError as ex:
            if ex.code == 401:
                raise SystemExit(
                    "401 Unauthorized -- LEADER_ID_BEARER_TOKEN has expired. "
                    "Re-capture via DevTools 'Copy as cURL' on a live "
                    "leader-id.ru/api/v4/... request while logged in, and "
                    "update .env."
                )
            print(f"  [{i}/{len(targets)}] {slug}: query {query!r} FAILED ({ex})")
            time.sleep(DELAY_SECONDS)
            continue
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as ex:
            print(f"  [{i}/{len(targets)}] {slug}: query {query!r} FAILED ({ex})")
            time.sleep(DELAY_SECONDS)
            continue

        matches = [flatten_hit(query, h) for h in hits]
        p["leader_id_matches"] = matches
        p["leader_id_screened_at"] = today
        if matches:
            hit_count += 1
            print(f"  [{i}/{len(targets)}] {slug}: {len(matches)} candidate(s) "
                  f"(name-only match -- verify before promoting)")
        else:
            print(f"  [{i}/{len(targets)}] {slug}: no hits")
        time.sleep(DELAY_SECONDS)

    return hit_count


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--slug", default=None, help="run for a single person slug only")
    args = ap.parse_args()

    token = load_token()
    today = date.today().isoformat()
    people = json.loads(PEOPLE.read_text(encoding="utf-8"))
    if args.slug:
        subset = [p for p in people if p.get("slug") == args.slug]
        if not subset:
            print(f"no person with slug {args.slug!r}")
            return
        process(subset, token, today, True, None)
    else:
        process(people, token, today, args.force, args.limit)

    PEOPLE.write_text(json.dumps(people, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\nDone. Every screened person now carries leader_id_matches[] + leader_id_screened_at.")
    print("Re-run scripts/check_registry.py, then hand-review matches -- there is NO identifier "
          "to cross-check on this platform (name-only search), so every hit is a candidate, "
          "never a confirmed match, until corroborated against something already documented "
          "(employer, city, role).")


if __name__ == "__main__":
    main()
