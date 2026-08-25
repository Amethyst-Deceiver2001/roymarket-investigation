#!/usr/bin/env python3
"""Screen every registry entity and person against OpenSanctions' batch
/match/default endpoint (api.opensanctions.org) — aggregates OFAC, EU, UK
OFSI, Ukraine's war-sanctions.gur.gov.ua and many more designation lists,
plus corporate-disqualification and PEP data.

Confirmed working 2026-08-24 (OPENSANCTIONS_API_KEY in .env, tested inline
against Osadchuk — returned an exact, high-confidence match reproducing this
project's own already-cited DOB/sourceUrl data).

**Quota (2026-08-25): the key is a non-commercial `journalist` grant, 150
requests/month, no expiration.** Each /match/default call below — one batch
of up to 20 records — counts as ONE request against that cap regardless of
batch size, so batching large is what makes the quota workable at all
(a full 149-entity + ~300-person sweep is ~23 requests at BATCH=20, not
450). Still, this script now refuses to run past `--budget` (default 100,
leaving headroom for the month's other usage) without `--force-budget` —
see `estimate_requests()` below. Don't raise BATCH past 20 without checking
OpenSanctions' own current limit for /match/default.

**Licensing (CC BY-NC, per OpenSanctions' 2026-08-25 reply):** quoting a
match in the published brief with attribution is fine under this key;
republishing the dataset itself, or a file derived from it, as a public
download or in a repository requires a commercial license. The archived
snapshots below land in `data/sources/`, which is gitignored — never commit
one directly, and don't fold raw OpenSanctions response bodies into any file
that IS committed (docs/index.html, data/registry/*.json already only ever
carry the hand-curated `matches[]` summary — caption/score/topics/source
URL — not the full response object; keep it that way).

**Live network job against a third-party API — per CLAUDE.md's crawling-jobs
policy, tested inline on a handful of records first (ordinary
reconnaissance), but the full-roster sweep should be run by you, not
executed in the background.**

This does NOT write into `sanctions[]` directly — that field is hand-curated
and source-verified elsewhere in this project (see CLAUDE.md's
sanctions_legal_basis convention), and an automated fuzzy match is a lead,
not a fact, per this project's standing "triage list, not a source" rule
(same discipline as mine_leads.py's output). Matches land in a SEPARATE
field, `opensanctions_matches[]`, plus `opensanctions_screened_at`, written
directly onto entities.json/people.json the same way screen_rom.py writes
`securing_measures[]` — screened data, not a hand correction, so this does
NOT go through corrections.json. A human still has to read each match and
decide whether it upgrades an entity/person's `sanctions[]` array.

Any match scoring >=0.7 (OpenSanctions' own "likely match" threshold) also
gets archived as a primary-source snapshot in data/sources/
(OPENSANCTIONS_<INN-or-slug>_<YYYYMMDD>_<slug>.json), same pattern as
ROM_*.json and EGRULAPI_*.json.

After running this, refresh the pipeline:
    python3 scripts/scan_sources.py --out data/sources/MANIFEST.md
    python3 scripts/inventory_sources.py
    python3 scripts/extract_registry.py
    python3 scripts/check_registry.py

Usage:
    python3 scripts/screen_opensanctions.py                  # everyone, skip already-screened today
    python3 scripts/screen_opensanctions.py --limit 5         # first 5 only
    python3 scripts/screen_opensanctions.py --kind people      # people only (default: both)
    python3 scripts/screen_opensanctions.py --kind entities
    python3 scripts/screen_opensanctions.py --force            # re-screen even if already done today
    python3 scripts/screen_opensanctions.py --budget 30         # cap this run's spend below the default 100
    python3 scripts/screen_opensanctions.py --force-budget      # run past --budget anyway (explicit override)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTITIES = REPO / "data" / "registry" / "entities.json"
PEOPLE = REPO / "data" / "registry" / "people.json"
SOURCES = REPO / "data" / "sources"
ENV_FILE = REPO / ".env"

API_URL = "https://api.opensanctions.org/match/default?algorithm=best"
MATCH_THRESHOLD_ARCHIVE = 0.7  # OpenSanctions' own "likely match" cutoff
DELAY_SECONDS = 0.5  # batch endpoint is generous, but still a shared service
BATCH = 20  # one /match/default call, however many records it holds, is 1 request against the monthly quota
DEFAULT_BUDGET = 100  # requests this run may spend; the key's monthly cap is 150 total


def load_api_key() -> str:
    key = os.environ.get("OPENSANCTIONS_API_KEY")
    if key:
        return key
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("OPENSANCTIONS_API_KEY="):
                return line.split("=", 1)[1].strip()
    sys.exit("OPENSANCTIONS_API_KEY not found in environment or .env")


def slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    ascii_name = re.sub(r"[^a-zA-Z0-9]+", "-", ascii_name).strip("-").lower()
    return ascii_name or "record"


def match_batch(api_key: str, queries: dict) -> dict:
    """queries: {query_id: {schema, properties}} — up to ~50 per call is safe."""
    body = json.dumps({"queries": queries}).encode("utf-8")
    req = urllib.request.Request(
        API_URL, data=body, method="POST",
        headers={
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_entity_query(e: dict) -> dict:
    props = {"name": [e["name_ru"]]}
    if e.get("name_latin"):
        props["name"].append(e["name_latin"])
    if e.get("inn"):
        props["innCode"] = [e["inn"]]
    if e.get("ogrn"):
        props["registrationNumber"] = [e["ogrn"]]
    props["country"] = ["ru"]
    return {"schema": "Company", "properties": props}


def build_person_query(p: dict) -> dict:
    name = p.get("fio_ru") or p.get("name_latin")
    if not name:
        return None
    props = {"name": [name]}
    if p.get("name_latin") and p["name_latin"] != name:
        props["name"].append(p["name_latin"])
    if p.get("dob"):
        props["birthDate"] = [p["dob"]]
    if p.get("inn_personal"):
        props["idNumber"] = [p["inn_personal"]]
    return {"schema": "Person", "properties": props}


def pending_targets(records: list, kind: str, today: str, force: bool) -> list:
    targets = []
    for r in records:
        field_screened = "opensanctions_screened_at"
        if not force and r.get(field_screened) == today:
            continue
        q = build_entity_query(r) if kind == "entities" else build_person_query(r)
        if q is None:
            continue
        targets.append((r, q))
    return targets


def requests_needed(n_targets: int) -> int:
    return (n_targets + BATCH - 1) // BATCH if n_targets else 0


def process(records: list, kind: str, api_key: str, today: str, force: bool) -> int:
    field_screened = "opensanctions_screened_at"
    field_matches = "opensanctions_matches"

    targets = pending_targets(records, kind, today, force)

    if not targets:
        print(f"  [{kind}] nothing to do (all already screened today, use --force to re-screen)")
        return 0

    print(f"  [{kind}] screening {len(targets)} record(s) in {requests_needed(len(targets))} request(s) ...")
    hit_count = 0
    for start in range(0, len(targets), BATCH):
        chunk = targets[start:start + BATCH]
        queries = {f"q{i}": q for i, (_, q) in enumerate(chunk)}
        try:
            resp = match_batch(api_key, queries)
        except urllib.error.HTTPError as ex:
            if ex.code == 429:
                body = ex.read().decode("utf-8", errors="replace")
                sys.exit(f"    batch {start}-{start+len(chunk)}: HTTP 429 — {body}\n"
                         f"    This is the monthly quota, not a burst limit — retrying won't help until "
                         f"it resets. Stopping (already-screened records from earlier batches were saved).")
            print(f"    batch {start}-{start+len(chunk)} FAILED: HTTP {ex.code}: {ex.reason}")
            time.sleep(DELAY_SECONDS)
            continue
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as ex:
            print(f"    batch {start}-{start+len(chunk)} FAILED: {ex}")
            time.sleep(DELAY_SECONDS)
            continue

        for i, (r, q) in enumerate(chunk):
            qid = f"q{i}"
            result = resp.get("responses", {}).get(qid, {})
            results = result.get("results", [])
            slug = r.get("slug") or slugify(r.get("name_ru") or r.get("fio_ru") or "record")

            matches = []
            for m in results:
                score = m.get("score", 0)
                matches.append({
                    "match_id": m.get("id"),
                    "caption": m.get("caption"),
                    "schema": m.get("schema"),
                    "score": round(score, 4),
                    "topics": (m.get("properties") or {}).get("topics", []),
                    "source_urls": (m.get("properties") or {}).get("sourceUrl", []),
                })

            r[field_matches] = matches
            r[field_screened] = today

            best = max((m["score"] for m in matches), default=0)
            if best >= MATCH_THRESHOLD_ARCHIVE:
                hit_count += 1
                inn_or_slug = r.get("inn") or r.get("inn_personal") or slug
                out = SOURCES / f"OPENSANCTIONS_{inn_or_slug}_{today.replace('-', '')}_{slug}.json"
                out.write_text(json.dumps({"query": q, "response": result}, ensure_ascii=False, indent=2),
                                encoding="utf-8")
                print(f"    *** {slug}: best score {best:.2f} — {matches[0]['caption']} — saved {out.name} ***")
            else:
                print(f"    {slug}: best score {best:.2f} (below archive threshold, still recorded)")

        time.sleep(DELAY_SECONDS)

    return hit_count


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--kind", choices=["entities", "people", "both"], default="both")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--budget", type=int, default=DEFAULT_BUDGET,
                     help=f"max /match/default requests this run may spend (default {DEFAULT_BUDGET}; "
                          "the key's monthly cap is 150 total, shared with any other use of it)")
    ap.add_argument("--force-budget", action="store_true",
                     help="run even if the estimated request count exceeds --budget")
    args = ap.parse_args()

    api_key = load_api_key()
    today = date.today().isoformat()

    entities = json.loads(ENTITIES.read_text(encoding="utf-8")) if args.kind in ("entities", "both") else []
    people = json.loads(PEOPLE.read_text(encoding="utf-8")) if args.kind in ("people", "both") else []

    entity_targets = (entities if args.limit is None else entities[:args.limit]) if entities else []
    people_targets = (people if args.limit is None else people[:args.limit]) if people else []

    n_entity_req = requests_needed(len(pending_targets(entity_targets, "entities", today, args.force))) if entity_targets else 0
    n_people_req = requests_needed(len(pending_targets(people_targets, "people", today, args.force))) if people_targets else 0
    estimated = n_entity_req + n_people_req

    print(f"Estimated requests this run: {estimated} (entities {n_entity_req} + people {n_people_req}), "
          f"budget {args.budget}, monthly cap 150.")
    if estimated > args.budget and not args.force_budget:
        sys.exit(f"Refusing to run: estimated {estimated} requests exceeds --budget {args.budget}. "
                  f"Re-run with a higher --budget or --force-budget if this is intentional, "
                  f"or narrow scope with --limit/--kind.")

    total_hits = 0

    if entity_targets:
        total_hits += process(entity_targets, "entities", api_key, today, args.force)
        ENTITIES.write_text(json.dumps(entities, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if people_targets:
        total_hits += process(people_targets, "people", api_key, today, args.force)
        PEOPLE.write_text(json.dumps(people, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"\nDone. {total_hits} record(s) with a likely match (score >= {MATCH_THRESHOLD_ARCHIVE}) archived to data/sources/.")
    print("Every screened record (hit or not) now carries opensanctions_matches[] + opensanctions_screened_at.")
    print("Re-run scripts/check_registry.py, then hand-review matches before promoting anything into sanctions[].")


if __name__ == "__main__":
    main()
