#!/usr/bin/env python3
"""Screen registry entities against proverki.gov.ru's ФГИС «Единый реестр
контрольных (надзорных) мероприятий» / «Единый реестр проверок» -- the
federal inspections registry (Rostrud/Rospotrebnadzor/MChS/Rostekhnadzor/
etc. control-and-oversight actions, by ИНН/ОГРН).

**Confirmed workable 2026-09-07 via chrome-devtools browser automation**
(see notes/source_expansion_methodology.md) -- reverse-engineered the real
API (the site's own client JS also fires a large number of scrambled/
per-session URLs that look like a custom API but are actually just
Dynatrace RUM telemetry beacons, e.g. POST to a random path returning
`{"status": "success", "result": 0}` -- ignore those entirely). The real,
FIXED, non-obfuscated endpoints are:

  1. GET  /public/api/captcha
         -> image/jpeg body (a distorted-text CAPTCHA). No id in the
            response; it's tied to the session cookie (JSESSIONID).
  2. POST /public/api/inspections/token?captcha=<solved text>
         -> 200 with a plain-text token body on success, e.g. a
            base64-looking string; 403 with body "Invalid captcha." on a
            wrong guess (plain text/plain, NOT JSON either way).
  3. GET  /public/api/inspections/find?page=50,1&searchString=<ИНН>
         header "token: <token from step 2>"
         -> 200 JSON with the inspection records; 403 InvalidTokenException
            if the token is missing/stale/reused after a search.

Each search appears to need a FRESH captcha/token -- reusing an old token
for a second searchString 403s. This makes the endpoint captcha-gated on
every single query, not just after N requests like pb.nalog.ru's wall.

**Live network job against a third-party service, and CAPTCHA-GATED ON
EVERY QUERY -- per CLAUDE.md's crawling-jobs policy this cannot run
unattended.** This script is interactive by design: it saves each fetched
captcha image to a temp file and prompts on stdin for the solved text
(open the file yourself, e.g. `open /tmp/proverki_captcha.jpg` on macOS,
or view it via whatever screenshot/preview tool is at hand -- an
agent session with vision can equally read the saved file). There is no
unattended/full-roster mode; run it one entity/ИНН at a time, same as any
other inline reconnaissance under the project's policy. A full sweep
across the registry is a sequence of individual interactive runs, not a
single command to hand the user.

Writes `proverki_inspections[]` + `proverki_checked_at` directly onto the
matching record in data/registry/entities.json -- same category as
`opensanctions_matches`/`aleph_matches`/etc (raw fetched screening data,
NOT settable via corrections.json -- see ENTITY_CARRY_FORWARD_FIELDS in
extract_registry.py, which this script's two field names were added to
2026-09-07 so a later regeneration doesn't silently drop them). Each
inspection record: {reg_number, law (248-FZ/294-FZ), inn, ogrn, entity_name,
period, control_body, prosecutor_office, url}.

A "Найдено 0 КНМ" (0 results) is a real answer for many entities --
especially ones registered recently enough to have no inspection history
yet -- not a sign the query failed. Treat a genuine hit list the same as
any other screen_*.py output: a lead/corroboration to fold into the
registry by hand (address_history, name_history, facility_type, etc via
corrections_entities.json), not an automatic fact.

Usage:
    python3 scripts/screen_proverki.py --slug ao-nii-stt
    python3 scripts/screen_proverki.py --inn 6730046954
    python3 scripts/screen_proverki.py --inn 6730046954 --captcha-file /tmp/cap.jpg
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import date
from pathlib import Path

import requests

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"

BASE_URL = "https://proverki.gov.ru"
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def new_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT, "Referer": f"{BASE_URL}/portal/public-search"})
    # Establishes JSESSIONID -- the captcha/token/find endpoints are all
    # session-scoped, not query-param-scoped.
    s.get(f"{BASE_URL}/portal/public-search", timeout=15)
    return s


def solve_captcha_interactively(session: requests.Session, save_path: Path) -> str:
    resp = session.get(f"{BASE_URL}/public/api/captcha", timeout=15)
    resp.raise_for_status()
    save_path.write_bytes(resp.content)
    print(f"Captcha image saved to {save_path} -- open it and read the text.")
    return input("Captcha text: ").strip()


def get_token(session: requests.Session, captcha_text: str) -> str | None:
    resp = session.post(
        f"{BASE_URL}/public/api/inspections/token",
        params={"captcha": captcha_text},
        timeout=15,
    )
    if resp.status_code == 200:
        return resp.text.strip()
    print(f"  token request failed ({resp.status_code}): {resp.text[:200]}")
    return None


def find_inspections(session: requests.Session, token: str, query: str) -> dict:
    resp = session.get(
        f"{BASE_URL}/public/api/inspections/find",
        params={"page": "50,1", "searchString": query},
        headers={"token": token},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def screen_one(session: requests.Session, query: str, captcha_file: Path) -> list[dict] | None:
    """Runs the full captcha -> token -> find flow for one query. Retries
    the captcha up to 5 times (a wrong guess just costs another round, per
    the site's own behavior observed interactively -- it does not appear to
    lock out after a few misses the way pb.nalog.ru's wall does)."""
    for attempt in range(1, 6):
        captcha_text = solve_captcha_interactively(session, captcha_file)
        token = get_token(session, captcha_text)
        if token:
            break
        print(f"  retrying captcha ({attempt}/5) ...")
    else:
        print("  giving up after 5 captcha attempts")
        return None

    result = find_inspections(session, token, query)
    rows = result.get("content") or result.get("data") or result.get("result") or []
    if isinstance(result, dict) and "totalElements" in result:
        print(f"  {result.get('totalElements')} total (fetched {len(rows)})")
    return rows if isinstance(rows, list) else [result]


def normalize_row(row: dict) -> dict:
    """Best-effort field mapping -- the exact JSON key names haven't been
    captured from a successful response yet (every session interactively
    tested through 2026-09-07 hit a captcha-solve failure before reaching a
    real payload for inspection). Adjust these keys the first time a real
    response body is seen, using the visible search-results-table columns
    as the guide: reg. number, ФЗ, ИНН, ОГРН, entity name, month, control
    body, prosecutor's office."""
    return {
        "reg_number": row.get("regNumber") or row.get("number") or row.get("id"),
        "law": row.get("law") or row.get("federalLaw"),
        "inn": row.get("inn"),
        "ogrn": row.get("ogrn"),
        "entity_name": row.get("name") or row.get("entityName"),
        "period": row.get("period") or row.get("startDate"),
        "control_body": row.get("controlBody") or row.get("supervisoryAuthority"),
        "prosecutor_office": row.get("prosecutorOffice"),
        "url": (f"{BASE_URL}/portal/public-knm/{row['id']}" if row.get("id") else None),
        "_raw": row,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None, help="entity slug in entities.json")
    ap.add_argument("--inn", default=None, help="ИНН to search directly (no registry write if --slug is also omitted)")
    ap.add_argument("--captcha-file", default=None, help="where to save the captcha image (default: a temp file)")
    args = ap.parse_args()

    if not args.slug and not args.inn:
        print("Need --slug or --inn.")
        return 1

    entities = json.loads(ENTITIES.read_text(encoding="utf-8")) if ENTITIES.exists() else []
    entity = None
    if args.slug:
        entity = next((e for e in entities if isinstance(e, dict) and e.get("slug") == args.slug), None)
        if not entity:
            print(f"No entity with slug {args.slug!r} in {ENTITIES}")
            return 1
        query = args.inn or entity.get("inn")
        if not query:
            print(f"Entity {args.slug!r} has no inn on file -- pass --inn explicitly.")
            return 1
    else:
        query = args.inn

    captcha_file = Path(args.captcha_file) if args.captcha_file else Path(tempfile.gettempdir()) / "proverki_captcha.jpg"

    session = new_session()
    print(f"Screening {query!r} against {BASE_URL} ...")
    rows = screen_one(session, query, captcha_file)
    if rows is None:
        return 1

    normalized = [normalize_row(r) for r in rows]
    print(f"Found {len(normalized)} inspection record(s).")
    for r in normalized:
        print(f"  {r['reg_number']}  {r['period']}  {r['control_body']}")

    if entity is not None:
        entity["proverki_inspections"] = normalized
        entity["proverki_checked_at"] = date.today().isoformat()
        ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote proverki_inspections/proverki_checked_at onto {entity['slug']} in {ENTITIES}")
    else:
        print("No --slug given -- not writing to the registry, printing only.")
        print(json.dumps(normalized, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
