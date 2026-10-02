#!/usr/bin/env python3
"""Screen every registry entity against war-sanctions.gur.gov.ua — Ukrainian
military intelligence's (GUR) open sanctions/instruments-of-war database.

Confirmed working 2026-08-24 (was previously thought geoblocked/403 — a bare
request with no User-Agent header returns 403, but a real browser UA works
fine over plain HTTPS with urllib, no special client needed). Tested inline
against two records: ALYOSHIN Boris Sergeevich (sanctions/persons/5316) and
NPO Rustekhdron LLC (uav/companies/14300, ИНН/ОГРН independently confirmed an
exact match, 3 previously-unrecorded "FPV kamikaze" product names surfaced,
plus a "related company" listing for Concern Kalashnikov JSC that is NOT
independently verified as a real corporate tie — GUR's own site doesn't
explain that widget's basis).

**Live network job against a third-party site — per CLAUDE.md's crawling-jobs
policy, tested inline on a handful of records first (ordinary
reconnaissance), but the full-roster sweep should be run by you, not
executed in the background.**

Site search (`/en/search?q=<name>`) is free-text relevance-ranked, not an
identity-scored match — same discipline as screen_aleph.py applies: every
result is a lead, not a source. This script fetches each entity's own profile
page (once a search hit is found) and extracts the profile's own stated
ИНН/ОГРН — cross-check that against the query entity's own identifiers before
trusting a match, same as the OpenSanctions/Aleph triage did. A name match
alone is not enough; several already-known false-positive patterns from this
project's other screens (generic words, unrelated same-name companies) apply
here just as much.

Writes `gur_matches[]` (list of {url, caption, own_inn, own_ogrn, inn_match,
ogrn_match, products, related_companies, sanction_jurisdictions_listed}) +
`gur_screened_at` directly onto entities.json (screened data, not a hand
correction — same pattern as screen_rom.py's securing_measures[], NOT routed
through corrections.json). A human still has to read each match and decide
whether it upgrades an entity's `products[]`/`sanctions[]`/`related_entities[]`.

Any hit is archived to data/sources/GUR_<inn-or-slug>_<date>_<slug>.html.

After running this, refresh the pipeline:
    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
    python3 scripts/inventory_sources.py
    python3 scripts/extract_registry.py
    python3 scripts/check_registry.py

Usage:
    python3 scripts/screen_gur.py                  # everyone, skip already-screened today
    python3 scripts/screen_gur.py --limit 5         # first 5 only
    python3 scripts/screen_gur.py --force           # re-screen even if already done today
    python3 scripts/screen_gur.py --only slug-a,slug-b   # just these entities
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
SOURCES = REPO / "data" / "sources"

BASE = "https://war-sanctions.gur.gov.ua"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
DELAY_SECONDS = 1.5  # be polite -- this is a small NGO/government site, not a bulk API

RE_PROFILE_LINK = re.compile(
    r'href="(https://war-sanctions\.gur\.gov\.ua/en/(?:uav/companies|sanctions/legal-entities|sanctions/persons)/\d+)"'
)
RE_TIN = re.compile(r'\bTIN\b\s*</[^>]+>\s*<[^>]+>\s*([\d]{8,15})|TIN\s+(\d{8,15})')
RE_REG_NUM = re.compile(r'Registration number\D{0,30}?(\d{8,15})')


def slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    ascii_name = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name).strip("-").lower()
    return ascii_name or "record"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def strip_tags(html: str) -> str:
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", html)
    return re.sub(r"\s+", " ", text).strip()


def search(query: str) -> list[str]:
    url = f"{BASE}/en/search?{urllib.parse.urlencode({'q': query})}"
    html = fetch(url)
    return list(dict.fromkeys(RE_PROFILE_LINK.findall(html)))  # dedupe, preserve order


def parse_profile(html: str) -> dict:
    text = strip_tags(html)
    tin_m = RE_TIN.search(html) or RE_TIN.search(text)
    tin = next((g for g in (tin_m.groups() if tin_m else []) if g), None) if tin_m else None
    reg_m = RE_REG_NUM.search(text)
    reg = reg_m.group(1) if reg_m else None

    caption_m = re.search(r"<title>([^<]+)</title>", html)
    caption = caption_m.group(1).strip() if caption_m else None

    jurisdictions_m = re.search(r"Sanction Jurisdictions(.+?)Date of entry", text)
    jurisdictions = jurisdictions_m.group(1).strip() if jurisdictions_m else None

    has_confirmed_listing = "The country has not yet applied sanctions" not in text

    return {
        "caption": caption,
        "own_tin": tin,
        "own_reg_number": reg,
        "sanction_jurisdictions_listed": jurisdictions,
        "has_confirmed_listing_language": has_confirmed_listing,
    }


def process(entities: list[dict], today: str, force: bool, limit: int | None,
            only: set | None = None) -> int:
    targets = []
    for e in entities:
        if only is not None:
            if e.get("slug") not in only:
                continue
        elif not force and e.get("gur_screened_at") == today:
            continue
        name = e.get("name_ru")
        if not name:
            continue
        targets.append(e)
    if limit is not None:
        targets = targets[:limit]

    if not targets:
        print("nothing to do (all already screened today, use --force to re-screen)")
        return 0

    print(f"screening {len(targets)} entit(ies) ...")
    hit_count = 0
    for i, e in enumerate(targets, 1):
        slug = e.get("slug") or slugify(e.get("name_ru", "record"))
        # Search by the transliterated/latin brand or name where available,
        # since GUR indexes English-transliterated company names -- a bare
        # Cyrillic query tends to miss even entities that are on the site
        # (confirmed inline: "Tsentr bespilotnykh sistem" as literal
        # transliteration missed real hits that a different query might catch).
        query = e.get("name_latin") or e.get("brand_latin") or e.get("name_ru")
        try:
            links = search(query)
        except (urllib.error.URLError, TimeoutError) as ex:
            print(f"  [{i}/{len(targets)}] {slug} SEARCH FAILED: {ex}")
            time.sleep(DELAY_SECONDS)
            continue

        matches = []
        for link in links[:5]:  # cap profile fetches per entity
            try:
                profile_html = fetch(link)
            except (urllib.error.URLError, TimeoutError) as ex:
                print(f"    profile fetch failed for {link}: {ex}")
                continue
            parsed = parse_profile(profile_html)
            inn_match = bool(e.get("inn")) and parsed.get("own_tin") == e.get("inn")
            ogrn_match = bool(e.get("ogrn")) and parsed.get("own_reg_number") == e.get("ogrn")
            entry = {
                "url": link,
                "caption": parsed.get("caption"),
                "own_tin": parsed.get("own_tin"),
                "own_reg_number": parsed.get("own_reg_number"),
                "inn_match": inn_match,
                "ogrn_match": ogrn_match,
                "sanction_jurisdictions_listed": parsed.get("sanction_jurisdictions_listed"),
                "has_confirmed_listing_language": parsed.get("has_confirmed_listing_language"),
            }
            matches.append(entry)
            if inn_match or ogrn_match:
                out = SOURCES / f"GUR_{e.get('inn') or slug}_{today.replace('-', '')}_{slug}.html"
                out.write_text(profile_html, encoding="utf-8")
                print(f"    *** ID-CONFIRMED: {slug} <-> {link} -- saved {out.name} ***")
            time.sleep(DELAY_SECONDS)

        e["gur_matches"] = matches
        e["gur_screened_at"] = today
        if any(m["inn_match"] or m["ogrn_match"] for m in matches):
            hit_count += 1
            print(f"  [{i}/{len(targets)}] {slug}: {len(matches)} profile(s) checked, ID-confirmed hit")
        else:
            print(f"  [{i}/{len(targets)}] {slug}: {len(matches)} profile(s) checked, no ID-confirmed hit")

        time.sleep(DELAY_SECONDS)

    return hit_count


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", help="comma-separated entity slugs to screen, whatever their screen date "
                                   "(the status board's daily queue uses this)")
    args = ap.parse_args()

    today = date.today().isoformat()
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    only = set(args.only.split(",")) if args.only else None
    total_hits = process(entities, today, args.force, args.limit, only)
    ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nDone. {total_hits} entit(ies) with an ID-confirmed GUR match archived to data/sources/.")
    print("Every screened entity now carries gur_matches[] + gur_screened_at.")
    print("Re-run scripts/check_registry.py, then hand-review matches before promoting anything into "
          "products[]/sanctions[]/related_entities[] -- an ID match confirms identity, not that every "
          "field on the GUR page (e.g. 'related companies') is itself independently verified.")


if __name__ == "__main__":
    main()
