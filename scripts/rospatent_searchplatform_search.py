#!/usr/bin/env python3
"""Search searchplatform.rospatent.gov.ru's live, unauthenticated JSON API
for every manufacturer-tier entity in the registry, two ways: by entity
name (patent_holders filter) and by director full name (IN_RU inventor
field).

Discovered 2026-08-24: the interactive frontend at searchplatform.rospatent.
gov.ru (distinct from rospatent_tm_search.py/rospatent_patent_search.py,
which stream Rospatent's separate monthly bulk CSV dumps) exposes a plain
JSON POST endpoint with NO auth/session/cookie requirement — confirmed via
two user-supplied HAR captures of their own browser sessions, then
reproduced with a bare curl/urllib POST and got identical responses.

Two distinct, complementary query techniques were found across both HARs,
and this script uses both per entity:

1. **`filter: {"patent_holders:search": {"search": "<substring>"}}`** — the
   technique the UI itself uses FIRST, as the user types (confirmed via
   sgs/autocomplete entries in both HARs). Accepts a plain, lowercased,
   hyphenated substring (e.g. "атлант-аэро", "рустехдрон", "гаскар") — no
   need to reconstruct the exact canonical legal-form string. This is what
   this script uses for entity-name search, via `id_patterns.norm()` to
   strip legal-form prefixes/quotes the same way the rest of this project
   already normalizes names.
2. **`q: 'IN_RU= "<exact full ФИО>"'`** — field-scoped query, used for
   inventor/director search. Requires the FULL fio_ru, quoted, exact
   (confirmed: `IN_RU="Дзема Вадим"` partial would likely under/over-match;
   always pass the complete name as stored in the registry).

**Do NOT use plain free-text `q` without a field/filter** — confirmed
unreliable both ways: bare "рустехдрон" returned a false-positive single
hit (an unrelated Tyumen military-academy patent that merely *cites*
RU218475U1 in its own prior-art discussion — free text finds mentions, not
holdings), and a bare company name can also return 0 where a filter/field
query correctly finds real hits.

Session history (chronological, all inline validation before this script
existed in its current form):
- PE_RU exact-string query on Рустехдрон's full canonical name → correctly
  found all 5 of its patents/industrial designs (2 already known, 3 new:
  RU138211S, RU139388S, RU139389S).
- IN_RU query on 5 known directors (Черезов, Лапин, Костюнин, Чернышов,
  Константинов) → 4 legitimate nulls, 1 (Константинов Е.А.) re-surfaced
  the exact pre-2010 Tula-State-University false positive already
  rejected in the bulk-CSV sweep (s0952) — good cross-validation, not a
  new lead.
- `patent_holders:search` filter on "атлант-аэро" → found ООО «Атлант
  Аэро»'s first-ever IP record, RU2859152C1 (filed 2025-08-25, published
  2026-03-30 — postdates the bulk CSV dump snapshots, explaining why the
  earlier sweeps missed it). Co-inventor is the entity's own director
  (Хутешен А.А.) — clean ID match, no ambiguity.
- `patent_holders:search` filter on "гаскар" → found ООО «Гаскар
  Интеграция»'s RU191888U1 (a biometric time-tracking card, unrelated to
  UAVs but a real, previously-unknown IP record for a network entity).
- `authors:search` filter (partial surname "дзема", not full ФИО) on the
  same session → 12 total hits, 7 of which are unrelated name collisions
  (Italian pharmaceutical inventors, an unrelated 2007 CNC-machine patent,
  an unrelated 1995 fishing-device patent) — confirms partial-surname
  filters are noisier than the full-ФИО IN_RU field query; this script
  uses IN_RU with the complete fio_ru/director string, not a surname filter.

No ИНН/ОГРН on this dataset (same limitation as the bulk patent CSV) —
every hit needs a human to read patentee/title against the entity's actual
business before promoting into patents[]/people_add_entities via
corrections.json, exactly like the Константинов and «Импульс»/«Ринтеп»
(an unrelated competitor product cited as prior art in RU2859152C1's own
background section) false-positive/noise cases already worked through.

**Live network job against a third-party site — per CLAUDE.md's crawling-
jobs policy, tested inline on a handful of entities first (see above), but
the full-roster run across all 93 manufacturer-tier entities should be run
by you, not executed in the background.**

After running this, refresh the pipeline:
    python3 scripts/extract_registry.py
    python3 scripts/check_registry.py

Usage:
    python3 scripts/rospatent_searchplatform_search.py                # every manufacturer-tier entity
    python3 scripts/rospatent_searchplatform_search.py --limit 5      # first 5 only
    python3 scripts/rospatent_searchplatform_search.py --force        # re-screen even if already done today
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
sys.path.insert(0, str(REPO / "scripts"))
from id_patterns import norm  # noqa: E402

SEARCH_URL = "https://searchplatform.rospatent.gov.ru/search"
DELAY_SECONDS = 1.5

DATASETS = [
    "ru_till_1994", "ru_since_1994", "cis", "dsgn_ru", "ap", "cn", "ch",
    "au", "gb", "kr", "ca", "at", "jp", "ep", "de", "fr", "pct", "us",
    "dsgn_kr", "dsgn_cn", "dsgn_jp", "others",
]


def _base_payload() -> dict:
    return {
        "offset": 0,
        "limit": 20,
        "include_facets": 0,
        "sort": "relevance",
        "countStatistics": False,
        "datasets": DATASETS,
        "preffered_lang": "ru",
    }


def _post(payload: dict) -> dict:
    req = urllib.request.Request(
        SEARCH_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _hits_from(data: dict, method: str) -> list[dict]:
    hits = []
    for h in data.get("hits", []):
        c = h.get("common", {})
        b = h.get("biblio", {}).get("ru", {})
        hits.append({
            "method": method,
            "doc_id": h.get("id"),
            "document_number": c.get("document_number"),
            "kind": c.get("kind"),
            "publication_date": c.get("publication_date"),
            "title": b.get("title"),
            "patentee": [p.get("name") for p in b.get("patentee", []) or []],
            "inventor": [p.get("name") for p in b.get("inventor", []) or []],
        })
    return hits


def search_holder(name_substring: str) -> list[dict]:
    payload = _base_payload()
    payload["filter"] = {"patent_holders:search": {"search": name_substring}}
    return _hits_from(_post(payload), "patent_holders_filter")


def search_inventor(fio: str) -> list[dict]:
    payload = _base_payload()
    payload["q"] = f'IN_RU= "{fio}"'
    return _hits_from(_post(payload), "inventor_field_query")


def dedupe(hits: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for h in hits:
        key = h.get("doc_id")
        if key not in seen:
            seen.add(key)
            out.append(h)
    return out


def process(entities: list[dict], today: str, force: bool, limit: int | None) -> int:
    targets = [e for e in entities if e.get("tier") == "manufacturer" and e.get("name_ru")]
    if not force:
        targets = [e for e in targets if e.get("rospatent_director_screened_at") != today]
    if limit is not None:
        targets = targets[:limit]

    if not targets:
        print("nothing to do (all already screened today, use --force to re-screen)")
        return 0

    print(f"screening {len(targets)} manufacturer(s) ...")
    hit_count = 0
    for i, e in enumerate(targets, 1):
        slug = e["slug"]
        name_substring = norm(e["name_ru"])
        director = e.get("director")
        all_hits: list[dict] = []

        try:
            all_hits += search_holder(name_substring)
        except (urllib.error.URLError, TimeoutError) as ex:
            print(f"  [{i}/{len(targets)}] {slug} holder-search FAILED: {ex}")
        time.sleep(DELAY_SECONDS)

        if director:
            try:
                all_hits += search_inventor(director)
            except (urllib.error.URLError, TimeoutError) as ex:
                print(f"  [{i}/{len(targets)}] {slug} inventor-search FAILED: {ex}")
            time.sleep(DELAY_SECONDS)

        hits = dedupe(all_hits)
        e["rospatent_director_matches"] = hits
        e["rospatent_director_screened_at"] = today
        if hits:
            hit_count += 1
            print(f"  [{i}/{len(targets)}] {slug}: {len(hits)} hit(s) — REVIEW, not auto-confirmed")
            for h in hits[:5]:
                print(f"      [{h['method']}] {h['document_number']}{h['kind']} — "
                      f"{h['title']} | patentee: {h['patentee']}")
        else:
            print(f"  [{i}/{len(targets)}] {slug}: no hits")

    return hit_count


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    today = date.today().isoformat()
    entities = json.loads(ENTITIES.read_text(encoding="utf-8"))
    total_hits = process(entities, today, args.force, args.limit)
    ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nDone. {total_hits} entit(ies) with at least one candidate hit.")
    print("Every screened entity now carries rospatent_director_matches[] + rospatent_director_screened_at")
    print("(each entry tagged with its 'method': patent_holders_filter or inventor_field_query).")
    print("NO hit here is auto-confirmed -- there is no ИНН/ОГРН on this dataset to cross-check.")
    print("A human must read each patentee/title against the entity's actual business before promoting")
    print("into patents[]/people_add_entities via corrections.json. Watch for common-surname/common-word")
    print("collisions the same way Константинов Евгений Александрович hit an unrelated pre-2010 Tula State")
    print("University welding patent, and RU2859152C1 cited an unrelated competitor product («Импульс» by")
    print("«Ринтеп») as prior art, during this script's inline validation.")


if __name__ == "__main__":
    main()
