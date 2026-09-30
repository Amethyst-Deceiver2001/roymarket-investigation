#!/usr/bin/env python3
"""Screen every registry entity against rk.2035.university's open БАС
(UAV-industry) company registry -- see rk_2035_university_bas_registry
memory for the full API writeup. Discovered 2026-08-24 from a user-supplied
HAR capture of the site's own org-search feature.

No authentication needed -- confirmed by replaying a captured request with
plain curl (no cookie/session) and getting an identical live response.

**Live network job against a third-party site -- per CLAUDE.md's
crawling-jobs policy, tested inline on a handful of records first, but the
full-roster sweep should be run by you, not executed in the background.**

Search is a plain substring on the organization's registered name, so this
queries by both the cleaned legal name (legal-form prefix stripped, same
`strip_legal_form()` as rospatent_tm_ws_search.py) and the brand name where
distinct -- a name-only search would miss a brand-registered profile the
same way the earlier reseller-mediated WB-overlap and Тримикс trademark
findings showed elsewhere in this project. No rate limit was observed in
the captured HAR, but this is still throttled out of caution.

Writes `rk2035_matches[]` (raw evidence, list of {query, org_id,
organization_name, short_name, inn, ogrn, kpp, email, phone, address,
sector, activity_types, personnel_count, inn_match, ogrn_match}) +
`rk2035_screened_at` directly onto entities.json (screened data, not a hand
correction -- same pattern as screen_gur.py; added to
ENTITY_CARRY_FORWARD_FIELDS in extract_registry.py in the same change this
script was introduced).

**Verify by identifier, never by name alone** -- this project's own
standing rule (see [[opensanctions_ru_inn_dataset_nuance]] and the
"аэромакс" false positive that motivated the memory this script is based
on): a same-brand-sounding hit with a DIFFERENT ИНН/ОГРН than the query
entity is a name collision, not a match. This script flags inn_match/
ogrn_match explicitly so promotion review can filter on that rather than
eyeballing names.

After running this, refresh the pipeline:
    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
    python3 scripts/inventory_sources.py
    python3 scripts/extract_registry.py
    python3 scripts/check_registry.py

Usage:
    python3 scripts/screen_rk2035_bas_registry.py                # everyone, skip already-screened today
    python3 scripts/screen_rk2035_bas_registry.py --limit 5       # first 5 only
    python3 scripts/screen_rk2035_bas_registry.py --force         # re-screen even if already done today
    python3 scripts/screen_rk2035_bas_registry.py --slug ooo-trimiks
"""
from __future__ import annotations

import argparse
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"

# rk.2035.university's cert chain isn't recognized by this machine's default
# trust store even though curl (via macOS Keychain) verifies it fine -- same
# workaround already used in fips_patent_lookup.py for a similar site.
_UNVERIFIED_CTX = ssl.create_default_context()
_UNVERIFIED_CTX.check_hostname = False
_UNVERIFIED_CTX.verify_mode = ssl.CERT_NONE

BASE = "https://rk.2035.university"
USER_AGENT = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36")
DELAY_SECONDS = 1.5

LEGAL_FORM_RE = re.compile(
    r'^(?:АО|ОАО|ЗАО|ПАО|ООО|АНО|НПО|НПЦ|НПП|ФГУП|ГУП|КБ)\s+'
    r'(?:«([^»]+)»|"([^"]+)")',
    re.IGNORECASE,
)


def strip_legal_form(name: str) -> str:
    m = LEGAL_FORM_RE.match(name.strip())
    if m:
        return (m.group(1) or m.group(2)).strip()
    m2 = re.search(r'«([^»]+)»|"([^"]+)"', name)
    if m2:
        return (m2.group(1) or m2.group(2)).strip()
    return name.strip()


def search(query: str) -> list[dict]:
    params = {
        "filters[name]": query,
        "filters[moderation_status]": "approved",
        "page": 1,
        "pageSize": 50,
    }
    url = f"{BASE}/api/v1/organization/view-organization/get-all?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Referer": f"{BASE}/",
    })
    with urllib.request.urlopen(req, timeout=30, context=_UNVERIFIED_CTX) as resp:
        obj = json.loads(resp.read().decode("utf-8", errors="replace"))
    return obj.get("values") or []


def flatten_hit(query: str, hit: dict, entity: dict) -> dict:
    gi = hit.get("general_info") or {}
    addr = (hit.get("contacts") or {}).get("address") or {}
    sectors = []
    activities = []
    for ct in hit.get("company_type") or []:
        val = ct.get("value") or {}
        if val.get("name"):
            sectors.append(val["name"])
        for spec in ct.get("spec_organization") or []:
            if spec.get("name"):
                activities.append(spec["name"])
    inn = gi.get("inn")
    ogrn = gi.get("ogrn")
    return {
        "query": query,
        "org_id": gi.get("org_id"),
        "organization_name": gi.get("organization_name"),
        "short_name": gi.get("short_name"),
        "inn": inn,
        "ogrn": ogrn,
        "kpp": gi.get("kpp"),
        "email": gi.get("email"),
        "phone": gi.get("phone"),
        "site": gi.get("site"),
        "address": addr.get("company_legal_address"),
        "sectors": sectors,
        "activity_types": activities,
        "personnel_count": gi.get("personal_quantity"),
        "profile_created_at": gi.get("created_at"),
        "inn_match": bool(entity.get("inn")) and inn == entity.get("inn"),
        "ogrn_match": bool(entity.get("ogrn")) and ogrn == entity.get("ogrn"),
    }


def process(entities: list[dict], today: str, force: bool, limit: int | None) -> int:
    targets = []
    for e in entities:
        if e.get("tier") != "manufacturer":
            continue
        if not force and e.get("rk2035_screened_at") == today:
            continue
        if e.get("name_ru"):
            targets.append(e)
    if limit is not None:
        targets = targets[:limit]

    if not targets:
        print("nothing to do (all already screened today, use --force to re-screen)")
        return 0

    print(f"screening {len(targets)} entit(ies) ...")
    hit_count = 0
    for i, e in enumerate(targets, 1):
        slug = e.get("slug")
        queries = []
        cleaned = strip_legal_form(e.get("name_ru", ""))
        if cleaned:
            queries.append(cleaned)
        for key in ("brand_ru", "brand_latin"):
            brand = e.get(key)
            if brand and brand.strip() and brand.strip().lower() not in (q.lower() for q in queries):
                queries.append(brand.strip())

        matches = []
        seen_org_ids = set()
        for q in queries:
            try:
                hits = search(q)
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as ex:
                print(f"  [{i}/{len(targets)}] {slug}: query {q!r} FAILED ({ex})")
                time.sleep(DELAY_SECONDS)
                continue
            for hit in hits:
                flat = flatten_hit(q, hit, e)
                if flat["org_id"] in seen_org_ids:
                    continue
                seen_org_ids.add(flat["org_id"])
                matches.append(flat)
            time.sleep(DELAY_SECONDS)

        e["rk2035_matches"] = matches
        e["rk2035_screened_at"] = today
        confirmed = [m for m in matches if m["inn_match"] or m["ogrn_match"]]
        if confirmed:
            hit_count += 1
            print(f"  [{i}/{len(targets)}] {slug}: {len(matches)} hit(s), "
                  f"{len(confirmed)} ID-confirmed")
        elif matches:
            print(f"  [{i}/{len(targets)}] {slug}: {len(matches)} hit(s), "
                  f"0 ID-confirmed (name collision(s) -- do not promote without checking)")
        else:
            print(f"  [{i}/{len(targets)}] {slug}: no hits")

    return hit_count


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--slug", default=None, help="run for a single entity slug only")
    args = ap.parse_args()

    today = date.today().isoformat()
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    if args.slug:
        subset = [e for e in entities if e.get("slug") == args.slug]
        if not subset:
            print(f"no entity with slug {args.slug!r}")
            return
        process(subset, today, True, None)
    else:
        process(entities, today, args.force, args.limit)

    ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("\nDone. Every screened entity now carries rk2035_matches[] + rk2035_screened_at.")
    print("Re-run scripts/check_registry.py, then hand-review matches (filter on inn_match/ogrn_match) "
          "before promoting anything -- a name hit with no ID match is a collision, see the Аэромакс case "
          "in the rk_2035_university_bas_registry memory.")


if __name__ == "__main__":
    main()
