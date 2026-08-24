#!/usr/bin/env python3
"""Screen every registry entity's own product names against
war-sanctions.gur.gov.ua's *components* catalogue — GUR's teardown-level
database of foreign electronic parts identified inside specific named
russian weapon systems (distinct from screen_gur.py, which covers GUR's
sanctions/uav-companies sections).

Discovered 2026-08-24 while manually investigating a user-supplied URL
(war-sanctions.gur.gov.ua/ru/components?f[title_uk]=witem-4751) that an
earlier ad-hoc search had missed: the catalogue titles each weapon-item
entry by WEAPON PLATFORM name, not by manufacturer/brand name, so a search
for a company or brand ("Ushkuynik", "Trimiks") finds nothing even when
the entity's own PRODUCT ("Knyaz Vandal Novgorodsky") is directly listed.
That inline check confirmed one real hit — npts-ushkuynik's own flagship
UAV, with 12 components (mostly Chinese: Sigmastar, Purui Semiconductor,
Hangzhou Zhongke, CapXon; also Taiwanese/US/Swiss) — archived as s0969 and
already written into entities.json via corrections.json. A same-session
"CBTS.611000" naming coincidence was investigated and explicitly REJECTED
(Ц transliterates as "Ts", not "C" — CBTS is not ЦБСТ) — a caution that
applies here too: a component-catalogue hit is a LEAD by string match, not
an identity match. There is no ИНН/ОГРН on this catalogue to cross-check
against (GUR's components pages carry no company identifiers at all), so
every hit needs a human to read the actual component list and judge
plausibility (does the product actually sound like this entity's product,
not a coincidental word overlap) — same discipline as the free-text
`search()` in screen_gur.py, just without even an ID field to lean on.

**Live network job against a third-party site — per CLAUDE.md's crawling-
jobs policy, tested inline on a handful of product names first (ordinary
reconnaissance — see the docstring above), but the full-roster sweep
across all ~235 product/brand names in the registry should be run by you,
not executed in the background.**

Query strategy: for each entity, build query strings from
`name_latin`/`brand_latin` (used directly) and `name_ru`/`brand_ru`
(transliterated via a standard practical GOST/BGN-style table, since GUR's
weapon-item titles are in English/transliterated Latin, not Cyrillic).
Cyrillic quote marks and parenthetical asides are stripped first. Queries
shorter than 4 characters are skipped (too generic — the Armament-field
substring search returns noise on short strings, as seen with "Molniya"/
"Orlan"/"Zala"/"Eleron"/"Supercam" all hitting *other* manufacturers'
well-known platforms during the inline check, confirmed NOT in this
registry's own product list).

For each search hit, this script does NOT auto-confirm a match — it has
no identifier to check against. It writes every hit's Armament title(s)
into `gur_components_matches[]` on the entity as a raw candidate for a
human to read, plus `gur_components_screened_at`. A human then decides
whether to pull the full component list (same pattern as the
npts-ushkuynik/CBTS pulls this session) and promote into
`foreign_components[]` via corrections.json — or reject it as a name
collision, same as the Orlan/Zala/Eleron/Supercam/Molniya false leads.

Any promoted hit's component-listing page should be archived to
data/sources/GUR_<inn-or-slug>_<date>_<slug>-components.html (or, for an
unattributed weapon item like "Delta (CBTS.611000)", with the ИНН segment
dropped per the no-ИНН-to-key-on naming convention).

After running this, refresh the pipeline:
    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
    python3 scripts/inventory_sources.py
    python3 scripts/extract_registry.py
    python3 scripts/check_registry.py

Usage:
    python3 scripts/screen_gur_components.py                # everyone, skip already-screened today
    python3 scripts/screen_gur_components.py --limit 5       # first 5 entities only
    python3 scripts/screen_gur_components.py --force         # re-screen even if already done today
"""
from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"

BASE = "https://war-sanctions.gur.gov.ua"
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
DELAY_SECONDS = 1.5

# Practical GOST/BGN-style Cyrillic -> Latin table. NOT the ГОСТ 7.79 machine
# standard (that produces less readable strings) -- close to how these product
# names actually appear transliterated in press/GUR text, which is what we're
# trying to match against. Multi-char sequences first.
TRANSLIT = [
    ("щ", "shch"), ("ш", "sh"), ("ч", "ch"), ("ц", "ts"), ("ю", "yu"),
    ("я", "ya"), ("ж", "zh"), ("х", "kh"), ("э", "e"),
    ("а", "a"), ("б", "b"), ("в", "v"), ("г", "g"), ("д", "d"), ("е", "e"),
    ("ё", "yo"), ("з", "z"), ("и", "i"), ("й", "y"), ("к", "k"), ("л", "l"),
    ("м", "m"), ("н", "n"), ("о", "o"), ("п", "p"), ("р", "r"), ("с", "s"),
    ("т", "t"), ("у", "u"), ("ф", "f"), ("ъ", ""), ("ы", "y"), ("ь", ""),
]


def transliterate(text: str) -> str:
    out = text.lower()
    for cyr, lat in TRANSLIT:
        out = out.replace(cyr, lat)
    return out


def clean_name(name: str) -> str:
    name = re.sub(r"[«»\"]", "", name)
    name = re.sub(r"\([^)]*\)", "", name)  # drop parenthetical asides
    return name.strip()


# Words that produced confirmed false positives on the 2026-08-24 full-roster
# sweep (16 candidate hits, ALL 16 rejected on review) -- generic English/
# Russian loanwords common across defense-industry vocabulary, or short words
# that happen to also name a real but unrelated GUR-catalogued platform.
# Skipping these outright avoids re-walking the same reviewed dead ends on
# every future re-run as new products get added to the registry.
STOPWORDS = {
    "technologies", "group", "signal", "radar", "antenna", "izdelie",
    "dron", "simple", "prime", "lite", "start", "orient", "moto",
    "programma", "orion", "forpost", "knyaz", "azar", "tower",
    "sistema", "sistemy", "system", "systems", "modul", "module",
}


def build_queries(name: str) -> list[str]:
    """One query per significant word, not the whole phrase -- GUR's search
    is a literal substring match on the Armament title, and multi-word
    transliterations routinely differ by a letter or two from GUR's own
    spelling (e.g. our "novgorodskiy" vs GUR's "Novgorodsky"), which silently
    breaks a whole-phrase match. Confirmed via inline test 2026-08-24: the
    known-good npts-ushkuynik hit returned nothing on the full transliterated
    name and only appeared once queried word-by-word."""
    name = clean_name(name)
    if not name:
        return []
    if re.search(r"[а-яё]", name, re.IGNORECASE):
        name = transliterate(name)
    words = [w.strip() for w in re.split(r"[\s\-/]+", name) if len(w.strip()) >= 4]
    return [w for w in words if w.lower() not in STOPWORDS and not w.isdigit()]


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def search(query: str) -> tuple[int, list[str]]:
    """Returns (total_count, list of distinct Armament titles on page 1)."""
    url = f"{BASE}/en/components?{urllib.parse.urlencode({'f[search]': query})}"
    html = fetch(url)
    total_m = re.search(r"Total:\s*(\d+)", html)
    total = int(total_m.group(1)) if total_m else 0
    if total == 0:
        return 0, []
    titles = re.findall(
        r'<div class="text-white">Armament</div>\s*<div class="yellow">([^<]+)</div>', html
    )
    return total, list(dict.fromkeys(t.strip() for t in titles))


def collect_queries(entities: list[dict]) -> dict[str, list[tuple[str, str]]]:
    """slug -> list of (query, original_name)"""
    out: dict[str, list[tuple[str, str]]] = {}
    for e in entities:
        pairs = []
        seen_q = set()
        candidates = []
        if e.get("brand_latin"):
            candidates.append(e["brand_latin"])
        if e.get("brand_ru"):
            candidates.append(e["brand_ru"])
        for p in e.get("products", []) or []:
            if isinstance(p, str):
                candidates.append(p)
            elif isinstance(p, dict):
                if p.get("name_latin"):
                    candidates.append(p["name_latin"])
                elif p.get("name_ru"):
                    candidates.append(p["name_ru"])
        for c in candidates:
            for q in build_queries(c):
                if q not in seen_q:
                    seen_q.add(q)
                    pairs.append((q, c))
        if pairs:
            out[e["slug"]] = pairs
    return out


def process(entities: list[dict], today: str, force: bool, limit: int | None) -> int:
    by_slug = {e["slug"]: e for e in entities}
    queries = collect_queries(entities)
    slugs = list(queries.keys())
    if not force:
        slugs = [s for s in slugs if by_slug[s].get("gur_components_screened_at") != today]
    if limit is not None:
        slugs = slugs[:limit]

    if not slugs:
        print("nothing to do (all already screened today, use --force to re-screen)")
        return 0

    print(f"screening {len(slugs)} entit(ies), {sum(len(queries[s]) for s in slugs)} quer(ies) total ...")
    hit_count = 0
    for i, slug in enumerate(slugs, 1):
        e = by_slug[slug]
        matches = []
        for query, original in queries[slug]:
            try:
                total, titles = search(query)
            except (urllib.error.URLError, TimeoutError) as ex:
                print(f"  [{i}/{len(slugs)}] {slug} query '{query}' FAILED: {ex}")
                time.sleep(DELAY_SECONDS)
                continue
            if total:
                matches.append({
                    "query": query,
                    "matched_product": original,
                    "total_components": total,
                    "armament_titles": titles,
                })
            time.sleep(DELAY_SECONDS)

        e["gur_components_matches"] = matches
        e["gur_components_screened_at"] = today
        if matches:
            hit_count += 1
            print(f"  [{i}/{len(slugs)}] {slug}: {len(matches)} candidate hit(s) — REVIEW, not auto-confirmed")
            for m in matches:
                print(f"      '{m['query']}' -> {m['total_components']} component(s), armament: {m['armament_titles']}")
        else:
            print(f"  [{i}/{len(slugs)}] {slug}: no hits ({len(queries[slug])} queries)")

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
    print("Every screened entity now carries gur_components_matches[] + gur_components_screened_at.")
    print("NO hit here is auto-confirmed -- there is no ИНН/ОГРН on GUR's components pages to cross-check.")
    print("A human must read each armament title against the entity's actual product before pulling the")
    print("full component list and promoting into foreign_components[] via corrections.json. Watch for")
    print("generic-word false positives the same way 'Molniya'/'Orlan'/'Zala'/'Eleron'/'Supercam' hit other,")
    print("unrelated manufacturers' well-known platforms during this script's inline validation.")


if __name__ == "__main__":
    main()
