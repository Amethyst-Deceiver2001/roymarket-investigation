#!/usr/bin/env python3
"""Screen every entity's legal name against br.fas.gov.ru's «База решений и
правовых актов» (FAS decisions & legal-acts database — antitrust rulings,
223-ФЗ/44-ФЗ procurement-complaint decisions, РНП inclusion decisions).

Confirmed scriptable 2026-09-05 via plain `curl` (no JS, no cookies, no
session): `GET https://br.fas.gov.ru/?text=<quoted name>&type=0` is a
server-rendered full-text case search; the result page's own "Всего: N"
line gives a hit count with no HTML parsing needed beyond that one regex.
Verified against a known-high-hit name ("Ростелеком" -> 136) and a known
small entity with no antitrust history (0 hits, page omits the "Всего:"
line entirely when empty) via both a real browser and a bare `curl` --
identical results, confirming no browser/session dependency.

**This is a name-text search, not an ИНН-keyed lookup** — searching a bare
ИНН as `text` returns 0 hits even for entities that do have cases (the
index appears to be case/document prose, not a structured party-ИНН field).
Every hit therefore needs manual reading of the actual case to confirm it's
the right entity and not a same-name collision, exactly like any other
name-based registry check in this project (cf. `screen_disqualified.py`'s
own DOB-collision caveat) -- a hit is a lead, not a citable fact until a
human reads at least one matching case page.

An organization-ID-based filter (`organizations=<uuid>` query param, fed by
a `/ajax/organizations/?term=` typeahead) also exists on this site and
would be a more precise filter than free-text name search, but that
typeahead endpoint ignores its own `term` parameter in testing (returns an
identical unfiltered page regardless of query) -- either the wrong param
name or a session/CSRF-bound "heavy" django-select2 widget that doesn't
work via a bare unauthenticated GET. Not pursued further; free-text search
is good enough for a first-pass screen.

Writes `fas_br_hit_count`/`fas_br_checked_at` onto each entity in
data/registry/entities.json. Fetched screening data, not a hand correction
-- must NOT be set via corrections_entities.json; wired into
extract_registry.py's ENTITY_CARRY_FORWARD_FIELDS so it survives a
regeneration.

Live network job against a third-party (government) service, but a single
unauthenticated GET per entity with no auth/polling/captcha -- same class
as screen_rmsp.py. `--slug` is ordinary inline reconnaissance; a full-
roster sweep (no `--slug`/`--limit`) is handed to the user per CLAUDE.md's
crawling-jobs policy.

Usage:
    python3 scripts/screen_fas_br.py --slug ooo-boevye-tekhnologii
    python3 scripts/screen_fas_br.py --limit 20
    python3 scripts/screen_fas_br.py --force
"""
from __future__ import annotations

import argparse
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
import json

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"

BASE_URL = "https://br.fas.gov.ru/"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
CONNECT_TIMEOUT = 12
DELAY_BETWEEN_QUERIES = 2.0

TOTAL_RE = re.compile(r"Всего:\s*(\d+)")


def query(name: str) -> int:
    q = urllib.parse.urlencode({"text": f'"{name}"', "type": "0"})
    url = f"{BASE_URL}?{q}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=CONNECT_TIMEOUT) as resp:
        html = resp.read().decode("utf-8", errors="replace")
    m = TOTAL_RE.search(html)
    return int(m.group(1)) if m else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", default=None)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    today = date.today().isoformat()

    targets = [e for e in entities if e.get("name_ru")]
    if args.slug:
        targets = [e for e in targets if e["slug"] == args.slug]
    if not args.force:
        targets = [e for e in targets if e.get("fas_br_checked_at") != today]
    if args.limit:
        targets = targets[: args.limit]

    if not targets:
        print("Nothing to do (everyone already checked today — use --force).")
        return

    print(f"Screening {len(targets)} entities against {BASE_URL} (free-text case search) ...")
    for i, entity in enumerate(targets, 1):
        # Strip legal-form prefix/quotes for a cleaner match -- "ООО «Х»" as a
        # literal quoted phrase rarely appears verbatim in case prose, but the
        # bare name inside the guillemets does.
        name = entity["name_ru"]
        m = re.search(r"«([^»]+)»", name)
        search_name = m.group(1) if m else name
        label = f"{entity['slug']} ({search_name})"
        try:
            count = query(search_name)
        except (urllib.error.URLError, TimeoutError) as e:
            print(f"  {i}/{len(targets)}  {label}  ERROR: {e}")
            continue

        entity["fas_br_hit_count"] = count
        entity["fas_br_checked_at"] = today
        ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        flag = " *** HIT — READ CASES BEFORE TREATING AS FINDING ***" if count else ""
        print(f"  {i}/{len(targets)}  {label}  {count} case(s){flag}")
        time.sleep(DELAY_BETWEEN_QUERIES)

    print("\nDone. A hit is a lead, not a fact -- read at least one matching case at "
          "br.fas.gov.ru before wiring anything into litigation[]/why[].")


if __name__ == "__main__":
    main()
